# Tasks: KubeMend

- [x] 1. Scaffold the repo: root pyproject, LICENSE, .gitignore, steering docs
- [x] 2. Write the spec (requirements, design, this task list) before code
- [x] 3. Engine foundation
  - [x] 3.1 `model.py`: Finding and WorkloadContext dataclasses
  - [x] 3.2 `loader.py`: YAML loading + pod-spec discovery for 7 workload kinds
  - [x] 3.3 `rules/base.py`: rule contract + registry
- [x] 4. Rules batch 1 (resources and probes)
  - [x] 4.1 KM001/KM002 in `rules/resources.py` + fixtures + tests
  - [x] 4.2 KM003/KM004 in `rules/probes.py` + fixtures + tests
- [x] 5. Rules batch 2 (image and security context)
  - [x] 5.1 KM005 in `rules/images.py` (guidance-only) + fixtures + tests
  - [x] 5.2 KM006-KM010 in `rules/security.py` + fixtures + tests
- [x] 6. `engine.py`: scan orchestration, fix application, unified diff output
- [x] 7. Application 1: `kubemend` CLI (scan, --write, --explain, --format, exit codes)
- [x] 8. Application 2: `kubemend-report` (Markdown + HTML audit reports)
- [x] 9. Kiro agent hook: run rule tests when a rule file is saved
- [x] 10. Examples + demo.sh walkthrough
- [x] 11. Full test pass, README, submission draft
