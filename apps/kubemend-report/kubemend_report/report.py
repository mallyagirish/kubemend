"""kubemend-report: turn a scan into a shareable audit report.

Same engine as the CLI, different audience: this is the artifact you attach
to a ticket or a review - counts by rule and severity, every finding with
its rationale, and the recommended fix - as Markdown or a single
self-contained HTML page.
"""

from __future__ import annotations

import argparse
import html
import sys
from collections import Counter

from kubemend_engine import ScanError, scan_path

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _sorted(findings):
    return sorted(
        findings,
        key=lambda f: (f.file, SEVERITY_ORDER.get(f.severity, 3), f.rule_id),
    )


def render_markdown(findings, target: str) -> str:
    findings = _sorted(findings)
    lines = [
        "# KubeMend audit report",
        "",
        f"Target: `{target}`  ",
        f"Findings: **{len(findings)}** across {len({f.file for f in findings})} file(s)",
        "",
        "## By rule",
        "",
        "| Rule | Title | Severity | Count |",
        "| --- | --- | --- | --- |",
    ]
    by_rule = Counter(f.rule_id for f in findings)
    seen = {}
    for f in findings:
        seen.setdefault(f.rule_id, f)
    for rule_id, count in sorted(by_rule.items()):
        f = seen[rule_id]
        lines.append(f"| {rule_id} | {f.title} | {f.severity} | {count} |")
    lines += ["", "## Findings", ""]
    for f in findings:
        where = f.resource + (f" (container: {f.container})" if f.container else "")
        lines += [
            f"### [{f.rule_id}] {f.title} - {f.severity}",
            "",
            f"- **Where:** `{f.file}` - {where}",
            f"- **Field:** `{f.field_path}`",
            f"- **Problem:** {f.message}",
            f"- **Fix:** {f.fix_description or 'manual - see rationale'}",
            f"- **Why it matters:** {f.explanation}",
            "",
        ]
    if not findings:
        lines.append("No findings. The scanned manifests pass every KubeMend rule.")
    return "\n".join(lines) + "\n"


def render_html(findings, target: str) -> str:
    findings = _sorted(findings)
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(f.rule_id)}</td>"
        f"<td>{html.escape(f.severity)}</td>"
        f"<td>{html.escape(f.resource)}</td>"
        f"<td><code>{html.escape(f.field_path)}</code></td>"
        f"<td>{html.escape(f.message)}</td>"
        f"<td>{html.escape(f.fix_description or 'manual')}</td>"
        "</tr>"
        for f in findings
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>KubeMend audit report</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }}
  th {{ background: #1f2430; color: #f5f0e6; }}
  code {{ font-size: 0.85em; }}
</style>
</head>
<body>
<h1>KubeMend audit report</h1>
<p>Target: <code>{html.escape(target)}</code> &middot; {len(findings)} finding(s)</p>
<table>
<tr><th>Rule</th><th>Severity</th><th>Resource</th><th>Field</th><th>Problem</th><th>Fix</th></tr>
{rows}
</table>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kubemend-report",
        description="Generate a KubeMend audit report (Markdown or HTML) for a YAML file or directory.",
    )
    parser.add_argument("path", help="YAML file or directory to scan")
    parser.add_argument("--format", choices=("md", "html"), default="md")
    parser.add_argument("--out", help="write the report here (default: stdout)")
    args = parser.parse_args(argv)
    try:
        findings = scan_path(args.path)
    except ScanError as exc:
        print(f"kubemend-report: {exc}", file=sys.stderr)
        return 2
    text = render_html(findings, args.path) if args.format == "html" else render_markdown(findings, args.path)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"wrote {args.out} ({len(findings)} finding(s))")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
