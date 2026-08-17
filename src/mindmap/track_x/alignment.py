from __future__ import annotations

from collections.abc import Callable, Sequence

from .model import AlignmentPair

ScoreFunction = Callable[[object, object], float]


def _hungarian_min_cost(cost: Sequence[Sequence[float]]) -> list[int]:
    """Return the assigned column for each row using the Hungarian algorithm.

    The input must be square. The implementation follows the standard
    potential-based O(n^3) formulation and is deterministic under ties.
    """

    n = len(cost)
    if n == 0:
        return []
    if any(len(row) != n for row in cost):
        raise ValueError("cost matrix must be square")

    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        minv = [float("inf")] * (n + 1)
        used = [False] * (n + 1)
        j0 = 0
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    assignment = [-1] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1
    return assignment


def maximum_weight_alignment(
    gold: Sequence[object],
    predicted: Sequence[object],
    score_fn: ScoreFunction,
    *,
    minimum_score: float = 0.5,
) -> tuple[AlignmentPair, ...]:
    """Compute a deterministic maximum-weight one-to-one event alignment.

    Scores below ``minimum_score`` are treated as absent edges before solving,
    which prevents several weak matches from displacing one valid match.
    Dummy rows/columns have zero weight and permit unmatched records.
    """

    if not 0.0 <= minimum_score <= 1.0:
        raise ValueError("minimum_score must lie in [0, 1]")
    if not gold or not predicted:
        return ()

    size = max(len(gold), len(predicted))
    weights = [[0.0 for _ in range(size)] for _ in range(size)]
    for i, left in enumerate(gold):
        for j, right in enumerate(predicted):
            value = float(score_fn(left, right))
            if not 0.0 <= value <= 1.0:
                raise ValueError("alignment scores must lie in [0, 1]")
            if value >= minimum_score:
                weights[i][j] = value

    # Minimize (1 - weight) for real and dummy cells. Since every row receives
    # exactly one column, this is equivalent to maximizing total weight.
    cost = [[1.0 - value for value in row] for row in weights]
    assignment = _hungarian_min_cost(cost)

    pairs: list[AlignmentPair] = []
    for i, j in enumerate(assignment):
        if i >= len(gold) or j < 0 or j >= len(predicted):
            continue
        score = weights[i][j]
        if score >= minimum_score:
            pairs.append(AlignmentPair(i, j, score))
    return tuple(sorted(pairs, key=lambda pair: (pair.gold_index, pair.predicted_index)))
