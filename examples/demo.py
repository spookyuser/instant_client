import os
from datetime import datetime, timezone

from generated_instant_client import Client
from generated_instant_client.models import (
    CommentCreate,
    PostCreate,
    PostExpandSpec,
    ProfileCreate,
    TagCreate,
    UserCreate,
)


async def main() -> None:
    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)

    # -- CREATE typed entities -------------------------------------------------
    user_id = await db.users.create(UserCreate(email="demo@example.com"))
    profile_id = await db.profiles.create(
        ProfileCreate(bio="Demo bio", avatar_url="https://picsum.photos/200")
    )
    await db.profiles.link(profile_id, user=user_id)

    post_id = await db.posts.create(
        PostCreate(
            title="Hello Instant",
            status="published",
            body="This is a demo post",
            published_at=datetime.now(timezone.utc),
            author=profile_id,
        )
    )

    tag1_id = await db.tags.create(TagCreate(name="demo"))
    tag2_id = await db.tags.create(TagCreate(name="python"))
    await db.tags.link(tag1_id, posts=post_id)
    await db.tags.link(tag2_id, posts=post_id)

    comment_id = await db.comments.create(
        CommentCreate(
            body="Nice post!",
            created_at=datetime.now(timezone.utc),
            post=post_id,
            author=profile_id,
        )
    )

    # -- READ with type-safe expand ------------------------------------------
    expand_spec: PostExpandSpec = {"author": {}, "tags": {}, "comments": {"author": {}, "post": {}}}
    posts = await db.posts.find(where={"id": post_id}, expand=expand_spec)
    print("Post count:", len(posts))
    if posts:
        p = posts[0]
        print("Post:", p.title, p.status)
        print("Author profile:", p.author[0].id if p.author else None)
        print("Tags:", [t.name for t in (p.tags or [])])
        print("Comments:", [c.body for c in (p.comments or [])])

    # Optional cleanup example
    # await db.comments.delete(comment_id)
    # await db.posts.delete(post_id)
    # await db.tags.delete(tag1_id)
    # await db.tags.delete(tag2_id)
    # await db.profiles.delete(profile_id)
    # await db.users.delete(user_id)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
