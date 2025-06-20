# Project : pytest-textualize
# File Name : lark_tests.py
# Dir Path : tests/rich_tests
from __future__ import annotations

import sys
import warnings
from argparse import ArgumentParser
from argparse import FileType
from logging import DEBUG
from logging import ERROR
from logging import INFO
from logging import WARN
from textwrap import indent

from lark import Lark
from lark import logger

try:
    from interegular import logger as interegular_logger

    has_interegular = True
except ImportError:
    has_interegular = False


def build_lalr(namespace):
    logger.setLevel((ERROR, WARN, INFO, DEBUG)[min(namespace.verbose, 3)])
    if has_interegular:
        interegular_logger.setLevel(logger.getEffectiveLevel())
    if len(namespace.start) == 0:
        namespace.start.append("start")
    kwargs = {n: getattr(namespace, n) for n in options}
    return Lark(namespace.grammar_file, parser="lalr", **kwargs), namespace.out


def showwarning_as_comment(message, category, filename, lineno, file=None, line=None):
    # Based on warnings._showwarnmsg_impl
    text = warnings.formatwarning(message, category, filename, lineno, line)
    text = indent(text, "# ")
    if file is None:
        file = sys.stderr
        if file is None:
            return
    try:
        file.write(text)
    except OSError:
        pass


def make_warnings_comments():
    warnings.showwarning = showwarning_as_comment


def test_lark():
    from lark.grammar import Rule
    from lark.lexer import TerminalDef
    from lark.tools import lalr_argparser, build_lalr
    import json

    import argparse

    argparser = argparse.ArgumentParser(
        prog="python -m lark.tools.serialize",
        parents=[lalr_argparser],
        description="Lark Serialization Tool - Stores Lark's internal state & LALR analysis as a JSON file",
        epilog="Look at the Lark documentation for more info on the options",
    )

    def serialize(lark_inst, outfile):
        data, memo = lark_inst.memo_serialize([TerminalDef, Rule])
        outfile.write("{\n")
        outfile.write('  "data": %s,\n' % json.dumps(data))
        outfile.write('  "memo": %s\n' % json.dumps(memo))
        outfile.write("}\n")

    def main():
        if len(sys.argv) == 1:
            argparser.print_help(sys.stderr)
            sys.exit(1)
        ns = argparser.parse_args()
        serialize(*build_lalr(ns))


def test_lark_2():
    lalr_argparser = ArgumentParser(
        add_help=False, epilog="Look at the Lark documentation for more info on the options"
    )

    flags = [
        ("d", "debug"),
        "keep_all_tokens",
        "regex",
        "propagate_positions",
        "maybe_placeholders",
        "use_bytes",
    ]

    options = ["start", "lexer"]

    lalr_argparser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase Logger output level, up to three times",
    )
    lalr_argparser.add_argument("-s", "--start", action="append", default=[])
    lalr_argparser.add_argument(
        "-l", "--lexer", default="contextual", choices=("basic", "contextual")
    )
    lalr_argparser.add_argument(
        "-o",
        "--out",
        type=FileType("w", encoding="utf-8"),
        default=sys.stdout,
        help="the output file (default=stdout)",
    )
    lalr_argparser.add_argument(
        "grammar_file", type=FileType("r", encoding="utf-8"), help="A valid .lark file"
    )
