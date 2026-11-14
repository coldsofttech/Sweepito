from __future__ import annotations

import pytest

from sweepito import errors


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (errors.SweepitoError, errors.EXIT_UNEXPECTED),
        (errors.ConfigError, errors.EXIT_USAGE),
        (errors.SafetyRefusal, errors.EXIT_REFUSED),
        (errors.GitError, errors.EXIT_UNEXPECTED),
    ],
)
def test_each_error_maps_to_its_exit_code(
    error: type[errors.SweepitoError], code: int
) -> None:
    assert error.exit_code == code


@pytest.mark.parametrize(
    "error", [errors.ConfigError, errors.SafetyRefusal, errors.GitError]
)
def test_specific_errors_are_sweepito_errors(error: type[Exception]) -> None:
    assert issubclass(error, errors.SweepitoError)
    with pytest.raises(errors.SweepitoError, match="boom"):
        raise error("boom")


def test_exit_codes_are_distinct_where_the_cli_relies_on_it() -> None:
    codes = {
        errors.EXIT_OK,
        errors.EXIT_FAILED,
        errors.EXIT_USAGE,
        errors.EXIT_UNEXPECTED,
        errors.EXIT_REFUSED,
        errors.EXIT_INTERRUPTED,
    }
    assert len(codes) == 6
    assert errors.EXIT_OK == 0
