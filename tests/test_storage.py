from src.storage import StoredPost, PostStorage, eligible_posts


def test_eligible_posts_requires_three_items(tmp_path):
    storage = PostStorage(tmp_path / "posts.json")
    posts = [StoredPost(message_id=1, kind="text", file_id=None, text="a")]
    storage.save(posts)
    assert eligible_posts(storage.load()) == []


def test_eligible_posts_skips_edges():
    posts = [
        StoredPost(message_id=1, kind="text", file_id=None, text="first"),
        StoredPost(message_id=2, kind="text", file_id=None, text="second"),
        StoredPost(message_id=3, kind="text", file_id=None, text="third"),
        StoredPost(message_id=4, kind="text", file_id=None, text="fourth"),
    ]
    assert eligible_posts(posts) == posts[1:-1]


def test_storage_upsert_overwrites(tmp_path):
    storage = PostStorage(tmp_path / "posts.json")
    storage.upsert(StoredPost(message_id=2, kind="text", file_id=None, text="old"))
    updated = storage.upsert(StoredPost(message_id=2, kind="text", file_id=None, text="new"))
    assert updated[0].text == "new"
