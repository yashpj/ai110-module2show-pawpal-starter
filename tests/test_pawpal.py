"""
tests/test_pawpal.py – unit tests for PawPal+ core logic.
Run with: python3 -m pytest
"""

from datetime import timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Scheduler


def make_task(**kwargs) -> Task:
    """Return a Task with sensible defaults; override any field via kwargs."""
    defaults = dict(
        name="Morning walk",
        task_type="walk",
        duration_minutes=30,
        priority="high",
    )
    defaults.update(kwargs)
    return Task(**defaults)


def make_pet(name="Mochi") -> Pet:
    """Return a Pet with sensible defaults."""
    return Pet(name=name, species="dog", age=3)


# ---------------------------------------------------------------------------
# Task validation
# ---------------------------------------------------------------------------

def test_task_rejects_zero_duration():
    with pytest.raises(ValueError, match="duration_minutes must be > 0"):
        make_task(duration_minutes=0)


def test_task_rejects_negative_duration():
    with pytest.raises(ValueError, match="duration_minutes must be > 0"):
        make_task(duration_minutes=-5)


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_mark_complete_daily_auto_resets_and_advances_due_date():
    task = make_task(frequency="daily")
    original_due = task.due_date
    task.mark_complete()
    assert task.completed is False                           # auto-reset for recurrence
    assert task.due_date == original_due + timedelta(days=1)


def test_mark_complete_weekly_advances_due_date_by_seven_days():
    task = make_task(frequency="weekly")
    original_due = task.due_date
    task.mark_complete()
    assert task.completed is False
    assert task.due_date == original_due + timedelta(weeks=1)


def test_mark_complete_as_needed_stays_completed():
    task = make_task(frequency="as-needed")
    task.mark_complete()
    assert task.completed is True                            # no auto-reset


def test_reset_clears_completed_status():
    task = make_task(frequency="as-needed")
    task.mark_complete()
    task.reset()
    assert task.completed is False


# ---------------------------------------------------------------------------
# Pet task management
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.tasks) == 0
    pet.add_task(make_task(name="Feeding", task_type="feeding", duration_minutes=10))
    assert len(pet.tasks) == 1
    pet.add_task(make_task(name="Walk", task_type="walk", duration_minutes=30))
    assert len(pet.tasks) == 2


def test_pet_with_no_tasks_has_empty_pending_list():
    pet = make_pet()
    assert pet.get_pending_tasks() == []


def test_get_pending_tasks_excludes_completed():
    pet = make_pet()
    task = make_task(frequency="as-needed")
    pet.add_task(task)
    task.mark_complete()
    assert pet.get_pending_tasks() == []


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    owner = Owner("Jordan", available_minutes=120)
    pet = make_pet()
    # Added out of order
    pet.add_task(make_task(name="Evening meds",  task_type="meds",    duration_minutes=5,  priority="high", start_time="19:00"))
    pet.add_task(make_task(name="Morning walk",  task_type="walk",    duration_minutes=30, priority="high", start_time="08:00"))
    pet.add_task(make_task(name="Lunch feeding", task_type="feeding", duration_minutes=10, priority="high", start_time="12:30"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    sorted_pairs = scheduler.sort_by_time(owner.get_all_tasks())
    names = [t.name for _, t in sorted_pairs]
    assert names == ["Morning walk", "Lunch feeding", "Evening meds"]


def test_sort_by_time_tasks_without_start_time_use_slot_defaults():
    # Tasks with preferred_time but no start_time should still sort correctly
    owner = Owner("Jordan", available_minutes=120)
    pet = make_pet()
    pet.add_task(make_task(name="Evening groom", task_type="grooming", duration_minutes=10, priority="medium", preferred_time="evening"))
    pet.add_task(make_task(name="Morning walk",  task_type="walk",     duration_minutes=30, priority="high",   preferred_time="morning"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    sorted_pairs = scheduler.sort_by_time(owner.get_all_tasks())
    names = [t.name for _, t in sorted_pairs]
    assert names == ["Morning walk", "Evening groom"]


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    owner = Owner("Jordan", available_minutes=120)
    pet = make_pet()
    # Walk starts 08:00, lasts 30 min → ends 08:30
    # Check-in starts 08:15 → overlaps
    pet.add_task(make_task(name="Morning walk", task_type="walk",  duration_minutes=30, priority="high",   start_time="08:00"))
    pet.add_task(make_task(name="Quick check",  task_type="other", duration_minutes=20, priority="medium", start_time="08:15"))
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1
    assert "Morning walk" in warnings[0]
    assert "Quick check" in warnings[0]


def test_detect_conflicts_exact_same_start_time():
    owner = Owner("Jordan", available_minutes=120)
    pet = make_pet()
    pet.add_task(make_task(name="Walk",    task_type="walk",    duration_minutes=30, priority="high", start_time="09:00"))
    pet.add_task(make_task(name="Feeding", task_type="feeding", duration_minutes=10, priority="high", start_time="09:00"))
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1


def test_detect_no_conflicts_when_tasks_are_sequential():
    owner = Owner("Jordan", available_minutes=120)
    pet = make_pet()
    # Walk 08:00–08:30, feeding 08:30 — back-to-back, no overlap
    pet.add_task(make_task(name="Walk",    task_type="walk",    duration_minutes=30, priority="high", start_time="08:00"))
    pet.add_task(make_task(name="Feeding", task_type="feeding", duration_minutes=10, priority="high", start_time="08:30"))
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_conflicts()
    assert warnings == []


def test_detect_conflicts_ignores_tasks_without_start_time():
    # Tasks with no start_time should not be compared (not enough info)
    owner = Owner("Jordan", available_minutes=120)
    pet = make_pet()
    pet.add_task(make_task(name="Walk",    task_type="walk",    duration_minutes=30, priority="high"))
    pet.add_task(make_task(name="Feeding", task_type="feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_conflicts()
    assert warnings == []


# ---------------------------------------------------------------------------
# Edge cases — scheduler with no tasks / no pets
# ---------------------------------------------------------------------------

def test_generate_plan_with_no_pets_returns_empty_plan():
    owner = Owner("Jordan", available_minutes=60)
    plan = Scheduler(owner).generate_plan()
    assert plan.scheduled_tasks == []
    assert plan.skipped_tasks == []


def test_generate_plan_with_pet_but_no_tasks_returns_empty_plan():
    owner = Owner("Jordan", available_minutes=60)
    owner.add_pet(make_pet())
    plan = Scheduler(owner).generate_plan()
    assert plan.scheduled_tasks == []


def test_generate_plan_skips_task_exceeding_budget():
    owner = Owner("Jordan", available_minutes=10)
    pet = make_pet()
    pet.add_task(make_task(name="Long walk", duration_minutes=60, priority="high"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_plan()
    assert plan.scheduled_tasks == []
    assert len(plan.skipped_tasks) == 1


def test_filter_tasks_by_pet_name():
    owner = Owner("Jordan", available_minutes=120)
    mochi = make_pet("Mochi")
    luna  = make_pet("Luna")
    mochi.add_task(make_task(name="Walk",    task_type="walk",    duration_minutes=30, priority="high"))
    luna.add_task( make_task(name="Feeding", task_type="feeding", duration_minutes=10, priority="high"))
    owner.add_pet(mochi)
    owner.add_pet(luna)

    results = Scheduler(owner).filter_tasks(pet_name="Luna")
    assert len(results) == 1
    assert results[0][1].name == "Feeding"
