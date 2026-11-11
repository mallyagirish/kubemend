"""Engine-level behaviour: discovery, dry-run purity, diffs, idempotence."""

import hashlib
import os

from kubemend_engine import fix_file, scan_path
from kubemend_engine.engine import unified_diff
from kubemend_engine.loader import contexts_for_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VULNERABLE = os.path.join(ROOT, "examples", "vulnerable-app.yaml")
HARDENED = os.path.join(ROOT, "examples", "hardened-app.yaml")


def _ids(findings):
    return {f.rule_id for f in findings}


def test_example_triggers_every_rule():
    findings = scan_path(VULNERABLE)
    assert _ids(findings) == {f"KM{ n:03d}" for n in range(1, 11)}


def test_hardened_example_is_clean():
    assert scan_path(HARDENED) == []


def test_dry_run_never_touches_the_file():
    before = hashlib.sha256(open(VULNERABLE, "rb").read()).hexdigest()
    scan_path(VULNERABLE)
    fix_file(VULNERABLE)  # computes a patch in memory only
    after = hashlib.sha256(open(VULNERABLE, "rb").read()).hexdigest()
    assert before == after


def test_fix_then_rescan_leaves_only_km005(tmp_path):
    _original, patched, fixed = fix_file(VULNERABLE)
    assert len(fixed) == 9  # everything except guidance-only KM005
    target = tmp_path / "app.yaml"
    target.write_text(patched)
    assert _ids(scan_path(str(target))) == {"KM005"}


def test_unified_diff_shows_the_fix():
    original, patched, _fixed = fix_file(VULNERABLE)
    diff = unified_diff("app.yaml", original, patched)
    assert "runAsNonRoot" in diff
    assert diff.startswith("--- a/app.yaml")


def test_cronjob_pod_spec_discovery(tmp_path):
    cronjob = tmp_path / "cron.yaml"
    cronjob.write_text(
        "apiVersion: batch/v1\n"
        "kind: CronJob\n"
        "metadata:\n"
        "  name: backup\n"
        "spec:\n"
        "  schedule: '0 3 * * *'\n"
        "  jobTemplate:\n"
        "    spec:\n"
        "      template:\n"
        "        spec:\n"
        "          restartPolicy: OnFailure\n"
        "          containers:\n"
        "            - name: backup\n"
        "              image: busybox:1.36\n"
    )
    contexts = contexts_for_file(str(cronjob))
    assert len(contexts) == 1
    assert contexts[0].path_prefix == "spec.jobTemplate.spec.template.spec"
    findings = scan_path(str(cronjob))
    km001 = [f for f in findings if f.rule_id == "KM001"][0]
    assert km001.field_path.startswith("spec.jobTemplate.spec.template.spec.containers[0]")


def test_directory_scan_is_recursive_and_sorted(tmp_path):
    nested = tmp_path / "sub"
    nested.mkdir()
    (tmp_path / "a.yaml").write_text(open(VULNERABLE).read())
    (nested / "b.yml").write_text(open(VULNERABLE).read())
    findings = scan_path(str(tmp_path))
    files = [f.file for f in findings]
    assert files == sorted(files)
    assert len({f.file for f in findings}) == 2
