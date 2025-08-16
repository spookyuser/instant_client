from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, overload

from pydantic import BaseModel

from instant_client.runtime.core import AsyncClient

from .models import *

# Auto-generated relations map: entity name -> {relation_field: target_class_name}
RELATIONS_MAP: dict[str, dict[str, str]] = {
    "comments": {"post": "Post", "author": "Profile"},
    "profiles": {"user": "User", "authored_posts": "Post", "authored_comments": "Comment"},
    "tags": {"posts": "Post"},
    "posts": {"tags": "Tag", "comments": "Comment", "author": "Profile"},
    "$files": {},
    "$users": {"profile": "Profile"},
}


def _normalize_relations(obj: dict[str, Any], entity_name: str) -> None:
    rels = RELATIONS_MAP.get(entity_name) or {}
    for field_name, target_class in rels.items():
        if field_name not in obj:
            continue
        value = obj[field_name]
        if value is None:
            continue
        # One relations may arrive as a single id; expanded relations always as lists
        if isinstance(value, str):
            obj[field_name] = [{"id": value}]
            continue
        if isinstance(value, dict):
            # Be tolerant: treat as single expanded object
            value = [value]
        if isinstance(value, list):
            normalized_list: list[dict[str, Any]] = []
            for item in value:
                if isinstance(item, str):
                    normalized_list.append({"id": item})
                elif isinstance(item, dict):
                    # Recurse into nested relations for the target entity
                    _normalize_relations(item, _entity_name_from_class(target_class))
                    normalized_list.append(item)
                else:
                    # Unknown type; attempt best-effort cast to dict
                    normalized_list.append({"id": item})
            obj[field_name] = normalized_list


_CLASS_TO_ENTITY: dict[str, str] = {
    "Comment": "comments",
    "Profile": "profiles",
    "Tag": "tags",
    "Post": "posts",
    "File": "$files",
    "User": "$users",
}


def _entity_name_from_class(class_name: str) -> str:
    return _CLASS_TO_ENTITY.get(class_name, class_name)


@dataclass
class _EntityService:
    name: str
    client: AsyncClient
    model: type[BaseModel]
    expand_keys: frozenset[str]
    relations_spec: dict[str, str]

    def _shape(
        self, where: Mapping[str, Any] | None, expand: Sequence[str] | dict[str, Any] | None
    ) -> dict[str, Any]:
        shape: dict[str, Any] = {self.name: {}}
        if where:
            shape[self.name]["$"] = {"where": where}
        if expand:
            root = shape[self.name]

            def add_path(path: str) -> None:
                if not isinstance(path, str) or not path:
                    return
                segments = path.split(".")
                first = segments[0]
                if first not in self.expand_keys:
                    raise ValueError(f"Illegal expand key {first} for {self.name}")
                node = root.setdefault(first, {})
                target_class = self.relations_spec.get(first)
                current_entity = _entity_name_from_class(target_class) if target_class else None
                for seg in segments[1:]:
                    if not current_entity:
                        raise ValueError(
                            f"Cannot expand '{path}': unknown relation after '{first}'"
                        )
                    rels = RELATIONS_MAP.get(current_entity, {})
                    if seg not in rels:
                        raise ValueError(
                            f"Illegal nested expand '{seg}' under '{current_entity}' in '{path}'"
                        )
                    node = node.setdefault(seg, {})
                    current_entity = _entity_name_from_class(rels[seg])

            def add_spec(spec: dict[str, Any], entity: str, parent: dict[str, Any]) -> None:
                rels = RELATIONS_MAP.get(entity, {})
                for k, v in spec.items():
                    if k not in rels:
                        raise ValueError(f"Illegal expand key {k} for {entity}")
                    child_node = parent.setdefault(k, {})
                    next_entity = _entity_name_from_class(rels[k])
                    if isinstance(v, dict) and next_entity:
                        add_spec(v, next_entity, child_node)

            if isinstance(expand, dict):
                add_spec(expand, self.name, root)
            else:
                for path in expand:
                    add_path(path)
        return shape

    def build_shape(
        self,
        *,
        where: Mapping[str, Any] | None = None,
        expand: Sequence[str] | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._shape(where, expand)

    async def _create(self, payload: dict[str, Any]) -> str:
        new_id = payload.get("id") or str(uuid.uuid4())
        payload["id"] = new_id
        tx = [["update", self.name, new_id, payload]]
        resp = await self.client.transact(tx)
        return (resp.get("ids") or [new_id])[0]

    async def _update(self, id: str, payload: dict[str, Any]) -> None:
        tx = [["update", self.name, id, payload]]
        await self.client.transact(tx)

    async def _delete(self, id: str) -> None:
        tx = [["delete", self.name, id]]
        await self.client.transact(tx)

    async def _link(self, id: str, edge: dict[str, str]) -> None:
        tx = [["link", self.name, id, edge]]
        await self.client.transact(tx)


class CommentService(_EntityService):
    @overload
    async def find(
        self,
        *,
        where: CommentWhere | None = None,
        expand: CommentExpandSpec,
        validate: bool = True,
    ) -> list[Comment]: ...

    @overload
    async def find(
        self,
        *,
        where: CommentWhere | None = None,
        expand: list[CommentExpandKey | str] | None = None,
        validate: bool = True,
    ) -> list[Comment]: ...
    async def find(
        self,
        *,
        where: CommentWhere | None = None,
        expand: list[CommentExpandKey | str] | CommentExpandSpec | None = None,
        validate: bool = True,
    ) -> list[Comment]:
        shape = self._shape(where, expand)
        data = (await self.client.query(shape)).get(self.name, [])
        if validate:
            for x in data:
                if isinstance(x, dict):
                    _normalize_relations(x, self.name)
        return [self.model.model_validate(x) for x in data] if validate else data  # type: ignore[return-value]

    async def create(self, data: CommentCreate) -> str:
        payload = data.model_dump(mode="json", exclude_none=True)
        return await self._create(payload)

    async def update(self, id: str, data: CommentUpdate) -> None:
        payload = data.model_dump(mode="json", exclude_none=True)
        await self._update(id, payload)

    async def delete(self, id: str) -> None:
        await self._delete(id)

    async def link(self, id: str, *, post: str | None = None, author: str | None = None) -> None:
        edge: dict[str, str] = {}
        if post is not None:
            edge["post"] = post
        if author is not None:
            edge["author"] = author
        if len(edge) != 1:
            raise ValueError("link() requires exactly one relation keyword argument for comments")
        await self._link(id, edge)


class ProfileService(_EntityService):
    @overload
    async def find(
        self,
        *,
        where: ProfileWhere | None = None,
        expand: ProfileExpandSpec,
        validate: bool = True,
    ) -> list[Profile]: ...

    @overload
    async def find(
        self,
        *,
        where: ProfileWhere | None = None,
        expand: list[ProfileExpandKey | str] | None = None,
        validate: bool = True,
    ) -> list[Profile]: ...
    async def find(
        self,
        *,
        where: ProfileWhere | None = None,
        expand: list[ProfileExpandKey | str] | ProfileExpandSpec | None = None,
        validate: bool = True,
    ) -> list[Profile]:
        shape = self._shape(where, expand)
        data = (await self.client.query(shape)).get(self.name, [])
        if validate:
            for x in data:
                if isinstance(x, dict):
                    _normalize_relations(x, self.name)
        return [self.model.model_validate(x) for x in data] if validate else data  # type: ignore[return-value]

    async def create(self, data: ProfileCreate) -> str:
        payload = data.model_dump(mode="json", exclude_none=True)
        return await self._create(payload)

    async def update(self, id: str, data: ProfileUpdate) -> None:
        payload = data.model_dump(mode="json", exclude_none=True)
        await self._update(id, payload)

    async def delete(self, id: str) -> None:
        await self._delete(id)

    async def link(self, id: str, *, user: str | None = None) -> None:
        edge: dict[str, str] = {}
        if user is not None:
            edge["user"] = user
        if len(edge) != 1:
            raise ValueError("link() requires exactly one relation keyword argument for profiles")
        await self._link(id, edge)


class TagService(_EntityService):
    @overload
    async def find(
        self,
        *,
        where: TagWhere | None = None,
        expand: TagExpandSpec,
        validate: bool = True,
    ) -> list[Tag]: ...

    @overload
    async def find(
        self,
        *,
        where: TagWhere | None = None,
        expand: list[TagExpandKey | str] | None = None,
        validate: bool = True,
    ) -> list[Tag]: ...
    async def find(
        self,
        *,
        where: TagWhere | None = None,
        expand: list[TagExpandKey | str] | TagExpandSpec | None = None,
        validate: bool = True,
    ) -> list[Tag]:
        shape = self._shape(where, expand)
        data = (await self.client.query(shape)).get(self.name, [])
        if validate:
            for x in data:
                if isinstance(x, dict):
                    _normalize_relations(x, self.name)
        return [self.model.model_validate(x) for x in data] if validate else data  # type: ignore[return-value]

    async def create(self, data: TagCreate) -> str:
        payload = data.model_dump(mode="json", exclude_none=True)
        return await self._create(payload)

    async def update(self, id: str, data: TagUpdate) -> None:
        payload = data.model_dump(mode="json", exclude_none=True)
        await self._update(id, payload)

    async def delete(self, id: str) -> None:
        await self._delete(id)

    async def link(self, id: str, *, posts: str | None = None) -> None:
        edge: dict[str, str] = {}
        if posts is not None:
            edge["posts"] = posts
        if len(edge) != 1:
            raise ValueError("link() requires exactly one relation keyword argument for tags")
        await self._link(id, edge)


class PostService(_EntityService):
    @overload
    async def find(
        self,
        *,
        where: PostWhere | None = None,
        expand: PostExpandSpec,
        validate: bool = True,
    ) -> list[Post]: ...

    @overload
    async def find(
        self,
        *,
        where: PostWhere | None = None,
        expand: list[PostExpandKey | str] | None = None,
        validate: bool = True,
    ) -> list[Post]: ...
    async def find(
        self,
        *,
        where: PostWhere | None = None,
        expand: list[PostExpandKey | str] | PostExpandSpec | None = None,
        validate: bool = True,
    ) -> list[Post]:
        shape = self._shape(where, expand)
        data = (await self.client.query(shape)).get(self.name, [])
        if validate:
            for x in data:
                if isinstance(x, dict):
                    _normalize_relations(x, self.name)
        return [self.model.model_validate(x) for x in data] if validate else data  # type: ignore[return-value]

    async def create(self, data: PostCreate) -> str:
        payload = data.model_dump(mode="json", exclude_none=True)
        return await self._create(payload)

    async def update(self, id: str, data: PostUpdate) -> None:
        payload = data.model_dump(mode="json", exclude_none=True)
        await self._update(id, payload)

    async def delete(self, id: str) -> None:
        await self._delete(id)

    async def link(self, id: str, *, author: str | None = None) -> None:
        edge: dict[str, str] = {}
        if author is not None:
            edge["author"] = author
        if len(edge) != 1:
            raise ValueError("link() requires exactly one relation keyword argument for posts")
        await self._link(id, edge)


class FileService(_EntityService):
    async def find(
        self,
        *,
        where: FileWhere | None = None,
        expand: list[str] | dict[str, Any] | None = None,
        validate: bool = True,
    ) -> list[File]:
        shape = self._shape(where, expand)
        data = (await self.client.query(shape)).get(self.name, [])
        if validate:
            for x in data:
                if isinstance(x, dict):
                    _normalize_relations(x, self.name)
        return [self.model.model_validate(x) for x in data] if validate else data  # type: ignore[return-value]

    async def create(self, data: FileCreate) -> str:
        payload = data.model_dump(mode="json", exclude_none=True)
        return await self._create(payload)

    async def update(self, id: str, data: FileUpdate) -> None:
        payload = data.model_dump(mode="json", exclude_none=True)
        await self._update(id, payload)

    async def delete(self, id: str) -> None:
        await self._delete(id)


class UserService(_EntityService):
    @overload
    async def find(
        self,
        *,
        where: UserWhere | None = None,
        expand: UserExpandSpec,
        validate: bool = True,
    ) -> list[User]: ...

    @overload
    async def find(
        self,
        *,
        where: UserWhere | None = None,
        expand: list[UserExpandKey | str] | None = None,
        validate: bool = True,
    ) -> list[User]: ...
    async def find(
        self,
        *,
        where: UserWhere | None = None,
        expand: list[UserExpandKey | str] | UserExpandSpec | None = None,
        validate: bool = True,
    ) -> list[User]:
        shape = self._shape(where, expand)
        data = (await self.client.query(shape)).get(self.name, [])
        if validate:
            for x in data:
                if isinstance(x, dict):
                    _normalize_relations(x, self.name)
        return [self.model.model_validate(x) for x in data] if validate else data  # type: ignore[return-value]

    async def create(self, data: UserCreate) -> str:
        payload = data.model_dump(mode="json", exclude_none=True)
        return await self._create(payload)

    async def update(self, id: str, data: UserUpdate) -> None:
        payload = data.model_dump(mode="json", exclude_none=True)
        await self._update(id, payload)

    async def delete(self, id: str) -> None:
        await self._delete(id)


class Client(AsyncClient):
    def __init__(
        self,
        app_id: str,
        admin_token: str,
        *,
        base_url: str = "https://api.instantdb.com",
        timeout: float = 30.0,
        max_retries: int = 0,
        backoff_factor: float = 0.5,
    ):
        super().__init__(
            app_id,
            admin_token,
            base_url,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
        self.comments = CommentService(
            "comments",
            self,
            Comment,
            frozenset({"post", "author"}),
            RELATIONS_MAP.get("comments", {}),
        )
        self.profiles = ProfileService(
            "profiles",
            self,
            Profile,
            frozenset({"user", "authored_posts", "authored_comments"}),
            RELATIONS_MAP.get("profiles", {}),
        )
        self.tags = TagService(
            "tags",
            self,
            Tag,
            frozenset({"posts"}),
            RELATIONS_MAP.get("tags", {}),
        )
        self.posts = PostService(
            "posts",
            self,
            Post,
            frozenset({"tags", "comments", "author"}),
            RELATIONS_MAP.get("posts", {}),
        )
        self.files = FileService(
            "$files",
            self,
            File,
            frozenset(()),
            RELATIONS_MAP.get("$files", {}),
        )
        self.users = UserService(
            "$users",
            self,
            User,
            frozenset({"profile"}),
            RELATIONS_MAP.get("$users", {}),
        )
