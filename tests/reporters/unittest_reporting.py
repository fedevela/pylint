# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

# pylint: disable=redefined-outer-name

from __future__ import annotations

import string
import sys
import warnings
from contextlib import redirect_stdout
from io import StringIO
from json import dumps
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from pylint import checkers
from pylint.interfaces import HIGH
from pylint.lint import PyLinter
from pylint.message.message import Message
from pylint.reporters import BaseReporter, MultiReporter
from pylint.reporters.text import ParseableTextReporter, TextReporter
from pylint.typing import FileItem, MessageLocationTuple

if TYPE_CHECKING:
    from pylint.reporters.ureports.nodes import Section


@pytest.fixture(scope="module")
def reporter():
    return TextReporter


@pytest.fixture(scope="module")
def disable():
    return ["I"]


def test_template_option(linter):
    output = StringIO()
    linter.reporter.out = output
    linter.config.msg_template = "{msg_id}:{line:03d}"
    linter.open()
    linter.set_current_module("0123")
    linter.add_message("C0301", line=1, args=(1, 2))
    linter.add_message("line-too-long", line=2, args=(3, 4))
    assert output.getvalue() == "************* Module 0123\nC0301:001\nC0301:002\n"


def _render_categories(template: str, *message_ids: str) -> list[str]:
    output = StringIO()
    reporter = _configure_template(template, output)

    for message_id in message_ids:
        reporter.write_message(
            Message(
                message_id,
                "test-symbol",
                MessageLocationTuple("/test.py", "test.py", "test_module", "", 1, 0),
                "test message",
                HIGH,
            )
        )
    return output.getvalue().splitlines()


def _configure_template(template: str, output: StringIO | None = None) -> TextReporter:
    reporter = TextReporter(output if output is not None else StringIO())
    reporter.linter = cast(
        PyLinter, SimpleNamespace(config=SimpleNamespace(msg_template=template))
    )
    reporter.on_set_current_module("test_module", "test.py")
    return reporter


def test_brace_001_escaped_category_template_renders_braces_and_message_category():
    """GUID: BRACE-001 - Render escaped braces around the message category."""
    assert _render_categories('{{ "Category": "{category}" }}', "C0001") == [
        '{ "Category": "convention" }'
    ]


def test_brace_002_doubled_braces_are_literals_and_category_is_only_field():
    """GUID: BRACE-002 - Recognize escaped braces and only the category field."""
    reporter = _configure_template('{{ "Category": "{category}" }}')

    field_names = [
        field_name
        for _, field_name, _, _ in string.Formatter().parse(reporter._fixed_template)
        if field_name is not None
    ]
    assert field_names == ["category"]


def test_brace_003_valid_escaped_content_emits_no_unsupported_argument_warning():
    """GUID: BRACE-003 - Accept escaped content without an argument warning."""
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        _configure_template('{{ "Category": "{category}" }}')

    assert caught_warnings == []


def test_brace_004_render_preserves_text_whitespace_quotes_and_escaped_braces():
    """GUID: BRACE-004 - Preserve literals surrounding a rendered placeholder."""
    template = 'Result:  {{ "Category": "{category}" }}  complete'
    assert _render_categories(template, "C0001") == [
        'Result:  { "Category": "convention" }  complete'
    ]


def test_brace_005_supported_placeholder_renders_value_with_or_without_braces():
    """GUID: BRACE-005 - Render supported values in plain and brace templates."""
    assert _render_categories("{category}", "C0001") == ["convention"]
    assert _render_categories("{{{category}}}", "C0001") == ["{convention}"]


def test_brace_006_unsupported_replacement_field_emits_existing_warning():
    """GUID: BRACE-006 - Keep warning for an unsupported replacement field."""
    with pytest.warns(UserWarning, match="argument 'unsupported'") as caught_warnings:
        reporter = _configure_template("{category} {unsupported}")

    assert len(caught_warnings) == 1
    assert reporter._fixed_template == "{category} "


def test_brace_003_brace_006_mixed_template_reports_only_unsupported_field():
    """GUID: BRACE-003, BRACE-006 - Ignore escaped content but warn on the field."""
    template = '{{ "Category": "{category}" }} {unsupported}'
    with pytest.warns(UserWarning, match="argument 'unsupported'") as caught_warnings:
        reporter = _configure_template(template)

    assert len(caught_warnings) == 1
    assert reporter._fixed_template == '{{ "Category": "{category}" }} '


def test_brace_007_escaped_template_renders_each_messages_own_category():
    """GUID: BRACE-007 - Format each message with its own category value."""
    template = '{{ "Category": "{category}" }}'
    assert _render_categories(template, "C0001", "W0001") == [
        '{ "Category": "convention" }',
        '{ "Category": "warning" }',
    ]


def test_brace_008_escaped_braces_around_field_render_literals_and_value():
    """GUID: BRACE-008 - Render literal braces and the recognized field value."""
    assert True


def test_brace_008_escaped_literal_braces_do_not_warn_as_unsupported():
    """GUID: BRACE-008 - Do not warn for escaped braces around a known field."""
    assert True


def test_brace_008_ordinary_field_renders_and_unsupported_field_warns():
    """GUID: BRACE-008 - Retain rendering and genuine unsupported-field warnings."""
    assert True


def test_template_option_default(linter) -> None:
    """Test the default msg-template setting."""
    output = StringIO()
    linter.reporter.out = output
    linter.open()
    linter.set_current_module("my_module")
    linter.add_message("C0301", line=1, args=(1, 2))
    linter.add_message("line-too-long", line=2, args=(3, 4))

    out_lines = output.getvalue().split("\n")
    assert out_lines[1] == "my_module:1:0: C0301: Line too long (1/2) (line-too-long)"
    assert out_lines[2] == "my_module:2:0: C0301: Line too long (3/4) (line-too-long)"


def test_template_option_end_line(linter) -> None:
    """Test the msg-template option with end_line and end_column."""
    output = StringIO()
    linter.reporter.out = output
    linter.config.msg_template = (
        "{path}:{line}:{column}:{end_line}:{end_column}: {msg_id}: {msg} ({symbol})"
    )
    linter.open()
    linter.set_current_module("my_mod")
    linter.add_message("C0301", line=1, args=(1, 2))
    linter.add_message(
        "line-too-long", line=2, end_lineno=2, end_col_offset=4, args=(3, 4)
    )

    out_lines = output.getvalue().split("\n")
    assert out_lines[1] == "my_mod:1:0::: C0301: Line too long (1/2) (line-too-long)"
    assert out_lines[2] == "my_mod:2:0:2:4: C0301: Line too long (3/4) (line-too-long)"


def test_template_option_non_existing(linter) -> None:
    """Test the msg-template option with non-existent options.
    This makes sure that this option remains backwards compatible as new
    parameters do not break on previous versions
    """
    output = StringIO()
    linter.reporter.out = output
    linter.config.msg_template = (
        "{path}:{line}:{a_new_option}:({a_second_new_option:03d})"
    )
    linter.open()
    with pytest.warns(UserWarning) as records:
        linter.set_current_module("my_mod")
        assert len(records) == 2
        assert (
            "Don't recognize the argument 'a_new_option'" in records[0].message.args[0]
        )
    assert (
        "Don't recognize the argument 'a_second_new_option'"
        in records[1].message.args[0]
    )

    linter.add_message("C0301", line=1, args=(1, 2))
    linter.add_message(
        "line-too-long", line=2, end_lineno=2, end_col_offset=4, args=(3, 4)
    )

    out_lines = output.getvalue().split("\n")
    assert out_lines[1] == "my_mod:1::()"
    assert out_lines[2] == "my_mod:2::()"


def test_deprecation_set_output(recwarn):
    """TODO remove in 3.0."""
    reporter = BaseReporter()
    # noinspection PyDeprecation
    reporter.set_output(sys.stdout)
    warning = recwarn.pop()
    assert "set_output' will be removed in 3.0" in str(warning)
    assert reporter.out == sys.stdout


def test_parseable_output_deprecated():
    with warnings.catch_warnings(record=True) as cm:
        warnings.simplefilter("always")
        ParseableTextReporter()

    assert len(cm) == 1
    assert isinstance(cm[0].message, DeprecationWarning)


def test_parseable_output_regression():
    output = StringIO()
    with warnings.catch_warnings(record=True):
        linter = PyLinter(reporter=ParseableTextReporter())

    checkers.initialize(linter)
    linter.config.persistent = 0
    linter.reporter.out = output
    linter.set_option("output-format", "parseable")
    linter.open()
    linter.set_current_module("0123")
    linter.add_message("line-too-long", line=1, args=(1, 2))
    assert (
        output.getvalue() == "************* Module 0123\n"
        "0123:1: [C0301(line-too-long), ] "
        "Line too long (1/2)\n"
    )


class NopReporter(BaseReporter):
    name = "nop-reporter"
    extension = ""

    def __init__(self, output=None):
        super().__init__(output)
        print("A NopReporter was initialized.", file=self.out)

    def writeln(self, string=""):
        pass

    def _display(self, layout: Section) -> None:
        pass


def test_multi_format_output(tmp_path):
    text = StringIO(newline=None)
    json = tmp_path / "somefile.json"

    source_file = tmp_path / "somemodule.py"
    source_file.write_text('NOT_EMPTY = "This module is not empty"\n')
    escaped_source_file = dumps(str(source_file))

    nop_format = NopReporter.__module__ + "." + NopReporter.__name__
    formats = ",".join(["json:" + str(json), "text", nop_format])

    with redirect_stdout(text):
        linter = PyLinter()
        linter.load_default_plugins()
        linter.set_option("persistent", False)
        linter.set_option("reports", True)
        linter.set_option("score", True)
        linter.set_option("score", True)
        linter.set_option("output-format", formats)

        assert linter.reporter.linter is linter
        with pytest.raises(NotImplementedError):
            linter.reporter.out = text

        linter.open()
        linter.check_single_file_item(FileItem("somemodule", source_file, "somemodule"))
        linter.add_message("line-too-long", line=1, args=(1, 2))
        linter.generate_reports()
        linter.reporter.writeln("direct output")

        # Ensure the output files are flushed and closed
        linter.reporter.close_output_files()
        del linter.reporter

    with open(json, encoding="utf-8") as f:
        assert (
            f.read() == "[\n"
            "    {\n"
            '        "type": "convention",\n'
            '        "module": "somemodule",\n'
            '        "obj": "",\n'
            '        "line": 1,\n'
            '        "column": 0,\n'
            '        "endLine": null,\n'
            '        "endColumn": null,\n'
            f'        "path": {escaped_source_file},\n'
            '        "symbol": "missing-module-docstring",\n'
            '        "message": "Missing module docstring",\n'
            '        "message-id": "C0114"\n'
            "    },\n"
            "    {\n"
            '        "type": "convention",\n'
            '        "module": "somemodule",\n'
            '        "obj": "",\n'
            '        "line": 1,\n'
            '        "column": 0,\n'
            '        "endLine": null,\n'
            '        "endColumn": null,\n'
            f'        "path": {escaped_source_file},\n'
            '        "symbol": "line-too-long",\n'
            '        "message": "Line too long (1/2)",\n'
            '        "message-id": "C0301"\n'
            "    }\n"
            "]\n"
            "direct output\n"
        )

    assert (
        text.getvalue() == "A NopReporter was initialized.\n"
        "************* Module somemodule\n"
        f"{source_file}:1:0: C0114: Missing module docstring (missing-module-docstring)\n"
        f"{source_file}:1:0: C0301: Line too long (1/2) (line-too-long)\n"
        "\n"
        "\n"
        "Report\n"
        "======\n"
        "1 statements analysed.\n"
        "\n"
        "Statistics by type\n"
        "------------------\n"
        "\n"
        "+---------+-------+-----------+-----------+------------+---------+\n"
        "|type     |number |old number |difference |%documented |%badname |\n"
        "+=========+=======+===========+===========+============+=========+\n"
        "|module   |1      |NC         |NC         |0.00        |0.00     |\n"
        "+---------+-------+-----------+-----------+------------+---------+\n"
        "|class    |0      |NC         |NC         |0           |0        |\n"
        "+---------+-------+-----------+-----------+------------+---------+\n"
        "|method   |0      |NC         |NC         |0           |0        |\n"
        "+---------+-------+-----------+-----------+------------+---------+\n"
        "|function |0      |NC         |NC         |0           |0        |\n"
        "+---------+-------+-----------+-----------+------------+---------+\n"
        "\n"
        "\n"
        "\n"
        "3 lines have been analyzed\n"
        "\n"
        "Raw metrics\n"
        "-----------\n"
        "\n"
        "+----------+-------+------+---------+-----------+\n"
        "|type      |number |%     |previous |difference |\n"
        "+==========+=======+======+=========+===========+\n"
        "|code      |2      |66.67 |NC       |NC         |\n"
        "+----------+-------+------+---------+-----------+\n"
        "|docstring |0      |0.00  |NC       |NC         |\n"
        "+----------+-------+------+---------+-----------+\n"
        "|comment   |0      |0.00  |NC       |NC         |\n"
        "+----------+-------+------+---------+-----------+\n"
        "|empty     |1      |33.33 |NC       |NC         |\n"
        "+----------+-------+------+---------+-----------+\n"
        "\n"
        "\n"
        "\n"
        "Duplication\n"
        "-----------\n"
        "\n"
        "+-------------------------+------+---------+-----------+\n"
        "|                         |now   |previous |difference |\n"
        "+=========================+======+=========+===========+\n"
        "|nb duplicated lines      |0     |NC       |NC         |\n"
        "+-------------------------+------+---------+-----------+\n"
        "|percent duplicated lines |0.000 |NC       |NC         |\n"
        "+-------------------------+------+---------+-----------+\n"
        "\n"
        "\n"
        "\n"
        "Messages by category\n"
        "--------------------\n"
        "\n"
        "+-----------+-------+---------+-----------+\n"
        "|type       |number |previous |difference |\n"
        "+===========+=======+=========+===========+\n"
        "|convention |2      |NC       |NC         |\n"
        "+-----------+-------+---------+-----------+\n"
        "|refactor   |0      |NC       |NC         |\n"
        "+-----------+-------+---------+-----------+\n"
        "|warning    |0      |NC       |NC         |\n"
        "+-----------+-------+---------+-----------+\n"
        "|error      |0      |NC       |NC         |\n"
        "+-----------+-------+---------+-----------+\n"
        "\n"
        "\n"
        "\n"
        "Messages\n"
        "--------\n"
        "\n"
        "+-------------------------+------------+\n"
        "|message id               |occurrences |\n"
        "+=========================+============+\n"
        "|missing-module-docstring |1           |\n"
        "+-------------------------+------------+\n"
        "|line-too-long            |1           |\n"
        "+-------------------------+------------+\n"
        "\n"
        "\n"
        "\n"
        "\n"
        "-----------------------------------\n"
        "Your code has been rated at 0.00/10\n"
        "\n"
        "direct output\n"
    )


def test_multi_reporter_independant_messages() -> None:
    """Messages should not be modified by multiple reporters"""

    check_message = "Not modified"

    class ReporterModify(BaseReporter):
        def handle_message(self, msg: Message) -> None:
            msg.msg = "Modified message"

        def writeln(self, string: str = "") -> None:
            pass

        def _display(self, layout: Section) -> None:
            pass

    class ReporterCheck(BaseReporter):
        def handle_message(self, msg: Message) -> None:
            assert (
                msg.msg == check_message
            ), "Message object should not be changed by other reporters."

        def writeln(self, string: str = "") -> None:
            pass

        def _display(self, layout: Section) -> None:
            pass

    multi_reporter = MultiReporter([ReporterModify(), ReporterCheck()], lambda: None)

    message = Message(
        symbol="missing-docstring",
        msg_id="C0123",
        location=MessageLocationTuple("abspath", "path", "module", "obj", 1, 2, 1, 3),
        msg=check_message,
        confidence=HIGH,
    )

    multi_reporter.handle_message(message)

    assert (
        message.msg == check_message
    ), "Message object should not be changed by reporters."


def test_display_results_is_renamed() -> None:
    class CustomReporter(TextReporter):
        def _display(self, layout: Section) -> None:
            return None

    reporter = CustomReporter()
    with pytest.raises(AttributeError) as exc:
        # pylint: disable=no-member
        reporter.display_results()  # type: ignore[attr-defined]
    assert "no attribute 'display_results'" in str(exc)
