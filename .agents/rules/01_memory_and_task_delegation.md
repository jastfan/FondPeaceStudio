# Agent Rule: Memory First & Multi-Agent Task Orchestration

## 1. Zero-Redundancy Principle (Remember What Is Done)
- **Mandatory Memory Check:** At the start of ANY task, check `.agents/PROJECT_MEMORY.md`.
- **Preserve Verified Code:** Never re-invent, overwrite, or rebuild features that are marked as completed. 
- **Delta-Only Progress:** Only implement what is requested or strictly missing. If a module works, leave it alone.

## 2. Multi-Agent Work Delegation Model
For any non-trivial or large-scale task, execute across 4 distinct phases:
1. **The Architect (Planner):**
   - Check existing contracts and memory.
   - Break requirements into atomic, verifiable steps.
   - Ensure zero edge-cases are missed.
2. **The Builder (Implementer):**
   - Implement the planned steps with precision.
   - Maintain architectural integrity and avoid regressions.
3. **The QA / Verifier (Tester):**
   - Verify execution across Desktop, Mobile (Android/iOS), and LAN.
   - Ensure servers, APIs, and builds succeed with zero errors.
4. **The Memory Keeper (State Syncer):**
   - Update `.agents/PROJECT_MEMORY.md` with what was completed.
   - Record any new architectural decisions (ADRs).

## 3. Exhaustive Verification (Nothing Missed)
- Never declare a feature done until the runtime, network, and endpoints have been checked and verified.
- Ensure cross-platform and multi-device parity on every release.
