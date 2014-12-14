
from a import amodule

def b_foo():
    print 'bfoo', amodule.a_foo()

    
if __name__ == "__main__":
    b_foo()
    
