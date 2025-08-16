from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict


class Comment(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    created_at: datetime
    likes: float | None = None
    sentiment: str | None = None
    body: str
    # relations
    post: list[Post] | None = None
    author: list[Profile] | None = None


class CommentCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    created_at: datetime
    likes: float | None = None
    sentiment: str | None = None
    body: str
    post: str | None = None
    author: str | None = None


class CommentUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    created_at: datetime | None = None
    likes: float | None = None
    sentiment: str | None = None
    body: str | None = None
    post: str | None = None
    author: str | None = None


class CommentWhere(TypedDict, total=False):
    id: str
    created_at: datetime
    likes: float
    sentiment: str
    body: str


CommentExpandKey = Literal["post", "author"]


class CommentExpandSpec(TypedDict, total=False):
    post: PostExpandSpec
    author: ProfileExpandSpec


CommentLinkKey = Literal["post", "author"]


class Profile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    # relations
    user: list[User] | None = None
    authored_posts: list[Post] | None = None
    authored_comments: list[Comment] | None = None


class ProfileCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    user: str | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    user: str | None = None


class ProfileWhere(TypedDict, total=False):
    id: str
    bio: str
    avatar_url: str


ProfileExpandKey = Literal["user", "authored_posts", "authored_comments"]


class ProfileExpandSpec(TypedDict, total=False):
    user: UserExpandSpec
    authored_posts: PostExpandSpec
    authored_comments: CommentExpandSpec


ProfileLinkKey = Literal["user"]


class Tag(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    name: str
    # relations
    posts: list[Post] | None = None


class TagCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    name: str
    posts: str | None = None


class TagUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    name: str | None = None
    posts: str | None = None


class TagWhere(TypedDict, total=False):
    id: str
    name: str


TagExpandKey = Literal["posts"]


class TagExpandSpec(TypedDict, total=False):
    posts: PostExpandSpec


TagLinkKey = Literal["posts"]


class Post(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: str
    metadata: Any | None = None
    body: str | None = None
    id: str | None = None
    published_at: datetime | None = None
    title: str
    # relations
    tags: list[Tag] | None = None
    comments: list[Comment] | None = None
    author: list[Profile] | None = None


class PostCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: str
    metadata: Any | None = None
    body: str | None = None
    id: str | None = None
    published_at: datetime | None = None
    title: str
    author: str | None = None


class PostUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: str | None = None
    metadata: Any | None = None
    body: str | None = None
    id: str | None = None
    published_at: datetime | None = None
    title: str | None = None
    author: str | None = None


class PostWhere(TypedDict, total=False):
    status: str
    body: str
    id: str
    published_at: datetime
    title: str


PostExpandKey = Literal["tags", "comments", "author"]


class PostExpandSpec(TypedDict, total=False):
    tags: TagExpandSpec
    comments: CommentExpandSpec
    author: ProfileExpandSpec


PostLinkKey = Literal["author"]


class File(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    path: str
    url: str


class FileCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    path: str
    url: str


class FileUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str | None = None
    path: str | None = None
    url: str | None = None


class FileWhere(TypedDict, total=False):
    id: str
    path: str
    url: str


class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    email: str | None = None
    id: str | None = None
    # relations
    profile: list[Profile] | None = None


class UserCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    email: str | None = None
    id: str | None = None


class UserUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    email: str | None = None
    id: str | None = None


class UserWhere(TypedDict, total=False):
    email: str
    id: str


UserExpandKey = Literal["profile"]


class UserExpandSpec(TypedDict, total=False):
    profile: ProfileExpandSpec


Comment.model_rebuild()
Profile.model_rebuild()
Tag.model_rebuild()
Post.model_rebuild()
File.model_rebuild()
User.model_rebuild()
