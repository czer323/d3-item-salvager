"""Utilities for canonicalizing class names."""

from __future__ import annotations

import re


def normalize_class_name(raw: str) -> str:
    """Normalize class names to a canonical display form.

    Rules:
    - Strip surrounding whitespace
    - Remove non-alphanumeric characters for keying
    - Map common compact or lowercased variants to Title Case display names
    - Fall back to title-casing the original string
    """
    s = (raw or "").strip()
    key = re.sub(r"[^a-z0-9]", "", s.lower())
    mapping = {
        "barbarian": "Barbarian",
        "crusader": "Crusader",
        "demonhunter": "Demon Hunter",
        "monk": "Monk",
        "necromancer": "Necromancer",
        "witchdoctor": "Witch Doctor",
        "wizard": "Wizard",
        "druid": "Druid",
    }
    if key in mapping:
        return mapping[key]
    return s.title() if s else s
