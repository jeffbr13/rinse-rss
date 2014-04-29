#!python
# -*- coding: utf-8 -*-
from collections import defaultdict


def groupby_all(iterable, key=None):
    """Sorts an iterable's elements into a dict of lists, based on the value of the item or the provided key function.

    Similar to itertools.groupby, except `classify` groups all items of a  sorting is done in-memory, and a dict is returned.
    """
    d = defaultdict(list)

    if key:
        for el in iterable:
            d[key(el)].append(el)

    else:
        for el in iterable:
            d[el].append(el)

    # Convert to a regular dict
    return dict(d)
