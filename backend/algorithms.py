"""
Section 2 — Integrated Algorithms Engine.

Hand-rolled insertion sort / binary search / linear search that power
two real endpoints in main.py (GET /tasks?sort=... and
GET /tasks/search). No use of Python's built-in sorted()/list.sort().

Not-found convention: functions here return -1 when a target is not found
(documented explicitly, per the brief's "pick one and document it").
"""
from typing import List, Dict, Any, Optional


def insertion_sort(records: List[Dict[str, Any]], key: str) -> None:
    """
    Standard insertion sort. Sorts `records` in place, ascending, by
    record[key]. No return value (mutates the list directly).
    """
    for i in range(1, len(records)):
        current = records[i]
        current_val = current[key]
        j = i - 1
        while j >= 0 and records[j][key] > current_val:
            records[j + 1] = records[j]
            j -= 1
        records[j + 1] = current


def binary_search(sorted_records: List[Dict[str, Any]], target_value, key: str) -> int:
    """
    Standard binary search over a list already sorted ascending by key.
    Returns the index of a record whose record[key] == target_value,
    or -1 if not found.
    """
    low = 0
    high = len(sorted_records) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_val = sorted_records[mid][key]
        if mid_val == target_value:
            return mid
        elif mid_val < target_value:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def linear_search(records: List[Dict[str, Any]], target_value, key: str) -> int:
    """
    Baseline linear search: scans every record in order, returns the
    index of the first match, or -1 if absent.
    """
    for i, record in enumerate(records):
        if record[key] == target_value:
            return i
    return -1


# ---------------------------------------------------------------------------
# Comparison-counting wrappers (Task 5). These reimplement the same logic
# as the functions above (same signatures/return contracts are NOT reused
# verbatim — these have their own contracts) purely so we can count how
# many key-comparisons each algorithm performs, for the benchmark.
# ---------------------------------------------------------------------------

def insertion_sort_count(records: List[Dict[str, Any]], key: str) -> int:
    """
    Sorts `records` in place exactly like insertion_sort, and returns a
    single int: the number of element comparisons performed.
    """
    comparisons = 0
    for i in range(1, len(records)):
        current = records[i]
        current_val = current[key]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if records[j][key] > current_val:
                records[j + 1] = records[j]
                j -= 1
            else:
                break
        records[j + 1] = current
    return comparisons


def binary_search_count(sorted_records: List[Dict[str, Any]], target_value, key: str) -> dict:
    """
    Binary search that also counts comparisons.
    Returns {"index": <int>, "comparison_count": <int>}.
    """
    comparisons = 0
    low = 0
    high = len(sorted_records) - 1
    index = -1
    while low <= high:
        mid = (low + high) // 2
        mid_val = sorted_records[mid][key]
        comparisons += 1
        if mid_val == target_value:
            index = mid
            break
        elif mid_val < target_value:
            low = mid + 1
        else:
            high = mid - 1
    return {"index": index, "comparison_count": comparisons}


def linear_search_count(records: List[Dict[str, Any]], target_value, key: str) -> dict:
    """
    Linear search that also counts comparisons.
    Returns {"index": <int>, "comparison_count": <int>}.
    On a miss, comparison_count equals len(records).
    """
    comparisons = 0
    index = -1
    for i, record in enumerate(records):
        comparisons += 1
        if record[key] == target_value:
            index = i
            break
    return {"index": index, "comparison_count": comparisons}
