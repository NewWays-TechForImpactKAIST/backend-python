from collections import Counter
import math

def count(data, stair = 0):
    """
    Count the number of occurrences of each value in a dataset
    """
    counts = Counter()
    for row in data:
        counts[row[stair]] += 1
    return counts

def gini_simpson(data, stair, opts):
    """
    Gini-Simpson diversity index
    """
    counts = count(data, stair)
    total = sum(counts.values())
    return 1 - sum((n / total) ** 2 for n in counts.values())

def shannon(data, stair, opts):
    """
    Shannon diversity index
    """
    counts = count(data, stair)
    total = sum(counts.values())
    return -sum((n / total) * math.log(n / total) for n in counts.values())