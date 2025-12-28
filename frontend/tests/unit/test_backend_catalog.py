"""Unit tests for frontend backend_catalog helpers."""

from __future__ import annotations

from frontend.src.services.backend_catalog import (
    normalize_class_name,
)


def test_normalize_class_name_variants() -> None:
    variants = ["barbarian", "Barbarian", "barbarian ", "barbar-ian", "BARBARIAN"]
    assert {normalize_class_name(v) for v in variants} == {"Barbarian"}

    dh_variants = ["demonhunter", "demon-hunter", "Demon Hunter", " DemonHunter "]
    assert {normalize_class_name(v) for v in dh_variants} == {"Demon Hunter"}

    # Unknown but reasonable fallbacks
    assert normalize_class_name("unknownclass") == "Unknownclass"
    assert normalize_class_name(None) == "Unknown"
