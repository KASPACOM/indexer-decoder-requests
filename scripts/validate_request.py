#!/usr/bin/env python3
"""Validate decoder request YAML files with standard-library tooling."""

from __future__ import annotations

import sys
from pathlib import Path
import re
from urllib.parse import urlparse

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

VALID_NETWORKS = {"mainnet", "tn10", "tn11", "tn12"}
VALID_REQUEST_KINDS = {
    "new_decoder",
    "decoder_update",
    "explorer_display",
    "api_projection",
}
HEX_64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
SECRET_RE = re.compile(
    r"(private[_-]?key|seed[_ -]?phrase|mnemonic|api[_-]?key|auth[_-]?token|"
    r"bearer\s+[a-z0-9._-]+|sk-[a-z0-9_-]{12,})",
    re.IGNORECASE,
)


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


def as_list(value):
    return value if isinstance(value, list) else []


def validate_url(errors, dotted, value):
    if is_blank(value):
        return
    if not isinstance(value, str):
        errors.append(f"{dotted} must be a URL string")
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append(f"{dotted} must be an http(s) URL")


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

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        print(f"ERROR: invalid YAML: {exc}", file=sys.stderr)
        return 1

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
    if isinstance(slug, str) and not SLUG_RE.match(slug):
        errors.append("request.slug must be lowercase kebab-case, 3-64 chars")
    if (
        not is_example
        and isinstance(slug, str)
        and path.name not in {f"{slug}.yml", f"{slug}.yaml"}
    ):
        errors.append("file name should match request.slug")

    request_kind = get_path(data, "request.request_type.kind")
    if request_kind and request_kind not in VALID_REQUEST_KINDS:
        errors.append(f"invalid request.request_type.kind: {request_kind}")

    networks = get_path(data, "request.target_networks")
    if isinstance(networks, list):
        for index, network in enumerate(networks):
            if network not in VALID_NETWORKS:
                errors.append(f"request.target_networks[{index}] invalid network: {network}")
    elif networks is not None:
        errors.append("request.target_networks must be a list")

    for dotted in ("protocol.public_spec_url", "protocol.source_repo_url"):
        validate_url(errors, dotted, get_path(data, dotted))

    txids = get_path(data, "chain_evidence.txids")
    if isinstance(txids, list):
        nonblank_txids = [item for item in txids if isinstance(item, dict) and not is_blank(item.get("txid"))]
        if not nonblank_txids:
            errors.append("chain_evidence.txids must include at least one txid")
        seen_txids: set[str] = set()
        for index, item in enumerate(txids):
            if not isinstance(item, dict):
                errors.append(f"chain_evidence.txids[{index}] must be a mapping")
                continue
            txid = item.get("txid")
            if not is_blank(txid):
                if not isinstance(txid, str) or not HEX_64_RE.match(txid):
                    errors.append(f"chain_evidence.txids[{index}].txid must be 64 hex chars")
                elif txid.lower() in seen_txids:
                    errors.append(f"duplicate txid in chain_evidence.txids: {txid}")
                else:
                    seen_txids.add(txid.lower())
            network = item.get("network")
            if not is_blank(network) and network not in VALID_NETWORKS:
                errors.append(f"chain_evidence.txids[{index}].network invalid network: {network}")
            validate_url(errors, f"chain_evidence.txids[{index}].explorer_url", item.get("explorer_url"))
    elif txids is not None:
        errors.append("chain_evidence.txids must be a list")

    for index, item in enumerate(as_list(get_path(data, "chain_evidence.addresses"))):
        if not isinstance(item, dict):
            errors.append(f"chain_evidence.addresses[{index}] must be a mapping")
            continue
        network = item.get("network")
        if not is_blank(network) and network not in VALID_NETWORKS:
            errors.append(f"chain_evidence.addresses[{index}].network invalid network: {network}")

    for index, item in enumerate(as_list(get_path(data, "chain_evidence.outpoints"))):
        if not isinstance(item, dict):
            errors.append(f"chain_evidence.outpoints[{index}] must be a mapping")
            continue
        txid = item.get("txid")
        if not is_blank(txid) and (not isinstance(txid, str) or not HEX_64_RE.match(txid)):
            errors.append(f"chain_evidence.outpoints[{index}].txid must be 64 hex chars")
        vout = item.get("vout")
        if not isinstance(vout, int) or vout < 0:
            errors.append(f"chain_evidence.outpoints[{index}].vout must be a non-negative integer")

    actions = get_path(data, "decode_contract.actions")
    if isinstance(actions, list):
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                errors.append(f"decode_contract.actions[{index}] must be a mapping")
                continue
            for field in ("name", "trigger", "expected_indexer_action"):
                if is_blank(action.get(field)):
                    errors.append(f"decode_contract.actions[{index}].{field} is required")
    elif actions is not None:
        errors.append("decode_contract.actions must be a list")

    for index, test_case in enumerate(as_list(get_path(data, "fixtures.expected_test_cases"))):
        if not isinstance(test_case, dict):
            errors.append(f"fixtures.expected_test_cases[{index}] must be a mapping")
            continue
        for field in ("name", "given", "expect"):
            if is_blank(test_case.get(field)):
                errors.append(f"fixtures.expected_test_cases[{index}].{field} is required")

    raw_text = path.read_text(encoding="utf-8")
    if SECRET_RE.search(raw_text):
        errors.append("request appears to contain a secret-looking field or value")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
