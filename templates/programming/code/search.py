def binary_search(values, target):
    """Return first matching index, or -1. Input must be sorted."""
    lo, hi = 0, len(values)
    while lo < hi:
        mid = (lo + hi) // 2
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo if lo < len(values) and values[lo] == target else -1
