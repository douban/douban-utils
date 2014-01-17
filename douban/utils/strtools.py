#!/usr/bin/env python
# encoding: utf-8
"""
string.py

string utility
"""

import re
import datetime

def trunc_utf8(string, num, etc="..."):
    """truncate a utf-8 string, show as num chars.
    arg: string, a utf-8 encoding string; num, look like num chars
    return: a utf-8 string
    """
    gb = string.decode("utf8", "ignore").encode("gb18030", "ignore")
    if num >= len(gb):
        return string
    ret = gb[:num].decode("gb18030", "ignore").encode("utf8")
    if etc:
        ret += etc
    return ret
    
def trunc_short(s, max_len=210, etc="..."):
    s = str(s).decode("utf-8")
    if len(s)>= max_len:
        s = s[:max_len] + str(etc)
    return s.encode("utf-8")
    
def utf8_length(string):
    return string and len(string.decode("utf8", "ignore").encode("gb18030", "ignore")) or 0   
    
def trunc_utf8_by_char(string, num, etc="..."):
    unistr = string.decode("utf8","ignore")
    if num>= len(unistr) :
        return string
    str = unistr[:num].encode("utf8")
    if etc :
        str += etc
    return str  
    
def js_quote(js):
    return js.replace('\\', r'\\').replace('\r', r'\r') \
           .replace('\n', r'\n').replace("'", r"\'").replace('"', r'\"')
           
EMAILRE = re.compile(r'^[_\.0-9a-zA-Z+-]+@([0-9a-zA-Z]+[0-9a-zA-Z-]*\.)+[a-zA-Z]{2,4}$')
def is_valid_email(email):
    if len(email) >= 6:
        return EMAILRE.match(email) != None
    return False
    
def format_rfc822_date(dt, localtime=True, cookie_format=False):
    if localtime:
        dt = dt - datetime.timedelta(hours=8)
    fmt = "%s, %02d %s %04d %02d:%02d:%02d GMT"
    if cookie_format:
        fmt = "%s, %02d-%s-%04d %02d:%02d:%02d GMT"

    # dt.strftime('%a, %d-%b-%Y %H:%M:%S GMT')
    return fmt % (
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()],
            dt.day,
            ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month-1],
            dt.year, dt.hour, dt.minute, dt.second)

def format_cookie_date(dt, localtime=True):
    return format_rfc822_date(dt, localtime=True, cookie_format=True)
    
def is_ascii_string(text):
    if not isinstance(text, basestring):
        return False
    replace = [c for c in text if not (' '<=c<='~')]
    if replace:
        return False
    else:
        return True