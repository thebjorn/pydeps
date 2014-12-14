
from ..c import c

def a_foo():
    print 'in afoo, calling c.foo...'
    c.foo()
    return 'returning from afoo'

    

