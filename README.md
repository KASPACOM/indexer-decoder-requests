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
4. Open a pull request back to this repo.

One request should cover one app or protocol family. Split unrelated flows into
separate request files so each decoder can be reviewed and implemented
independently.

Do not include private keys, seed phrases, auth tokens, API keys, unpublished
user data, or anything that cannot be public.

## What Maintainers Do

Maintainers review the request as the decoder contract. If it has enough public
evidence and the behavior is valid, acceptance starts implementation work.

Normal lifecycle:

1. `proposed` - contributor opens a request PR.
2. `accepted` - maintainers agree the indexer/explorer should support it.
3. `implementing` - maintainer or coding agent is building decoder/API/explorer
   support.
4. `implemented` - code merged, but live deployment or reindex verification is
   still pending.
5. `deployed` - public API/explorer verified against the request evidence.
6. `blocked` - request needs more evidence, a chain tx, fixture, or design
   decision.

Implementation can include decoder logic, persistence/projection changes, API
fields or routes, explorer display changes, fixtures, tests, deployment, and
live verification.

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
