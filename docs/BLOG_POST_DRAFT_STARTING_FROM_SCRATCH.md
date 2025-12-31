# Starting From Scratch: Why I'm Rebuilding My AI Agent in Parallel

> *"Should we refactor, or should we rewrite?"—the question that haunts every technical decision-maker.*

---

## Draft Outline & Analysis: Benefits and Rewards of Spiking This Project

This document analyzes the decision to build a "spike" (parallel prototype) for the AI Task Management system rather than incrementally refactoring the existing codebase. It provides material for a Substack/LinkedIn post exploring when starting from scratch is the right call.

---

## The Situation: What I'm Working With

### The Current System (Production)

The existing AI Task Management system is a **working production application** that:

| Capability | How It Works |
|------------|--------------|
| **Email Intake** | Gmail IMAP polling → Flask API → AI extraction |
| **Task Extraction** | Custom Python agents using Gemini 1.5 |
| **Storage** | Notion databases as the canonical task store |
| **Corrections** | PostgreSQL for correction logs, email-based correction flow |
| **Architecture** | 5-layer architecture with plugin system |
| **Orchestration** | Custom Python + Celery for async tasks |
| **Deployment** | Google Cloud Run + Cloud Scheduler |

**It works.** Users send emails, tasks get extracted, corrections get processed. The system handles edge cases, has comprehensive documentation, and runs in production.

### The Spike (Proposed Parallel Rebuild)

The spike proposes a **from-scratch implementation** with:

| Aspect | Current System | Spike |
|--------|----------------|-------|
| **Orchestration** | Custom Python + Celery | LangGraph (graph-based) |
| **Task Storage** | Notion API | PostgreSQL (canonical store) |
| **State Management** | File-based (JSON) | LangGraph checkpoints (PostgreSQL) |
| **LLM** | Gemini 1.5 (direct calls) | Gemini 3.0 via LangChain |
| **Architecture** | Single pipeline | Three distinct processes |
| **User Behavior** | None | AI-powered Behavior Analyzer |
| **Query System** | None | Full Query Router + access control |
| **Insights** | Basic coaching | Best Practices DB + personalized insights |

---

## Why Spike Instead of Refactor?

### The Refactoring Trap

Refactoring the existing system seemed like the "responsible" choice:
- Smaller changes = lower risk
- Preserve working functionality
- Gradual migration path
- No throwaway code

But here's what I realized: **the current architecture's shape constrains what's possible to imagine**.

The system was designed around a single-pipeline flow: Email → Extract → Store → Respond. Every enhancement became a bolt-on:
- Corrections? Add a correction agent and separate PostgreSQL table.
- Context verification? Add a pending conversations JSON file.
- Behavior patterns? Where would they even go?

Each addition made the next addition harder. The architecture had accumulated **structural debt**—not buggy code, but shape that didn't match where the product needed to go.

### What the Spike Enables

Starting fresh allows rethinking the fundamental shape:

| Design Decision | Current Constraint | Spike Freedom |
|-----------------|-------------------|---------------|
| **Three Processes** | Everything is one pipeline | Task Intake, Prioritization, Query are independent processes with clear interfaces |
| **PostgreSQL as Source of Truth** | Notion is the canonical store; everything routes through Notion API | Direct database access, proper relational schemas, LangGraph checkpoint integration |
| **Behavior Analysis** | No clear place to add this | First-class Behavior Analyzer node that feeds into all processes |
| **Query System** | Would require major surgery to add | Designed from day one with access control matrix |
| **LangGraph Orchestration** | Would require rewriting all agents | Native graph-based state management from the start |

---

## The Honest Case for Starting Fresh

### 1. **Architectural Debt Is Harder to See Than Code Debt**

Code debt shows up in linting warnings, test failures, and slow builds. Architectural debt shows up as:
- "We can't easily add X because Y was built assuming Z"
- "This feature requires changes in 8 places"
- "We need to work around this limitation from 6 months ago"

The current system has clean code. The agents are well-tested. The plugins work. But the **shape** of the system—single pipeline, Notion as database, file-based state—limits what's possible without massive refactoring anyway.

**Insight for readers:** If you find yourself saying "we'd need to change the fundamental architecture to add this," you might already be in spike territory.

### 2. **The Spike Validates Before Committing**

The spike isn't a full rewrite. It's a **time-boxed experiment** (5-7 days) that answers:

- Can LangGraph actually handle our orchestration needs?
- Does PostgreSQL as the canonical store simplify or complicate things?
- Is the three-process architecture actually cleaner?
- What's the latency and cost of the new LLM call structure?

If the spike fails, we've lost a week. If refactoring the existing system fails, we've lost months and have a half-migrated mess.

**Key concept:** A spike is cheaper than a bad refactor.

### 3. **Fresh Architecture Enables Features That Were "Too Hard"**

The spike's three-process architecture makes certain features straightforward that would be surgery in the current system:

| Feature | In Current System | In Spike |
|---------|-------------------|----------|
| **Natural Language Queries** | Would need new API endpoints, query parsing, response synthesis, all bolted onto the existing flow | Process 3 is designed for this from day one |
| **Manager Dashboard** | Would need to add access control throughout the codebase | Access control matrix is built into the Query Router |
| **User Behavior Tracking** | No clear place to add observations | Behavior Analyzer node persists to dedicated User Behaviour DB |
| **Daily Prioritization Email** | Would need to add scheduling and a new email type | Process 2 is exactly this use case |

---

## The Honest Case Against Starting Fresh

It would be intellectually dishonest to pretend this is all upside. Here are the real risks:

### 1. **Second System Syndrome**

The temptation to over-engineer the spike is real. The spike architecture document is 1,400+ lines. The prompt specifications are detailed. There's a risk of building a cathedral when we need a chapel.

**Mitigation:** The 5-7 day timebox. The explicit "out of scope" list. The focus on three processes, not ten.

### 2. **Throwing Away Working Code**

The current system has:
- Tested agents with real-world edge cases handled
- Production-proven email parsing
- Working Notion integration
- Comprehensive documentation

Some of this can be ported (the AI prompts, the parsing logic), but some will be rewritten.

**Mitigation:** The spike isn't replacing the current system—it's running in parallel. If the spike succeeds, migration happens. If it fails, the current system continues.

### 3. **The Grass Is Always Greener**

Every new architecture seems cleaner because it hasn't encountered the messy reality of production. The spike's three-process design looks elegant now; will it still look elegant after handling:
- Reply chains with missing context?
- Users who send malformed emails?
- Gemini API rate limits?
- Database connection timeouts?

**Mitigation:** The spike includes explicit error handling design and observability requirements. It's not a proof-of-concept; it's meant to be production-grade.

---

## What This Spike Specifically Unlocks

### From the Architecture Documents

The spike enables a progression that the current system couldn't easily support:

```
Phase 0 (Spike MVP)     → Validate three processes, 5-7 days
Phase 1                  → Multi-user auth, per-user data
Phase 2                  → Multi-channel intake, Web UI for queries
Phase 3                  → Enterprise: RBAC, compliance, integrations
Phase 4                  → Advanced AI coaching, predictive insights
Phase 5                  → Specialized ML models, reduced LLM dependency
```

The current system was designed for Phase 0. The spike is designed to scale through Phase 5.

### The Numbers Tell a Story

| Metric | Current System | Spike |
|--------|----------------|-------|
| **LLM Calls per Email** | Variable (4-5 calls typical) | 2 calls (consolidated UnifiedExtractionNode) |
| **State Persistence** | File-based JSON | PostgreSQL checkpoints |
| **Process Separation** | None (single pipeline) | Three independent processes |
| **Access Control** | Application-level | Designed for database-level RLS |
| **User Behavior Tracking** | None | First-class feature |
| **Query Capability** | None | Full natural language query system |

---

## When Should *You* Spike Instead of Refactor?

Here's the framework I've developed:

### Spike If:

1. **The architecture's shape no longer matches the product's direction**
   - You're adding workarounds, not features
   - New capabilities require "surgery" not "extension"
   - The original assumptions (single user, email-only, Notion storage) no longer hold

2. **You can timebox the experiment**
   - A spike should answer questions, not build the whole system
   - 5-7 days is enough to validate architecture
   - If you can't timebox, you're doing a rewrite, not a spike

3. **The risk of a bad refactor exceeds the risk of a failed spike**
   - A half-migrated system is worse than either the old or new system
   - If refactoring requires touching everything anyway, start fresh
   - Parallel development means the production system stays stable

4. **You've learned enough to design it better**
   - The current system taught you what the problem actually is
   - Edge cases are now known, not surprises
   - The spike can encode lessons learned

### Refactor If:

1. **The architecture is fundamentally sound**
   - Just needs cleanup, not redesign
   - Adding features extends the existing shape naturally

2. **The scope is too large for a timebox**
   - If the spike would take months, it's a rewrite
   - Rewrites have different risk profiles

3. **You don't have the current system's lessons yet**
   - If you haven't run in production, you don't know what you don't know
   - Build the simple thing first, then spike the complex thing

---

## My Specific Case: The Decision Factors

For this AI Task Management system, here's what tipped the scales toward spiking:

| Factor | Weight | Notes |
|--------|--------|-------|
| **Notion as Database** | High | This was the right choice for MVP, wrong choice for scale. Changing it touches everything. |
| **Single Pipeline Architecture** | High | Adding a Query System (Process 3) would require fundamental restructuring. |
| **No User Behavior Tracking** | Medium | This would be a bolt-on in the current system; it's foundational in the spike. |
| **LangGraph Benefits** | Medium | State management and checkpointing would replace custom code. |
| **Timebox Feasibility** | High | 5-7 days for MVP of all three processes is achievable. |
| **Production System Stability** | High | The current system continues running; no migration pressure. |

---

## The Meta-Lesson: Spikes as Learning Tools

The spike isn't just about building a better system. It's about **learning whether a better system is possible**.

By designing the spike architecture in detail *before* building, I've already:
- Identified consolidation opportunities (11 LLM calls → 6)
- Mapped out access control requirements
- Designed the database schema for multi-tenancy
- Thought through error handling and observability

Even if the spike fails, these artifacts inform how to improve the current system.

**The spike is a thinking tool, not just a building project.**

---

## Call to Action for Readers

If you're facing the "refactor vs. rewrite" question:

1. **Document what you'd do differently.** Write your version of SPIKE_ARCHITECTURE.md. The act of designing the ideal system clarifies whether it's worth building.

2. **Timebox ruthlessly.** A spike that takes 3 months isn't a spike; it's a rewrite wearing a different hat.

3. **Keep the current system running.** Parallel development removes the pressure to ship the spike before it's ready.

4. **Define success criteria.** What does the spike need to prove? Latency? Maintainability? Feature enablement?

5. **Be honest about Second System Syndrome.** The spike document should include "out of scope" and "assumptions." Ambition is the enemy of validation.

---

## Closing Thought

The best engineers I know aren't the ones who never throw away code—they're the ones who know *when* to throw away code.

This spike might prove that LangGraph + PostgreSQL + three processes is the right architecture. Or it might prove that the current system's shape is fine with some targeted improvements.

Either answer is valuable. The worst outcome is never asking the question.

---

## Notes for Editing

### Sections to Expand:
- [ ] Personal anecdotes: specific moments when the current architecture felt limiting
- [ ] Code examples: before/after of a specific flow (like correction handling)
- [ ] Screenshots: LangGraph node diagram vs. current flow diagram
- [ ] Cost analysis: estimated savings from LLM call consolidation

### Sections to Tighten:
- [ ] The comparison tables might be too dense for LinkedIn—consider key highlights only
- [ ] The "Spike If / Refactor If" section could be a standalone graphic

### Questions to Answer:
- [ ] Is the target audience technical leaders or individual developers?
- [ ] How much of the spike documents should be linked vs. summarized?
- [ ] Should the post end with the spike's outcome (if known) or leave it as a cliffhanger?

### Possible Titles:
1. "Starting From Scratch: Why I'm Rebuilding My AI Agent in Parallel"
2. "The Spike Decision: When Refactoring Isn't Enough"
3. "Why I Wrote 1,400 Lines of Architecture Before Writing Code"
4. "Refactor vs. Rewrite: A Framework for the Hardest Technical Decision"
5. "The Case for Throwing Away Working Code (Sometimes)"
6. "From Single Pipeline to Three Processes: Designing the Spike"

### Tie-in to Previous Post:
This could be framed as a sequel to "Tools Shape Work"—the tools (LangGraph, PostgreSQL) enabled *imagining* a different architecture, which led to the spike decision.

---

## Appendix: Summary of Spike Documents

For readers who want to go deeper:

| Document | Summary |
|----------|---------|
| **SPIKE_SCOPE.md** | Defines the three processes to validate: Task Intake, Prioritization & Insights, Query System. Success criteria and constraints. |
| **SPIKE_ARCHITECTURE.md** | Complete blueprint: data flows, database schemas, LangGraph nodes, prompt specifications. The "how" of the spike. |
| **SPIKE_TECH_STACK.md** | Technology choices: LangGraph, Gemini 3.0, PostgreSQL, Cloud Run. Comparison with current stack. |
| **SPIKE_EXECUTION_PLAN.md** | Day-by-day implementation guide. Testing strategy. Deliverables checklist. |
| **SPIKE_ROADMAP.md** | Evolution from MVP → Phase 5 (enterprise platform). Shows why the spike's architecture matters for the long term. |

---

*Draft created: December 2024*
*Based on analysis of: Current codebase, SPIKE_SCOPE.md, SPIKE_ARCHITECTURE.md, SPIKE_TECH_STACK.md, SPIKE_EXECUTION_PLAN.md, SPIKE_ROADMAP.md, LAYERED_ARCHITECTURE.md, TECH_STACK.md, SUPABASE_TRADEOFF_ANALYSIS.md*

