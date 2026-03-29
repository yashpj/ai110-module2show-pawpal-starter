"""
main.py – demo script to verify PawPal+ logic in the terminal.
Run with: python3 main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

# --- Owner ------------------------------------------------------------------
jordan = Owner(name="Jordan", available_minutes=90)

# --- Pets -------------------------------------------------------------------
mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

# --- Tasks for Mochi (dog) --------------------------------------------------
mochi.add_task(Task("Morning walk",      "walk",       30, "high",   "daily",     "morning"))
mochi.add_task(Task("Breakfast feeding", "feeding",    10, "high",   "daily",     "morning"))
mochi.add_task(Task("Teeth brushing",    "grooming",   15, "medium", "daily",     "evening"))
mochi.add_task(Task("Enrichment puzzle", "enrichment", 60, "low",    "as-needed", "afternoon"))

# --- Tasks for Luna (cat) ---------------------------------------------------
luna.add_task(Task("Dinner feeding",  "feeding",     10, "high",   "daily",     "evening"))
luna.add_task(Task("Brush coat",      "grooming",    10, "medium", "weekly",    "any"))
luna.add_task(Task("Flea medication", "meds",        5,  "high",   "weekly",    "any"))

# --- Register pets with owner -----------------------------------------------
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- Generate plan ----------------------------------------------------------
scheduler = Scheduler(jordan)
plan = scheduler.generate_plan()

# --- Print results ----------------------------------------------------------
print("=" * 55)
print("           PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 55)
print(plan.display())
print()
print("-" * 55)
print("WHY THIS PLAN?")
print("-" * 55)
print(plan.explain())
print("=" * 55)
