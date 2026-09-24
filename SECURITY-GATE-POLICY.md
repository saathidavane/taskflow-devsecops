# Security Gate Policy

This defines what each scanner in the pipeline (Phase 4) must find for a
build to fail. Anything not listed here is reported but does not block.

## Gitleaks (secret scanning)
- **Blocks the build:** any finding, with zero exceptions.
- **Rationale:** a real secret leak has no acceptable severity threshold.
  Exceptions are handled via `.gitleaks.toml`'s allowlist, reviewed in PR,
  never by ignoring CI output.

## pip-audit (dependency scanning)
- **Blocks the build:** any vulnerability with no severity filter — pip-audit
  does not report severity, only presence of a known advisory.
- **Rationale:** application dependencies are directly reachable from
  request-handling code; any known CVE here is a live risk until patched
  or explicitly waived.
- **Exception process:** a vulnerability with no available fix, or one
  confirmed unreachable in this codebase, is documented in
  `SECURITY-EXCEPTIONS.md` with reasoning, then explicitly ignored via
  `pip-audit --ignore-vuln <ID>` in the CI workflow, never silently.

## Bandit (SAST)
- **Blocks the build:** any HIGH severity finding with HIGH or MEDIUM
  confidence.
- **Does not block, but is visible in CI output:** LOW severity findings,
  or any finding with LOW confidence (Bandit's own confidence rating on
  how likely a match is a true positive).
- **Rationale:** LOW-confidence matches have a high false-positive rate;
  gating on them trains developers to ignore CI failures altogether.

## Trivy (container image scanning)
- **Blocks the build:** any HIGH or CRITICAL vulnerability with
  `--ignore-unfixed` applied and a fix genuinely available.
- **Does not block:** unfixed findings (no patch exists yet), and anything
  MEDIUM or below.
- **Exception process:** same as pip-audit — documented in
  `SECURITY-EXCEPTIONS.md`, then suppressed via a `.trivyignore` file
  listing the specific CVE/GHSA ID, with a comment linking to the
  documented reasoning.
- **Known current exceptions:** see `SECURITY-EXCEPTIONS.md` — vendored
  `pip` msgpack (no fix available) and a Trivy 0.71.2 false positive on
  `setuptools`.

## General principles
1. A scanner finding a real, fixable, in-scope issue always blocks — no
   "just this once."
2. Every suppression is a file, not a verbal agreement or a skipped step —
   `.gitleaks.toml`, `.trivyignore`, or `pip-audit --ignore-vuln`, each with
   a matching entry in `SECURITY-EXCEPTIONS.md`.
3. Suppressions are reviewed the same as code changes, via pull request.
4. This policy applies equally regardless of deadline pressure. A gate that
   can be overridden under pressure is not a gate.
