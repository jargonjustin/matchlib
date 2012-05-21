import thread, token
import matchlib.pattern_parser as parser

class CodeGenerator (object):
    def __init__ (self, target=None):
        if target is None: target = list ()
        self.target = target
        self.indent = 0
    
    ### Emitting ###
    
    def emit (self, line):
        self.target.append (line)
    
    def inline (self, lines):
        self.target.extend (lines)
    
    ### Lines ###
    
    def line (self, tokens):
        self.emit ((parser.LINE, tokens + [(token.NEWLINE, '\n')]))
    
    def block (self, tokens):
        self.emit ((parser.BLOCK, tokens + [(token.OP, ':'), (token.NEWLINE, '\n')]))
        self.indent += 1
    
    def dedent (self, amount=1):
        for _ in range(amount):
            self.emit ((parser.END, []))
        self.indent -= amount
    
    ### Statements ###
    
    def Def (self, name, *params):
        self.block (Id ('def') + Call (name, *params))
    
    def Return (self, value):
        self.line (Id ('return') + value)
    
    def Raise (self, *args):
        self.line (Id ('raise') + sepBy (args, Op (', ')))
    
    def If (self, condition):
        self.block (Id('if') + condition)
    
    def ElIf (self, condition):
        self.block (Id('elif') + condition)
    
    def Assign (self, lhs, rhs):
        self.line (lhs + Op('=') + rhs)

### Token Generation ###

# Use a lock for thread-safety
__id_lock = thread.allocate_lock ()
__id_count = 0
def UniqueName ():
    global __id_count, __id_lock
    __id_lock.acquire ()
    __id_count += 1
    ident = '__matchlib_id%d' % __id_count
    __id_lock.release ()
    return ident

def lift (value):
    if isinstance (value, int) or isinstance (value, float):
        return [(token.NUMBER, str (value))]
    elif value is None or value is True or value is False:
        return [(token.NAME, repr (value))]
    elif isinstance (value, str):
        return [(token.STRING, repr (value))]
    else:
        raise TypeError, 'unable to lift %s as a token' % repr (value)

def sepBy (exps, seperator):
    tokens = list ()
    for i, exp in enumerate (exps):
        if i > 0: tokens.extend (seperator)
        tokens.extend (exp) 
    return tokens

def Token (tok): return [tok]

def Op (op): return [(token.OP, op)]
def Id (name): return [(token.NAME, name)]

def Eq (lhs, rhs): return lhs + Op ('==') + rhs
def Gt (lhs, rhs): return lhs + Op ('>') + rhs
def In (lhs, rhs): return lhs + Id ('in') + rhs
def Method (obj, name): return obj + Op ('.') + Id (name)

def Is (lhs, rhs): return lhs + Id ('is') + rhs
def IsNot (lhs, rhs): return lhs + [(token.NAME, 'is'), (token.NAME, 'not')] + rhs

def Index (obj, index): return obj + Op ('[') + index + Op (']')
def Slice (obj, left=None, right=None):
    if left is None: left = []
    if right is None: right = []
    return obj + Op ('[') + left + Op (':') + right + Op (']')

def And (*exps): return sepBy (exps, Id ('and'))
def Tuple (*exps): return Op('(') + sepBy (exps, Op (',')) + Op (',') + Op(')')
def Call (func, *args): return func + Op ('(') + sepBy (args, Op (',')) + Op (')')

