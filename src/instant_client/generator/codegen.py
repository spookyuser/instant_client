from __future__ import annotations

from pathlib import Path
from typing import Any

import inflection
from jinja2 import Environment, FileSystemLoader
from slugify import slugify

SAFE_IDENT_REGEX = r"[^0-9A-Za-z_]+"


def to_snake(name: str) -> str:
    s = name.lstrip("$")
    s = inflection.underscore(s)
    s = slugify(
        s, separator="_", lowercase=True, regex_pattern=SAFE_IDENT_REGEX, allow_unicode=False
    )
    if s and s[0].isdigit():
        s = "_" + s
    return s


def to_class_name(entity: str) -> str:
    base = entity.lstrip("$")
    base = inflection.singularize(base)
    snake = to_snake(base)
    return inflection.camelize(snake, uppercase_first_letter=True)


def _py_type(attr: dict[str, Any]) -> str:
    dt = attr.get("checked-data-type")
    if not dt:
        inferred = attr.get("inferred-types")
        dt = inferred[0] if isinstance(inferred, list) and inferred else None
    if dt == "string":
        return "str"
    if dt == "number":
        return "float"
    if dt in ("integer", "int"):
        return "int"
    if dt in ("boolean", "bool"):
        return "bool"
    if dt == "date":
        return "datetime"
    if dt == "json":
        return "Any"
    return "Any"


def _required(attr: dict[str, Any]) -> bool:
    return bool(attr.get("required?"))


def _norm_entities(blobs: dict[str, Any]) -> list[dict[str, Any]]:
    ents: list[dict[str, Any]] = []
    for ename, fields in blobs.items():
        if not isinstance(fields, dict):
            continue
        attrs: list[dict[str, Any]] = []
        for fname, meta in fields.items():
            if not isinstance(meta, dict):
                continue
            if meta.get("value-type") == "ref":
                continue
            attrs.append(
                {
                    "name": fname,
                    "py_name": to_snake(fname),
                    "py_type": _py_type(meta),
                    "required": _required(meta),
                }
            )
        ents.append(
            {
                "name": ename,
                "py_name": to_snake(ename),
                "class_name": to_class_name(ename),
                "attrs": attrs,
            }
        )
    return ents


def _norm_relations(refs: dict[str, Any]) -> list[dict[str, Any]]:
    rels: list[dict[str, Any]] = []
    for _, r in refs.items():
        if not isinstance(r, dict):
            continue
        fwd = r.get("forward-identity") or [None, None, None]
        rev = r.get("reverse-identity") or [None, None, None]
        from_entity = fwd[1]
        fwd_name = fwd[2]
        to_entity = rev[1]
        rev_name = rev[2]
        cardinality = r.get("cardinality")
        rels.append(
            {
                "from_entity": from_entity,
                "to_entity": to_entity,
                "fwd_name": fwd_name,
                "rev_name": rev_name,
                "fwd_py": to_snake(fwd_name) if isinstance(fwd_name, str) else None,
                "rev_py": to_snake(rev_name) if isinstance(rev_name, str) else None,
                "cardinality": cardinality,
                "required": bool(r.get("required?")),
            }
        )
    return rels


def _merge_relations(entities: list[dict[str, Any]], rels: list[dict[str, Any]]) -> None:
    by = {e["name"]: e for e in entities}
    for r in rels:
        fe = by.get(r["from_entity"])
        te = by.get(r["to_entity"])
        if not fe or not te:
            continue
        fe.setdefault("relations", []).append(
            {
                "name": r["fwd_name"],
                "py_name": r["fwd_py"],
                "target_class": to_class_name(r["to_entity"]),
                "cardinality": r["cardinality"],
                "required": r["required"],
            }
        )
        te.setdefault("relations", []).append(
            {
                "name": r["rev_name"],
                "py_name": r["rev_py"],
                "target_class": to_class_name(r["from_entity"]),
                "cardinality": "many" if r["cardinality"] == "one" else "one",
                "required": False,
            }
        )


def _derive_create_update_where(entities: list[dict[str, Any]]) -> None:
    for e in entities:
        attrs = e.get("attrs", [])
        rels = e.get("relations", [])
        one_refs = [r for r in rels if r["cardinality"] == "one" and r["name"]]

        create_fields: list[dict[str, Any]] = []
        update_fields: list[dict[str, Any]] = []
        where_fields: list[dict[str, Any]] = []

        for a in attrs:
            create_fields.append(
                {"py_name": a["py_name"], "py_type": a["py_type"], "required": a["required"]}
            )
            update_fields.append(
                {"py_name": a["py_name"], "py_type": a["py_type"], "required": False}
            )
            if a["py_type"] in ("str", "float", "datetime"):
                where_fields.append({"py_name": a["py_name"], "py_type": a["py_type"]})

        for r in one_refs:
            field_name = f"{to_snake(r['name'])}"
            create_fields.append(
                {"py_name": field_name, "py_type": "str", "required": bool(r["required"])}
            )
            update_fields.append({"py_name": field_name, "py_type": "str", "required": False})

        e["create_fields"] = create_fields
        e["update_fields"] = update_fields
        e["where_fields"] = where_fields
        e["expand_alias"] = f"{e['class_name']}ExpandKey" if rels else None
        e["expand_keys"] = [r["py_name"] for r in rels if r.get("py_name")]
        # Keys allowed for link(...) kwargs: one-to-one forward relations only
        e["link_keys"] = [
            r["py_name"] for r in rels if r.get("py_name") and r["cardinality"] == "one"
        ]


def generate_from_api_schema(schema: dict[str, Any], out_dir: Path) -> None:
    blobs = schema.get("blobs", {}) or {}
    refs = schema.get("refs", {}) or {}
    entities = _norm_entities(blobs)
    rels = _norm_relations(refs)
    _merge_relations(entities, rels)
    _derive_create_update_where(entities)

    # Get the directory containing this file to locate templates
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)

    models = env.get_template("models.py.j2").render(entities=entities)
    client = env.get_template("client.py.j2").render(entities=entities)
    initpy = env.get_template("__init__.py.j2").render()

    (out_dir / "models.py").write_text(models, encoding="utf-8")
    (out_dir / "client.py").write_text(client, encoding="utf-8")
    (out_dir / "__init__.py").write_text(initpy, encoding="utf-8")
