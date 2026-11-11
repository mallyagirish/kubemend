"""KM003/KM004: readiness and liveness probes.

The generated probe points at /health on the container's first declared
port (falling back to 8080). /health is the near-universal convention; the
fix description tells the user to adjust the path if their app differs.
"""

from __future__ import annotations

from ..model import Finding, WorkloadContext
from .base import Rule


def _probe_port(container: dict) -> int:
    for port in container.get("ports") or []:
        if isinstance(port, dict) and port.get("containerPort"):
            return int(port["containerPort"])
    return 8080


def _probe(container: dict, initial_delay: int, period: int) -> dict:
    return {
        "httpGet": {"path": "/health", "port": _probe_port(container)},
        "initialDelaySeconds": initial_delay,
        "periodSeconds": period,
        "timeoutSeconds": 5,
        "failureThreshold": 3,
    }


class MissingReadinessProbe(Rule):
    id = "KM003"
    severity = "medium"
    title = "Missing readiness probe"
    explanation = (
        "Without a readiness probe, Kubernetes sends traffic to a pod the "
        "moment its container starts - before the app has loaded models, "
        "warmed caches, or opened its database pool. Users see 5xx errors on "
        "every deploy and every scale-up. A readiness probe holds traffic "
        "back until the app says it is actually ready."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        for i, container in enumerate(ctx.containers):
            if not container.get("readinessProbe"):
                findings.append(
                    self.finding(
                        ctx,
                        container=container.get("name"),
                        field_path=f"{ctx.container_path(i)}.readinessProbe",
                        message="container has no readinessProbe",
                        fix_description=(
                            "add an httpGet readiness probe on /health "
                            "(adjust the path if your app uses a different one)"
                        ),
                    )
                )
        return findings

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        for container in ctx.containers:
            if container.get("name") == finding.container and not container.get("readinessProbe"):
                container["readinessProbe"] = _probe(container, initial_delay=5, period=10)
                return True
        return False


class MissingLivenessProbe(Rule):
    id = "KM004"
    severity = "low"
    title = "Missing liveness probe"
    explanation = (
        "A liveness probe is how Kubernetes notices a process that is alive "
        "but wedged - deadlocked, stuck on a dead connection, out of file "
        "handles - and restarts it instead of leaving it to fail requests "
        "forever. Without one, the only cure for a zombie pod is a human "
        "with kubectl at 3am."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        for i, container in enumerate(ctx.containers):
            if not container.get("livenessProbe"):
                findings.append(
                    self.finding(
                        ctx,
                        container=container.get("name"),
                        field_path=f"{ctx.container_path(i)}.livenessProbe",
                        message="container has no livenessProbe",
                        fix_description=(
                            "add an httpGet liveness probe on /health "
                            "(adjust the path if your app uses a different one)"
                        ),
                    )
                )
        return findings

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        for container in ctx.containers:
            if container.get("name") == finding.container and not container.get("livenessProbe"):
                container["livenessProbe"] = _probe(container, initial_delay=15, period=20)
                return True
        return False
