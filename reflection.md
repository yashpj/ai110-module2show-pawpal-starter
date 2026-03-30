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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
