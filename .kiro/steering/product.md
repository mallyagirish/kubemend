# Product: KubeMend

KubeMend finds common Kubernetes hardening mistakes in manifests and Helm
output, and instead of stopping at a report, it writes the fix as a
reviewable patch.

## Who it is for

- Platform and application engineers who ship YAML to Kubernetes clusters and
  want a fast pre-merge hardening pass.
- Reviewers who would rather read a small diff than a list of warnings.

## Product principles

1. **Fixes, not just findings.** Every rule either produces a minimal,
   apply-able patch or says plainly why a human has to make the call.
2. **Safe by default.** Scanning never modifies a file unless `--write` is
   passed. A dry run prints the patch so it can be reviewed first.
3. **No fabricated values.** KubeMend never invents data it cannot know, such
   as an image digest. Where a safe mechanical default exists (resource
   requests, probes, security context flags) it uses one and labels it as a
   starting point to tune.
4. **Explainable.** Every rule carries a short plain-English rationale so a
   finding doubles as a teaching moment (`--explain`).
5. **Small and boring.** One runtime dependency (PyYAML). No cluster access,
   no network calls, no daemon. It runs in CI in seconds.

## Scope

In scope: static YAML (plain manifests, kustomize output, `helm template`
output), workload kinds Pod, Deployment, StatefulSet, DaemonSet, ReplicaSet,
Job, CronJob. Out of scope: live cluster scanning, admission control, policy
languages, auto-applying patches to a cluster.
