# Important & Urgent Issues (2026-04-23)

## Scope
This triage focuses on issues that block core reliability, release readiness, or daily development workflows.

## 1) Critical: Syntax-corrupted executor modules break lint/import paths

**Severity:** P0 (release blocker)

### Why this is urgent
- `make lint` currently fails with parser-level syntax errors (not style issues), which means CI quality gates cannot pass.
- The broken files are core execution modules (`ingestion/executor`, `offline/downloader/executor`) used in data ingestion/download paths.
- This likely indicates a bad merge/refactor that duplicated/injected partial code blocks.

### Evidence
- `src/akshare_data/ingestion/executor/base.py` contains overlapping/duplicated class and method definitions with invalid indentation and duplicate signatures.
- `src/akshare_data/offline/downloader/executor.py` contains malformed return blocks and duplicated `execute_structured` definitions.

### Immediate action
1. Reconstruct these files from last known good commit (or manually resolve duplicated blocks).
2. Re-run `make lint` and ensure parser errors are zero.
3. Add a CI guard that runs `python -m compileall src/` before linting to fail fast on syntax corruption.

---

## 2) Critical: `sources/router.py` has malformed `__all__` export block

**Severity:** P0 (import/runtime blocker)

### Why this is urgent
- `src/akshare_data/sources/router.py` has a duplicated/nested `__all__` assignment, which is syntactically invalid.
- Any import path referencing this compatibility router can fail early, impacting source routing functionality.

### Evidence
- Duplicate `__all__` start appears before the previous list is closed.

### Immediate action
1. Keep one canonical `__all__` list.
2. Validate compatibility exports with a targeted import smoke test:
   - `python -c "import akshare_data.sources.router as r; print(r.__all__)"`

---

## 3) High: Local test bootstrap depends on networked build dependencies

**Severity:** P1 (workflow blocker in restricted environments)

### Why this matters
- `make test-unit` failed while attempting to install build dependency `hatchling` from index due to proxy/network constraints.
- In locked-down CI/dev environments, this prevents tests from starting, reducing confidence and slowing incident response.

### Immediate action
1. Provide a fully pinned lockfile and internal mirror guidance for offline/proxied environments.
2. Add a documented fallback path for test runs when bootstrap install fails.
3. Consider pre-building a dev/test container image with dependencies baked in.

---

## Recommended order of remediation
1. **Fix syntax corruption in executor + router files first** (restore repo to importable/lintable state).
2. **Re-run lint + targeted unit tests** around ingestion/downloader/router.
3. **Harden test bootstrap/dependency strategy** for restricted environments.

## Commands used in this triage
- `make lint`
- `make test-unit`
- `sed -n '210,380p' src/akshare_data/ingestion/executor/base.py | nl -ba`
- `sed -n '90,240p' src/akshare_data/offline/downloader/executor.py | nl -ba`
- `sed -n '1,90p' src/akshare_data/sources/router.py | nl -ba`
