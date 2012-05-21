import new

def extractor(func):
    "Decorator to convert a function into an extractor object"
    return new.classobj(func.__name__, (object,), {
        '__match__': staticmethod(func)
    })

def caseclass(*attrs):
    """Creates a caseclass useful as an algebraic data type
    
    A caseclass handles the common case of a class that is defined primarily by
    it's structure (that is, the attribute's it contains as data.)  Abstract
    syntax trees and simple algebraic data-types are common examples.  Caseclasses
    contain a constructor taking it's arguments in the order they were given,
    methods for matching, equality comparison, and displaying themselves.
    
    class Num(caseclass('value')):
        def __init__(self, value):
            self.value = int(value)
    
    Num(3) == Num(3)    # => True
    repr(Num('5'))      # => Num(5)
    
    """
    return new.classobj('caseclass', (__CaseClass,), {
        '__slots__': attrs
    })

def matchattrs(*attrs):
    """Generates a classmethod to be used as __match__ in an extractor.
    
    The generated method checks that the object is an instance of the class to
    which the __match__ method is attached.  It then extracts the listed
    listed attributes.
    
    class Add(object):
        def __init__(self, lhs, rhs):
            self.lhs, self.rhs = lhs, rhs
        __match__ = matchattrs('lhs', 'rhs')
    
    match Add(1, 2) with:
        case Add(x, y): print x, y
    
    """
    def __match__(cls, obj):
        if isinstance(obj, cls):
            return tuple([ getattr(obj, attr) for attr in attrs ])
    return classmethod(__match__)

class __CaseClass(object):
    __slots__ = ()
    
    def __init__(self, *args):
        if len(args) != len(self.__slots__):
            raise TypeError, "%s.__init__() takes exactly %d arguments (%d given)" % (self.__class__.__name__, len(self.__slots__), len(args))
        for (attr, value) in zip(self.__slots__, args):
            setattr(self, attr, value)
    
    @classmethod
    def __match__(cls, obj):
        if isinstance(obj, cls):
            return tuple([ getattr(obj, attr) for attr in cls.__slots__ ])
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        for attr in self.__slots__:
            if not getattr(self, attr) == getattr(other, attr):
                return False
        return True
    
    def __ne__(self, other):
        return not self == other
    
    def __hash__(self):
        hashed = []
        for attr in self.__slots__:
            try:
                hashed.append(hash(getattr(self, attr)))
            except TypeError:
                continue
        return hash(tuple(hashed))
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join([ repr(getattr(self, attr)) for attr in self.__slots__ ]))
    

