"""Deterministic fixture set for RAG evaluation and regression testing."""

from __future__ import annotations

EVALUATION_DATASET = [
    {
        "id": "case_1_exact_lookup",
        "name": "Exact Task Lookup",
        "user_id": 101,
        "memories": [
            {
                "id": "mem_101",
                "task_id": 1,
                "action": "CREATE",
                "content": "Created task 'Prepare quarterly budget report' due on 2026-09-01 with priority HIGH.",
            }
        ],
        "query": "Prepare quarterly budget report",
        "expected_top_source": "mem_101",
        "min_precision": 1.0,
        "min_recall": 1.0,
    },
    {
        "id": "case_2_semantic_lookup",
        "name": "Semantic Lookup",
        "user_id": 102,
        "memories": [
            {
                "id": "mem_201",
                "task_id": 2,
                "action": "CREATE",
                "content": "Created task 'Study graph algorithms and shortest paths for technical interview'.",
            }
        ],
        "query": "Dijkstra algorithm study session",
        "expected_top_source": "mem_201",
        "min_precision": 1.0,
        "min_recall": 1.0,
    },
    {
        "id": "case_3_recent_task",
        "name": "Recent Task Lookup",
        "user_id": 103,
        "memories": [
            {
                "id": "mem_301",
                "task_id": 3,
                "action": "COMPLETE",
                "content": "Completed task 'Update production database indexes' in 45 minutes on 2026-08-10.",
            }
        ],
        "query": "What database work did I complete recently?",
        "expected_top_source": "mem_301",
        "min_precision": 1.0,
        "min_recall": 1.0,
    },
    {
        "id": "case_4_completed_task",
        "name": "Completed Task Lookup",
        "user_id": 104,
        "memories": [
            {
                "id": "mem_401",
                "task_id": 4,
                "action": "COMPLETE",
                "content": "Completed task 'Setup Docker Compose Orchestration' in 30 minutes.",
            }
        ],
        "query": "Did I finish setting up Docker Compose?",
        "expected_top_source": "mem_401",
        "min_precision": 1.0,
        "min_recall": 1.0,
    },
    {
        "id": "case_5_irrelevant_task",
        "name": "Irrelevant Task Filtering",
        "user_id": 105,
        "memories": [
            {
                "id": "mem_501",
                "task_id": 5,
                "action": "CREATE",
                "content": "Created task 'Buy groceries: apples, milk, bread'.",
            }
        ],
        "query": "Quantum computing research notes",
        "expected_top_source": None,
        "min_precision": 0.0,
        "min_recall": 0.0,
    },
    {
        "id": "case_6_multiple_relevant",
        "name": "Multiple Relevant Memories",
        "user_id": 106,
        "memories": [
            {
                "id": "mem_601",
                "task_id": 6,
                "action": "CREATE",
                "content": "Created task 'React component architecture review'.",
            },
            {
                "id": "mem_602",
                "task_id": 7,
                "action": "COMPLETE",
                "content": "Completed task 'React state management with Redux Toolkit' in 90 minutes.",
            },
        ],
        "query": "Frontend React development tasks",
        "expected_top_source": None,  # Either mem_601 or mem_602 is valid
        "min_precision": 0.5,
        "min_recall": 1.0,
    },
    {
        "id": "case_7_empty_history",
        "name": "Empty History",
        "user_id": 107,
        "memories": [],
        "query": "What are my upcoming tasks?",
        "expected_top_source": None,
        "min_precision": 0.0,
        "min_recall": 0.0,
    },
    {
        "id": "case_8_ambiguous_query",
        "name": "Ambiguous Query",
        "user_id": 108,
        "memories": [
            {
                "id": "mem_801",
                "task_id": 8,
                "action": "UPDATE",
                "content": "Updated task 'Review pull requests' status to IN_PROGRESS.",
            }
        ],
        "query": "status",
        "expected_top_source": "mem_801",
        "min_precision": 0.0,
        "min_recall": 0.0,
    },
]
