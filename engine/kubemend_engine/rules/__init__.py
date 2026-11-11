"""Rule registry: every rule class, in stable ID order."""

from .base import Rule
from .images import MutableImageTag
from .probes import MissingLivenessProbe, MissingReadinessProbe
from .resources import MissingLimits, MissingRequests
from .security import (
    CapabilitiesNotDropped,
    HostNamespacesEnabled,
    MissingSeccompProfile,
    PrivilegeEscalationAllowed,
    RunningAsRoot,
)

ALL_RULES: list[Rule] = [
    MissingRequests(),
    MissingLimits(),
    MissingReadinessProbe(),
    MissingLivenessProbe(),
    MutableImageTag(),
    RunningAsRoot(),
    PrivilegeEscalationAllowed(),
    MissingSeccompProfile(),
    HostNamespacesEnabled(),
    CapabilitiesNotDropped(),
]

RULES_BY_ID = {rule.id: rule for rule in ALL_RULES}

__all__ = ["ALL_RULES", "RULES_BY_ID", "Rule"]
