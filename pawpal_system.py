"""
PawPal+ – backend logic layer.
All core classes live here; app.py imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Data classes (plain data holders – no scheduling logic)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet whose care tasks are being planned."""

    name: str
    species: Literal["dog", "cat", "other"]
    age: int  # years

    def get_info(self) -> str:
        """Return a human-readable summary of the pet."""
        ...


@dataclass
class Task:
    """A single pet-care task (walk, feeding, meds, etc.)."""

    name: str
    task_type: Literal["walk", "feeding", "meds", "grooming", "enrichment", "other"]
    duration_minutes: int
    priority: Literal["low", "medium", "high"]
    preferred_time: Literal["morning", "afternoon", "evening", "any"] = "any"

    def is_valid(self) -> bool:
        """Return True if the task has all required fields with sensible values."""
        ...

    def to_dict(self) -> dict:
        """Return a plain-dict representation (useful for Streamlit tables)."""
        ...


# ---------------------------------------------------------------------------
# Owner – holds user preferences and constraints
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their daily availability."""

    def __init__(self, name: str, available_minutes: int) -> None:
        self.name = name
        self.available_minutes = available_minutes  # total time free for pet care

    def get_available_time(self) -> int:
        """Return the number of minutes available for pet care today."""
        ...


# ---------------------------------------------------------------------------
# Scheduler – core logic layer
# ---------------------------------------------------------------------------

class Scheduler:
    """Selects and orders tasks to fit within the owner's available time."""

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the candidate list."""
        ...

    def remove_task(self, name: str) -> None:
        """Remove a task from the candidate list by name."""
        ...

    def generate_plan(self) -> DailyPlan:
        """
        Build a DailyPlan by selecting tasks that fit within available time,
        ordered by priority (high → medium → low).
        """
        ...


# ---------------------------------------------------------------------------
# DailyPlan – the output produced by Scheduler
# ---------------------------------------------------------------------------

class DailyPlan:
    """The result of a scheduling run: which tasks fit and which were skipped."""

    def __init__(
        self,
        scheduled_tasks: list[Task],
        skipped_tasks: list[Task],
    ) -> None:
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_duration: int = sum(t.duration_minutes for t in scheduled_tasks)

    def display(self) -> str:
        """Return a formatted string listing the scheduled tasks in order."""
        ...

    def explain(self) -> str:
        """Explain why each task was included or skipped."""
        ...
