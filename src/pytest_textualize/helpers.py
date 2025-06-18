# Project : pytest-textualize
# File Name : helpers.py
# Dir Path : src/pytest_textualize
from __future__ import annotations

from typing import Any


def get_bool_opt(opt_name: str, string: str) -> bool:
    if isinstance(string, bool):
        return string
    elif isinstance(string, int):
        return bool(string)
    elif not isinstance(string, str):
        raise ValueError(f'Invalid type {string!r} for option {opt_name}; use '
                         '1/0, yes/no, true/false, on/off')
    elif string.lower() in ('1', 'yes', 'true', 'on'):
        return True
    elif string.lower() in ('0', 'no', 'false', 'off'):
        return False
    else:
        raise ValueError(f'Invalid value {string!r} for option {opt_name}; use '
                         '1/0, yes/no, true/false, on/off')


def get_int_opt(opt_name: str, string: str) -> int:
    """As :func:`get_bool_opt`, but interpret the value as an integer."""
    try:
        return int(string)
    except TypeError:
        raise ValueError(f'Invalid type {string!r} for option {opt_name}; you '
                         'must give an integer value')
    except ValueError:
        raise ValueError(f'Invalid value {string!r} for option {opt_name}; you '
                         'must give an integer value')


def get_list_opt(opt_name: str, string: str) -> list[str]:
    if isinstance(string, str):
        return string.split()
    elif isinstance(string, (list, tuple)):
        return list(string)
    else:
        raise ValueError(f'Invalid type {string!r} for option {opt_name}; you '
                         'must give a list value')
