# Design: KubeMend

## Architecture

```
            +----------------------+
 files ---> | loader               |  YAML docs -> WorkloadContext list
            +----------+-----------+
                       v
            +----------------------+        +------------------+
            | engine.scan          | -----> | rules KM001-010  |
            +----------+-----------+        +------------------+
                       | findings (+ fix closures on the parsed doc)
                       v
            +----------------------+
            | engine.fix           |  mutate doc -> re-serialize -> unified diff
            +----------+-----------+
                       v
        +--------------+---------------+
        |                              |
  kubemend CLI (apps/kubemend-cli)   kubemend-report (apps/kubemend-report)
  scan / --write / --explain / JSON  Markdown + HTML audit reports
```

The engine is the foundation; the two apps are thin front-ends. This is the
Skeleton Crew bet: one small, well-tested core, multiple distinct tools on
top.

## Components

- **model.py** — `Finding` (rule id, severity, file, resource identity,
  container, field path, message, explanation, fix description) and
  `WorkloadContext` (parsed pod spec plus its location in the document).
- **loader.py** — file/directory walking, multi-document YAML loading, and
  pod-spec discovery for Pod / Deployment / StatefulSet / DaemonSet /
  ReplicaSet / Job / CronJob. Non-workload documents are skipped.
- **rules/** — one class per rule implementing `check(ctx)` and
  `apply_fix(ctx, finding)`. Rules mutate only the parsed document they were
  handed, which keeps fixes composable: the engine applies every fix to one
  in-memory copy, then diffs once.
- **engine.py** — orchestrates scan (all rules x all workloads), fix
  (apply every auto-fixable finding, re-serialize with PyYAML, unified diff
  via `difflib`), and per-file result grouping.
- **kubemend/cli.py** — argparse front-end: `scan` subcommand, `--write`,
  `--explain`, `--format text|json`, `--rules` filter. Exit codes 0/1/2 per
  the requirements.
- **kubemend_report/report.py** — renders findings as a Markdown report or a
  single self-contained HTML page (inline CSS, no external assets).

## Fix strategy per rule

| Rule | Detection | Fix |
| --- | --- | --- |
| KM001 requests | container `resources.requests` missing cpu or memory | set cpu=250m, memory=512Mi (labelled starting point) |
| KM002 limits | `resources.limits` missing cpu or memory | set cpu=500m, memory=1Gi |
| KM003 readiness | no `readinessProbe` | add httpGet `/health` on the first declared container port (fallback 8080) |
| KM004 liveness | no `livenessProbe` | same shape as KM003, longer delays |
| KM005 image tag | no tag, `:latest`, or no digest | guidance-only: never fabricate a digest; print pinning instructions |
| KM006 root | `runAsNonRoot` not true at pod or container level, or `runAsUser: 0` | set container `runAsNonRoot: true`; rewrite uid 0 to 10001 |
| KM007 priv-esc | `allowPrivilegeEscalation` is not `false` | set `false` |
| KM008 seccomp | no seccomp profile at pod or container level | set pod `seccompProfile.type: RuntimeDefault` |
| KM009 host ns | `hostNetwork`/`hostPID`/`hostIPC` true | set the offending flags to `false` |
| KM010 caps | `capabilities.drop` does not include `ALL` | set `drop: ["ALL"]` |

## Correctness properties

- **Dry-run purity:** without `--write`, no scanned file's bytes change.
  Tested by hashing fixtures before/after a scan.
- **Idempotence:** for every auto-fixable rule, scan(fix(x)) has no finding
  for that rule. Tested per rule with fixture pairs.
- **Minimal patches:** fixtures and examples are kept in canonical 2-space
  YAML so PyYAML re-serialization produces small, readable diffs. (Known
  trade-off: heavily hand-formatted files will see formatting normalization
  in the diff; the patch remains correct and reviewable.)
- **No invented data:** the only rule whose fix needs external truth (image
  digests) is guidance-only by design.

## Error handling

Unreadable or invalid YAML files are reported on stderr and counted as scan
errors (exit 2 if a requested path does not exist; a single bad file in a
directory does not abort the rest of the scan).
