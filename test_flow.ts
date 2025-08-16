import { $ } from "bun";

// 0. Create client
await $`uv run instant`;

// 1. test js
await $`bun test ./tests/1_write_from_js.spec.ts`;

// 2. test py read
await $`uv run pytest -q ./tests/2_read_from_python.py`;

// 3. test py write
await $`uv run pytest -q ./tests/3_write_from_python.py`;

// 4. read from js
await $`bun test ./tests/4_read_from_js.spec.ts`;
