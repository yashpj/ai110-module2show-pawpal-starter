// classDiagram
//     class Owner {
//         +String name
//         +int available_minutes
//         +get_available_time() int
//     }

//     class Pet {
//         +String name
//         +String species
//         +int age
//         +get_info() String
//     }

//     class Task {
//         +String name
//         +String task_type
//         +int duration_minutes
//         +String priority
//         +String preferred_time
//         +is_valid() bool
//         +to_dict() dict
//     }

//     class Scheduler {
//         +Owner owner
//         +Pet pet
//         +List tasks
//         +add_task(task) void
//         +remove_task(name) void
//         +generate_plan() DailyPlan
//     }

//     class DailyPlan {
//         +List scheduled_tasks
//         +List skipped_tasks
//         +int total_duration
//         +display() String
//         +explain() String
//     }

//     Owner "1" --> "1" Pet : owns
//     Scheduler --> Owner : uses
//     Scheduler --> Pet : uses
//     Scheduler --> Task : manages
//     Scheduler --> DailyPlan : produces
//     DailyPlan --> Task : contains
