/**
 * @see https://www.instantdb.com/docs/modeling-data.md
 */
import { i } from "@instantdb/core";

const _schema = i.schema({
  // @https://www.instantdb.com/docs/modeling-data.md
  entities: {
    $files: i.entity({
      path: i.string().unique().indexed(),
      url: i.string(),
    }),
    $users: i.entity({
      email: i.string().unique().indexed().optional(),
    }),

    profiles: i.entity({
      bio: i.string().optional(),
      avatar_url: i.string().optional(),
    }),

    posts: i.entity({
      title: i.string(),
      body: i.string().optional(),
      status: i.string<"draft" | "published">(),
      published_at: i.date().optional(),
      metadata: i.json().optional(),
    }),

    comments: i.entity({
      body: i.string(),
      created_at: i.date(),
      sentiment: i.string<"pos" | "neu" | "neg">().optional(),
      likes: i.number().optional(),
    }),

    tags: i.entity({
      name: i.string().unique().indexed(),
    }),
  },
  links: {
    // posts.author <=> profiles.authoredPosts
    postAuthor: {
      forward: { on: "posts", has: "one", label: "author" },
      reverse: { on: "profiles", has: "many", label: "authoredPosts" },
    },
    // comments.post <=> posts.comments
    commentPost: {
      forward: { on: "comments", has: "one", label: "post" },
      reverse: { on: "posts", has: "many", label: "comments" },
    },
    // comments.author <=> profiles.authoredComments
    commentAuthor: {
      forward: { on: "comments", has: "one", label: "author" },
      reverse: { on: "profiles", has: "many", label: "authoredComments" },
    },
    // posts.tags <=> tags.posts (many-to-many)
    postsTags: {
      forward: { on: "posts", has: "many", label: "tags" },
      reverse: { on: "tags", has: "many", label: "posts" },
    },
    // profiles.$user <=> $users.profile (one-to-one)
    profileUser: {
      forward: { on: "profiles", has: "one", label: "$user" },
      reverse: { on: "$users", has: "one", label: "profile" },
    },
  },
  rooms: {},
});

// This helps Typescript display nicer intellisense
type _AppSchema = typeof _schema;
interface AppSchema extends _AppSchema {}
const schema: AppSchema = _schema;

export type { AppSchema };
export default schema;
