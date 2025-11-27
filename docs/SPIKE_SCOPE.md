# Spike Scope – AI Task Management Flow (Parallel Prototype)

## Objective
Validate a next-generation platform stack by delivering a minimal, business-critical flow end-to-end: intake a task request, extract structured tasks with an AI agent, persist them, accept a correction, apply it, and emit an insight/summary. The spike results will inform the decision to migrate or integrate the new architecture with the existing system.

---

## Use Cases to Demonstrate

1. **New Task Intake**
   - Trigger: HTTP POST (mocked email payload with subject, body, metadata).
   - Output: Structured task entries stored in the database + generated confirmation summary.

2. **Correction Request**
   - Trigger: HTTP POST referencing original task IDs plus natural language correction text.
   - Output: Updated tasks with before/after audit trail; correction summary for the user.

3. **Insight Generation**
   - For each run, produce a lightweight insight or recommendation that illustrates AI reasoning (e.g., “You have 3 tasks due this week.”).

---

## Success Criteria

| Category | Criteria |
|----------|----------|
| Functionality | Endpoints accept intake and correction payloads; tasks persisted; corrections applied; summaries returned |
| AI Quality | Extracted tasks match expected structure (title, status, due_date, etc.); corrections interpreted accurately |
| Observability | Each orchestrated step logs start/end, latency, and status; run IDs trace through storage |
| Architecture | Documentation + diagram describing layers, components, data flow, and future plugs (Gmail, Notion, Slack) |
| Extendability | Clear seams identified for swapping intake channels, AI providers, or storage backends |
| Decision Support | Spike report compares new stack against existing system (pros, cons, migration path) |

---

## Constraints & Assumptions

- **Scope:** Focus on the core agent flow; defer UI, authentication hardening, and non-essential plugins.
- **Stability:** No production traffic; spike runs in an isolated project/environment.
- **Timebox:** 5–7 day effort including build, validation, and documentation.
- **Team:** Primary owner (you) with optional reviewers; no dependency on current production pipeline operators.
- **Data:** Use synthetic or anonymized email samples; demo-ready but not production-grade.

---

## Deliverables

1. **Working Prototype**
   - Minimal API (task intake, correction intake).
   - LangGraph/Vertex agent orchestration implementing the flow.
   - Persistence layer storing tasks, corrections, and run metadata.
   - Insight/summary generator.
   - *(Optional stretch)* Operator UI built with Vercel v0 consuming the same endpoints.

2. **Architecture Documentation**
   - Layered diagram showing components, integrations, and data flows.
   - Text explanation of responsibilities, technology choices, and future extension points.

3. **Evaluation Report**
   - Performance metrics (latency, cost estimates, AI accuracy observations).
   - Comparison against current architecture.
   - Recommendation for next steps (integrate, iterate, or sunset).

---

## Next Steps

1. Build the architecture diagram (see accompanying documentation).
2. Scaffold the spike repository with agreed layering.
3. Implement minimal LangGraph template and endpoints.
4. Capture results and synthesize the evaluation.

This scope keeps the spike laser-focused on demonstrating the new platform’s viability while generating actionable insights for strategic planning. When satisfied with the flow, you can iterate on channel integrations, UI, and enterprise hardening.

