import { describe, it, expect } from "bun:test";
import { init } from "@instantdb/admin";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const APP_ID = process.env.INSTANT_APP_ID;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_TOKEN;

const db = init({ appId: APP_ID!, adminToken: ADMIN_TOKEN! });

function loadExpected() {
  const p = join(process.cwd(), "tests", ".snapshots", "expected.json");
  return JSON.parse(readFileSync(p, "utf8"));
}

function loadExpectedPy() {
  const p = join(process.cwd(), "tests", ".snapshots", "expected_py.json");
  return JSON.parse(readFileSync(p, "utf8"));
}

describe("JS reads data written by Python", () => {
  it("reads post graph and includes the Python-written comment", async () => {
    if (!APP_ID || !ADMIN_TOKEN) {
      throw new Error(
        "Missing INSTANT_APP_ID or INSTANT_ADMIN_TOKEN in environment."
      );
    }

    const expected = loadExpected();
    const expectedPy = loadExpectedPy();

    const data = await db.query({
      posts: {
        $: { where: { id: expected.postId } },
        comments: { author: {}, post: {} },
        author: {},
        tags: {},
      },
    });

    const posts = data.posts as any[];
    expect(posts.length).toBe(1);
    const p = posts[0];

    expect(p.id).toBe(expected.postId);
    expect(p.title).toBe(expected.title);

    const comments: any[] = p.comments ?? [];
    const found = comments.find(
      (c: any) =>
        c.id === expectedPy.newCommentId || c.body === expectedPy.newCommentBody
    );
    expect(Boolean(found)).toBe(true);
    expect(found.post?.[0]?.id).toBe(expected.postId);
    expect(found.author?.[0]?.id).toBe(expected.profileId);
  });
});
