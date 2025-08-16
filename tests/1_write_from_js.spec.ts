import { describe, it, expect, beforeAll } from "bun:test";
import { $ } from "bun";
import { faker } from "@faker-js/faker";
import { init, id } from "@instantdb/admin";
import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const APP_ID = process.env.INSTANT_APP_ID;
const ADMIN_TOKEN = process.env.INSTANT_ADMIN_TOKEN;

if (!APP_ID || !ADMIN_TOKEN) {
  throw new Error(
    "Missing INSTANT_APP_ID or INSTANT_ADMIN_TOKEN in environment."
  );
}

const db = init({
  appId: APP_ID,
  adminToken: ADMIN_TOKEN,
});

beforeAll(async () => {
  const res = await $`bun run instant-cli push schema -y`.text();
});

describe("InstantDB seed and read with Faker", () => {
  it("creates linked data and reads it back", async () => {
    // IDs
    const userId = id();
    const profileId = id();
    const postId = id();
    const commentId = id();
    const tagId1 = id();
    const tagId2 = id();

    // Data
    const email = faker.internet.email();
    const bio = faker.lorem.sentence();
    const avatar_url = faker.image.url();

    const title = faker.lorem.sentence();
    const body = faker.lorem.paragraph();
    const status: "draft" | "published" = "published";
    const published_at = new Date().toISOString();
    const metadata = { source: "test", seed: faker.string.uuid() } as const;

    const tagName1 = `tag-${faker.string.alphanumeric({ length: 8 })}`;
    const tagName2 = `tag-${faker.string.alphanumeric({ length: 8 })}`;

    const commentBody = faker.lorem.sentence();
    const created_at = new Date().toISOString();

    // Create entities and links
    await db.transact([
      // Base entities
      db.tx.$users[userId].update({ email }),
      db.tx.profiles[profileId].update({ bio, avatar_url }),
      db.tx.tags[tagId1].update({ name: tagName1 }),
      db.tx.tags[tagId2].update({ name: tagName2 }),
      db.tx.posts[postId].update({
        title,
        body,
        status,
        published_at,
        metadata,
      }),
      db.tx.comments[commentId].update({ body: commentBody, created_at }),

      // Links
      db.tx.profiles[profileId].link({ $user: userId }),
      db.tx.posts[postId].link({ author: profileId, tags: [tagId1, tagId2] }),
      db.tx.comments[commentId].link({ post: postId, author: profileId }),
    ]);

    // Write expectations for Python test into snapshot
    const snapshotsDir = join(process.cwd(), "tests", ".snapshots");
    mkdirSync(snapshotsDir, { recursive: true });
    const expectedPath = join(snapshotsDir, "expected.json");
    const expected = {
      userId,
      profileId,
      postId,
      commentId,
      tagId1,
      tagId2,
      email,
      bio,
      avatar_url,
      title,
      body,
      status,
      published_at,
      metadata,
      tagName1,
      tagName2,
      commentBody,
      created_at,
    } as const;
    writeFileSync(expectedPath, JSON.stringify(expected, null, 2), "utf8");

    // Read back the graph around the post
    const data = await db.query({
      posts: {
        $: { where: { id: postId } },
        author: {},
        tags: {},
        comments: { author: {} },
      },
    });

    const posts = data.posts as any[];
    expect(posts.length).toBe(1);
    const p = posts[0];

    // Post basics
    expect(p.id).toBe(postId);
    expect(p.title).toBe(title);
    expect(p.status).toBe(status);

    // Author link

    expect(p.author[0]?.id).toBe(profileId);

    // Tags link
    const tagIds = (p.tags ?? []).map((t: any) => t.id);
    expect(tagIds).toContain(tagId1);
    expect(tagIds).toContain(tagId2);

    // Comments link
    expect((p.comments ?? []).length).toBe(1);
    expect(p.comments[0].author[0]?.id).toBe(profileId);
    expect(p.comments[0].body).toBe(commentBody);
  });
});
