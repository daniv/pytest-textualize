# Project : pytest-textualize
# File Name : __main__.py
# Dir Path : tests
from __future__ import annotations

import sys

import pytest

if __name__ == '__main__':
    from pathlib import Path
    f = Path.cwd()
    sys.exit(pytest.main(sys.argv))
