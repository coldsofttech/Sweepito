"""Link detection used by the planner and executor."""

from __future__ import annotations

import stat
from types import SimpleNamespace

from sweepito.planner import is_link


def test_is_link_recognises_symlinks_and_reparse_points() -> None:
    plain_dir = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x10)
    symlink = SimpleNamespace(st_mode=stat.S_IFLNK)
    # CPython 3.11 reports a junction as a plain directory with the reparse bit set.
    junction = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x10 | 0x400)
    posix_dir = SimpleNamespace(st_mode=stat.S_IFDIR)
    assert is_link(symlink)
    assert is_link(junction)
    assert not is_link(plain_dir)
    assert not is_link(posix_dir)
