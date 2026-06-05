# Covenant Indexer Best Practices

This guide is for app teams that want their Kaspa covenant flows to index
cleanly in KaspaCom APIs and explorers.

The current public TN10 surfaces are:

- Indexer API: `https://tn10-indexer.kaspa.com`
- Explorer: `https://tn10-covenants.kaspa.com`
- Swagger: `https://tn10-indexer.kaspa.com/swagger-ui/`
- OpenAPI: `https://tn10-indexer.kaspa.com/openapi.json`

## Golden Path

For the best app UX, every protocol should make its covenant identity and
constructor data easy to recover from public chain data.

1. Deploy on TN10.
2. Store the canonical `covenantId` returned by the deploy transaction.
3. Put a small public `tx.payload` claim on deploy and important continuation
   transactions.
4. Keep constructor args stable and typed.
5. Submit a decoder request with txids, covenant IDs, expected decoded args,
   and the API/explorer behavior your app needs.
6. Treat payload claims as early hints, not final product truth. Verified rows
   come from matched decoder output after the script is revealed.

## Covenant ID Standard

Use canonical `covenantId` as the primary app key whenever it is available.

Recommended app storage:

```json
{
  "network": "tn10",
  "protocol": "ExampleVault",
  "version": "1",
  "covenantId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "genesisTxid": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "genesisVout": 0,
  "covenantAddress": "kaspatest:q..."
}
```

Use the ID in product URLs and API reads:

```bash
curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants/by-id/<COVENANT_ID>' | jq

curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants/by-id/<COVENANT_ID>/actions' | jq

curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants/by-id/<COVENANT_ID>/utxos' | jq
```

`/covenants/{covenant_id_or_script_hash}` also exists for compatibility, but
new apps should prefer `/covenants/by-id/{covenant_id}` when they know the
canonical ID.

## Payload Claim Standard

Put public constructor metadata in `tx.payload` on deploy. This lets the
indexer and explorer show useful information before the first spend reveals the
full script.

Use a network-keyed JSON envelope:

```json
{
  "tn10": {
    "v": 1,
    "tmpl": "ExampleVaultV1",
    "args": [
      {
        "name": "owner",
        "type": "address",
        "value": "kaspatest:q..."
      },
      {
        "name": "unlockTimeMs",
        "type": "u64",
        "value": "1780652491753"
      },
      {
        "name": "assetId",
        "type": "string",
        "value": "sword-0001"
      }
    ],
    "meta": {
      "app": "Example Wallet",
      "label": "Example vault for sword-0001",
      "source": "example-wallet"
    }
  }
}
```

Rules:

- Keep payload data public. Never include keys, auth tokens, user secrets, or
  unpublished private user data.
- Use stable arg names. Do not rename `owner` to `wallet` in one tx and
  `user` in another.
- Use decimal strings for large integers such as sompi amounts, token amounts,
  blue scores, and millisecond timestamps.
- Include identifiers your app will search by, such as `owner`, `seller`,
  `buyer`, `assetId`, `ticker`, `marketId`, or `orderId`.
- Include both the human label and machine ID when your app has both.
- Keep payloads compact. Large off-chain metadata should be linked by URL or
  content hash, not embedded.

The indexer stores these as wallet-declared `claimedArgs`. They are useful for
early display and debugging. They are not final truth until a decoder can match
the revealed script and decoded constructor/state.

## Lookup Routes

Common reads:

```bash
# List covenants by verified or wallet-declared template.
curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants?template=ExampleVaultV1&limit=50' | jq

# List only verified matched covenants.
curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants?template=ExampleVaultV1&verified_only=true' | jq

# Search by a wallet-declared payload arg.
curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants?claimArg=assetId&claimArgValue=sword-0001' | jq

# Generic "my app covenants" lookup by owner-like wallet arg. This composes
# with template, q, active, sort, limit, and offset.
curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants?wallet=kaspatest:q...&template=ExampleVaultV1&sort=recent&limit=50' | jq

# Narrow the wallet search to one explicit public arg name.
curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants?wallet=kaspatest:q...&walletArg=stateOwner&template=KCC20V2' | jq

# Search by text across covenant ID, script hash, genesis txid, address,
# template, classification, and claim source.
curl -fsS \
  'https://tn10-indexer.kaspa.com/covenants?q=ExampleVaultV1&limit=50' | jq

# Get covenants at one covenant P2SH address.
curl -fsS \
  'https://tn10-indexer.kaspa.com/addresses/<COVENANT_ADDRESS>/covenants' | jq

# Check whether a submitted transaction is indexed and decoded yet.
curl -fsS \
  'https://tn10-indexer.kaspa.com/tx/<TXID>/settlement-status' | jq
```

Address lookup nuance:

- `GET /addresses/{address}/covenants` is for the indexed covenant address.
- It is not a generic "all covenants owned by this wallet" route.
- For generic wallet-owner lookup, use `GET /covenants?wallet=<address-or-pubkey>`.
  It matches the covenant address, common owner-like `claimedArgs`, and decoded
  top-level constructor args.
- Add `walletArg=<argName>` when your app knows the exact public arg to match,
  such as `owner`, `seller`, `buyer`, `deployerAddress`, `ownerIdentifier`, or
  `stateOwner`.
- `wallet` combines with `template`, `q`, `active`, `sort`, `limit`, and
  `offset`, so app UIs can build pages like "my active vaults, newest first."
- If your app needs current owner state, historical owner state, nested fields,
  or domain-specific aggregation, request the API projection you need in this
  repo.
- KCC20-specific owner reads already exist under routes such as
  `/addresses/{owner}/kcc20/balances`, `/addresses/{owner}/kcc20/orders`, and
  `/addresses/{owner}/kcc20/trades`.

Type/template lookup:

- Use `/covenants?template=<TemplateName>` for template family.
- Add `verified_only=true` when product UX must exclude wallet-declared claims
  that have not been matched to revealed bytecode yet.
- Use `/covenant-templates` for template counts and explorer sidebars.
- Use `classification=covenant`, `classification=inscription`, or
  `classification=unknown` for broader grouping.

## Decoder Request Checklist

A good request includes enough public evidence for maintainers to implement and
test without private context.

Include:

- app/protocol name and public source/spec links,
- target network, normally `tn10`,
- deploy txid, spend txids, and continuation txids,
- canonical covenant IDs and covenant addresses,
- expected template/action names,
- expected decoded constructor args and state args,
- payload schema with required fields,
- expected API routes and explorer fields,
- fixtures or deterministic reproduction steps,
- live URLs showing current unknown or incomplete behavior.

Use [`../TEMPLATE.yml`](../TEMPLATE.yml) for the request shape.

## Example Request Snippet

```yaml
chain_evidence:
  txids:
    - network: tn10
      txid: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
      expected_action: createVault
      explorer_url: "https://tn10-covenants.kaspa.com/tx/0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  addresses:
    - network: tn10
      address: "kaspatest:q..."
      role: covenant_address
  covenant_ids:
    - "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

decode_contract:
  template_or_protocol_marker: "ExampleVaultV1"
  payload_schema:
    description: "Deploy payload contains owner, assetId, and unlockTimeMs."
    required_fields:
      - owner
      - assetId
      - unlockTimeMs
  actions:
    - name: createVault
      trigger: "deploy creates an active vault UTXO"
      expected_indexer_action: createVault
      expected_template_name: ExampleVaultV1
      expected_decoded_args:
        owner: "kaspatest:q..."
        assetId: "sword-0001"
        unlockTimeMs: "1780652491753"
      expected_api_response:
        route: /covenants/by-id/{covenant_id}
        fields:
          - name: template
            example: ExampleVaultV1
          - name: decodedArgs.assetId
            example: sword-0001
```
