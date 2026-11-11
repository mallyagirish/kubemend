"""YAML loading and pod-spec discovery.

Supports plain manifests, multi-document files, and rendered output from
tools like `helm template` or `kustomize build` (which is just YAML).
Non-workload documents (Services, ConfigMaps, ...) are skipped quietly.
"""

from __future__ import annotations

import os

import yaml

from .model import WorkloadContext

# kind -> path of the pod spec inside the document
_POD_SPEC_PATHS = {
    "Pod": ("spec",),
    "Deployment": ("spec", "template", "spec"),
    "StatefulSet": ("spec", "template", "spec"),
    "DaemonSet": ("spec", "template", "spec"),
    "ReplicaSet": ("spec", "template", "spec"),
    "Job": ("spec", "template", "spec"),
    "CronJob": ("spec", "jobTemplate", "spec", "template", "spec"),
}

YAML_SUFFIXES = (".yaml", ".yml")


def iter_yaml_files(path: str) -> list[str]:
    """Expand a file or directory path into a sorted list of YAML files."""
    if os.path.isfile(path):
        return [path]
    found = []
    for root, _dirs, names in os.walk(path):
        for name in names:
            if name.endswith(YAML_SUFFIXES):
                found.append(os.path.join(root, name))
    return sorted(found)


def load_documents(path: str) -> list[dict]:
    """Parse a YAML file into its documents (dicts only, empties dropped)."""
    with open(path, encoding="utf-8") as handle:
        docs = list(yaml.safe_load_all(handle))
    return [doc for doc in docs if isinstance(doc, dict)]


def _dig(doc: dict, keys: tuple[str, ...]):
    node = doc
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def find_workloads(doc: dict, file: str) -> list[WorkloadContext]:
    """Return a WorkloadContext for the doc if it is a supported workload."""
    kind = doc.get("kind")
    if kind not in _POD_SPEC_PATHS:
        return []
    keys = _POD_SPEC_PATHS[kind]
    pod_spec = _dig(doc, keys)
    if not isinstance(pod_spec, dict) or not isinstance(pod_spec.get("containers"), list):
        return []
    metadata = doc.get("metadata") or {}
    return [
        WorkloadContext(
            file=file,
            kind=kind,
            name=metadata.get("name", "<unnamed>"),
            namespace=metadata.get("namespace", "default"),
            pod_spec=pod_spec,
            path_prefix=".".join(keys),
            document=doc,
        )
    ]


def contexts_for_file(path: str) -> list[WorkloadContext]:
    contexts: list[WorkloadContext] = []
    for doc in load_documents(path):
        contexts.extend(find_workloads(doc, path))
    return contexts
