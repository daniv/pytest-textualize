from __future__ import annotations

from pytest_textualize.textualize.settings import get_textualize_settings, locate

__all__ = ("get_textualize_settings", "locate")


def setup_pytest_textualize():
    from dotenv import load_dotenv

    locate("")
    load_dotenv()

    settings = get_textualize_settings()
