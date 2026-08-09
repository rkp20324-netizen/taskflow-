"""
Section 2 Task 7 — automated checks for the algorithms engine.
Run with:  python3 check_algorithms.py
Prints one PASS/FAIL line per case. No assert/pytest/unittest used.
"""
from algorithms import (
    insertion_sort,
    binary_search,
    linear_search,
    insertion_sort_count,
    binary_search_count,
    linear_search_count,
)


def check(case_name, result, expected):
    if result == expected:
        print(f"PASS: {case_name}")
    else:
        print(f"FAIL: {case_name} — expected {expected}, got {result}")


def run_checks():
    # 1. insertion_sort on empty list leaves it empty, no error.
    records = []
    insertion_sort(records, "val")
    check("insertion_sort empty list", records, [])

    # 2. insertion_sort on single-element list leaves it unchanged.
    records = [{"val": 42}]
    insertion_sort(records, "val")
    check("insertion_sort single element", records, [{"val": 42}])

    # 3. binary_search finds value at first, last, and middle index.
    sorted_records = [{"val": v} for v in [1, 2, 3, 4, 5]]
    check("binary_search first index", binary_search(sorted_records, 1, "val"), 0)
    check("binary_search last index", binary_search(sorted_records, 5, "val"), 4)
    check("binary_search middle index", binary_search(sorted_records, 3, "val"), 2)

    # 4. binary_search returns not-found (-1) when target absent.
    check("binary_search not found", binary_search(sorted_records, 99, "val"), -1)

    # 5. insertion_sort_count: small hand-checkable list.
    records = [{"val": 3}, {"val": 1}, {"val": 2}]
    count = insertion_sort_count(records, "val")
    check("insertion_sort_count sorts correctly", records, [{"val": 1}, {"val": 2}, {"val": 3}])
    check("insertion_sort_count returns positive int", type(count) == int and count > 0, True)

    # 6. binary_search_count on sorted list, value present at known index.
    sorted_records = [{"val": v} for v in [10, 20, 30, 40, 50]]
    result = binary_search_count(sorted_records, 30, "val")
    check("binary_search_count index correct", result["index"], 2)
    check("binary_search_count comparison_count positive int",
          type(result["comparison_count"]) == int and result["comparison_count"] > 0, True)

    # 7. linear_search_count on a list, value absent.
    records = [{"val": v} for v in [5, 6, 7, 8]]
    result = linear_search_count(records, 999, "val")
    check("linear_search_count not-found index", result["index"], -1)
    check("linear_search_count comparison_count equals list length", result["comparison_count"], len(records))


if __name__ == "__main__":
    run_checks()
