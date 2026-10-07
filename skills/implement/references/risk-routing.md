# Risk and execution settings

Use explicit priority, release-gate, impact and blocking metadata when present.
Normative requirements, public contracts, mandatory evidence and dependency or
status semantics can have high impact even when the change is documentation.

- **Mechanical:** exact non-semantic metadata or link correction; no production,
  normative, status, dependency or release effect.
- **Bounded:** isolated reversible behavior, clear acceptance, local tests and no
  critical-risk marker.
- **Standard:** production code, multi-file behavior, integration work, several
  interacting criteria or ordinary implementation uncertainty.
- **Critical:** concurrency, streaming, durability, security/privacy/auth, data or
  schema migration, public protocol compatibility, lifecycle, data-loss risk,
  architecture boundaries, cross-process E2E or a wide/uncertain blast radius.

Use the highest applicable level. Unknown production impact requires at least
standard; explicit high or critical impact can promote a seemingly small change.
A large word count alone is not a critical marker.

Match the level to currently exposed capabilities and the user's constraints.
Verify the exact supported model/effort before a switch or worker dispatch.
Runtime availability is not a price table. Keep current settings when adequate;
do not guess a model, claim a switch, edit profiles or lower required quality.
