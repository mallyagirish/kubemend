"""The rule contract.

A rule looks at one WorkloadContext and produces Findings. If the rule can
fix what it found mechanically and safely, it also implements apply_fix,
which mutates the parsed pod spec in place. Rules never do I/O.
"""

from __future__ import annotations

from ..model import Finding, WorkloadContext


class Rule:
    id: str = "KM000"
    severity: str = "medium"
    title: str = ""
    explanation: str = ""

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        raise NotImplementedError

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        """Mutate ctx.pod_spec to resolve `finding`. Return True if changed.

        Rules that cannot fix safely (they would have to invent data) leave
        this unimplemented and return False.
        """
        return False

    # -- helpers shared by rules -------------------------------------------

    def finding(
        self,
        ctx: WorkloadContext,
        *,
        container: str | None,
        field_path: str,
        message: str,
        fix_description: str | None,
    ) -> Finding:
        return Finding(
            rule_id=self.id,
            severity=self.severity,
            title=self.title,
            file=ctx.file,
            resource=ctx.resource,
            container=container,
            field_path=field_path,
            message=message,
            explanation=self.explanation,
            fix_description=fix_description,
        )

    @staticmethod
    def container_security_context(container: dict) -> dict:
        return container.get("securityContext") or {}

    @staticmethod
    def ensure_container_security_context(container: dict) -> dict:
        sc = container.get("securityContext")
        if not isinstance(sc, dict):
            sc = {}
            container["securityContext"] = sc
        return sc

    @staticmethod
    def pod_security_context(ctx: WorkloadContext) -> dict:
        return ctx.pod_spec.get("securityContext") or {}

    @staticmethod
    def ensure_pod_security_context(ctx: WorkloadContext) -> dict:
        sc = ctx.pod_spec.get("securityContext")
        if not isinstance(sc, dict):
            sc = {}
            ctx.pod_spec["securityContext"] = sc
        return sc
