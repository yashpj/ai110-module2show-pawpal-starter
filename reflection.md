# PawPal+ Project Reflection

## 1. System Design

3 Actions user can do:
i - user should be able to add/edit tasks.
ii - Generate a daily schedule/plan based on constraints and priorities.
iii - Let a user enter basic owner + pet info

**a. Initial design**

The system is built around five classes:

- **`Pet`** (dataclass) — holds the pet's name, species, and age. A pure data holder with no scheduling logic.
- **`Task`** (dataclass) — represents one care activity (walk, feeding, meds, etc.) with a duration, priority, and optional preferred time of day.
- **`Owner`** (dataclass) — stores the owner's name and how many minutes per day they have available for pet care.
- **`Scheduler`** — the core logic class. It holds a list of candidate tasks and an Owner + Pet reference. Its `generate_plan()` method selects and orders tasks that fit within the owner's time budget, prioritising high-priority tasks first.
- **`DailyPlan`** — the output of a scheduling run. It separates tasks into scheduled vs. skipped, tracks total duration, and exposes `display()` and `explain()` for the UI.

**b. Design changes**

After reviewing the skeleton with AI, three changes were made:

1. **`Owner` converted to a dataclass** — the initial draft used a manual `__init__`, which was inconsistent with `Pet` and `Task`. Making it a dataclass removes boilerplate and keeps all three data-holder classes uniform.

2. **`Task.is_valid()` replaced with `__post_init__`** — originally `is_valid()` was a standalone method the caller had to remember to invoke. Moving validation into `__post_init__` means a `Task` with bad data (e.g. negative duration) raises an error at construction time, making it impossible to add an invalid task to the scheduler.

3. **`DailyPlan` now receives `owner`** — `explain()` needs to say why tasks were skipped (e.g. "only 60 minutes available"). Without a reference to `Owner`, the plan had no access to the time budget it was built against.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: (1) the owner's total available minutes per day — tasks that don't fit are skipped entirely; (2) task priority (high → medium → low) — higher-priority tasks are always scheduled first regardless of duration; (3) within the same priority tier, shorter tasks are preferred (greedy fit) to maximise the number of tasks completed.

Priority was chosen as the primary constraint because a missed medication is more harmful than a missed enrichment session. Time budget is secondary — it's a hard cap. Duration as a tiebreaker is a performance heuristic, not a user-facing preference.

**b. Tradeoffs**

The conflict detector flags overlaps using exact `start_time` + `duration_minutes` interval arithmetic, but it only warns — it does not remove conflicting tasks from the schedule. This means a user can see two tasks flagged as overlapping and still choose to keep both (e.g., if one pet can be fed while the other is on a walk with a helper). The tradeoff is flexibility over strictness: a hard block would be safer but would require the user to manually resolve every overlap before generating a plan, which adds friction for a simple daily-planning tool.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase of the project, but in different modes depending on the task:

- **Design brainstorming** — used Claude Code chat to identify the five core classes and their responsibilities before writing any code. Asking "what are the main objects in a pet care scheduling system?" produced a useful first draft that I then trimmed and refined.
- **Skeleton generation** — used Agent Mode to turn the UML directly into Python class stubs with proper dataclass annotations and type hints, which saved significant boilerplate time.
- **Algorithm implementation** — used Inline Chat to flesh out `sort_by_time()` with a `lambda` sort key and `detect_conflicts()` with interval overlap logic (`a_start < b_end and b_start < a_end`). Explaining the math behind the overlap condition in natural language ("two intervals overlap if one starts before the other ends") got an accurate result immediately.
- **Test generation** — asked Copilot to draft edge-case tests using `#codebase` context. The most useful prompt pattern was: "What are the boundary conditions for this method?" rather than "Write tests for this method."
- **Debugging** — when the `test_mark_complete_sets_completed_true` test failed after the recurrence feature was added, Inline Chat instantly identified that the test's expectation was now wrong, not the logic. This saved time that would otherwise be spent re-reading the code manually.

The most effective Copilot features were **Agent Mode** (for multi-file, multi-step tasks like wiring the UI) and **Inline Chat** (for targeted questions about a specific function).

**b. Judgment and verification**

When generating the `Scheduler` skeleton, Copilot initially placed `add_task()` and `remove_task()` directly on the `Scheduler` class. This felt wrong — the scheduler's job is to *plan*, not to *own* tasks. Tasks belong to a `Pet`, which belongs to an `Owner`. Accepting the AI's version would have created a second, parallel way to manage tasks that could easily get out of sync with `pet.tasks`.

The fix was to reject that suggestion and instead move task management to `Pet`, with the `Scheduler` reading tasks through `Owner.get_all_tasks()`. I verified this was the right call by asking: "If I call `scheduler.add_task()` and `pet.add_task()` on the same task, which list is the source of truth?" — the ambiguity made the problem obvious.

**c. Separate chat sessions**

Keeping separate chat sessions for design, implementation, and testing prevented context bleed. During the testing session, Copilot only had test-related context, so it suggested edge cases (empty pet list, task exceeding full budget) rather than drifting into implementation suggestions. During the design session, the conversation stayed at the architecture level without getting pulled into Streamlit UI details. Mixing everything into one session would have produced unfocused, inconsistent suggestions.

**d. Being the lead architect**

The most important lesson was that AI is excellent at executing a well-specified task and poor at deciding *which* task to execute. Every time I gave Copilot a vague prompt ("make the scheduler smarter"), the result required heavy revision. Every time I gave it a precise, constrained prompt ("add a method that returns overlapping task pairs as warning strings, don't modify the schedule"), the result was close to correct on the first try.

Being lead architect means translating ambiguous requirements ("the app should feel professional") into specific, verifiable decisions ("use `st.warning()` for conflicts and `st.progress()` for the time budget") before involving AI. The human's job is to hold the design vision and make the judgment calls; the AI's job is to execute within those boundaries quickly and correctly.

---

## 4. Testing and Verification

**a. What you tested**

19 tests across 6 categories: task validation (construction-time errors), recurrence logic (daily/weekly/as-needed `due_date` advancement), pet task management (`add_task`, pending filtering), sorting correctness (chronological order with and without explicit `start_time`), conflict detection (overlap vs. back-to-back vs. no `start_time`), and scheduler edge cases (no pets, no tasks, task exceeding full budget).

These tests were important because the most fragile part of the system is the interaction between `mark_complete()` and `due_date` — a subtle bug there (e.g. advancing by 7 days for a daily task) would silently produce wrong schedules with no visible error. Tests made that contract explicit and machine-verifiable.

**b. Confidence**

★★★★☆ — The core logic is well covered. The gap is the Streamlit UI layer (no automated tests) and exhaustive scheduler combinations (e.g., mixed-priority tasks where a greedy fit produces a suboptimal result a human would notice). Next edge cases to test: two tasks that together fit the budget but individually neither would trigger a skip, and a pet with all tasks already completed (should produce an empty plan, not an error).

---

## 5. Reflection

**a. What went well**

The class separation worked cleanly throughout the project. Because `Task`, `Pet`, and `Owner` are pure data classes and `Scheduler` is the only place with logic, every feature addition (recurrence, conflict detection, sorting) could be added to `Scheduler` without touching the data classes. That boundary made the codebase easy to navigate and test independently.

**b. What you would improve**

The greedy scheduling algorithm is simple but not optimal — it can miss combinations where skipping a long high-priority task would allow three medium-priority tasks to fit. A next iteration could implement a knapsack-style approach or let the user set a "minimum required tasks" threshold. I would also add a `start_time` input field to the Streamlit task form so users can use conflict detection directly from the UI.

**c. Key takeaway**

Designing the system on paper (UML) before writing any code forced every class to have a clear, single responsibility. When AI suggestions violated that structure (like putting task management on the Scheduler), the violation was immediately visible because the design existed as a reference. Without the upfront design, those structural mistakes would have been accepted and would have accumulated into technical debt. The UML was not wasted time — it was the artifact that made every subsequent AI interaction more precise and the code easier to reason about.
