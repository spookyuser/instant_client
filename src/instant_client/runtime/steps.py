from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass
class Step:
    """Base class for InstantDB transaction steps."""

    def to_list(self) -> list[Any]:
        raise NotImplementedError


@dataclass
class Update(Step):
    collection: str
    id: str | None
    data: Mapping[str, Any]

    def to_list(self) -> list[Any]:
        return ["update", self.collection, self.id, dict(self.data)]


@dataclass
class Merge(Step):
    collection: str
    id: str
    data: Mapping[str, Any]

    def to_list(self) -> list[Any]:
        return ["merge", self.collection, self.id, dict(self.data)]


@dataclass
class Delete(Step):
    collection: str
    id: str

    def to_list(self) -> list[Any]:
        return ["delete", self.collection, self.id]


@dataclass
class Link(Step):
    collection: str
    id: str
    links: Mapping[str, str | list[str]]

    def to_list(self) -> list[Any]:
        return ["link", self.collection, self.id, dict(self.links)]


@dataclass
class Unlink(Step):
    collection: str
    id: str
    links: Mapping[str, str | list[str]]

    def to_list(self) -> list[Any]:
        return ["unlink", self.collection, self.id, dict(self.links)]


def parse_step(raw: Sequence[Any]) -> Step:
    """Parse a raw step (list form) into a typed Step instance.

    Accepts typical InstantDB step formats like:
    - ["update", collection, id_or_none, data]
    - ["merge", collection, id, data]
    - ["delete", collection, id]
    - ["link", collection, id, links]
    - ["unlink", collection, id, links]
    """
    if not raw or not isinstance(raw, (list, tuple)):
        raise ValueError("Step must be a non-empty list or tuple")

    kind = raw[0]
    if kind == "update":
        if len(raw) != 4:
            raise ValueError(
                "update step must have 4 elements: ['update', collection, id|None, data]"
            )
        _, collection, identifier, data = raw
        if not isinstance(collection, str):
            raise ValueError("update collection must be a string")
        if not isinstance(data, Mapping):
            raise ValueError("update data must be a mapping")
        if identifier is not None and not isinstance(identifier, str):
            raise ValueError("update id must be a string or None")
        return Update(collection, identifier, data)

    if kind == "merge":
        if len(raw) != 4:
            raise ValueError("merge step must have 4 elements: ['merge', collection, id, data]")
        _, collection, identifier, data = raw
        if not isinstance(collection, str) or not isinstance(identifier, str):
            raise ValueError("merge collection and id must be strings")
        if not isinstance(data, Mapping):
            raise ValueError("merge data must be a mapping")
        return Merge(collection, identifier, data)

    if kind == "delete":
        if len(raw) != 3:
            raise ValueError("delete step must have 3 elements: ['delete', collection, id]")
        _, collection, identifier = raw
        if not isinstance(collection, str) or not isinstance(identifier, str):
            raise ValueError("delete collection and id must be strings")
        return Delete(collection, identifier)

    if kind == "link":
        if len(raw) != 4:
            raise ValueError("link step must have 4 elements: ['link', collection, id, links]")
        _, collection, identifier, links = raw
        if not isinstance(collection, str) or not isinstance(identifier, str):
            raise ValueError("link collection and id must be strings")
        if not isinstance(links, Mapping):
            raise ValueError("link links must be a mapping")
        return Link(collection, identifier, links)  # type: ignore[arg-type]

    if kind == "unlink":
        if len(raw) != 4:
            raise ValueError("unlink step must have 4 elements: ['unlink', collection, id, links]")
        _, collection, identifier, links = raw
        if not isinstance(collection, str) or not isinstance(identifier, str):
            raise ValueError("unlink collection and id must be strings")
        if not isinstance(links, Mapping):
            raise ValueError("unlink links must be a mapping")
        return Unlink(collection, identifier, links)  # type: ignore[arg-type]

    raise ValueError(f"Unknown step kind: {kind}")
