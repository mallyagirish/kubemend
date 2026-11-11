"""KM001/KM002: resource requests and limits.

Defaults are deliberately modest starting points. A patch sets them so the
manifest passes review and the scheduler behaves sanely; teams are expected
to tune the numbers to real usage afterwards (the fix text says so).
"""

from __future__ import annotations

from ..model import Finding, WorkloadContext
from .base import Rule

DEFAULT_REQUESTS = {"cpu": "250m", "memory": "512Mi"}
DEFAULT_LIMITS = {"cpu": "500m", "memory": "1Gi"}


def _missing(container: dict, block: str) -> list[str]:
    resources = container.get("resources") or {}
    values = resources.get(block) or {}
    return [key for key in ("cpu", "memory") if not values.get(key)]


def _set_block(container: dict, block: str, defaults: dict) -> bool:
    resources = container.get("resources")
    if not isinstance(resources, dict):
        resources = {}
        container["resources"] = resources
    values = resources.get(block)
    if not isinstance(values, dict):
        values = {}
        resources[block] = values
    changed = False
    for key, default in defaults.items():
        if not values.get(key):
            values[key] = default
            changed = True
    return changed


class MissingRequests(Rule):
    id = "KM001"
    severity = "medium"
    title = "Missing resource requests"
    explanation = (
        "Requests tell the scheduler how much CPU and memory a container "
        "actually needs. Without them, pods get packed onto nodes blind: a "
        "few greedy containers can starve their neighbours, and the pod has "
        "no guaranteed floor when the node is under pressure. Setting "
        "requests is the single highest-leverage scheduling fix."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        for i, container in enumerate(ctx.containers):
            missing = _missing(container, "requests")
            if missing:
                findings.append(
                    self.finding(
                        ctx,
                        container=container.get("name"),
                        field_path=f"{ctx.container_path(i)}.resources.requests",
                        message=f"no {'/'.join(missing)} request set",
                        fix_description=(
                            "set requests to cpu=250m, memory=512Mi "
                            "(starting point - tune to real usage)"
                        ),
                    )
                )
        return findings

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        for container in ctx.containers:
            if container.get("name") == finding.container:
                return _set_block(container, "requests", DEFAULT_REQUESTS)
        return False


class MissingLimits(Rule):
    id = "KM002"
    severity = "medium"
    title = "Missing resource limits"
    explanation = (
        "Limits are the ceiling that keeps one runaway container from eating "
        "the whole node. A memory leak or a busy loop without limits can "
        "OOM-kill neighbouring pods that did nothing wrong. Limits make the "
        "blast radius of a misbehaving container its own pod."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        for i, container in enumerate(ctx.containers):
            missing = _missing(container, "limits")
            if missing:
                findings.append(
                    self.finding(
                        ctx,
                        container=container.get("name"),
                        field_path=f"{ctx.container_path(i)}.resources.limits",
                        message=f"no {'/'.join(missing)} limit set",
                        fix_description=(
                            "set limits to cpu=500m, memory=1Gi "
                            "(starting point - tune to real usage)"
                        ),
                    )
                )
        return findings

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        for container in ctx.containers:
            if container.get("name") == finding.container:
                return _set_block(container, "limits", DEFAULT_LIMITS)
        return False
