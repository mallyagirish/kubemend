"""kubemend command line: `kubemend scan <path> [--write] [--explain]`.

Dry-run is the default: findings and the patch are printed, nothing on
disk changes. --write applies the patch in place. Exit codes: 0 = clean,
1 = findings, 2 = the scan itself failed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from kubemend_engine import ScanError, fix_file, scan_path
from kubemend_engine.engine import unified_diff


def _print_text(findings, explain: bool) -> None:
    current_file = None
    for finding in findings:
        if finding.file != current_file:
            current_file = finding.file
            print(f"\n{finding.file}")
        where = finding.resource
        if finding.container:
            where += f" (container: {finding.container})"
        print(f"  {where}")
        print(f"    [{finding.rule_id}] {finding.severity:<6} {finding.title} - {finding.message}")
        print(f"      at {finding.field_path}")
        if finding.fix_description:
            print(f"      fix: {finding.fix_description}")
        else:
            print("      fix: manual - see --explain for how to resolve")
        if explain:
            print(f"      why: {finding.explanation}")


def _summary(findings, fixed_count: int | None = None) -> str:
    fixable = sum(1 for f in findings if f.fix_description)
    files = len({f.file for f in findings})
    text = f"\n{len(findings)} finding(s) in {files} file(s); {fixable} auto-fixable"
    if fixed_count is not None:
        text += f"; {fixed_count} fixed"
    return text


def cmd_scan(args: argparse.Namespace) -> int:
    rule_ids = args.rules.split(",") if args.rules else None
    try:
        findings = scan_path(args.path, rule_ids)
    except ScanError as exc:
        print(f"kubemend: {exc}", file=sys.stderr)
        return 2

    fixed: list = []
    diffs: list[str] = []
    if findings:
        for file in sorted({f.file for f in findings}):
            original, patched, file_fixed = fix_file(file, rule_ids)
            fixed.extend(file_fixed)
            diff = unified_diff(file, original, patched)
            if diff:
                diffs.append(diff)
            if args.write and patched != original:
                with open(file, "w", encoding="utf-8") as handle:
                    handle.write(patched)

    if args.format == "json":
        payload = {
            "findings": [asdict(f) for f in findings],
            "fixed": [asdict(f) for f in fixed] if args.write else [],
            "patch": "".join(diffs),
        }
        print(json.dumps(payload, indent=2))
    else:
        if not findings:
            print("No findings - everything scanned passes all KubeMend rules.")
        else:
            _print_text(findings, args.explain)
            print(_summary(findings, len(fixed) if args.write else None))
            if diffs:
                heading = "patch applied:" if args.write else "patch preview (dry run; pass --write to apply):"
                print(f"\n--- {heading} ---")
                print("".join(diffs), end="")
    return 1 if findings else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kubemend",
        description="Scan Kubernetes YAML for hardening mistakes and generate the fixes as patches.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="scan a YAML file or directory")
    scan.add_argument("path", help="YAML file or directory to scan")
    scan.add_argument(
        "--write",
        action="store_true",
        help="apply the generated patch in place (default is a dry run)",
    )
    scan.add_argument(
        "--explain",
        action="store_true",
        help="print the plain-English rationale for each rule",
    )
    scan.add_argument("--format", choices=("text", "json"), default="text")
    scan.add_argument("--rules", help="comma-separated rule IDs to run (default: all)")
    scan.set_defaults(func=cmd_scan)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
