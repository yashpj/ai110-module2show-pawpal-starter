import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state – initialise once, persist across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None   # set properly when the user submits the form below

# ---------------------------------------------------------------------------
# Section 1: Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner & Time Budget")

with st.form("owner_form"):
    owner_name      = st.text_input("Your name", value="Jordan")
    avail_minutes   = st.number_input("Minutes available today", min_value=10, max_value=480, value=90)
    submitted       = st.form_submit_button("Save owner")

if submitted:
    # If owner already exists, keep their pets; only update name/time.
    if st.session_state.owner is None:
        st.session_state.owner = Owner(name=owner_name, available_minutes=avail_minutes)
    else:
        st.session_state.owner.name              = owner_name
        st.session_state.owner.available_minutes = avail_minutes
    st.success(f"Owner saved: {owner_name} ({avail_minutes} min available)")

# Guard: nothing below works without an owner
if st.session_state.owner is None:
    st.info("Fill in your name and available time above to get started.")
    st.stop()

owner = st.session_state.owner   # convenience alias

# ---------------------------------------------------------------------------
# Section 2: Add a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Add a Pet")

with st.form("pet_form"):
    pet_name    = st.text_input("Pet name", value="Mochi")
    pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    pet_age     = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    add_pet     = st.form_submit_button("Add pet")

if add_pet:
    # Avoid duplicate pet names
    existing = [p.name.lower() for p in owner.pets]
    if pet_name.lower() in existing:
        st.warning(f"A pet named '{pet_name}' already exists.")
    else:
        new_pet = Pet(name=pet_name, species=pet_species, age=pet_age)
        owner.add_pet(new_pet)          # <-- calls Pet.add_pet() via Owner.add_pet()
        st.success(f"Added {pet_name} the {pet_species}!")

if owner.pets:
    st.write("**Your pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.get_info()}")   # <-- calls Pet.get_info()
else:
    st.info("No pets yet — add one above.")

# ---------------------------------------------------------------------------
# Section 3: Add a task to a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Add a Task")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("task_form"):
        target_pet  = st.selectbox("Which pet?", [p.name for p in owner.pets])
        task_name   = st.text_input("Task name", value="Morning walk")
        task_type   = st.selectbox("Type", ["walk", "feeding", "meds", "grooming", "enrichment", "other"])
        duration    = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority    = st.selectbox("Priority", ["high", "medium", "low"])
        pref_time   = st.selectbox("Preferred time", ["any", "morning", "afternoon", "evening"])
        add_task    = st.form_submit_button("Add task")

    if add_task:
        pet = next(p for p in owner.pets if p.name == target_pet)
        try:
            new_task = Task(
                name=task_name,
                task_type=task_type,
                duration_minutes=int(duration),
                priority=priority,
                preferred_time=pref_time,
            )
            pet.add_task(new_task)      # <-- calls Pet.add_task()
            st.success(f"Added '{task_name}' to {target_pet}.")
        except ValueError as e:
            st.error(str(e))

    # Show current tasks per pet, sorted chronologically
    scheduler_preview = Scheduler(owner)
    for pet in owner.pets:
        if pet.tasks:
            st.write(f"**{pet.name}'s tasks** (sorted by time):")
            sorted_pairs = scheduler_preview.sort_by_time([(pet, t) for t in pet.tasks])
            st.table([t.to_dict() for _, t in sorted_pairs])   # <-- sort_by_time + to_dict()

# ---------------------------------------------------------------------------
# Section 4: Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Generate Today's Schedule")

all_tasks = owner.get_all_tasks()   # <-- calls Owner.get_all_tasks()
if not all_tasks:
    st.info("Add at least one task before generating a schedule.")
else:
    if st.button("Generate schedule"):
        scheduler = Scheduler(owner)
        plan      = scheduler.generate_plan()

        # ---- Conflict warnings (shown first so owner can act on them) --------
        if plan.conflicts:
            st.subheader("⚠️ Scheduling Conflicts")
            for warning in plan.conflicts:
                st.warning(warning)
            st.caption("Conflicts are shown as warnings — your plan is still generated below. Adjust task start times to resolve them.")

        # ---- Scheduled tasks as a table -------------------------------------
        st.subheader("Scheduled Tasks")
        if plan.scheduled_pairs:
            progress = plan.total_duration / owner.available_minutes
            st.progress(min(progress, 1.0), text=f"{plan.total_duration} / {owner.available_minutes} min used")

            scheduled_rows = [
                {
                    "pet":       pet.name,
                    "task":      task.name,
                    "start":     task.start_time or task.preferred_time,
                    "duration":  f"{task.duration_minutes} min",
                    "priority":  task.priority,
                    "frequency": task.frequency,
                }
                for pet, task in plan.scheduled_pairs
            ]
            st.table(scheduled_rows)
        else:
            st.info("No tasks fit within your available time.")

        # ---- Skipped tasks --------------------------------------------------
        if plan.skipped_pairs:
            with st.expander(f"Skipped tasks ({len(plan.skipped_pairs)})"):
                for pet, task in plan.skipped_pairs:
                    st.error(f"{pet.name}: {task.name} — {task.duration_minutes} min ({task.priority} priority) didn't fit.")

        # ---- Reasoning ------------------------------------------------------
        with st.expander("Why this plan?"):
            st.text(plan.explain())
