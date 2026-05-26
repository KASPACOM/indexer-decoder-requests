#!/usr/bin/env python3
"""Validate decoder request YAML files with standard-library tooling."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("missing PyYAML: install pyyaml or use ruby -e \"require 'yaml'\"", file=sys.stderr)
    sys.exit(2)


VALID_STATUSES = {
    "proposed",
    "accepted",
    "implementing",
    "implemented",
    "deployed",
    "blocked",
}


def is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0 or all(is_blank(item) for item in value)
    if isinstance(value, dict):
        return len(value) == 0 or all(is_blank(item) for item in value.values())
    return False


def get_path(data, dotted):
    value = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def require(errors, data, dotted):
    value = get_path(data, dotted)
    if is_blank(value):
        errors.append(f"missing required field: {dotted}")
    return value


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: scripts/validate_request.py requests/<slug>.yml", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    errors: list[str] = []

    if not path.exists():
        errors.append(f"file does not exist: {path}")
    if path.suffix not in {".yml", ".yaml"}:
        errors.append("request file must be .yml or .yaml")
    is_example = len(path.parts) >= 2 and path.parts[0] == "examples"
    if len(path.parts) < 2 or path.parts[0] not in {"requests", "examples"}:
        errors.append("request file must live under requests/ or examples/")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        print("ERROR: top-level YAML must be a mapping", file=sys.stderr)
        return 1

    required_fields = [
        "request.app_name",
        "request.slug",
        "request.requester.github",
        "request.status",
        "request.target_networks",
        "request.request_type.kind",
        "protocol.family",
        "protocol.description",
        "explorer_goal.summary",
        "explorer_goal.needed_api_routes",
        "explorer_goal.success_criteria",
        "chain_evidence.txids",
        "decode_contract.template_or_protocol_marker",
        "decode_contract.actions",
        "fixtures.reproduction_steps",
        "fixtures.expected_test_cases",
    ]

    for field in required_fields:
        require(errors, data, field)

    status = get_path(data, "request.status")
    if status and status not in VALID_STATUSES:
        errors.append(f"invalid request.status: {status}")

    slug = get_path(data, "request.slug")
    if (
        not is_example
        and isinstance(slug, str)
        and path.name not in {f"{slug}.yml", f"{slug}.yaml"}
    ):
        errors.append("file name should match request.slug")

    txids = get_path(data, "chain_evidence.txids")
    if isinstance(txids, list):
        nonblank_txids = [item for item in txids if isinstance(item, dict) and not is_blank(item.get("txid"))]
        if not nonblank_txids:
            errors.append("chain_evidence.txids must include at least one txid")

    actions = get_path(data, "decode_contract.actions")
    if isinstance(actions, list):
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                errors.append(f"decode_contract.actions[{index}] must be a mapping")
                continue
            for field in ("name", "trigger", "expected_indexer_action"):
                if is_blank(action.get(field)):
                    errors.append(f"decode_contract.actions[{index}].{field} is required")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
