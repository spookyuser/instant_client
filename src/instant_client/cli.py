from __future__ import annotations

import os
import pathlib

import httpx
import typer

from .generator.codegen import generate_from_api_schema
from .runtime import endpoints as ep

app = typer.Typer(add_completion=False)


def _echo(s: str) -> None:
    typer.echo(s)


@app.command("generate")
def generate(
    app_id: str = typer.Option(os.getenv("INSTANT_APP_ID"), help="Instant App ID"),
    admin_token: str = typer.Option(os.getenv("INSTANT_ADMIN_TOKEN"), help="Admin token (Bearer)"),
    base_url: str = typer.Option(
        os.getenv("INSTANT_BASE_URL", "https://api.instantdb.com"), help="Base API URL"
    ),
    out_dir: str = typer.Option("src/generated_instant_client"),
) -> None:
    if not app_id or not admin_token:
        typer.secho("Missing app_id or admin_token", fg=typer.colors.RED)
        raise typer.Exit(2)

    schema_url = f"{base_url.rstrip('/')}{ep.schema(app_id)}"
    _echo(f"Fetching schema: {schema_url}")
    with httpx.Client(timeout=30.0, headers={"Authorization": f"Bearer {admin_token}"}) as client:
        r = client.get(schema_url)
        r.raise_for_status()
        payload = r.json()

    schema = payload.get("schema")
    if not isinstance(schema, dict):
        typer.secho("Unexpected schema shape", fg=typer.colors.RED)
        raise typer.Exit(2)

    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _echo("Generating client...")
    # import json

    # schema_json_path = out / "schema.json"
    # with open(schema_json_path, "w", encoding="utf-8") as f:
    # json.dump(schema, f, indent=2, ensure_ascii=False)
    generate_from_api_schema(schema, out)

    try:
        import subprocess
        import sys

        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", out_dir, "--quiet"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    typer.secho(f"✅ Client generated in {out_dir}", fg=typer.colors.GREEN)
