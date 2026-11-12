from search import binary_search
cases = [([],4,-1),([2,4,6],4,1),([2,4,6],5,-1),([2,2,2],2,0)]
for values, target, expected in cases:
    assert binary_search(values, target) == expected
# Differential check against a linear oracle, including duplicates and misses.
from itertools import combinations_with_replacement
for size in range(7):
    for data in combinations_with_replacement(range(4), size):
        for target in range(-1,5):
            expected = data.index(target) if target in data else -1
            assert binary_search(data,target) == expected
print('Search cases and exhaustive small-input oracle comparison passed.')
