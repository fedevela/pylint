# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pylint.checkers import BaseChecker
from pylint.lint.expand_modules import _is_in_ignore_list_re, expand_modules
from pylint.testutils import CheckerTestCase, set_config
from pylint.typing import (
    ErrorDescriptionDict,
    MessageDefinitionTuple,
    ModuleDescriptionDict,
)


def test__is_in_ignore_list_re_match() -> None:
    patterns = [
        re.compile(".*enchilada.*"),
        re.compile("unittest_.*"),
        re.compile(".*tests/.*"),
    ]
    assert _is_in_ignore_list_re("unittest_utils.py", patterns)
    assert _is_in_ignore_list_re("cheese_enchiladas.xml", patterns)
    assert _is_in_ignore_list_re("src/tests/whatever.xml", patterns)


def _expand_implicit_namespace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    module_filenames: tuple[str, ...] = ("a.py",),
) -> tuple[list[ModuleDescriptionDict], list[ErrorDescriptionDict]]:
    namespace = tmp_path / "a"
    namespace.mkdir()
    for module_filename in module_filenames:
        (namespace / module_filename).touch()
    monkeypatch.chdir(tmp_path)
    return expand_modules(["a"], [], [], [])


def test_pylint7114_001_namespace_discovery_skips_missing_init(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PYLINT7114-001: Discovery must not parse a nonexistent a/__init__.py."""
    modules, errors = _expand_implicit_namespace(tmp_path, monkeypatch)

    assert not errors
    assert modules
    assert all(Path(module["path"]).name != "__init__.py" for module in modules)
    assert all(Path(module["basepath"]).name != "__init__.py" for module in modules)


def test_pylint7114_002_namespace_a_discovery_preserves_identity_a(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PYLINT7114-002: An implicit namespace directory a must remain module a."""
    modules, errors = _expand_implicit_namespace(tmp_path, monkeypatch)

    assert not errors
    assert {module["basename"] for module in modules} == {"a"}
    assert {Path(module["basepath"]).resolve() for module in modules} == {
        (tmp_path / "a").resolve()
    }


def test_pylint7114_003_a_a_py_discovery_assigns_identity_a_a(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PYLINT7114-003: The real same-named file a/a.py must be module a.a."""
    modules, errors = _expand_implicit_namespace(tmp_path, monkeypatch)

    assert not errors
    assert [(Path(module["path"]).resolve(), module["name"]) for module in modules] == [
        ((tmp_path / "a" / "a.py").resolve(), "a.a")
    ]


def test_pylint7114_004_a_a_and_a_b_discovery_keeps_a_b_resolvable_as_a_b(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PYLINT7114-004: With a/a.py and a/b.py, discovery preserves a/b.py as a.b."""
    modules, errors = _expand_implicit_namespace(
        tmp_path, monkeypatch, ("a.py", "b.py")
    )

    assert not errors
    assert {(Path(module["path"]).resolve(), module["name"]) for module in modules} == {
        ((tmp_path / "a" / "a.py").resolve(), "a.a"),
        ((tmp_path / "a" / "b.py").resolve(), "a.b"),
    }


def test_pylint7114_008_conventional_package_real_init_and_modules_remain_discoverable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PYLINT7114-008: Discovery retains real __init__.py and package modules."""
    package = tmp_path / "a"
    package.mkdir()
    initializer = package / "__init__.py"
    first_module = package / "a.py"
    second_module = package / "b.py"
    for module in (initializer, first_module, second_module):
        module.touch()
    monkeypatch.chdir(tmp_path)

    modules, errors = expand_modules(["a"], [], [], [])

    assert not errors
    discovered = {
        Path(module["path"]).resolve(): (
            module["name"],
            module["isarg"],
            Path(module["basepath"]).resolve(),
            module["basename"],
        )
        for module in modules
    }
    assert discovered == {
        initializer.resolve(): ("a", True, initializer.resolve(), "a"),
        first_module.resolve(): ("a.a", False, initializer.resolve(), "a"),
        second_module.resolve(): ("a.b", False, initializer.resolve(), "a"),
    }


TEST_DIRECTORY = Path(__file__).parent.parent
INIT_PATH = str(TEST_DIRECTORY / "lint/__init__.py")
EXPAND_MODULES = str(TEST_DIRECTORY / "lint/unittest_expand_modules.py")
this_file = {
    "basename": "lint.unittest_expand_modules",
    "basepath": EXPAND_MODULES,
    "isarg": True,
    "name": "lint.unittest_expand_modules",
    "path": EXPAND_MODULES,
}

this_file_from_init = {
    "basename": "lint",
    "basepath": INIT_PATH,
    "isarg": False,
    "name": "lint.unittest_expand_modules",
    "path": EXPAND_MODULES,
}

unittest_lint = {
    "basename": "lint",
    "basepath": INIT_PATH,
    "isarg": False,
    "name": "lint.unittest_lint",
    "path": str(TEST_DIRECTORY / "lint/unittest_lint.py"),
}

test_utils = {
    "basename": "lint",
    "basepath": INIT_PATH,
    "isarg": False,
    "name": "lint.test_utils",
    "path": str(TEST_DIRECTORY / "lint/test_utils.py"),
}

test_pylinter = {
    "basename": "lint",
    "basepath": INIT_PATH,
    "isarg": False,
    "name": "lint.test_pylinter",
    "path": str(TEST_DIRECTORY / "lint/test_pylinter.py"),
}

test_caching = {
    "basename": "lint",
    "basepath": INIT_PATH,
    "isarg": False,
    "name": "lint.test_caching",
    "path": str(TEST_DIRECTORY / "lint/test_caching.py"),
}


init_of_package = {
    "basename": "lint",
    "basepath": INIT_PATH,
    "isarg": True,
    "name": "lint",
    "path": INIT_PATH,
}


class TestExpandModules(CheckerTestCase):
    """Test the expand_modules function while allowing options to be set."""

    class Checker(BaseChecker):
        """This dummy checker is needed to allow options to be set."""

        name = "checker"
        msgs: dict[str, MessageDefinitionTuple] = {}
        options = (("test-opt", {"action": "store_true", "help": "help message"}),)

    CHECKER_CLASS: type = Checker

    @pytest.mark.parametrize(
        "files_or_modules,expected",
        [
            ([__file__], [this_file]),
            (
                [str(Path(__file__).parent)],
                [
                    init_of_package,
                    test_caching,
                    test_pylinter,
                    test_utils,
                    this_file_from_init,
                    unittest_lint,
                ],
            ),
        ],
    )
    @set_config(ignore_paths="")
    def test_expand_modules(self, files_or_modules, expected):
        """Test expand_modules with the default value of ignore-paths."""
        ignore_list, ignore_list_re = [], []
        modules, errors = expand_modules(
            files_or_modules,
            ignore_list,
            ignore_list_re,
            self.linter.config.ignore_paths,
        )
        modules.sort(key=lambda d: d["name"])
        assert modules == expected
        assert not errors

    @pytest.mark.parametrize(
        "files_or_modules,expected",
        [
            ([__file__], []),
            (
                [str(Path(__file__).parent)],
                [
                    init_of_package,
                ],
            ),
        ],
    )
    @set_config(ignore_paths=".*/lint/.*")
    def test_expand_modules_with_ignore(self, files_or_modules, expected):
        """Test expand_modules with a non-default value of ignore-paths."""
        ignore_list, ignore_list_re = [], []
        modules, errors = expand_modules(
            files_or_modules,
            ignore_list,
            ignore_list_re,
            self.linter.config.ignore_paths,
        )
        modules.sort(key=lambda d: d["name"])
        assert modules == expected
        assert not errors
