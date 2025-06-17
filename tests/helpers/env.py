# Project : pytest-textualize
# File Name : env.py
# Dir Path : tests/fixtures
from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class SetEnv:
    """
    This class was taken from https://github.com/pydantic/pydantic-settings
    """

    def __init__(self) -> None:
        self.envars: set[Any] = set()

    def set(self, name: str, value: Any) -> None:
        self.envars.add(name)
        os.environ[name] = value

    def pop(self, name: str) -> None:
        self.envars.remove(name)
        os.environ.pop(name)

    def clear(self) -> None:
        for n in self.envars:
            os.environ.pop(n)
