"""KM006-KM010: pod and container security context basics."""

from __future__ import annotations

from ..model import Finding, WorkloadContext
from .base import Rule


class RunningAsRoot(Rule):
    id = "KM006"
    severity = "high"
    title = "Container may run as root"
    explanation = (
        "If a container runs as root and the app is compromised, the "
        "attacker is root inside the container - one kernel bug or one "
        "mis-mounted socket away from the node. Most applications never "
        "need it. Setting runAsNonRoot makes the kubelet refuse to start a "
        "container that would run as uid 0, turning a silent risk into a "
        "loud, early failure."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        pod_sc = self.pod_security_context(ctx)
        for i, container in enumerate(ctx.containers):
            sc = self.container_security_context(container)
            uid = sc.get("runAsUser", pod_sc.get("runAsUser"))
            non_root = sc.get("runAsNonRoot", pod_sc.get("runAsNonRoot"))
            if uid == 0:
                message = "container explicitly runs as uid 0 (root)"
            elif non_root is not True:
                message = "runAsNonRoot is not set at pod or container level"
            else:
                continue
            findings.append(
                self.finding(
                    ctx,
                    container=container.get("name"),
                    field_path=f"{ctx.container_path(i)}.securityContext",
                    message=message,
                    fix_description="set runAsNonRoot=true (and uid 0 becomes 10001)",
                )
            )
        return findings

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        for container in ctx.containers:
            if container.get("name") == finding.container:
                sc = self.ensure_container_security_context(container)
                changed = False
                if sc.get("runAsNonRoot") is not True:
                    sc["runAsNonRoot"] = True
                    changed = True
                if sc.get("runAsUser") == 0:
                    sc["runAsUser"] = 10001
                    changed = True
                return changed
        return False


class PrivilegeEscalationAllowed(Rule):
    id = "KM007"
    severity = "high"
    title = "Privilege escalation not disabled"
    explanation = (
        "allowPrivilegeEscalation controls whether a process can gain more "
        "privileges than its parent - via setuid binaries like sudo or "
        "su. Almost no workload needs it. Setting it to false is a one-line "
        "change that closes a classic container-escape helper, and the "
        "restricted Pod Security Standard requires it."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        for i, container in enumerate(ctx.containers):
            sc = self.container_security_context(container)
            if sc.get("allowPrivilegeEscalation") is not False:
                findings.append(
                    self.finding(
                        ctx,
                        container=container.get("name"),
                        field_path=(
                            f"{ctx.container_path(i)}.securityContext.allowPrivilegeEscalation"
                        ),
                        message="allowPrivilegeEscalation is not set to false",
                        fix_description="set allowPrivilegeEscalation=false",
                    )
                )
        return findings

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        for container in ctx.containers:
            if container.get("name") == finding.container:
                sc = self.ensure_container_security_context(container)
                if sc.get("allowPrivilegeEscalation") is not False:
                    sc["allowPrivilegeEscalation"] = False
                    return True
        return False


class MissingSeccompProfile(Rule):
    id = "KM008"
    severity = "medium"
    title = "Missing seccomp profile"
    explanation = (
        "Seccomp filters the system calls a container can make. The "
        "RuntimeDefault profile blocks the dangerous minority (the calls "
        "used for kernel exploits and container escapes) while letting "
        "normal applications run untouched. Without any profile the "
        "container gets the kernel's full syscall surface."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        pod_sc = self.pod_security_context(ctx)
        if (pod_sc.get("seccompProfile") or {}).get("type"):
            return []
        for container in ctx.containers:
            sc = self.container_security_context(container)
            if (sc.get("seccompProfile") or {}).get("type"):
                return []
        return [
            self.finding(
                ctx,
                container=None,
                field_path=f"{ctx.path_prefix}.securityContext.seccompProfile",
                message="no seccompProfile set at pod or container level",
                fix_description="set pod seccompProfile.type=RuntimeDefault",
            )
        ]

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        sc = self.ensure_pod_security_context(ctx)
        if not (sc.get("seccompProfile") or {}).get("type"):
            sc["seccompProfile"] = {"type": "RuntimeDefault"}
            return True
        return False


class HostNamespacesEnabled(Rule):
    id = "KM009"
    severity = "high"
    title = "Host namespaces enabled"
    explanation = (
        "hostNetwork, hostPID, and hostIPC tear down the walls between a "
        "pod and its node: the pod can see the node's network traffic, its "
        "processes, or its shared memory. A compromised pod with a host "
        "namespace is effectively a process on the node. A handful of "
        "system daemons need this; application workloads essentially never "
        "do."
    )
    FLAGS = ("hostNetwork", "hostPID", "hostIPC")

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        enabled = [flag for flag in self.FLAGS if ctx.pod_spec.get(flag) is True]
        if not enabled:
            return []
        return [
            self.finding(
                ctx,
                container=None,
                field_path=ctx.path_prefix,
                message=f"host namespaces enabled: {', '.join(enabled)}",
                fix_description=f"set {', '.join(enabled)} to false",
            )
        ]

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        changed = False
        for flag in self.FLAGS:
            if ctx.pod_spec.get(flag) is True:
                ctx.pod_spec[flag] = False
                changed = True
        return changed


class CapabilitiesNotDropped(Rule):
    id = "KM010"
    severity = "medium"
    title = "Capabilities not dropped"
    explanation = (
        "Linux capabilities slice root's powers into pieces, but the "
        "default set still includes several an ordinary app never uses. "
        "Dropping ALL and adding back only what is needed is the standard "
        "least-privilege posture - it is required by the restricted Pod "
        "Security Standard and costs a typical web app nothing."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        for i, container in enumerate(ctx.containers):
            sc = self.container_security_context(container)
            caps = sc.get("capabilities") or {}
            drop = caps.get("drop") or []
            if "ALL" not in drop:
                findings.append(
                    self.finding(
                        ctx,
                        container=container.get("name"),
                        field_path=f"{ctx.container_path(i)}.securityContext.capabilities",
                        message="capabilities.drop does not include ALL",
                        fix_description='set capabilities.drop to ["ALL"]',
                    )
                )
        return findings

    def apply_fix(self, ctx: WorkloadContext, finding: Finding) -> bool:
        for container in ctx.containers:
            if container.get("name") == finding.container:
                sc = self.ensure_container_security_context(container)
                caps = sc.get("capabilities")
                if not isinstance(caps, dict):
                    caps = {}
                    sc["capabilities"] = caps
                drop = caps.get("drop") or []
                if "ALL" not in drop:
                    caps["drop"] = ["ALL"]
                    return True
        return False
