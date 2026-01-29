import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


@dataclass
class StoredPost:
    message_id: int
    kind: str
    file_id: str | None
    text: str | None


class PostStorage:
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def load(self) -> List[StoredPost]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return [StoredPost(**item) for item in raw]

    def save(self, posts: List[StoredPost]) -> None:
        payload = [asdict(post) for post in posts]
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def upsert(self, post: StoredPost) -> List[StoredPost]:
        posts = self.load()
        existing = {item.message_id: item for item in posts}
        existing[post.message_id] = post
        updated = sorted(existing.values(), key=lambda item: item.message_id)
        self.save(updated)
        return updated


def eligible_posts(posts: List[StoredPost]) -> List[StoredPost]:
    if len(posts) < 3:
        return posts
    return posts[1:-1]
