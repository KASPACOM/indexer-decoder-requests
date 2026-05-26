# AGENTS.md - Decoder Request Intake

This repo is public intake for indexer/explorer decoder requests.

If you are an agent preparing a request PR:

1. Copy `TEMPLATE.yml` to `requests/<stable-slug>.yml`.
2. Fill one request per PR.
3. Include public chain evidence that a maintainer can reproduce.
4. Run `python3 scripts/validate_request.py requests/<stable-slug>.yml`.
5. Do not include private keys, seed phrases, auth tokens, API keys, unpublished
   user data, or anything that cannot be public.

Do not claim the request is implemented or deployed unless the public API or
explorer link proves it. Use `request.status: proposed` for new contributor
requests.

Implementation agents use accepted request files as the contract for work in
the relevant implementation repo, not this intake repo. Put decoder/API/explorer
code, deploy changes, and forward-index verification in the implementation repo. Then update
the request with `maintainer_notes.implementation_pr`,
`maintainer_notes.deployment_status_url`, and
`maintainer_notes.verified_live_links`.

A request is implementation ready only when it has enough evidence to write
fixtures and verify live output.
