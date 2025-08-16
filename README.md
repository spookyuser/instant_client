## instant-client

Typed, async Python client generator for InstantDB. You bring your own schema (from your Instant app), and this tool generates a strongly-typed Python client that you can commit to your repo or regenerate on demand. It also ships a minimal runtime. I just wanted something that i can do mutations with in python with some type safety and these are the first steps toward that. Also it was mostly 78 shotted with gpt-5.

### How it works

- **API-first generation**: The CLI fetches your app schema from Instant and renders a typed Python client using Jinja templates. You control when to regenerate, commit the output if you like, and keep generation independent from distribution.
  - Generator: `src/instant_client/generator/codegen.py`
  - Templates: `src/instant_client/generator/templates/*.j2`
  - Runtime: `src/instant_client/runtime/*`
- **Generated output**: Written to `src/generated_instant_client/` (do not edit by hand or do i'm not your boss).
- **Type-safe expand**: You can expand relations via dotted paths or a typed dict. Relations are normalized so nested references are always lists with `{ id }` at minimum.
- **Operations provided** per entity: `find`, `create`, `update`, `delete`, and `link`.

### Install



```bash
uv add git+https://github.com/spookyuser/instant_client
```

### Prerequisites

- Python 3.11+ with `uv` installed
- Bun (for JS tests and schema push)
- An Instant sandbox app (App ID + Admin Token)

### Create a sandbox app (recommended for first-time users)

1. In the Instant dashboard, create a new app.
2. Copy the App ID and Admin Token.
3. Export environment variables:

```bash
export INSTANT_APP_ID=your_app_id
export INSTANT_ADMIN_TOKEN=your_admin_token
# optional, defaults to https://api.instantdb.com
# export INSTANT_BASE_URL=https://api.instantdb.com
```

### Push the sample schema to your sandbox

This repo includes `instant.schema.ts` and `instant.perms.ts`. Push them to your sandbox app:

```bash
bun run instant-cli push schema -y
```

### Generate a client from your own schema

```bash
# if installed with uv
uv run instant generate

# or if installed in your current environment
instant generate
```

This writes the client into `src/generated_instant_client/`. Regenerate whenever your schema changes.

Optional flags (future-friendly):

- `--out-dir`: customize output directory (default: `src/generated_instant_client`)
- `--base-url`: override API base (default: env `INSTANT_BASE_URL` or `https://api.instantdb.com`)
- `--app-id`, `--admin-token`: override env vars

### Use the generated client

```python
import asyncio
from generated_instant_client import Client

async def main():
    client = Client(app_id="...", admin_token="...", timeout=30.0, max_retries=1)
    posts = await client.posts.find(where={"status": "published"}, expand=["author", "comments.author"])
    print(posts)

asyncio.run(main())
```

Typed expand (dict form):

```python
from generated_instant_client.models import PostExpandSpec

expand_spec: PostExpandSpec = {"author": {}, "comments": {"author": {}}}
posts = await client.posts.find(expand=expand_spec)
```

see [example](examples/demo.py)

### Optional: end-to-end test flow (JS ↔ Python)

The tests perform this flow:

1. JS writes seeded data and saves IDs into `tests/.snapshots/expected.json`.
2. Python reads the JS-written graph and asserts shape.
3. Python writes a new comment and saves it to `tests/.snapshots/expected_py.json`.
4. JS reads the Python-written comment and asserts links.

Run everything:

```bash
bun -q ./test_flow.ts
```

Or step-by-step:

```bash
# 0) Ensure client is generated
uv run instant

# 1) JS write
bun test ./tests/1_write_from_js.spec.ts

# 2) Python read
uv run pytest -q ./tests/2_read_from_python.py

# 3) Python write
uv run pytest -q ./tests/3_write_from_python.py

# 4) JS read
bun test ./tests/4_read_from_js.spec.ts
```
