# KubeMend

**Scanners tell you what's wrong. KubeMend writes the fix.**

KubeMend scans Kubernetes manifests and Helm-rendered YAML for the hardening
mistakes that show up in almost every code review - missing resource
requests, missing probes, containers that can run as root - and generates
the correction as a minimal, reviewable patch instead of another warning
list. Every finding cites the exact field path, and every rule can explain
itself in plain English.

```console
$ kubemend scan app.yaml

app.yaml
  Deployment/default/web (container: web)
    [KM001] medium Missing resource requests - no cpu/memory request set
      at spec.template.spec.containers[0].resources.requests
      fix: set requests to cpu=250m, memory=512Mi (starting point - tune to real usage)
    ...

10 finding(s) in 1 file(s); 9 auto-fixable

--- patch preview (dry run; pass --write to apply): ---
```

## Install

```bash
pip install -e .
```

That is the whole setup: Python 3.11+, one runtime dependency (PyYAML), no
cluster, no network, no account. It installs two commands, `kubemend` and
`kubemend-report`, both built on the same rule engine.

## Usage

```bash
# Dry run (default): findings + patch preview, nothing on disk changes
kubemend scan path/to/manifests/

# Apply the patch in place
kubemend scan app.yaml --write

# Plain-English rationale for every rule that fires
kubemend scan app.yaml --explain

# Machine-readable output for CI
kubemend scan app.yaml --format json

# Just the security-context rules
kubemend scan app.yaml --rules KM006,KM007,KM008,KM010
```

Exit codes are CI-friendly: `0` = clean, `1` = findings, `2` = the scan
itself failed. Point it at a single file, a directory (scanned recursively),
plain manifests, or rendered output saved to a file first (e.g.
`helm template mychart > out.yaml` - KubeMend reads any YAML, including
multi-document files).

### The second app: audit reports

`kubemend-report` turns the same scan into a shareable artifact - counts by
rule and severity, every finding with its rationale and recommended fix -
for attaching to a ticket or a review:

```bash
kubemend-report manifests/ --format md --out report.md
kubemend-report manifests/ --format html --out report.html
```

## Rules

| Rule | Severity | What it catches | Fix |
| --- | --- | --- | --- |
| KM001 | medium | No CPU/memory requests | Sets 250m / 512Mi starting-point requests |
| KM002 | medium | No CPU/memory limits | Sets 500m / 1Gi starting-point limits |
| KM003 | medium | No readiness probe | Adds an httpGet probe on `/health` |
| KM004 | low | No liveness probe | Adds an httpGet probe on `/health` |
| KM005 | high | Image not pinned by digest (`:latest`, no tag) | Guidance only - see below |
| KM006 | high | Container may run as root | Sets `runAsNonRoot: true` (uid 0 -> 10001) |
| KM007 | high | Privilege escalation allowed | Sets `allowPrivilegeEscalation: false` |
| KM008 | medium | No seccomp profile | Sets pod `seccompProfile: RuntimeDefault` |
| KM009 | high | hostNetwork / hostPID / hostIPC enabled | Sets the flags to `false` |
| KM010 | medium | Capabilities not dropped | Sets `capabilities.drop: ["ALL"]` |

**Why KM005 has no patch:** pinning an image means writing a real `sha256`
digest, and the true digest lives in your registry, not in the manifest. A
tool that invents one produces patches that fail to pull - worse than no
patch. KubeMend flags the exact field and tells you the command to get the
real digest. Every default it *does* write (resource numbers, probe paths)
is labelled a starting point to tune.

**A note on patches:** fixes are applied to the parsed YAML and
re-serialized in standard Kubernetes style, so a heavily hand-formatted
file may see formatting normalization in the diff. The patch is a
reviewable draft - read it like any other diff before you commit it. That
is the point of generating one.

## Try the demo

```bash
./demo.sh
```

Scans the vulnerable example, previews and applies the patch on a temp
copy, rescans, and builds an audit report. The examples in the repo are
never modified.

## Project layout (Skeleton Crew)

One foundation, two applications:

- `engine/kubemend_engine/` - the rule engine: loader, ten rules, scan/fix
  orchestration, diff generation. No CLI code in here.
- `apps/kubemend-cli/` - **app 1:** the `kubemend` CLI (scan + patch).
- `apps/kubemend-report/` - **app 2:** `kubemend-report` audit reports
  (Markdown / HTML).
- `tests/` - pytest suite; every rule ships with a vulnerable/fixed fixture
  pair under `tests/fixtures/`.
- `examples/` - the manifests used by `demo.sh`.

## How this was built with Kiro

This project was built spec-first in Kiro, and the artifacts live in the
repo under `.kiro/`:

- **Specs** (`.kiro/specs/kubemend/`) - `requirements.md` (user stories with
  EARS acceptance criteria), `design.md` (architecture, per-rule fix
  strategy, correctness properties), and `tasks.md` (the implementation
  checklist, in execution order). The code follows the spec's structure:
  engine first, then rules in two batches, then the two apps.
- **Steering** (`.kiro/steering/`) - `product.md` (principles: safe by
  default, no fabricated values), `tech.md` (the rule contract, determinism,
  the fixture-pair rule), and `structure.md` (layout and naming
  conventions). These kept every generated file consistent with decisions
  made once, up front.
- **Agent hook** (`.kiro/hooks/run-tests-on-rule-save.kiro.hook`) - saving a
  file under `engine/kubemend_engine/rules/` runs the rule test suite
  immediately, so a broken check or fix surfaces in the same edit session.

The spec-driven approach mattered most for the correctness properties:
dry-run purity and fix idempotence were written as acceptance criteria
before the engine existed, and they are now tests, not aspirations.

## Development

```bash
pip install -e . pytest
python -m pytest -q        # 38 tests
./demo.sh
```

## License

MIT - see [LICENSE](LICENSE).
