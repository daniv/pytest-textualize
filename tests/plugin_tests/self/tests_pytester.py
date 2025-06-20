# Project : pytest-textualize
# File Name : tests_pytester.py
# Dir Path : tests/plugin_tests/self
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from conftest import TextualizePytester


def gtest_help_message(testdir):
    result = testdir.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "textualize:",
            "*--textualize*Enable rich output for the terminal reporter (default:",
            "*False)",
        ]
    )


"""
pytest-textualize:
  --textualize          activate the textualize plugin

"""


@pytest.mark.xfail
def test_help_message(textualize_pytester: TextualizePytester) -> None:
    result = textualize_pytester.run_pytest("-h")
    result.stdout.fnmatch_lines(
        [
            "*textualize:*",
            "*--textualize*Enable rich terminal reporting using pytest-textualize.  Default to False*",
            "*dotenv_path (string): path to .env file*",
        ]
    )
