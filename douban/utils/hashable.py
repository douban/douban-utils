import collections

def hashable(obj):
    if isinstance(obj, collections.Hashable):
        return obj
    if isinstance(obj, collections.Mapping):
        items = [(k,hashable(v)) for (k,v) in obj.iteritems()]
        return frozenset(items)
    if isinstance(obj, collections.Iterable):
        return tuple([hashable(item) for item in obj])
    raise TypeError(type(obj))