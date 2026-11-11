"""Data types shared by the engine, the rules, and both applications."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Finding:
    """One rule violation in one workload (or one container in it)."""

    rule_id: str
    severity: str  # "high" | "medium" | "low"
    title: str
    file: str  # path of the YAML file the finding came from
    resource: str  # e.g. "Deployment/default/web"
    container: str | None  # container name, or None for pod-level findings
    field_path: str  # e.g. "spec.template.spec.containers[0].resources"
    message: str  # what is wrong, one line
    explanation: str  # plain-English rationale (risks + why the fix helps)
    fix_description: str | None  # what the patch does; None = guidance-only


@dataclass
class WorkloadContext:
    """A pod spec located inside a YAML document, plus where it lives."""

    file: str
    kind: str
    name: str
    namespace: str
    pod_spec: dict
    path_prefix: str  # e.g. "spec.template.spec" ("spec" for a bare Pod)
    document: dict = field(repr=False, default=None)  # the whole YAML doc

    @property
    def resource(self) -> str:
        return f"{self.kind}/{self.namespace}/{self.name}"

    @property
    def containers(self) -> list[dict]:
        return self.pod_spec.get("containers") or []

    def container_path(self, index: int) -> str:
        return f"{self.path_prefix}.containers[{index}]"
