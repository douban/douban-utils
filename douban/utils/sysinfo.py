#!/usr/bin/env python
# encoding: UTF-8

import gc
import os
import platform
import pwd
import sys

def get_sysinfo():
    return {
            'pid': get_pid(),
            'mem': get_memory(),
            'gcobj': get_biggest_gc_objects(),
            }

def get_pid():
    return os.getpid()

def get_memory(pid=None):
    vsz, rss = 0, 0
    if platform.system() == 'Linux':
        f = open('/proc/%d/status' % (pid or os.getpid()))
        for line in f:
            if line.startswith('VmSize:'):
                vsz = int(line.split()[1])
            elif line.startswith('VmRSS:'):
                rss = int(line.split()[1])
        f.close()
    return vsz, rss

def get_login(pid=None):
    '''get login name when can not get USER or LOGNAME from os.environ'''
    try:
        login_name = os.getlogin()
    except:
        login_name = ''
    if login_name:
        return login_name

    if platform.system() == 'Linux':
        f = open('/proc/%d/status' % (pid or os.getpid()))
        uid_line = [s for s in f.readlines() if s.startswith('Uid:')]
        f.close()
        if uid_line:
            try:
                uid = int(uid_line[0].split()[1])
                login_name = pwd.getpwuid(uid)[0]
            except:
                pass
    return login_name

def get_biggest_gc_objects(count=20):
    objects = gc.get_objects()
    lists = []
    dicts = []
    for i in objects:
        if isinstance(i, list):
            lists.append(i)
        elif isinstance(i, dict):
            dicts.append(i)
    lists.sort(cmp=lambda x, y: cmp(len(x), len(y)), reverse=True)
    dicts.sort(cmp=lambda x, y: cmp(len(x), len(y)), reverse=True)
    return lists[:count], dicts[:count]

