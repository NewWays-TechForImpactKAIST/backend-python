from collections import Counter
import math

def count(data, stair = 0):
    return Counter(data)

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