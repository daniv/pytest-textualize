# Project : pytest-textualize
# File Name : __init__.py
# Dir Path : tests/helpers
from __future__ import annotations


def clean_dict_recursive(d):
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, dict):
            # Recursively clean nested dictionaries
            nested_cleaned = clean_dict_recursive(v)
            if nested_cleaned:  # Only add if the nested dictionary is not empty after cleaning
                cleaned[k] = nested_cleaned
        elif v is not None:
            # Add non-None values
            cleaned[k] = v
    return cleaned

cleaned_dict = lambda d: {k: v for k, v in d.items() if v is not None}
