"""Exception hierarchy. Each error maps to a process exit code."""

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_UNEXPECTED = 3
EXIT_REFUSED = 4
EXIT_INTERRUPTED = 130


class SweepitoError(Exception):
    exit_code = EXIT_UNEXPECTED


class ConfigError(SweepitoError):
    """Invalid configuration or command line usage."""

    exit_code = EXIT_USAGE


class SafetyRefusal(SweepitoError):
    """A safety gate refused the requested operation."""

    exit_code = EXIT_REFUSED


class GitError(SweepitoError):
    """Git is missing or a git command failed."""

    exit_code = EXIT_UNEXPECTED
