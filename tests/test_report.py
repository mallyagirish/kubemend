"""Report app: same engine results, rendered for sharing."""

import os

from kubemend_engine import scan_path
from kubemend_report.report import main, render_html, render_markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VULNERABLE = os.path.join(ROOT, "examples", "vulnerable-app.yaml")


def test_markdown_report_contents():
    report = render_markdown(scan_path(VULNERABLE), VULNERABLE)
    assert "# KubeMend audit report" in report
    assert "## By rule" in report
    for rule_id in ("KM001", "KM005", "KM009"):
        assert rule_id in report


def test_html_report_contents():
    page = render_html(scan_path(VULNERABLE), VULNERABLE)
    assert page.startswith("<!DOCTYPE html>")
    assert "<table>" in page and "KM001" in page


def test_report_main_writes_file(tmp_path):
    out = tmp_path / "report.md"
    assert main([VULNERABLE, "--out", str(out)]) == 0
    assert "KubeMend audit report" in out.read_text()
