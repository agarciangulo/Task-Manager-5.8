# Spike Execution Plan – Day-by-Day Roadmap

This plan turns the spike scope and architecture into a day-by-day execution schedule. Adjust pacing as needed, but use it as the default playbook when running the parallel prototype.

---

## Day 0 – Preparation
- Confirm spike objectives, constraints, and success criteria (`docs/SPIKE_SCOPE.md`).
- Secure required accounts/quotas (Vertex AI project, Cloud SQL instance, GitHub repo).
- Gather sample/intake payloads and anonymized correction examples.

---

## Day 1 – Bootstrapping
- Initialize the repository (`ai-agent-platform-spike`) with base folders:
  - `apps/api/` (API gateway placeholder)
  - `services/orchestrator/` (LangGraph flow)
  - `services/domain/` (task + correction services)
  - `infra/` (IaC, deployment scripts)
  - `docs/` (architecture, scope, execution)
- Add developer tooling: Python/Node version files, lint/format configs, GitHub Actions skeleton.
- Document initial README describing spike intent.

---

## Day 2 – Orchestration Skeleton
- Implement API gateway stub with `/tasks/intake` and `/tasks/corrections` returning mock responses.
- Scaffold LangGraph flow with placeholder nodes for intake → extraction → persistence → response.
- Wire logging and run ID propagation through nodes.
- Check in automated tests for pipeline wiring (unit tests verifying node transitions).

---

## Day 3 – AI & Data Foundations
- Integrate Vertex AI/Gemini into the Extraction and Correction nodes (structured output enforcement).
- Stand up Postgres/Cloud SQL schema (`runs`, `tasks`, `corrections`, `insights`).
- Implement repository layer with migration tooling (e.g., Alembic or Prisma).
- Persist run metadata and tasks during the new-task flow.

---

## Day 4 – Correction Loop & Insights
- Complete correction flow: intake, agent interpretation, apply updates, audit logging.
- Implement insight service to generate summary data for both new tasks and corrections.
- Add error handling and retry policies around LangGraph nodes.
- Stub notification service interface (even if it logs instead of sends).

---

## Day 5 – Observability & Validation
- Instrument per-node metrics (latency, success counts) and push to Cloud Logging/Monitoring.
- Run end-to-end tests using synthetic payloads covering intake and correction scenarios.
- Capture latency metrics and initial AI accuracy observations.
- Draft spike evaluation findings and update `docs/SPIKE_ARCHITECTURE.md` with any deviations.

---

## Day 6 – Demo & Comparison (Optional Buffer)
- Prepare demo script: sequence of API calls, DB inspection, log review.
- Compare spike outcomes versus current production system (pros/cons, risks).
- Recommend next actions: integrate, iterate, or archive.
- *(Optional)* Prototype operator UI with Vercel v0 consuming the API endpoints for manual intake/correction triggers.

---

### Deliverables Recap
- Working prototype (API + LangGraph + DB + insights).
- Architecture and execution docs (`docs/SPIKE_SCOPE.md`, `docs/SPIKE_ARCHITECTURE.md`, `docs/SPIKE_EXECUTION_PLAN.md`).
- Observability snapshots (metrics/logs).
- Evaluation report or slide summarizing decision inputs.

Adjust the schedule as teams/resources shift, but maintain the order to keep dependencies flowing cleanly.***

