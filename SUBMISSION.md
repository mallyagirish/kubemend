# Devpost submission draft - Kiroween 2026

> Draft for review. Everything below maps to the official rules at
> https://kiroween.devpost.com/rules (checked 2026-11-11).
> Submission deadline: **December 4, 2026, 2:00 pm Pacific Time.**

## Project name

KubeMend

## Tagline

Kubernetes scanners tell you what's wrong. KubeMend writes the fix - as a
reviewable patch.

## Category

**Skeleton Crew** - one lean foundation (the `kubemend_engine` rule engine)
shown through two distinct applications in two separate repo folders, as
the category requires:

- `apps/kubemend-cli/` - **kubemend**, the scan-and-patch CLI for engineers
  in the terminal and in CI.
- `apps/kubemend-report/` - **kubemend-report**, an audit-report generator
  (Markdown / HTML) for reviewers and tickets.

Bonus categories: none claimed. (Optional extras if time permits before
Dec 4: Bonus Blog post about the build, and a Social Blitz post starting
with #KiroweenHackathon26 - both are cheap and judged separately.)

## Description (for the Devpost form)

Every Kubernetes team knows the review comments by heart: no resource
requests, no readiness probe, this can run as root. Scanners already find
these problems - teams drown in warning lists and then hand-edit YAML,
which is slow and easy to get wrong.

KubeMend is a CLI that scans manifests and Helm-rendered YAML for ten
well-known hardening misconfigurations and generates the fix as a minimal,
unified-diff patch you can review like any other code change. Every finding
cites the exact field path (`spec.template.spec.containers[0].resources.requests`),
and `--explain` prints a short plain-English rationale per rule, so a
finding doubles as a teaching moment. It is safe by default: a scan never
modifies a file unless you pass `--write`, and exit codes (0 clean / 1
findings / 2 scan error) make it CI-friendly.

One rule is deliberately patch-free: KM005 flags images that are not pinned
by digest, but KubeMend refuses to invent a digest it cannot know - it
prints the exact registry command to get the real one instead. A patch that
fails to pull is worse than no patch.

The foundation is a small, thoroughly tested rule engine
(`kubemend_engine`, 38 tests, a vulnerable/fixed fixture pair per rule).
Two applications sit on top of it: the `kubemend` CLI and `kubemend-report`,
which renders the same findings as a shareable Markdown or HTML audit
report. Install is one command (`pip install -e .`), the only runtime
dependency is PyYAML, and there is no cluster, network, or account involved
at scan time.

## How Kiro was used (required write-up)

KubeMend was built spec-first with Kiro, and the evidence is in the public
repo under `/.kiro/` (committed, not gitignored, per the rules):

- **Spec-driven development:** `.kiro/specs/kubemend/requirements.md` was
  written first - user stories with EARS acceptance criteria (including
  dry-run purity and fix idempotence as explicit criteria) - followed by
  `design.md` (architecture and the per-rule fix strategy) and `tasks.md`,
  the checklist the implementation then followed in order: engine, rules in
  two batches, CLI, report app, hook, demo. Compared with vibe coding, the
  spec paid off most where correctness is checkable: the acceptance
  criteria became the test suite almost verbatim.
- **Steering docs:** `.kiro/steering/product.md` fixed the principles
  (safe by default, never fabricate values - the decision that made KM005
  guidance-only came from here), `tech.md` fixed the rule contract and
  determinism rules, and `structure.md` fixed layout and naming. Writing
  these once kept ten rules and two apps consistent without re-explaining
  conventions in every prompt.
- **Agent hooks:** `.kiro/hooks/run-tests-on-rule-save.kiro.hook` runs the
  rule test suite automatically whenever a file under
  `engine/kubemend_engine/rules/` is saved. Rules are the heart of the
  tool; the hook turns "did I break a check?" into an instant signal
  instead of a release-time surprise.
- **What was not used:** no MCP servers and no custom agents - the project
  is a single-package Python tool, and the honest stack was specs +
  steering + one well-aimed hook.

## What-to-submit checklist (mapped to the rules)

- [x] **GitHub repo public** with all source + instructions:
      https://github.com/mallyagirish/kubemend (published 2026-11-11).
- [x] **Open-source license file** at repo root, detectable in the About
      section - MIT `LICENSE` is in place (verified via GitHub API).
- [ ] **`/.kiro` directory at repo root**, committed, NOT in `.gitignore` -
      in place (specs, steering, hooks). Double-check `.gitignore` after
      publishing: it ignores Python artifacts only.
- [ ] **Category identified:** Skeleton Crew; repo contains 2 separate
      folders for the 2 applications (`apps/kubemend-cli/`,
      `apps/kubemend-report/`).
- [ ] **Text description** - the Description above.
- [ ] **Kiro usage write-up** - the section above (also in the README).
- [x] **Demo video < 3 minutes, public on YouTube**, showing the project
      running: https://youtu.be/6NNdYAMbQNI (1:27, published 2026-11-11;
      narrated version — voiceover walkthrough of demo.sh: scan -> explain
      -> --write -> rescan -> report, plus the `.kiro/` folder. Replaced
      the original silent upload on 2026-11-11 at Girish's choice; the
      old youtu.be/a3rQq3h3dDY video was deleted).
- [ ] **Project built during the Submission Period** (Oct 30 - Dec 4,
      2026) and new - yes; built Nov 2026.
- [ ] **Testing access:** repo is public and self-contained; judges can
      `pip install -e .` and run `./demo.sh` or `python -m kubemend scan
      examples/vulnerable-app.yaml`. No credentials needed.
- [x] **Register + submit** on kiroween.devpost.com before Dec 4, 2026,
      2:00 pm PT. Solo entry (teams up to 3 allowed). **SUBMITTED
      2026-11-11: https://devpost.com/software/kubemend** (green SUBMITTED
      badge; editable until the deadline). Route there was bumpy:
      Cloudflare Turnstile blocked the registration page in the automated
      browser, so Girish registered in his own browser and created the
      project shell there (reCAPTCHA), then Muse filled and submitted
      from the cloud session. No Kiro user ID field appeared in the
      Devpost flow — the ID is only for the separate credits form.
- [ ] Optional: request the 4,000 Kiro credits via the Credit Request Form
      **by Dec 1, 2026, 12:00 pm PT** (needs Kiro user ID / AWS account ID).
- [ ] Optional bonus: publish the build blog post (must mention Kiroween
      2026) and/or a Social Blitz post starting with #KiroweenHackathon26,
      both during the submission period, and paste the links in the form.

## Judging-criteria notes (for the final review pass)

- *Potential Impact:* real, common problem; patch output is the difference
  between a warning and a fix.
- *Technological Implementation:* specs + steering + hook are real,
  load-bearing artifacts in the repo, not decoration.
- *Design:* one-command install, dry-run default, consistent output,
  honest edge cases (KM005).
- *Innovation:* scanners are common; reviewable auto-patches with an
  explain mode and a no-fabrication rule are the twist.
- *Presentation:* demo.sh is the video script; keep it under 3 minutes.
