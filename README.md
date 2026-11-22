# nix-builders

Public runner repository for [nix-remote](https://github.com/dweee/Nix_Remote-Builders-Distributed).
`nix-remote` dispatches `.github/workflows/nix-builder.yml`, which starts
ephemeral Nix builders on the tailnet. This repository holds no flakes.

Secrets: `TS_OAUTH_CLIENT_ID` + `TS_AUDIENCE` (or `TS_OAUTH_SECRET`), and the
cache settings `NIX_SUBSTITUTERS` and `NIX_TRUSTED_PUBLIC_KEYS`. They are secrets
because GitHub prints variables and inputs in public run logs. Builders read and
publish the private Niks3 cache through GitHub OIDC; no cache token is stored.
Variable: `NIKS3_PUSH_ENABLED` (`false` stops publishing to Niks3).

The optional `push_paths` dispatch input overrides publication for one session:
`built` selects built outputs and their runtime closures; `all` also selects
copied build-only inputs. An empty input preserves the repository default from
`NIKS3_PUSH_PATHS`. Private sessions should explicitly select `built`.
