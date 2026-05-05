"""Lock in `adapters.storage.filesystem.FilesystemStorage` edge cases.

Locks in:
  - put/get round-trips bytes,
  - exists() reflects put + delete,
  - delete on a missing key is a no-op (idempotent),
  - list_prefix on a non-existent prefix yields nothing,
  - list_prefix walks recursively and returns rel-from-root keys,
  - presign_put / presign_get return /cdn/<key> URLs,
  - keys that try to escape the data root via .. components are rejected.
"""

from __future__ import annotations

import pytest

from pd_prep_for_pgdp.adapters.storage.filesystem import FilesystemStorage


@pytest.fixture
def storage(tmp_path) -> FilesystemStorage:
    return FilesystemStorage(root=tmp_path / "data")


@pytest.mark.asyncio
async def test_put_get_roundtrips_bytes(storage: FilesystemStorage) -> None:
    await storage.put_bytes("a/b/c.txt", b"hello")
    assert await storage.get_bytes("a/b/c.txt") == b"hello"
    assert await storage.exists("a/b/c.txt") is True


@pytest.mark.asyncio
async def test_delete_is_idempotent_on_missing_key(storage: FilesystemStorage) -> None:
    # Should NOT raise.
    await storage.delete("nope/nothing.txt")
    # And the real delete still works after.
    await storage.put_bytes("k", b"x")
    await storage.delete("k")
    assert await storage.exists("k") is False


@pytest.mark.asyncio
async def test_list_prefix_yields_nothing_for_unknown_prefix(storage: FilesystemStorage) -> None:
    out = [obj async for obj in storage.list_prefix("does/not/exist/")]
    assert out == []


@pytest.mark.asyncio
async def test_list_prefix_walks_recursively(storage: FilesystemStorage) -> None:
    await storage.put_bytes("p/a/x.txt", b"x")
    await storage.put_bytes("p/a/b/y.txt", b"y")
    await storage.put_bytes("q/z.txt", b"z")  # outside the prefix

    keys = sorted([obj.key async for obj in storage.list_prefix("p/")])
    assert keys == ["p/a/b/y.txt", "p/a/x.txt"]


@pytest.mark.asyncio
async def test_presign_returns_cdn_url(storage: FilesystemStorage) -> None:
    put_url = await storage.presign_put("projects/a/source.zip", "application/zip")
    get_url = await storage.presign_get("projects/a/source.zip")
    assert put_url == "/cdn/projects/a/source.zip"
    assert get_url == "/cdn/projects/a/source.zip"


@pytest.mark.asyncio
async def test_path_traversal_rejected(storage: FilesystemStorage) -> None:
    with pytest.raises(ValueError, match="escapes data root"):
        await storage.put_bytes("../escape.txt", b"x")
    with pytest.raises(ValueError, match="escapes data root"):
        await storage.get_bytes("../etc/passwd")
    with pytest.raises(ValueError, match="escapes data root"):
        await storage.exists("../../../shadow")
