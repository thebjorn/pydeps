
from ab.c import cmodule

def a_foo():
    print 'in afoo, calling c.foo...'
    cmodule.foo()
    return 'returning from afoo'

    

