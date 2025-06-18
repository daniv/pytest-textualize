from __future__ import annotations

from importlib import metadata

__version__ = metadata.version("pytest_textualize")

__all__ = ["TextualizeSettings", "ConsoleFactory"]

from pytest_textualize.console_factory import ConsoleFactory
from pytest_textualize.settings import TextualizeSettings
