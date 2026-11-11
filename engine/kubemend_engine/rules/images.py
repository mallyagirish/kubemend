"""KM005: mutable image tags.

This rule is guidance-only on purpose. Pinning an image means writing a
real sha256 digest, and the correct digest lives in the registry, not in
the manifest. A tool that invents one would produce patches that fail to
pull - worse than no patch. KubeMend flags the exact field and prints the
commands to get the real digest instead.
"""

from __future__ import annotations

from ..model import Finding, WorkloadContext
from .base import Rule


def _is_mutable(image: str) -> bool:
    if "@sha256:" in image:
        return False  # pinned by digest
    last_slash = image.rfind("/")
    last_colon = image.rfind(":")
    if last_colon <= last_slash:
        return True  # no tag at all -> implicit :latest
    return image[last_colon + 1 :] in ("", "latest")


class MutableImageTag(Rule):
    id = "KM005"
    severity = "high"
    title = "Mutable image tag"
    explanation = (
        "An image referenced by a mutable tag (or no tag, which means "
        ":latest) can change under you: the same manifest deploys different "
        "bits on different days, rollbacks stop being reliable, and a "
        "compromised or careless push goes straight to production. Pinning "
        "by digest makes a deployment reproducible. KubeMend does not "
        "auto-fix this rule because it cannot know the real digest - get it "
        "from your registry, e.g. `docker buildx imagetools inspect "
        "<image>:<tag>`, and write `image: <image>@sha256:<digest>`."
    )

    def check(self, ctx: WorkloadContext) -> list[Finding]:
        findings = []
        for i, container in enumerate(ctx.containers):
            image = container.get("image") or ""
            if not image or _is_mutable(image):
                findings.append(
                    self.finding(
                        ctx,
                        container=container.get("name"),
                        field_path=f"{ctx.container_path(i)}.image",
                        message=f"image {image or '<missing>'!r} is not pinned by digest",
                        fix_description=None,  # guidance-only, see explanation
                    )
                )
        return findings

    # apply_fix intentionally not implemented: never fabricate a digest.
