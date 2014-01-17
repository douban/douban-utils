import hotshot, hotshot.stats
from cStringIO import StringIO
from os import getpid

PROFILE_LIMIT = 60

PROFILE_LOG_FILENAME_PATTERN = '/tmp/profile-%s.prof'

def start_profile(filename=None):
    if filename is None:
        filename = PROFILE_LOG_FILENAME_PATTERN % getpid()
    prof = hotshot.Profile(filename)
    return prof

def load_stats(filename):
    stats = hotshot.stats.load(filename)
    return stats

def format_stats(stats, strip_dirs=False, sort='time'):
    if strip_dirs:
        stats.strip_dirs()
    stats.sort_stats(sort, 'calls')
    so = StringIO()
    stats.stream = so
    stats.print_stats(PROFILE_LIMIT)
    stats.print_callers(PROFILE_LIMIT)
    return so.getvalue()



