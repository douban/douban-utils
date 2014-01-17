#!/usr/bin/env python
# encoding: utf-8

import os.path
import imp
from .read_object import read_object

config_dir = '/etc/douban'

PYTHON_OBJECT = 0
PYTHON_MODULE = 1

def read_config(env, module, format=PYTHON_OBJECT):
    if format == PYTHON_OBJECT:
        config_file = os.path.join(config_dir, module, env)
        config_obj = read_object(config_file)
    elif format == PYTHON_MODULE:
        path = os.path.join(config_dir, module)
        config_obj = read_object_from_python_module(path, env)
    else:
        raise NotImplementedError()
    return config_obj    
    

def read_object_from_python_module(path, name):
    config_obj = {}
    try:
        mod = imp.load_module(name, *imp.find_module(name, [path,]))
        for (k,v) in mod.__dict__.items():
            if not k.startswith('_'):
                config_obj[k] = v
    except ImportError, e:
        if e.args[0].startswith('No module named %s'%name):
            pass
        else:
            # the ImportError is raised inside python module to be imported
            raise
    return config_obj        


    
