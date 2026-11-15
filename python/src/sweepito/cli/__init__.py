"""Command line interface: a thin wrapper over :mod:`sweepito.api`."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    from sweepito.cli.parser import build_parser as _build_parser

    return _build_parser()


def main(argv: list[str] | None = None) -> int:
    from sweepito.cli.entry import main as _main

    return _main(argv)
