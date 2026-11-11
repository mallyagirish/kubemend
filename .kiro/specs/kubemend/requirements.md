# Requirements: KubeMend

## Introduction

Kubernetes manifests in the wild routinely ship without resource requests,
health probes, or basic pod security settings. Existing scanners report
these problems as warning lists; engineers then hand-edit YAML, which is
slow and error-prone. KubeMend scans static YAML and generates the fix as a
minimal, reviewable patch, with a plain-English explanation for every rule.

## Glossary

- **Workload**: a Pod, Deployment, StatefulSet, DaemonSet, ReplicaSet, Job,
  or CronJob document.
- **Finding**: one rule violation in one workload (or one container in it),
  citing an exact field path.
- **Patch**: a unified diff that, applied to the scanned file, resolves one
  or more findings.
- **Guidance-only rule**: a rule whose correct fix needs information the tool
  cannot know (for example an image digest); it reports instructions instead
  of a patch.

## Requirements

### Requirement 1: Scanning

**User story:** As an engineer, I want to scan a file or directory of YAML so
that I can see every hardening problem before I merge.

#### Acceptance criteria

1. WHEN a user runs `kubemend scan <path>` on a file or directory, THE SYSTEM
   SHALL parse every YAML document, locate workload pod specs, and evaluate
   all enabled rules against each container and pod spec.
2. WHEN a finding is produced, THE SYSTEM SHALL cite the rule ID, severity,
   workload identity, container name (when applicable), and the exact field
   path of the offending setting.
3. WHEN a directory is scanned, THE SYSTEM SHALL process `*.yaml` and
   `*.yml` files recursively in sorted order.
4. WHEN a document is not a workload, THE SYSTEM SHALL ignore it without
   error.

### Requirement 2: Reviewable patches

**User story:** As a reviewer, I want the tool to show me the fix as a diff
so that I can approve it like any other code change.

#### Acceptance criteria

1. WHEN findings have automatic fixes, THE SYSTEM SHALL print a unified diff
   that resolves them, before any file is modified.
2. WHEN a patch is applied with `--write`, THE SYSTEM SHALL modify only the
   files that contain fixed findings.
3. WHEN a patched file is scanned again, THE SYSTEM SHALL report no findings
   for the rules that were fixed (fixes are idempotent).
4. WHERE a rule is guidance-only, THE SYSTEM SHALL NOT fabricate values; it
   SHALL print concrete manual instructions instead of a patch hunk.

### Requirement 3: Safe by default

**User story:** As an engineer, I want scanning to be read-only unless I
explicitly opt in, so the tool is safe to run anywhere, including CI.

#### Acceptance criteria

1. WHEN `--write` is not passed, THE SYSTEM SHALL NOT modify any scanned
   file (dry-run).
2. WHEN findings exist, THE SYSTEM SHALL exit with code 1; WHEN no findings
   exist, exit code 0; WHEN the scan itself fails, exit code 2.

### Requirement 4: Explanations

**User story:** As a newer Kubernetes user, I want each rule explained in
plain English so that I learn why the fix matters.

#### Acceptance criteria

1. WHEN `--explain` is passed, THE SYSTEM SHALL print a short rationale for
   each reported rule covering the risk and why the suggested fix helps.
2. THE SYSTEM SHALL include the same rationale in JSON output and in audit
   reports regardless of flags.

### Requirement 5: Rule set v1

**User story:** As a platform engineer, I want the ten most common hardening
gaps covered so that one tool handles the usual review checklist.

#### Acceptance criteria

1. THE SYSTEM SHALL implement rules KM001-KM010: missing resource requests,
   missing resource limits, missing readiness probe, missing liveness probe,
   mutable image tag, running as root not prevented, privilege escalation not
   disabled, missing seccomp profile, host namespaces enabled, and
   capabilities not dropping ALL.
2. WHEN a rule is added or changed, THE SYSTEM SHALL ship a vulnerable/fixed
   fixture pair and unit tests for it.

### Requirement 6: Two applications on one engine

**User story:** As a maintainer, I want the rule engine to be a reusable
foundation so that new front-ends do not duplicate rule logic.

#### Acceptance criteria

1. THE SYSTEM SHALL expose the engine as an importable package
   (`kubemend_engine`) with no CLI concerns inside it.
2. THE SYSTEM SHALL provide a CLI application (`kubemend`) for scan + patch
   workflows.
3. THE SYSTEM SHALL provide a reporting application (`kubemend-report`)
   that renders a shareable audit report (Markdown or HTML) from the same
   engine results.
4. WHEN the engine's findings change, both applications SHALL reflect the
   change without code edits in the applications.

### Requirement 7: One-command setup

**User story:** As a judge or new user, I want to install and run the tool
from a fresh checkout with no ceremony.

#### Acceptance criteria

1. WHEN a user runs `pip install -e .` at the repo root, THE SYSTEM SHALL
   install the engine and both applications.
2. THE SYSTEM SHALL require no dependency beyond PyYAML at runtime and no
   network or cluster access at scan time.
