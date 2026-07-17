# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt
"""Behavioral tests for the unrecognized command-line option contract.

PYLINT-001 maps to the E0015 diagnostic verification nodes.
PYLINT-002 maps to the traceback-free error handling verification nodes.
PYLINT-003 maps to the option rejection verification nodes.
PYLINT-004 maps to the non-zero exit status verification nodes.
PYLINT-005 maps to the recognized-option behavior preservation verification node.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch

from pylint.lint.pylinter import PyLinter
from pylint.testutils._run import _Run as Run

EMPTY_MODULE = Path(__file__).parent / ".." / "regrtest_data" / "empty.py"


@pytest.fixture()
def unrecognized_option_result(
    unsupported_option: str, capsys: CaptureFixture
) -> tuple[pytest.ExceptionInfo[SystemExit], str, str]:
    """Invoke Pylint with an unsupported option and capture its rejection."""
    with pytest.raises(SystemExit) as exc_info:
        Run([str(EMPTY_MODULE), unsupported_option], exit=False)
    output = capsys.readouterr()
    return exc_info, output.out, output.err


@pytest.fixture(params=["-Q", "--unknown-option=yes"], ids=["short", "long"])
def unsupported_option(request: pytest.FixtureRequest) -> str:
    """Supply both command-line spellings covered by the contract."""
    return request.param


def test_pylint_001_processing_unrecognized_option_emits_e0015_identifying_option(
    unsupported_option: str,
    unrecognized_option_result: tuple[pytest.ExceptionInfo[SystemExit], str, str],
) -> None:
    """PYLINT-001: An unsupported option produces its identifying E0015 diagnostic."""
    _, stdout, _ = unrecognized_option_result
    option_name = unsupported_option.lstrip("-")
    assert f"E0015: Unrecognized option found: {option_name}" in stdout


def test_pylint_002_processing_unrecognized_option_has_no_traceback_or_uncaught_error(
    unrecognized_option_result: tuple[pytest.ExceptionInfo[SystemExit], str, str],
) -> None:
    """PYLINT-002: An unsupported option exposes no traceback or uncaught error."""
    _, stdout, stderr = unrecognized_option_result
    combined_output = stdout + stderr
    assert "Traceback (most recent call last)" not in combined_output
    assert "_UnrecognizedOptionError" not in combined_output


def test_pylint_003_processing_unrecognized_option_rejects_instead_of_accepting(
    unsupported_option: str, monkeypatch: MonkeyPatch
) -> None:
    """PYLINT-003: An unsupported option is rejected, not accepted or ignored."""

    def fail_if_linting_continues(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Pylint continued to lint after an unsupported option")

    monkeypatch.setattr(PyLinter, "check", fail_if_linting_continues)
    with pytest.raises(SystemExit):
        Run([str(EMPTY_MODULE), unsupported_option], exit=False)


def test_pylint_004_processing_unrecognized_option_exits_with_nonzero_status(
    unrecognized_option_result: tuple[pytest.ExceptionInfo[SystemExit], str, str],
) -> None:
    """PYLINT-004: An invocation with an unsupported option exits non-zero."""
    exc_info, _, _ = unrecognized_option_result
    assert exc_info.value.code != 0


def test_pylint_005_processing_only_recognized_options_preserves_observable_behavior(
    capsys: CaptureFixture,
) -> None:
    """PYLINT-005: Recognized-only invocations retain observable behavior."""
    run = Run([str(EMPTY_MODULE), "--reports=no"], exit=False)
    assert run.linter.config.reports is False

    with pytest.raises(SystemExit) as exc_info:
        Run([str(EMPTY_MODULE), "--reports=no"])
    assert exc_info.value.code == 0

    output = capsys.readouterr()
    assert "E0015: Unrecognized option found" not in output.out
    assert "Traceback (most recent call last)" not in output.err
