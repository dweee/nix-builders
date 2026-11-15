# Local public caller candidate — publication and comparison held

This branch forwards the default-false experimental_darwin_userspace input to
shared helper58983a20fc8b13ca8a8a6998a265885fe5b08ac3 (PR19). That helper is a
review candidate: final exact-head review binding and required CI qualification
must complete before this caller is published/adopted. The private immutable
provider tag, private executor policy and installed worker remain unchanged.

Only one future disposable PUBLIC fixture is planned, after review and normal
landing of both pieces. Dispatch from dweee/nix-builders main, with environment
empty, existing tag:nix-builder, ordinary OIDC identities, explicit opt-in and
one aarch64-darwin runner. Keep the same admitted/pinned node for inbound SSH,
Nix daemon stdio RPC and constant public derivation transfer/build with no local
build jobs. Require actual ordinary Niks3 publication and a fresh normal
signature-required substitution of that one output. No Flakey/private inputs,
raw maps, private names, daemon debug logs or exhaustive closure audit.

Effective Niks3 configuration was read without credentials from the running
Faeri service's referenced OIDC JSON. Both github/write and github-reader/read
rules admit repository dweee/nix-builders, ref refs/heads/main and event
workflow_dispatch. Audiences are respectively https://niks3.monke.fail and
https://niks3.monke.fail/read. These effective rules do not bind job_workflow_ref
or environment. This establishes claim compatibility, not successful runtime
OIDC exchange/publication. No rule was changed.

The maintained Tailscale description only establishes that the public identity
is main-only. Its full existing live subject/customClaimRules/scopes/tag readback
is still needed. It must already permit the above public caller and the reviewed
reusable-workflow SHA; no broadening is authorized. A missing/mismatched existing
claim is a blocker before dispatch. The private identity requires an exact
private environment/tag/old reusable SHA and is not a substitute.

The shared candidate's DNS window is accepted only for this disposable public
comparison. Its official action can briefly set Ethernet DNS before immediate
restoration; abrupt runner loss in that interval is not recoverable. A public
smoke passing does not prove a historical root cause or full-graph reliability.
