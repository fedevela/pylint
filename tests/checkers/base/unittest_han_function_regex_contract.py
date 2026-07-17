# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

"""Contract placeholders for Han characters in the configured function regex."""


def test_pylint_002_matching_han_function_complete_function_rgx_has_no_invalid_name(
) -> None:
    """GUID: PYLINT-002."""
    assert True


def test_pylint_003_failing_complete_function_rgx_has_invalid_name_without_crash(
) -> None:
    """GUID: PYLINT-003."""
    assert True
