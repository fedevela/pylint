# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

"""Tests for Han characters in the configured function regex."""

import re
from pathlib import Path

from pytest import CaptureFixture

from pylint.config.argument import _regexp_with_han_transformer
from pylint.testutils._run import _Run as Run


FUNCTION_RGX = r"[\p{Han}a-z_][\p{Han}a-z0-9_]{2,30}$"
NON_HAN_FUNCTION_RGX = r"[a-z_][a-z0-9_]{2,30}$"


def _run_name_check(
    source: Path, capsys: CaptureFixture, function_rgx: str = FUNCTION_RGX
) -> str:
    Run(
        [
            str(source),
            "--disable=all",
            "--enable=invalid-name",
            f"--function-rgx={function_rgx}",
            "--reports=no",
            "--score=no",
        ],
        exit=False,
    )
    return capsys.readouterr().out


def test_pylint_002_matching_han_function_complete_function_rgx_has_no_invalid_name(
    tmp_path: Path, capsys: CaptureFixture
) -> None:
    """GUID: PYLINT-002."""
    source = tmp_path / "valid_han_name.py"
    source.write_text("def 汉字函():\n    pass\n", encoding="utf-8")

    assert "invalid-name" not in _run_name_check(source, capsys)


def test_pylint_003_failing_complete_function_rgx_has_invalid_name_without_crash(
    tmp_path: Path, capsys: CaptureFixture
) -> None:
    """GUID: PYLINT-003."""
    source = tmp_path / "invalid_han_name.py"
    source.write_text("def 汉字():\n    pass\n", encoding="utf-8")

    output = _run_name_check(source, capsys)

    assert "invalid-name" in output
    assert 'Function name "汉字" doesn\'t conform' in output


def test_pylint_005_supported_non_han_naming_regex_parsing_remains_accepted() -> None:
    """GUID: PYLINT-005; preserve parsing of supported non-Han naming regexes."""
    pattern = _regexp_with_han_transformer(NON_HAN_FUNCTION_RGX)

    assert isinstance(pattern, re.Pattern)
    assert pattern.pattern == NON_HAN_FUNCTION_RGX


def test_pylint_005_supported_non_han_naming_regex_matching_remains_unchanged(
    tmp_path: Path, capsys: CaptureFixture
) -> None:
    """GUID: PYLINT-005; preserve matching by supported non-Han naming regexes."""
    source = tmp_path / "non_han_names.py"
    source.write_text(
        "def valid_name():\n    pass\n\ndef InvalidName():\n    pass\n",
        encoding="utf-8",
    )

    output = _run_name_check(source, capsys, NON_HAN_FUNCTION_RGX)

    assert 'Function name "valid_name"' not in output
    assert 'Function name "InvalidName" doesn\'t conform' in output
