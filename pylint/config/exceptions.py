# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

from __future__ import annotations


class UnrecognizedArgumentAction(Exception):
    """Raised if an ArgumentManager instance tries to add an argument for which the action
    is not recognized.
    """


class _UnrecognizedOptionError(Exception):
    """Private rejection signal for options unknown to an argument manager.

    Architecture contract (PYLINT-001, PYLINT-002, PYLINT-003, PYLINT-004,
    PYLINT-005): configuration parsing owns production of this signal and the
    identifying diagnostic; the invocation boundary owns consuming the signal
    and selecting non-zero, traceback-free termination. Recognized-option paths
    do not produce the signal. The dependency points from those two boundaries
    to this private configuration exception, not between the boundaries.
    """

    def __init__(self, options: list[str], *args: object) -> None:
        self.options = options
        super().__init__(*args)


class ArgumentPreprocessingError(Exception):
    """Raised if an error occurs during argument pre-processing."""
