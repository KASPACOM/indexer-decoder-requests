# Indexer Decoder Requests

Public intake repo for apps that need KaspaCom indexers and explorers to decode
their on-chain data.

Use this repo when you are building a wallet, marketplace, token, game, or app
and want your transactions to show as structured data instead of unknown raw
transactions.

## Contributor Flow

1. Fork this repo.
2. Copy [`TEMPLATE.yml`](TEMPLATE.yml) to `requests/<app-or-protocol>.yml`.
3. Fill the request with public evidence: txids, addresses, outpoints, compiled
   artifacts, fixtures, and the explorer/API behavior you expect.
4. Run `python3 scripts/validate_request.py requests/<app-or-protocol>.yml`.
5. Open a pull request back to this repo.

One request should cover one app or protocol family. Split unrelated flows into
separate request files so each decoder can be reviewed and implemented
independently.

Do not include private keys, seed phrases, auth tokens, API keys, unpublished
user data, or anything that cannot be public.

See [`examples/complete-request.yml`](examples/complete-request.yml) for the
level of detail maintainers and coding agents need.

## Implementation-Ready Requests

A request is ready to assign to a coding agent when it includes:

- at least one public txid, fixture, or deterministic reproduction step,
- the target network and public explorer/API links when available,
- the exact action names that should appear in decoded output,
- expected decoded args for each action,
- expected explorer fields and API routes,
- how to recognize the flow on-chain, such as a reveal shape, protocol marker,
  covenant template, payload field, or compiled artifact,
- known overlap with KRC-20, KRC-721, KCC20, KNS, or existing covenant templates,
- success criteria for live verification.

If those fields are missing, maintainers should mark the request `blocked` or
ask for more evidence before assigning implementation.

## What Maintainers Do

Maintainers review the request as the decoder contract. If it has enough public
evidence and the behavior is valid, acceptance starts implementation work.

This public repo is the intake and tracking layer. The actual code PR belongs
in the relevant implementation repo, for example the indexer, API, explorer, or
deployment/infra repo.

Normal lifecycle:

1. `proposed` - contributor opens a request PR.
2. `accepted` - maintainers agree the indexer/explorer should support it.
3. `implementing` - maintainer or coding agent is building support in the
   implementation repo, with the implementation PR linked from this request.
4. `implemented` - implementation repo PR merged, but live deployment or reindex
   verification is still pending.
5. `deployed` - public API/explorer verified against the request evidence.
6. `blocked` - request needs more evidence, a chain tx, fixture, or design
   decision.

The implementation repo work can include decoder logic, persistence/projection
changes, API fields or routes, explorer display changes, fixtures, tests,
deployment, reindexing, and live verification.

This request repo should keep the public status updated with:

- the assigned implementation owner,
- the implementation PR link,
- deployment or reindex status,
- verified public API/explorer links.

## Acceptance vs Deployment

Accepted means:

```text
The requested behavior is valid and assigned for implementation.
```

Deployed means:

```text
The public API/explorer was verified against the request's txids or fixtures.
```

Accepted requests should not be treated as done until the request has live
verification links or an explicit blocker.

## Request Files

Use lowercase slugs:

```text
requests/<app-or-protocol>.yml
```

Examples:

```text
requests/kaspa-game-items.yml
requests/example-marketplace-orders.yml
requests/custom-vault-v2.yml
```
