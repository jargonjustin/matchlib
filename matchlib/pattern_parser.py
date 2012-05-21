import token, tokenize, sys
from cStringIO import StringIO
from matchlib.ast import *

def parse_file (filename):
    inp = None
    try:
        inp = open (filename)
        return parse_handle (inp, filename)
    finally:
        if inp: inp.close ()

def parse_string (source, filename=None):
    return parse_handle (StringIO (source), filename)

def parse_handle (handle, filename=None):
    return parse (lines (handle.readline), filename)

### Magic Numbers ###
LINE, BLOCK, END = 1, 2, 3
MATCH, CASE = 4, 5

INDENTS = [ BLOCK, MATCH, CASE ]

### Parser ###

def parse (lines, filename=None):
    lines = iter(lines)
    try:
        while True:
            line = lines.next ()
            match_expr = parse_match_statement (line)
            if match_expr is None:
                fail_on_keywords (line[1], 'match', 'with')
                yield line
            else:
                yield (MATCH, match_expr)
                while True:
                    line = lines.next ()
                    if line[0] is END:
                        yield line
                        break
                    yield (CASE, parse_case_statement (line))
                    for line in extract_block (parse (lines)):
                        yield line
    except ParseError, err:
        err.filename = filename
        raise

def parse_match_statement (line):
    if line[0] is BLOCK and \
       len (line[1]) > 2 and \
       iskeyword ('match', line[1][0]) and \
       iskeyword ('with', line[1][-3]):
        return line[1][1:-3]

### Case Statement Parser ###

def parse_case_statement (line):
    if line[0] is not BLOCK:
        fail ("expected case statement")
    elif not iskeyword ('case', line[1][0]):
        fail ("expected case statement", line[1][0])
    elif len (line[1]) < 4:
        fail ("empty case statement", line[1][0])
    expr_iter = PeekableIterator (line[1][1:-2])
    patterns = [ parse_case_pattern (expr_iter) ]
    while True:
        try:
            tok = expr_iter.next ()
        except StopIteration:
            return (patterns, None)
        if iskeyword ('if', tok):
            return (patterns, list (expr_iter))
        elif isop (',', tok):
            patterns.append (parse_case_pattern (expr_iter))
        else:
            fail ('illegal token in case statement', tok)

def parse_case_pattern (expr_iter):
    try:
        pat = parse_nonbinding_pattern (expr_iter)
        if iskeyword ('as', expr_iter.peek ()):
            expr_iter.next ()
            ident = expr_iter.next ()
            if ident[0] is not token.NAME:
                fail ('binding pattern must bind to a name', ident)
            return PBind (ident[1], pat)
        else:
            return pat
    except StopIteration:
        fail ('premature end of pattern expression')

def parse_nonbinding_pattern (expr_iter):
    tok = expr_iter.next ()
    lit = parse_literal_token (tok)
    if lit is not None:
        return lit
    elif tok[0] == token.NAME:
        idents = [ tok[1] ]
        while True:
            tok = expr_iter.peek ()
            if isop ('.', tok):
                expr_iter.next ()
                tok = expr_iter.next ()
                if tok[0] is not token.NAME:
                    fail ('illegal identifier in case expression', tok)
                idents.append (tok[1])
            else:
                break
        tok = expr_iter.peek ()
        if isop ('(', tok):
            expr_iter.next ()
            return PExtractor ('.'.join (idents), parse_listlike (expr_iter, parse_case_pattern, ')'))
        elif len (idents) > 1:
            return PSym ('.'.join (idents))
        else:
            return PVar (idents[0])
    elif isop ('[', tok):
        return PList (parse_listlike (expr_iter, parse_case_pattern, ']'))
    elif isop ('(', tok):
        return PTuple (parse_listlike (expr_iter, parse_case_pattern, ')'))
    elif isop ('{', tok):
        return PDict (parse_listlike (expr_iter, parse_dict_entry, '}', allowsplat=False))
    else:
        fail ('illegal case expression', tok)


def parse_dict_entry (expr_iter):
    key_token = expr_iter.next ()
    key_lit = parse_literal_token (key_token)
    if key_lit is None:
        fail ('dictionary key must be a literal', key_token)
    colon_token = expr_iter.next ()
    if not isop (':', colon_token):
        fail ('dictionary entries must contain a colon', colon_token)
    return (key_lit, parse_case_pattern (expr_iter))

def parse_literal_token (tok):
    if tok[0] is token.NUMBER or tok[0] is token.STRING or \
       (tok[0] is token.NAME and tok[1] in ['True', 'False', 'None']):
        return PLit (tok)

def parse_listlike (expr_iter, parser, ending, allowsplat=True):
    parsed, started = list(), False
    while True:
        tok = expr_iter.peek ()
        if isop (ending, tok):
            expr_iter.next ()
            return parsed
        elif started:
            if not isop (',', tok):
                fail ('expected comma or "%s" in sequence' % ending, tok)
            expr_iter.next ()
        if allowsplat and isop ('*', expr_iter.peek ()):
            splat_tok = expr_iter.next ()
            name_tok = expr_iter.next ()
            if name_tok[0] is not token.NAME:
                fail ('expected variable to bind splat', name_tok)
            parsed.append (PSplat (name_tok[1]))
            allowsplat = False
        else:
            parsed.append (parser (expr_iter))
        if not started: started = True

### Parsing to Python Line objects and Back ###

def lines (reader):
    logical = list ()
    for tok in tokenize.generate_tokens (reader):
        if tok[0] is token.DEDENT:
            if logical:
                for line in __break_tokens (logical):
                    yield line
            yield (END, [])
        elif tok[0] not in [ token.INDENT, tokenize.NL, tokenize.COMMENT, token.ENDMARKER ]:
            logical.append (tok)
        if tok[0] is token.NEWLINE:
            block_index = __block_operator_index (logical)
            for line in __break_tokens (logical):
                yield line
            logical = list ()

def __break_tokens (logical):
    block_index = __block_operator_index (logical)
    if block_index is None:
        return [(LINE, logical)]
    elif block_index == len(logical) - 2:
        return [(BLOCK, logical)]
    else:
        return [(BLOCK, logical[:block_index+1] + [logical[-1]]),
                (LINE, logical[block_index+1:]),
                (END, [])]

def __block_operator_index (tokens):
    "Returns the index of the start block operator in the token list"
    nesting, index, ignore1 = 0, 0, False
    while index < len (tokens):
        if tokens[index][0] == token.OP:
            if tokens[index][1] == ':' and ignore1:
                ignore1 = False
            elif tokens[index][1] == '[' or tokens[index][1] == '{':
                nesting += 1
            elif tokens[index][1] == ']' or tokens[index][1] == '}':
                nesting -= 1
            elif tokens[index][1] == ':' and nesting == 0:
                return index
        elif tokens[index][0] == token.NAME and tokens[index][1] == 'lambda':
            ignore1 = True
        index += 1

def unlines (lines, spaces=4):
    indent = 0
    for (linetype, tokens) in lines:
        if tokens:
            tokens = [ token[:2] for token in tokens ] # Work around http://bugs.python.org/issue12691
            yield ' ' * indent * spaces + tokenize.untokenize (tokens)
        if linetype in INDENTS:
            indent += 1
        elif linetype is END:
            indent -= 1

def extract_block (lines, indent=1):
    while indent > 0:
        line = lines.next ()
        if line[0] in INDENTS:
            indent += 1
        elif line[0] is END:
            indent -= 1
        yield line

### Token Processing ###

def iskeyword (keyword, tok):
    return tok is not None and tok[0] is token.NAME and tok[1] == keyword

def isop (op, tok):
    return tok is not None and tok[0] is token.OP and tok[1] == op

class PeekableIterator(object):
    def __init__(self, iterator):
        self.iterator = iter(iterator)
        self.peeked = None
    
    def __iter__(self):
        return self
    
    def next(self):
        if self.peeked is None:
            return self.iterator.next()
        else:
            previously_peeked = self.peeked[0]
            self.peeked = None
            return previously_peeked
    
    def peek(self):
        if self.peeked is None:
            try:
                self.peeked = (self.iterator.next(),)
            except StopIteration:
                return None
        return self.peeked[0]
    

### Error Handling ###

class ParseError (Exception):
    "Signals an error occured during parsing"
    def __init__(self, message, tok=None, filename=None):
        super (ParseError, self).__init__ (message)
        self.filename = filename
        if tok is not None:
            (self.lineno, self.offset) = tok[2]
            self.token = tok
        else:
            self.lineno = self.offset = self.token = None

def fail (reason, tok=None):
    raise ParseError(reason, tok)

def fail_on_keywords (tokens, *keywords):
    "Fails upon encountering any of the specified keywords in the tokens"
    for tok in tokens:
        for keyword in keywords:
            if iskeyword (keyword, tok):
                fail ('illegal use of keyword "%s"' % keyword, tok)

def print_failure (err, dev=sys.stderr):
    if err.token is not None:
        if err.filename and err.lineno:
            print >>dev, '  File "%s", line %d' % (err.filename, err.lineno)
        elif err.lineno:
            print >>dev, '  Line %d' % err.lineno
        if err.token and len (err.token) > 4:
            print >>dev, err.token[4]
            print >>dev, ' ' * err.offset + '^'
    print >>dev, '%s: %s' % (err.__class__.__name__, err.message)

if __name__ == '__main__':
    from cStringIO import StringIO
    
    if len (sys.argv) != 2:
        print >>sys.stderr, 'usage: python %s filename' % sys.argv[0]
        sys.exit (1)
    
    def unparse (lines):
        for line in lines:
            if line[0] is MATCH:
                yield (BLOCK, [(token.NAME, 'match')] + line[1] + [(token.NAME, 'with'), (token.OP, ':'), (token.NEWLINE, '\n')])
            elif line[0] is CASE:
                predicates = list (tokenize.generate_tokens (StringIO (repr (line[1][0])).readline))[:-1]
                if line[1][1] is None:
                    yield (BLOCK, predicates + [(token.OP, ':'), (token.NEWLINE, '\n')])
                else:
                    yield (BLOCK, predicates + [(token.NAME, 'if')] + line[1][1] + [(token.OP, ':'), (token.NEWLINE, '\n')])
            else:
                yield line
    
    buf = StringIO()
    try:
        for chunk in unlines (unparse (parse_file (sys.argv[1]))):
            buf.write (chunk)
        print buf.getvalue ()
    except ParseError, err:
        print_failure (err)
