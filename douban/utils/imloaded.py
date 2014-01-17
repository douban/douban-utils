# encoding: UTF-8

"""保持打开一个特定文件，以便使外部工具可以得知哪些进程加载了指定模块"""

import os
from warnings import warn

def imloaded(name):
    """Keep /tmp/imloaded-{name} open.

    So that executing `lsof /tmp/imloaded-{name}` could give out all processes
    that called this function.

    """
    filepath = '/tmp/imloaded-{name}'.format(name=name)
    old_umask = os.umask(0)
    try:
        os.open(filepath, os.O_CREAT)
    except (IOError, OSError), e:
        warn("open %s failed: %s" % (filepath, e), RuntimeWarning)
    finally:
        os.umask(old_umask)
