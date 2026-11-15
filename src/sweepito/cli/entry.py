"""Entry point: parse arguments, dispatch the command, map errors to exit codes."""

from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    from sweepito.cli.helpers import stderr_console
    from sweepito.cli.parser import build_parser
    from sweepito.errors import (
        EXIT_INTERRUPTED,
        EXIT_UNEXPECTED,
        EXIT_USAGE,
        SweepitoError,
    )
    from sweepito.ui import error, warning

    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return EXIT_USAGE
    try:
        code: int = args.func(args)
        return code
    except SweepitoError as exc:
        error(stderr_console(args), str(exc))
        return exc.exit_code
    except KeyboardInterrupt:
        warning(stderr_console(args), "sweepito: interrupted")
        return EXIT_INTERRUPTED
    except Exception as exc:  # noqa: BLE001 - last-resort handler
        error(stderr_console(args), f"unexpected error: {exc!r}")
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
