import socket
import sys
from time import time, ctime, strftime

host = socket.gethostname()

try:
    from scribeclib.client import scribeclient
except ImportError:
    scribeclient = None


def log(category, message):
    timestamp = strftime('%Y-%m-%d %H:%M:%S')
    message = '%s %s %s %s' % (timestamp, host, category, message)
    if scribeclient is not None:
        try:
            scribeclient.send(category, message)
            return
        except Exception:
            pass
    sys.stderr.write(message + '\n')


