# Project : pytest-textualize
# File Name : __init__.py
# Dir Path : src/pytest_textualize/textualize
from __future__ import annotations


__all__ = ("locate",)

from enum import IntEnum

from pytest_textualize.settings import locate


class Verbosity(IntEnum):
    QUIET = -1  # --quiet
    NORMAL = 0
    VERBOSE = 1  # -v
    VERY_VERBOSE = 2  # -vv
    DEBUG = 3  # -vvv


class OutputType(IntEnum):
    NORMAL = 1
    RAW = 2
