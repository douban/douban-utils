#!/usr/bin/env python
# encoding: utf-8
"""
read and eval object from file
"""

import os

class Error(Exception):
    pass

class InvalidObject(Error):
    pass
    
def read_object(filename):
    try:
        return eval(open(filename).read())
    except ValueError,e:
        raise InvalidObject(e)    

