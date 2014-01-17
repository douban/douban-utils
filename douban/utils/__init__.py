#!/usr/bin/env python
# encoding: utf-8

from .read_object import read_object
from .empty import Empty
from .format import format

import threading
from .decorators import trans, ptrans

class ThreadedObject:
    "threaded objects"
    def __init__(self, cls, *args, **kw):
        self.local = threading.local()
        self._args = (cls, args, kw)

        def creator():
            return cls(*args, **kw)
        self.creator = creator

    def __getstate__(self):
        return self._args

    def __setstate__(self, state):
        cls, args, kw = state
        self.__init__(cls, *args, **kw)

    def __getattr__(self, name):
        obj = getattr(self.local, 'obj', None)
        if obj is None:
            self.local.obj = obj = self.creator()
        return getattr(obj, name)

class LazyObject:
    "create obj when necessary"
    def __init__(self, cls, *args, **kwargs):
        def creator():
            return cls(*args, **kwargs)
        self.creator = creator
        self.obj = None

    def __getattr__(self, name):
        if self.obj is None:
            self.obj = self.creator()
        return getattr(self.obj, name)

def hashdict(d):
    """
    make dictionary becomes a immutable tuple (from dae.util)
    """
    if isinstance(d, list):
        return tuple(hashdict(v) for v in d)
    elif isinstance(d, dict):
        return tuple(sorted((k, hashdict(v)) for k, v in d.iteritems()))
    else:
        return d
