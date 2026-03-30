"""
main.py – demo script for PawPal+ smarter scheduling features.
Run with: python3 main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

SEP = "=" * 60

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
jordan = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

# Tasks added OUT OF ORDER to demonstrate sort_by_time()
mochi.add_task(Task("Enrichment puzzle", "enrichment", 60, "low",    "as-needed", "afternoon", start_time="14:00"))
mochi.add_task(Task("Breakfast feeding", "feeding",    10, "high",   "daily",     "morning",   start_time="07:30"))
mochi.add_task(Task("Morning walk",      "walk",       30, "high",   "daily",     "morning",   start_time="08:00"))
mochi.add_task(Task("Teeth brushing",    "grooming",   15, "medium", "daily",     "evening",   start_time="19:00"))

luna.add_task(Task("Flea medication", "meds",    5,  "high",   "weekly", "any",     start_time="09:00"))
luna.add_task(Task("Dinner feeding",  "feeding", 10, "high",   "daily",  "evening", start_time="18:00"))
# Intentional conflict: both Mochi tasks overlap at 08:00–08:30 with 08:15
mochi.add_task(Task("Quick check-in", "other",   20, "medium", "daily",  "morning", start_time="08:15"))

jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(jordan)

# ---------------------------------------------------------------------------
# 1. Sort by time
# ---------------------------------------------------------------------------
print(SEP)
print("1. ALL TASKS SORTED BY START TIME")
print(SEP)
sorted_pairs = scheduler.sort_by_time(jordan.get_all_tasks())
for pet, task in sorted_pairs:
    print(f"  {task.start_time or task.preferred_time:>7}  [{task.priority.upper():6}] {pet.name}: {task.name}")

# ---------------------------------------------------------------------------
# 2. Filter by pet and by completion status
# ---------------------------------------------------------------------------
print()
print(SEP)
print("2. FILTER: only Mochi's tasks")
print(SEP)
for pet, task in scheduler.filter_tasks(pet_name="Mochi"):
    print(f"  {task.name} ({task.frequency})")

print()
print(SEP)
print("2. FILTER: pending tasks only (all pets)")
print(SEP)
for pet, task in scheduler.filter_tasks(completed=False):
    print(f"  {pet.name}: {task.name}")

# ---------------------------------------------------------------------------
# 3. Generate plan (includes conflict warnings inside)
# ---------------------------------------------------------------------------
print()
print(SEP)
print("3. TODAY'S SCHEDULE")
print(SEP)
plan = scheduler.generate_plan()
print(plan.display())
print()
print("-" * 60)
print("WHY THIS PLAN?")
print("-" * 60)
print(plan.explain())

# ---------------------------------------------------------------------------
# 4. Conflict detection (explicit)
# ---------------------------------------------------------------------------
print()
print(SEP)
print("4. CONFLICT DETECTION")
print(SEP)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for w in conflicts:
        print(f"  ⚠  {w}")
else:
    print("  No conflicts detected.")

# ---------------------------------------------------------------------------
# 5. Recurring tasks – mark complete and observe due_date advance
# ---------------------------------------------------------------------------
print()
print(SEP)
print("5. RECURRING TASKS — mark Mochi's 'Morning walk' complete")
print(SEP)
walk = next(t for t in mochi.tasks if t.name == "Morning walk")
print(f"  Before: due={walk.due_date}, completed={walk.completed}")
scheduler.mark_task_complete("Mochi", "Morning walk")
print(f"  After:  due={walk.due_date}, completed={walk.completed}  ← auto-advanced +1 day")

print()
print("  Mark Luna's 'Flea medication' (weekly) complete:")
flea = next(t for t in luna.tasks if t.name == "Flea medication")
print(f"  Before: due={flea.due_date}, completed={flea.completed}")
scheduler.mark_task_complete("Luna", "Flea medication")
print(f"  After:  due={flea.due_date}, completed={flea.completed}  ← auto-advanced +7 days")

print(SEP)
