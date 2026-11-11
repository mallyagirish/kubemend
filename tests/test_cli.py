"""CLI behaviour: exit codes, --write, --explain, JSON output."""

import json
import shutil

from kubemend.cli import main

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VULNERABLE = os.path.join(ROOT, "examples", "vulnerable-app.yaml")
HARDENED = os.path.join(ROOT, "examples", "hardened-app.yaml")


def _copy(tmp_path):
    target = tmp_path / "app.yaml"
    shutil.copy(VULNERABLE, target)
    return str(target)


def test_scan_reports_findings_and_exits_1(tmp_path, capsys):
    assert main(["scan", _copy(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "KM001" in out and "KM005" in out
    assert "patch preview (dry run" in out


def test_scan_clean_exits_0(capsys):
    assert main(["scan", HARDENED]) == 0


def test_missing_path_exits_2(capsys):
    assert main(["scan", "/nonexistent/nope.yaml"]) == 2


def test_write_applies_patch(tmp_path, capsys):
    target = _copy(tmp_path)
    assert main(["scan", target, "--write"]) == 1  # KM005 still open
    capsys.readouterr()
    # auto-fixable rules are now clean; only guidance-only KM005 remains
    assert main(["scan", target, "--rules", "KM001,KM002,KM003,KM004,KM006,KM007,KM008,KM009,KM010"]) == 0


def test_explain_prints_rationale(tmp_path, capsys):
    assert main(["scan", _copy(tmp_path), "--rules", "KM006", "--explain"]) == 1
    out = capsys.readouterr().out
    assert "why:" in out and "root" in out


def test_json_format(tmp_path, capsys):
    assert main(["scan", _copy(tmp_path), "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["findings"]
    assert payload["patch"].startswith("--- a/")
    km005 = [f for f in payload["findings"] if f["rule_id"] == "KM005"][0]
    assert km005["fix_description"] is None
