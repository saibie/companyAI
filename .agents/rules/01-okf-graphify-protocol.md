---
trigger: always_on
description: Mandatory pre-flight inspection of OKF and Graphify, plus post-flight synchronization for any codebase modification.
---

# 🛡️ Development Protocol: OKF First & Graphify Second

Whenever planning or implementing changes to this repository, you MUST follow this protocol:

## 1. PRE-MODIFICATION (수정 전)
1. **OKF Consultation**:
   - Always check `okf/index.md` first.
   - Read the relevant domain concepts, architecture docs, or ADRs before proposing or writing code.
2. **Graphify AST Inspection**:
   - Run `graphify query "<symbol>"` or check `graphify-out/GRAPH_REPORT.md` / `graphify-out/graph.json` to analyze AST call hierarchies, dependencies, and impacted areas.
   - Run `graphify path "<A>" "<B>"` if tracing relationships between two components.

## 2. POST-MODIFICATION (수정 후)
1. **Sync OKF**: If entities, workflows, services, or decisions were added or modified, update the respective markdown files in `okf/`.
2. **Sync Graphify**: Run `./scripts/update_knowledge.sh` or `graphify extract . --code-only && graphify cluster-only .` to keep `graphify-out/graph.json` up to date.
