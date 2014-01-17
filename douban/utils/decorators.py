#!/usr/bin/env python
# encoding: UTF-8

import sys
import time
from functools import wraps

def trans(op):
    def deco(f):
        @wraps(f)
        def _(*a, **kw):
            r = f(*a, **kw)
            if r is not None:
                return op(r)
        return _
    return deco

def ptrans(op):
    def deco(f):
        @wraps(f)
        def _(*a, **kw):
            return [op(r) for r in f(*a, **kw)]
        return _
    return deco

def retry(func):
    def _(*args, **kwargs):
        tries = 3 
        while tries:
            try:
                return func(*args, **kwargs)
            except Exception, e:
                print >>sys.stderr, 'error while %s' %func.func_name, tries, e, args, kwargs
                tries -= 1
                if tries == 0:
                    raise
                time.sleep(0.1)
    return _ 
