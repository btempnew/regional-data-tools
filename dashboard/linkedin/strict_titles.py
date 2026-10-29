"""Exact catalog-title matching: no substring or fuzzy expansion."""
import re
import unicodedata


def normalize_title(value):
    value = unicodedata.normalize('NFKC', str(value or '')).casefold()
    return re.sub(r'\s+', ' ', value).strip()


def strict_role(title, catalog):
    target = normalize_title(title)
    return next((role for role in catalog if normalize_title(role) == target), '')
