from collections import Counter
import math


def count(data, stair=0):
    """
    Returns a counter object of the data, while stairing them to appropriate bins if stair > 0
    """
    if stair > 0:
        if isinstance(data[0], str):
            raise TypeError("stair is not defined for string data")
        data = [math.floor(d / stair) * stair for d in data]
    return Counter(data)


def gini_simpson(data, stair=0, opts=False):
    """
    Gini-Simpson diversity index
    """
    counts = count(data, stair)
    total = sum(counts.values())
    gs_idx = 1 - sum((n / total) ** 2 for n in counts.values())

    if opts:
        num_cats = len([c for c in counts.values() if c > 0])
        max_gs_idx = (num_cats - 1) / num_cats * total / (total - 1)
        gs_idx /= max_gs_idx

    return gs_idx


def shannon(data, stair=0, opts=False):
    """
    Shannon diversity index
    """
    counts = count(data, stair)
    total = sum(counts.values())
    sh_idx = -sum((n / total) * math.log(n / total) for n in counts.values())

    if opts:
        num_cats = len([c for c in counts.values() if c > 0])
        max_sh_idx = math.log(num_cats)
        sh_idx /= max_sh_idx

    return sh_idx
