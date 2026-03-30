"""
tests/test_pawpal.py – unit tests for PawPal+ core logic.
Run with: python3 -m pytest
"""

from pawpal_system import Pet, Task


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


# ---------------------------------------------------------------------------
# Task completion
# ---------------------------------------------------------------------------

def test_mark_complete_daily_auto_resets_and_advances_due_date():
    # Daily tasks auto-reset completed=False and advance due_date by 1 day
    from datetime import timedelta
    task = make_task(frequency="daily")
    original_due = task.due_date
    task.mark_complete()
    assert task.completed is False                          # auto-reset for recurrence
    assert task.due_date == original_due + timedelta(days=1)


def test_mark_complete_as_needed_stays_completed():
    # as-needed tasks stay completed=True (no recurrence)
    task = make_task(frequency="as-needed")
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_weekly_advances_due_date_by_seven_days():
    from datetime import timedelta
    task = make_task(frequency="weekly")
    original_due = task.due_date
    task.mark_complete()
    assert task.due_date == original_due + timedelta(weeks=1)


def test_reset_clears_completed_status():
    task = make_task(frequency="as-needed")   # as-needed stays True after mark_complete
    task.mark_complete()
    task.reset()
    assert task.completed is False


# ---------------------------------------------------------------------------
# Pet task management
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(make_task(name="Feeding", task_type="feeding", duration_minutes=10))
    assert len(pet.tasks) == 1
    pet.add_task(make_task(name="Walk", task_type="walk", duration_minutes=30))
    assert len(pet.tasks) == 2
