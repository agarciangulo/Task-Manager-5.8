# Spike Roadmap – Progression from MVP to Enterprise Platform

This roadmap outlines the planned evolution of the spike prototype into a full-featured, multi-tenant agent platform. Use it to prioritize work after the MVP is validated.

---

## Phase 0 – Spike MVP (Current Focus)

**Objective:** Validate end-to-end flow (intake → extraction → persistence → correction → insight).

- Single-tenant operation (no user segregation).
- Manual HTTP endpoints for intake and correction.
- LangGraph orchestrator with state persistence in Postgres.
- Vertex AI (Gemini) prompts for extraction and correction.
- Basic observability (logs, latency metrics).
- Manual or stubbed notifications.

**Exit criteria:** Flow works reliably, latency/cost acceptable, architecture documentation complete.

---

## Phase 1 – Multi-User Foundations

**Objective:** Introduce user management and secure access.

- Add `users` table and authentication layer (JWT or OAuth).
- Scope runs, tasks, and corrections by `user_id` / tenant.
- Implement API key or OAuth token intake for channel integrations.
- Extend LangGraph state to include user context (permissions, preferences).
- Provide basic user onboarding/admin endpoints.

**Dependencies:** Spike MVP completed, decision to proceed with migration.

---

## Phase 2 – Multi-Channel & Automations

**Objective:** Move beyond manual endpoints to production-grade intake/output.

- Gmail webhook or Cloud Function feeding intake endpoint.
- Slack/Teams bot integration for task capture and corrections.
- n8n or Temporal workflows to orchestrate reminders, escalations, reporting.
- Notification service wired to email/Slack with template management.
- Introduce feature flags for channel rollouts.
- Operator dashboard/UI built with Vercel v0 (or migrated to custom Next.js) for manual oversight.

**Dependencies:** Phase 1 auth in place; stable spike infrastructure.

---

## Phase 3 – Enterprise Readiness

**Objective:** Harden for production scale and compliance.

- Observability dashboards (BigQuery exports, Data Studio/Grafana).
- RBAC and tenant isolation (workspaces, quotas).
- Full audit logging and retention policies.
- Integrations with downstream systems (Notion, Jira, ServiceNow, etc.).
- Disaster recovery plan, backup automation.
- Performance optimization and cost tuning.

**Dependencies:** Multi-user adoption; automation flows operating reliably.

---

## Phase 4 – Intelligence & Insights Expansion (Optional)

**Objective:** Turn the platform into a proactive advisor.

- Advanced analytics (trend detection, anomaly alerts).
- Recommendation engine powered by historical runs.
- Evaluation harness for agent performance (Vertex Eval, custom metrics).
- Marketplace for plugins or third-party tool adapters.

**Dependencies:** Enterprise rollout stable; metrics demonstrating value.

---

## Roadmap Governance

- Review and adjust phases after Spike MVP evaluation.
- Maintain this roadmap in `docs/` and update quarterly or after major milestones.
- Align each phase with resource planning (team members, budget, infra commitments).

This staged path lets you go live quickly with the core flow while building a clear bridge to a robust, multi-tenant, enterprise-grade platform.***

