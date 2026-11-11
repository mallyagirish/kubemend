# Tech

- **Language:** Python 3.11+, standard library plus PyYAML (only runtime
  dependency). Tests use pytest.
- **Layout:** a shared rule engine package (`engine/kubemend_engine`) and two
  thin applications on top of it (`apps/kubemend-cli`, `apps/kubemend-report`).
  Apps never re-implement rule logic; they call the engine.
- **Install:** one root `pyproject.toml`; `pip install -e .` from the repo
  root installs the engine and both apps and registers the `kubemend` and
  `kubemend-report` console scripts. `python -m kubemend` must also work.
- **Rule contract:** each rule is a class with `id` (KM0xx), `severity`,
  `title`, `explanation`, `check(ctx) -> list[Finding]` and
  `apply_fix(ctx, finding) -> bool`. Rules are pure functions of the parsed
  YAML document plus mutation of that same document for fixes; no I/O inside
  rules.
- **Patches:** fixes mutate the parsed document; the engine re-serializes and
  produces a unified diff against the original file text. Fixes must be
  idempotent: scanning a patched file yields no finding for the fixed rule.
- **Determinism:** directory scans process files in sorted order; findings
  are ordered by file, then rule id. No timestamps inside findings.
- **Testing:** every rule ships with a vulnerable/fixed fixture pair under
  `tests/fixtures/`; a rule is not done until its pair passes.
