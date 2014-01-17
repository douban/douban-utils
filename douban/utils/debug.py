#!/usr/bin/env python
# encoding: utf-8
"""
debug.py
"""

import re
import time
import sys
import types
import gc
import os
from cStringIO import StringIO


normalize_re = re.compile(r'\d+')
class ObjCallLogger(object):
    """Log every call"""

    def __init__(self, obj):
        self.obj = obj
        self.log = []

    def __getattr__(self, name):
        attr = getattr(self.obj, name)
        def _(*a, **kw):
            call = format_call(name, *a, **kw)
            ncall = normalize_re.sub('-', call)
            t1 = time.time()
            r = attr(*a, **kw)
            cost = time.time() - t1
            self.log.append((call, ncall, cost))
            return r
        return _

def format_call(funcname, *a, **kw):
    arglist = [(repr(x)) for x in a]
    arglist += ["%s=%r" % (k, v) for k, v in kw.iteritems()]
    return "%s(%s)" % (funcname, ", ".join(arglist))

class CallLogger(object):
    def __init__(self, funcpath):
        self.orig_func = obj_from_string(funcpath)
        if isinstance(self.orig_func, types.MethodType):
            raise NotImplementedError("Do not support methods yet.")
        self.funcpath = funcpath
        self.log = []
        self.__global_replace__ = False
        global_replace(self.orig_func, self)

    def __call__(self, *a, **kw):
        call = format_call(self.funcpath, *a, **kw)
        t1 = time.time()
        try:
            return self.orig_func(*a, **kw)
        finally:
            cost = time.time() - t1
            self.log.append((call, cost))

    def close(self):
        global_replace(self, self.orig_func)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

def obj_from_string(s):
    # stolen from Mocker http://labix.org/mocker
    import_stack = s.split(".")
    attr_stack = []
    while import_stack:
        module_path = ".".join(import_stack)
        try:
            object = __import__(module_path, {}, {}, [""])
        except ImportError:
            attr_stack.insert(0, import_stack.pop())
            if not import_stack:
                raise
            continue
        else:
            for attr in attr_stack:
                object = getattr(object, attr)
            break
    return object

def global_replace(remove, install):
    """Replace object 'remove' with object 'install' on all dictionaries."""
    # stolen from Mocker http://labix.org/mocker
    for referrer in gc.get_referrers(remove):
        if (type(referrer) is dict and
            referrer.get("__global_replace__", True)):
            for key, value in referrer.items():
                if value is remove:
                    referrer[key] = install

    
def capture_output(func, *args, **kw):
    # Not threadsafe!
    out = StringIO()
    old_stdout = sys.stdout
    sys.stdout = out
    try:
        func(*args, **kw)
    finally:
        sys.stdout = old_stdout
    return out.getvalue()


def is_process_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError, e:
        if e.errno == 3:  # process is dead
            return False
        elif e.errno == 1:  # no permission
            return True
        else:
            raise
    else:
        return True
        


