"""Scan + fix orchestration.

scan_path: parse files, find workloads, run rules, collect findings.
fix_file:  parse one file, apply every auto-fixable finding to the parsed
           documents, re-serialize, and return a unified diff. Nothing is
           written by this module - the caller decides (dry-run by default).
"""

from __future__ import annotations

import difflib
import os

import yaml

from .loader import contexts_for_file, iter_yaml_files, load_documents, find_workloads
from .model import Finding
from .rules import ALL_RULES, RULES_BY_ID


class ScanError(Exception):
    """Raised when a scan target cannot be read at all."""


class _IndentDumper(yaml.SafeDumper):
    """SafeDumper that indents list items under their key (the usual
    Kubernetes YAML style), so generated patches stay minimal."""

    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow, False)


def _rules(rule_ids: list[str] | None):
    if not rule_ids:
        return ALL_RULES
    unknown = [r for r in rule_ids if r not in RULES_BY_ID]
    if unknown:
        raise ScanError(f"unknown rule id(s): {', '.join(unknown)}")
    return [RULES_BY_ID[r] for r in rule_ids]


def scan_path(path: str, rule_ids: list[str] | None = None) -> list[Finding]:
    """Scan a file or directory and return all findings, in stable order."""
    if not os.path.exists(path):
        raise ScanError(f"no such file or directory: {path}")
    rules = _rules(rule_ids)
    findings: list[Finding] = []
    for file in iter_yaml_files(path):
        try:
            contexts = contexts_for_file(file)
        except yaml.YAMLError:
            continue  # a broken file in a tree should not abort the scan
        for ctx in contexts:
            for rule in rules:
                findings.extend(rule.check(ctx))
    return findings


def fix_file(path: str, rule_ids: list[str] | None = None) -> tuple[str, str, list[Finding]]:
    """Apply fixes to one file in memory.

    Returns (original_text, patched_text, fixed_findings). The caller writes
    patched_text only when the user passed --write.
    """
    rules = _rules(rule_ids)
    with open(path, encoding="utf-8") as handle:
        original_text = handle.read()
    docs = load_documents(path)
    fixed: list[Finding] = []
    for doc in docs:
        for ctx in find_workloads(doc, path):
            for rule in rules:
                for finding in rule.check(ctx):
                    if finding.fix_description is not None and rule.apply_fix(ctx, finding):
                        fixed.append(finding)
    if not fixed:
        return original_text, original_text, []
    patched_text = yaml.dump_all(
        docs, Dumper=_IndentDumper, default_flow_style=False, sort_keys=False
    )
    return original_text, patched_text, fixed


def unified_diff(path: str, original: str, patched: str) -> str:
    """Render a git-style unified diff for one file ('' when unchanged)."""
    if original == patched:
        return ""
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        patched.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(diff)
