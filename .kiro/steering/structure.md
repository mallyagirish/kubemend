# Structure

```
.kiro/                 Kiro specs, steering, and hooks for this project
engine/
  kubemend_engine/     Shared rule engine (the foundation)
    model.py           Finding / WorkloadContext dataclasses
    loader.py          YAML loading and pod-spec discovery
    engine.py          Scan + fix orchestration, diff generation
    rules/             One module per rule family
      base.py          Rule base class and registry helpers
      resources.py     KM001, KM002
      probes.py        KM003, KM004
      images.py        KM005
      security.py      KM006-KM010
apps/
  kubemend-cli/        Application 1: the `kubemend` CLI (scan + patch)
    kubemend/
  kubemend-report/     Application 2: `kubemend-report` audit reports
    kubemend_report/
examples/              Sample manifests used by demo.sh and the README
tests/                 pytest suite + fixtures/<rule>/vulnerable|fixed pairs
```

Conventions:

- Rule IDs are stable (`KM001`...). Never renumber a shipped rule; add new
  ones at the end.
- New rule = engine rule module change + fixture pair + test + README table
  row, in that order.
- Fixture files are written in canonical 2-space YAML so generated patches
  stay minimal and readable.
