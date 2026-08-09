"""
Section 2 Task 5/6 — benchmark the counting wrappers against
synthetic task data shaped exactly like the app's real task fields
(title, priority, due_date), at three sizes: 10, 500, 3000.

Run with:  python3 benchmark.py
Writes raw numbers to benchmark_results.txt (also printed to stdout).
"""
import random
import copy

from algorithms import insertion_sort_count, binary_search_count, linear_search_count

PRIORITIES = ["low", "medium", "high"]
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
SIZES = [10, 500, 3000]


def make_records(n):
    records = []
    for i in range(n):
        records.append({
            "id": i,
            "title": f"task-{i}-{random.randint(0, 999999)}",
            "priority": random.choice(PRIORITIES),
            "due_date": random.choice([None, "tomorrow", "next friday"]),
        })
    return records


def run_benchmark():
    lines = []
    lines.append("TaskFlow Section 2 Benchmark — comparison counts\n")

    for n in SIZES:
        lines.append(f"\n=== Size: {n} tasks ===")

        # insertion_sort_count by priority rank
        records = make_records(n)
        for r in records:
            r["_rank"] = PRIORITY_RANK[r["priority"]]
        sort_comparisons = insertion_sort_count(records, "_rank")
        lines.append(f"insertion_sort_count (sort by priority): {sort_comparisons} comparisons")

        # build a sorted-by-title index for binary search
        index = [{"id": r["id"], "title": r["title"]} for r in records]
        insertion_sort_count(index, "title")  # sort by title (cost not counted here, only search cost below)

        target_title = index[n // 2]["title"] if n > 0 else None
        missing_title = "___does_not_exist___"

        if n > 0:
            bs_hit = binary_search_count(index, target_title, "title")
            lines.append(f"binary_search_count (hit):  index={bs_hit['index']}, comparisons={bs_hit['comparison_count']}")
        bs_miss = binary_search_count(index, missing_title, "title")
        lines.append(f"binary_search_count (miss): index={bs_miss['index']}, comparisons={bs_miss['comparison_count']}")

        if n > 0:
            ls_hit = linear_search_count(index, target_title, "title")
            lines.append(f"linear_search_count (hit):  index={ls_hit['index']}, comparisons={ls_hit['comparison_count']}")
        ls_miss = linear_search_count(index, missing_title, "title")
        lines.append(f"linear_search_count (miss): index={ls_miss['index']}, comparisons={ls_miss['comparison_count']}")

    output = "\n".join(lines)
    print(output)
    with open("benchmark_results.txt", "w") as f:
        f.write(output + "\n")


if __name__ == "__main__":
    run_benchmark()
