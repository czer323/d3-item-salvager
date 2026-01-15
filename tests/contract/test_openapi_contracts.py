"""Contract tests to ensure OpenAPI includes the contract paths and responses."""

from __future__ import annotations

import json
from pathlib import Path

from d3_item_salvager.api.factory import create_app

CONTRACT_DIR = (
    Path(__file__).parents[2] / "specs" / "002-frontend-ui-redesign" / "contracts"
)


def test_openapi_contains_contract_paths() -> None:
    app = create_app()
    spec = app.openapi()

    for contract_file in CONTRACT_DIR.glob("*.json"):
        contract = json.loads(contract_file.read_text())
        for path in contract.get("paths", {}):
            assert path in spec.get("paths", {}), f"Path {path} missing from OpenAPI"
            # check GET response exists
            contract_methods = contract["paths"][path]
            spec_methods = spec["paths"][path]
            for method, c_method in contract_methods.items():
                assert method in spec_methods, (
                    f"Method {method} for {path} missing in OpenAPI"
                )
                assert "200" in c_method.get("responses", {}), (
                    f"Contract missing 200 response for {method} {path}"
                )
