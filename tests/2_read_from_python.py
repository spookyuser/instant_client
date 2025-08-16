import json
import os
from typing import Any, cast

import pytest
from generated_instant_client import Client
from generated_instant_client.models import PostExpandSpec


def load_expected() -> dict[str, Any]:
    expected_path = os.path.join(os.path.dirname(__file__), ".snapshots", "expected.json")
    with open(expected_path, encoding="utf8") as f:
        return json.load(f)


async def read_post_by_id(post_id: str) -> dict[str, Any] | None:
    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)
    expand_spec: PostExpandSpec = {"comments": {"author": {}, "post": {}}, "author": {}, "tags": {}}
    posts = await db.posts.find(where={"id": post_id}, expand=expand_spec)
    return posts[0].model_dump(mode="json") if posts else None


@pytest.mark.asyncio
async def test_python_reads_expected_graph() -> None:
    expected = load_expected()
    post_id: str = expected["postId"]

    # Fetch from Instant via Python client
    actual = await read_post_by_id(post_id)
    assert actual is not None, "Post not found"

    # Basic fields
    assert actual["id"] == expected["postId"]
    assert actual["title"] == expected["title"]
    assert actual["status"] == expected["status"]

    # Author link
    author = actual.get("author") or []
    assert len(author) == 1
    assert author[0]["id"] == expected["profileId"]

    # Tags link
    tag_ids = [t["id"] for t in (actual.get("tags") or [])]
    assert expected["tagId1"] in tag_ids
    assert expected["tagId2"] in tag_ids

    # Comments link
    comments = actual.get("comments") or []
    assert len(comments) == 1
    assert comments[0]["body"] == expected["commentBody"]
    comment_author = comments[0].get("author") or []
    assert len(comment_author) == 1
    assert comment_author[0]["id"] == expected["profileId"]


@pytest.mark.asyncio
async def test_read_post_no_expand_raw() -> None:
    expected = load_expected()
    post_id: str = expected["postId"]

    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)
    # No expand, return raw dicts to avoid strict validation on nested ids
    raw: list[dict[str, Any]] = cast(
        list[dict[str, Any]], await db.posts.find(where={"id": post_id}, validate=False)
    )
    assert len(raw) == 1
    doc = raw[0]
    assert doc["id"] == expected["postId"]
    assert doc["title"] == expected["title"]


@pytest.mark.asyncio
async def test_expand_author_only() -> None:
    expected = load_expected()
    post_id: str = expected["postId"]

    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)
    posts = await db.posts.find(where={"id": post_id}, expand={"author": {}})
    assert len(posts) == 1
    p = posts[0].model_dump(mode="json")
    author = p.get("author") or []
    assert len(author) == 1
    assert author[0]["id"] == expected["profileId"]


@pytest.mark.asyncio
async def test_expand_tags_only() -> None:
    expected = load_expected()
    post_id: str = expected["postId"]

    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)
    posts = await db.posts.find(where={"id": post_id}, expand={"tags": {}})
    assert len(posts) == 1
    p = posts[0].model_dump(mode="json")
    tag_ids = [t["id"] for t in (p.get("tags") or [])]
    assert expected["tagId1"] in tag_ids
    assert expected["tagId2"] in tag_ids


@pytest.mark.asyncio
async def test_expand_comments_with_nested_author_and_post() -> None:
    expected = load_expected()
    post_id: str = expected["postId"]

    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)
    posts = await db.posts.find(
        where={"id": post_id},
        expand={"comments": {"author": {}, "post": {}}},
    )
    assert len(posts) == 1
    p = posts[0].model_dump(mode="json")
    comments = p.get("comments") or []
    assert len(comments) == 1
    assert comments[0]["body"] == expected["commentBody"]
    assert (comments[0].get("author") or [])[0]["id"] == expected["profileId"]
    # The nested post inside each comment should be fully expanded now
    assert (comments[0].get("post") or [])[0]["id"] == expected["postId"]


@pytest.mark.asyncio
async def test_expand_with_string_paths() -> None:
    expected = load_expected()
    post_id: str = expected["postId"]

    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)
    posts = await db.posts.find(
        where={"id": post_id},
        expand=["author", "comments.author", "comments.post", "tags"],
    )
    assert len(posts) == 1
    p = posts[0].model_dump(mode="json")
    assert (p.get("author") or [])[0]["id"] == expected["profileId"]
    tag_ids = [t["id"] for t in (p.get("tags") or [])]
    assert expected["tagId1"] in tag_ids and expected["tagId2"] in tag_ids
    comments = p.get("comments") or []
    assert len(comments) == 1
    assert (comments[0].get("author") or [])[0]["id"] == expected["profileId"]
    assert (comments[0].get("post") or [])[0]["id"] == expected["postId"]
