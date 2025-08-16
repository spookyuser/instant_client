import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from generated_instant_client import Client
from generated_instant_client.models import CommentCreate


def _snapshots_dir() -> str:
    path = os.path.join(os.path.dirname(__file__), ".snapshots")
    os.makedirs(path, exist_ok=True)
    return path


def load_expected() -> dict:
    path = os.path.join(_snapshots_dir(), "expected.json")
    with open(path, encoding="utf8") as f:
        return json.load(f)


def write_expected_py(payload: dict) -> None:
    path = os.path.join(_snapshots_dir(), "expected_py.json")
    with open(path, "w", encoding="utf8") as f:
        json.dump(payload, f, indent=2)


@pytest.mark.asyncio
async def test_python_writes_new_comment() -> None:
    expected = load_expected()

    app_id = os.environ["INSTANT_APP_ID"]
    admin_token = os.environ["INSTANT_ADMIN_TOKEN"]
    db = Client(app_id=app_id, admin_token=admin_token)

    # Create a new comment using the typed client models
    body = f"py-write-{uuid4()}"
    created_at = datetime.now(timezone.utc)
    new_comment_id = await db.comments.create(CommentCreate(body=body, created_at=created_at))

    # Link comment to the post and author written by JS in test 1
    await db.comments.link(new_comment_id, post=expected["postId"])  # type: ignore[arg-type]
    await db.comments.link(new_comment_id, author=expected["profileId"])  # type: ignore[arg-type]

    # Persist for JS read verification
    write_expected_py(
        {
            "newCommentId": new_comment_id,
            "newCommentBody": body,
        }
    )
