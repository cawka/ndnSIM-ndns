
import sys
import time as _time

sys.modules['_time'] = sys.modules['time']
sys.modules['time'] = sys.modules['_simulation_hacks.time_']

import ns.core

def time ():
    return ns.core.Simulator.Now ().ToDouble (ns.core.Time.S)

def localtime (sec = None, sec2 = None):
    if sec2 is not None:
        sec = sec2

    if sec is None:
        sec = time ()

    return _time.localtime (sec)

def asctime(t = None):
    if t is None:
        t = localtime ()

    return _time.asctime (t)

def sleep ():
    raise Exception ("Not allowed...")

def strftime (*kw, **kwargs):
    return _time.strftime (*kw, **kwargs)
