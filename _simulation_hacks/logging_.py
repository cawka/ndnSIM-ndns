
import sys

sys.modules['logging'] = sys.modules['_simulation_hacks.logging_']

DEBUG = 0
INFO = 0
WARNING = 0
ERROR = 0
CRITICAL = 0
NOTSET = 0

class Logger (object):
    level = None
    
    def setLevel (self, *kw, **kwargs):
        pass

    def debug (self, *kw, **kwargs):
        pass

    def info (self, *kw, **kwargs):
        pass

    def warning (self, *kw, **kwargs):
        pass

    def error (self, *kw, **kwargs):
        pass

    def critical (self, *kw, **kwargs):
        pass

    def addHandler (self, *kw, **kwargs):
        pass
    
    def isEnabledFor (self, *kw, **kwargs):
        return False

class StreamHandler (object):
    def __init__ (self, *kw, **kwargs):
        pass

    def setFormatter (self, *kw, **kwargs):
        pass

class Formatter (object):
    def __init__ (self, *kw, **kwargs):
        pass
    
nologger = Logger ()
    
def getLogger (*kw, **kwargs):
    return nologger
    
def setLevel (*kw, **kwargs):
    pass

def debug (*kw, **kwargs):
    pass

def info (*kw, **kwargs):
    pass

def warning (*kw, **kwargs):
    pass

def error (*kw, **kwargs):
    pass

def critical (*kw, **kwargs):
    pass
