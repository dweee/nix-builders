# nix-builders

Public runner repository for [nix-remote](https://github.com/dweee/Nix_Remote-Builders-Distributed).
`nix-remote` dispatches `.github/workflows/nix-builder.yml`, which starts
ephemeral Nix builders on the tailnet. This repository holds no flakes.

Secrets: `TS_OAUTH_CLIENT_ID` + `TS_AUDIENCE` (or `TS_OAUTH_SECRET`), `ATTIC_TOKEN`,
and the cache settings `ATTIC_ENDPOINT`, `ATTIC_CACHE`, `ATTIC_SUBSTITUTER`,
`ATTIC_PUBLIC_KEY`, `NIX_SUBSTITUTERS`, `NIX_TRUSTED_PUBLIC_KEYS`. They are secrets
because GitHub prints variables and inputs in public run logs.
Variable: `ATTIC_PUSH_ENABLED` (`false` stops pushing to the cache).
