# Spike Execution Plan – Day-by-Day Roadmap

This plan turns the spike scope and architecture into a day-by-day execution schedule. The spike implements three core processes; adjust pacing as needed, but use this as the default playbook.

---

## Day 0 – Preparation

- [ ] Confirm spike objectives and three processes (`docs/SPIKE_SCOPE.md`)
- [ ] Review architecture blueprint (`docs/SPIKE_ARCHITECTURE.md`)
- [ ] Secure required accounts/quotas:
  - Vertex AI project with Gemini API access
  - Cloud SQL instance (PostgreSQL)
  - GitHub repository
- [ ] Gather sample data:
  - Sample emails (activities, corrections, context replies)
  - Seed data for Best Practices DB
  - Test queries for Process 3

---

## Day 1 – Bootstrapping & Data Layer

### Repository Setup
- [ ] Initialize repository with process-based structure:
  ```
  spike/
  ├── processes/
  │   ├── intake/          # Process 1: Task Intake
  │   ├── prioritization/  # Process 2: Prioritization & Insights
  │   └── query/           # Process 3: Query System
  ├── shared/
  │   ├── database/        # Database models and connections
  │   ├── email/           # Email send/receive utilities
  │   └── llm/             # Gemini client wrapper
  ├── infra/               # Deployment configs
  └── docs/                # Documentation
  ```
- [ ] Add developer tooling: Python version, requirements.txt, linting, pre-commit hooks

### Database Foundation
- [ ] Create PostgreSQL schemas for all four databases:
  - `tasks` table (Task DB)
  - `user_behaviours` table (User Behaviour DB)
  - `best_practices` table (Best Practices DB)
  - `insights` table (Insights DB)
- [ ] Implement basic repository pattern for each database
- [ ] Seed Best Practices DB with 10-15 sample practices

---

## Day 2 – Process 1: Task Intake (Core Flow)

### Task Extractor
- [ ] Implement `EmailIntakeNode` - parse raw email into structured format
- [ ] Implement `IntentClassifierNode` - classify as activity/correction/context (Gemini)
- [ ] Implement `TaskExtractorNode` - extract tasks from email content (Gemini)
- [ ] Implement `ContextCheckerNode` - detect missing info, generate questions (Gemini)

### Basic Pipeline
- [ ] Wire nodes together in LangGraph flow
- [ ] Add run ID tracking and logging
- [ ] Test with sample activity emails

---

## Day 3 – Process 1: Task Processing & Presentation

### Task Processor
- [ ] Implement `TaskComparisonNode` - compare extracted tasks vs. DB
- [ ] Implement add/update logic based on comparison
- [ ] Implement `BehaviorLoggerNode` - log user patterns to User Behaviour DB
- [ ] Implement `TaskPersistNode` - write changes to Task DB

### Task Presenter
- [ ] Implement `PresenterNode` - generate summary, priorities, confirmations
- [ ] Implement email sending (SMTP)
- [ ] Test complete Process 1 flow end-to-end

### Correction Handling
- [ ] Add correction flow branch in Task Extractor
- [ ] Test correction scenarios (update due date, change priority, etc.)

---

## Day 4 – Process 2: Prioritization & Insights

### Task Prioritizer
- [ ] Implement `TaskFetchNode` - get user's open tasks
- [ ] Implement `PrioritizerNode` - generate prioritized list (Gemini)
- [ ] Test prioritization logic with various task sets

### Insight Generator
- [ ] Implement `BestPracticesFetchNode` - get relevant practices
- [ ] Implement `InsightGeneratorNode` - compare tasks to practices (Gemini)
- [ ] Implement `InsightPersistNode` - store insights to Insights DB

### Combined Output
- [ ] Implement `EmailComposerNode` - combine priorities + insights
- [ ] Format email with separate sections
- [ ] Test complete Process 2 flow

---

## Day 5 – Process 3: Query System (MVP)

### Query Router
- [ ] Implement `QueryIntakeNode` - parse natural language query (Gemini)
- [ ] Implement `BreakdownNode` - decompose complex queries (Gemini)
- [ ] Implement `AccessControlNode` - determine allowed data scopes

### Data Access
- [ ] Implement `CoordinatorNode` - route queries to appropriate DBs
- [ ] Implement `DataFetchNode` - execute queries
- [ ] Implement `SummarizerNode` - apply privacy rules to results (Gemini)
- [ ] Implement `SynthesizerNode` - combine results into response (Gemini)

### Access Control Testing
- [ ] Test User queries (own data: full, team/firm: summarized)
- [ ] Test Manager queries (team members: full, firm: summarized)

---

## Day 6 – Integration & Observability

### Email Integration
- [ ] Set up Gmail IMAP for receiving emails
- [ ] Configure email routing to appropriate process
- [ ] Test email-triggered Process 1 flow

### Observability
- [ ] Add per-node latency logging
- [ ] Add LLM call tracking (tokens, latency)
- [ ] Set up Cloud Logging integration
- [ ] Create simple metrics dashboard

### Error Handling
- [ ] Add retry logic for database operations
- [ ] Add graceful error responses
- [ ] Test failure scenarios

---

## Day 7 – Demo & Evaluation

### Demo Preparation
- [ ] Prepare demo script with realistic scenarios:
  1. User sends email with new activities → tasks created
  2. User sends correction → tasks updated
  3. User receives daily priorities + insights
  4. User asks query → gets appropriate response
  5. Manager asks team query → gets full detail
- [ ] Record demo walkthrough (optional)

### Evaluation
- [ ] Measure end-to-end latency for each process
- [ ] Assess AI accuracy (task extraction, intent classification)
- [ ] Compare architecture with current production system
- [ ] Document pros, cons, risks, recommendations

### Deliverables
- [ ] Working prototype with all three processes
- [ ] Updated architecture documentation
- [ ] Evaluation report with recommendations

---

## Deliverables Checklist

### Code
- [ ] Process 1: Task Intake & Processing - complete
- [ ] Process 2: Prioritization & Insights - complete
- [ ] Process 3: Query System - MVP complete
- [ ] All four databases - implemented and seeded
- [ ] Email integration - working

### Documentation
- [ ] `docs/SPIKE_SCOPE.md` - updated with final scope
- [ ] `docs/SPIKE_ARCHITECTURE.md` - updated with implementation details
- [ ] `docs/SPIKE_EXECUTION_PLAN.md` - this document, with completion status

### Evaluation
- [ ] Latency metrics for each process
- [ ] AI accuracy observations
- [ ] Architecture comparison report
- [ ] Recommendations for next phase

---

## Contingency Notes

### If Running Behind
- **Day 3-4 cramped:** Simplify Task Presenter output; focus on task persistence
- **Day 5 incomplete:** Process 3 can be stub-only; document intended design
- **Day 6-7 short:** Combine demo and evaluation; skip detailed metrics

### If Running Ahead
- **Extra time:** Add Notion sync as extension
- **Extra time:** Build simple admin UI for query testing
- **Extra time:** Implement more sophisticated prioritization algorithm

---

Adjust this schedule as needed, but maintain the order to keep dependencies flowing cleanly. Process 1 is the critical path; Processes 2 and 3 build on its foundation.
