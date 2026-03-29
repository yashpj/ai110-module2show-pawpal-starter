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

def test_mark_complete_sets_completed_true():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_reset_clears_completed_status():
    task = make_task()
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
