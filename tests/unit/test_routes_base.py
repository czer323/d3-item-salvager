from flask import Flask

from frontend.src.routes import base


def _make_app() -> Flask:
    app = Flask(__name__)
    return app


def test_deduplicates_values_from_primary_and_fallback() -> None:
    app = _make_app()
    # order: primary class_ids=1, fallback class_id=1, primary class_ids=2
    with app.test_request_context("/?class_ids=1&class_id=1&class_ids=2"):
        values = base.extract_list_values(
            primary_key="class_ids", fallback_keys=("class_id",)
        )
    assert values == ["1", "2"]


def test_preserves_order_when_duplicates_present() -> None:
    app = _make_app()
    # duplicates but order should be preserved: first seen 2 then 3
    with app.test_request_context("/?class_ids=2&class_ids=3&class_id=2"):
        values = base.extract_list_values(
            primary_key="class_ids", fallback_keys=("class_id",)
        )
    assert values == ["2", "3"]


def test_single_fallback_only_returns_single_value() -> None:
    app = _make_app()
    with app.test_request_context("/?class_id=barbarian"):
        values = base.extract_list_values(
            primary_key="class_ids", fallback_keys=("class_id",)
        )
    assert values == ["barbarian"]
