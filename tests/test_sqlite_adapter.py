"""Tiny edge-case tests for `adapters.database.sqlite.SqliteDatabase`.

Locks in:
  - constructing with a malformed URL raises ValueError immediately,
  - `put_pages([])` is a no-op (defensive guard, called by the assign-prefixes
    loop when nothing changed).
"""

from __future__ import annotations

import pytest

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase


def test_constructor_rejects_unrecognised_url() -> None:
    with pytest.raises(ValueError, match="unrecognised SQLite URL"):
        SqliteDatabase("postgres://nope")


@pytest.mark.asyncio
async def test_put_pages_empty_list_is_noop(tmp_path) -> None:
    """`put_pages([])` must not crash and must not require a connection —
    short-circuits before touching the cursor."""
    db = SqliteDatabase(f"sqlite:///{(tmp_path / 's.db').as_posix()}")
    await db.initialize()
    # Should NOT raise.
    await db.put_pages([])
    await db.close()
