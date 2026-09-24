# Known Security Scan Exceptions

This file documents Trivy findings that are investigated and accepted rather
than fixed, with the reasoning, so future scans aren't re-litigated from
scratch every time.

## msgpack 1.1.2 (GHSA-6v7p-g79w-8964) — vendored inside pip

**Status:** Accepted, not exploitable in this application.

**Finding:** Trivy flags `msgpack 1.1.2` as HIGH severity inside the built
image.

**Root cause:** This is not a dependency of the application. It is a private,
vendored copy bundled inside `pip` itself
(`/usr/local/lib/python3.13/site-packages/pip/_vendor/msgpack`), used
internally by `pip`'s own resolver. The application's actual `msgpack`
dependency (pulled in via `uvicorn[standard]`) is correctly resolved to
`1.2.2` at `/app/.venv/lib/python3.13/site-packages/msgpack-1.2.2.dist-info`,
which Trivy itself confirms as clean.

**Why it can't be fixed here:** `pip`'s vendored dependencies are bundled at
build time by the pip maintainers and are not independently upgradable via
`uv add` or `pip install`. As of pip 26.2.1 (the current latest release
verified on <DATE>), this is still the bundled version.

**Mitigation:** The vendored copy is only used internally by pip's own
package-resolution logic during `pip install` at image build time. It is
never imported or reachable by the running application, and `pip` itself is
removed from the final runtime image entirely in Phase 2's multi-stage build
(only present in the `builder` stage). No runtime attack surface exists.

**Review cadence:** Re-check on each `pip` version bump.

---

## setuptools 70.3.0 (CVE-2025-47273) — Trivy 0.71.2 false positive

**Status:** Not a real finding. No action needed.

**Finding:** Trivy's aggregated Python summary table lists
`setuptools 70.3.0` as HIGH severity.

**Root cause:** Direct filesystem inspection
(`find / -iname '*setuptools*'`) confirms no `setuptools` package, egg-info,
or dist-info exists anywhere in the built image. The only filesystem match
is an unrelated file, `cffi/setuptools_ext.py`, a helper module inside the
`cffi` package that is not `setuptools` itself. This appears to be a
scanner-side bug in Trivy 0.71.2, not a real installed package.

**Review cadence:** Re-check when upgrading the Trivy version used in CI.
