from __future__ import annotations

from sweepito.doctor import Check, passed


def test_passed_only_considers_required_checks() -> None:
    assert passed([Check("a", True, ""), Check("b", False, "", required=False)])
    assert not passed([Check("a", False, "", required=True)])
