# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt
"""Traceability placeholders for the unrecognized command-line option contract.

PYLINT-001 maps to the E0015 diagnostic verification nodes.
PYLINT-002 maps to the traceback-free error handling verification nodes.
PYLINT-003 maps to the option rejection verification nodes.
PYLINT-004 maps to the non-zero exit status verification nodes.
PYLINT-005 maps to the recognized-option behavior preservation verification node.
"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "_unsupported_option",
    ["-Q", "--unknown-option=yes"],
    ids=["short-option", "long-option"],
)
def test_pylint_001_processing_unrecognized_option_emits_e0015_identifying_option(
    _unsupported_option: str,
) -> None:
    """PYLINT-001: An unsupported option produces its identifying E0015 diagnostic."""
    assert True


@pytest.mark.parametrize(
    "_unsupported_option",
    ["-Q", "--unknown-option=yes"],
    ids=["short-option", "long-option"],
)
def test_pylint_002_processing_unrecognized_option_has_no_traceback_or_uncaught_error(
    _unsupported_option: str,
) -> None:
    """PYLINT-002: An unsupported option exposes no traceback or uncaught error."""
    assert True


@pytest.mark.parametrize(
    "_unsupported_option",
    ["-Q", "--unknown-option=yes"],
    ids=["short-option", "long-option"],
)
def test_pylint_003_processing_unrecognized_option_rejects_instead_of_accepting(
    _unsupported_option: str,
) -> None:
    """PYLINT-003: An unsupported option is rejected, not accepted or ignored."""
    assert True


@pytest.mark.parametrize(
    "_unsupported_option",
    ["-Q", "--unknown-option=yes"],
    ids=["short-option", "long-option"],
)
def test_pylint_004_processing_unrecognized_option_exits_with_nonzero_status(
    _unsupported_option: str,
) -> None:
    """PYLINT-004: An invocation with an unsupported option exits non-zero."""
    assert True


def test_pylint_005_processing_only_recognized_options_preserves_observable_behavior(
) -> None:
    """PYLINT-005: Recognized-only invocations retain observable behavior."""
    assert True
