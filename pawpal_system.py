"""
PawPal+ – backend logic layer.
All core classes live here; app.py imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task – a single care activity
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity."""

    name: str
    task_type: Literal["walk", "feeding", "meds", "grooming", "enrichment", "other"]
    duration_minutes: int
    priority: Literal["low", "medium", "high"]
    frequency: Literal["daily", "weekly", "as-needed"] = "daily"
    preferred_time: Literal["morning", "afternoon", "evening", "any"] = "any"
    completed: bool = False

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError(f"Task '{self.name}': duration_minutes must be > 0.")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"Task '{self.name}': priority must be low/medium/high.")

    def mark_complete(self) -> None:
        """Mark this task as done for today."""
        self.completed = True

    def reset(self) -> None:
        """Clear completion status (e.g. at the start of a new day)."""
        self.completed = False

    def to_dict(self) -> dict:
        """Return a plain-dict representation (useful for Streamlit tables)."""
        return {
            "name": self.name,
            "type": self.task_type,
            "duration (min)": self.duration_minutes,
            "priority": self.priority,
            "frequency": self.frequency,
            "preferred time": self.preferred_time,
            "completed": self.completed,
        }


# ---------------------------------------------------------------------------
# Pet – stores pet details and owns its task list
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet and the care tasks associated with it."""

    name: str
    species: Literal["dog", "cat", "other"]
    age: int  # years
    tasks: list[Task] = field(default_factory=list)

    def get_info(self) -> str:
        """Return a human-readable summary of the pet."""
        return f"{self.name} ({self.species}, {self.age} yr old) — {len(self.tasks)} task(s)"

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove a task by name. Raises ValueError if not found."""
        for i, t in enumerate(self.tasks):
            if t.name.lower() == name.lower():
                self.tasks.pop(i)
                return
        raise ValueError(f"No task named '{name}' found for {self.name}.")

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


# ---------------------------------------------------------------------------
# Owner – manages one or more pets
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Represents the pet owner and their daily availability."""

    name: str
    available_minutes: int  # total time budget for pet care per day
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name. Raises ValueError if not found."""
        for i, p in enumerate(self.pets):
            if p.name.lower() == name.lower():
                self.pets.pop(i)
                return
        raise ValueError(f"No pet named '{name}' found for owner {self.name}.")

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_available_time(self) -> int:
        """Return the number of minutes available for pet care today."""
        return self.available_minutes


# ---------------------------------------------------------------------------
# Scheduler – the "brain" that organises tasks across all pets
# ---------------------------------------------------------------------------

class Scheduler:
    """Selects and orders pending tasks across all pets to fit within the owner's daily time budget."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def _sorted_pending(self) -> list[tuple[Pet, Task]]:
        """Return all pending (pet, task) pairs sorted by priority then duration."""
        pairs = [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed
        ]
        return sorted(pairs, key=lambda pt: (PRIORITY_ORDER[pt[1].priority], pt[1].duration_minutes))

    def generate_plan(self) -> DailyPlan:
        """Build a DailyPlan by greedily fitting tasks into the available time budget, highest priority first."""
        budget = self.owner.get_available_time()
        scheduled: list[tuple[Pet, Task]] = []
        skipped: list[tuple[Pet, Task]] = []

        for pet, task in self._sorted_pending():
            if task.duration_minutes <= budget:
                scheduled.append((pet, task))
                budget -= task.duration_minutes
            else:
                skipped.append((pet, task))

        return DailyPlan(scheduled_pairs=scheduled, skipped_pairs=skipped, owner=self.owner)

    def mark_task_complete(self, pet_name: str, task_name: str) -> None:
        """Mark a specific task as completed."""
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                for task in pet.tasks:
                    if task.name.lower() == task_name.lower():
                        task.mark_complete()
                        return
                raise ValueError(f"No task '{task_name}' on pet '{pet_name}'.")
        raise ValueError(f"No pet named '{pet_name}'.")

    def reset_all_tasks(self) -> None:
        """Clear completion status on every task (call at the start of a new day)."""
        for _, task in self.owner.get_all_tasks():
            task.reset()


# ---------------------------------------------------------------------------
# DailyPlan – the output produced by Scheduler.generate_plan()
# ---------------------------------------------------------------------------

class DailyPlan:
    """The result of a scheduling run: which tasks fit and which were skipped."""

    def __init__(
        self,
        scheduled_pairs: list[tuple[Pet, Task]],
        skipped_pairs: list[tuple[Pet, Task]],
        owner: Owner,
    ) -> None:
        self.scheduled_pairs = scheduled_pairs
        self.skipped_pairs = skipped_pairs
        self.owner = owner
        self.total_duration: int = sum(t.duration_minutes for _, t in scheduled_pairs)

    # Convenience accessors ---------------------------------------------------

    @property
    def scheduled_tasks(self) -> list[Task]:
        return [t for _, t in self.scheduled_pairs]

    @property
    def skipped_tasks(self) -> list[Task]:
        return [t for _, t in self.skipped_pairs]

    # Display -----------------------------------------------------------------

    def display(self) -> str:
        """Return a formatted string listing the scheduled tasks in order."""
        if not self.scheduled_pairs:
            return "No tasks scheduled — either no tasks exist or the time budget is 0."

        lines = [f"Daily plan for {self.owner.name} ({self.total_duration} / {self.owner.available_minutes} min used)\n"]
        for pet, task in self.scheduled_pairs:
            status = "[done]" if task.completed else "[ ]"
            lines.append(f"  {status} [{task.priority.upper()}] {pet.name}: {task.name} ({task.duration_minutes} min)")

        if self.skipped_pairs:
            lines.append("\nSkipped (not enough time):")
            for pet, task in self.skipped_pairs:
                lines.append(f"  - {pet.name}: {task.name} ({task.duration_minutes} min, {task.priority} priority)")

        return "\n".join(lines)

    def explain(self) -> str:
        """Explain why each task was included or skipped."""
        budget = self.owner.available_minutes
        lines = [
            f"{self.owner.name} has {budget} minutes available today.",
            f"{len(self.scheduled_pairs)} task(s) scheduled, "
            f"{len(self.skipped_pairs)} skipped.\n",
        ]

        for pet, task in self.scheduled_pairs:
            lines.append(
                f"✓ '{task.name}' ({pet.name}) included — {task.priority} priority, {task.duration_minutes} min."
            )

        for pet, task in self.skipped_pairs:
            lines.append(
                f"✗ '{task.name}' ({pet.name}) skipped — {task.duration_minutes} min needed but budget ran out."
            )

        return "\n".join(lines)
