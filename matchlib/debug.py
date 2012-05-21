import tokenize, re
import parser as pyparser

import matchlib.pattern_parser as parser

### Anotations ###
# Adds annotation comments to the lines containing debugging information
# sufficient to reconstruct the original file and line information for
# debugging in tracebacks

def annotate (lines, filename=None):
    for line in lines:
        if line[1]:
            (generated, startLine, endLine) = line_info (line[1])
            if startLine is not None:
                comment = 'line %s' % startLine
                if endLine != startLine:
                    comment += '-%s' % endLine
                if filename is not None:
                    comment += ' (%s)' % filename
                if generated:
                    comment += ' (generated)'
                yield (line[0], comment_line (line[1], comment))
                continue
        yield line

def line_info (tokens):
    generated, startLine, endLine = False, None, None
    for token in tokens:
        if len (token) > 2:
            if startLine is None or startLine > token[2][0]:
                startLine = token[2][0]
            if endLine is None or endLine < token[2][0]:
                endLine = token[2][0]
        else:
            generated = True
    return (generated, startLine, endLine)

def comment_line (tokens, comment):
    comment = (tokenize.COMMENT, ' # %s' % comment)
    tokens = list (tokens)
    index = 0
    while tokens[index - 1][0] in [ tokenize.NEWLINE, tokenize.NL ]:
        index -= 1
    if index is 0:
        tokens.append (comment)
    else:
        tokens.insert (index, comment)
    return tokens

### Traceback Rewritting ###
# Rewrites an exception traceback raised at runtime, using debugging annotations
# from compiled .mpy files

__debugging_comment_re = re.compile (r'''
    ^(.*)\#\s+                  # source code and comment begin
    line\s+(\d+)(-\d+)?         # original line(s)
    (:?\s+\(([^)]+)\))?         # original filename
    (:?\s+(\(generated\)))?     # indicates partially generated source
''', re.VERBOSE)
def rewrite_frame (frame):
    (filename, lineno, funcname, text) = frame
    if funcname.startswith ('__matchlib_id'):
        return None
    else:
        annotation = __debugging_comment_re.match (text)
        if annotation is not None:
            return (annotation.group (5), int (annotation.group (2)), funcname, annotation.group (1))
        else:
            return frame

def rewrite_extracted_tb (frames):
    return filter(None, map(rewrite_frame, frames))

def rewrite_syntactic_frame (frame):
    (filename, lineno, offset, text) = frame
    annotation = __debugging_comment_re.match (text)
    if annotation is not None:
        return (annotation.group (5), int (annotation.group (2)), offset, annotation.group (1))
    else:
        return frame

def excepthook(exctype, exc, tb):
    pass

### Static Syntax Checking ###
# Checks to ensure the compiled output is syntactically valid

def check_syntax (source):
    try:
        pyparser.suite (source)
    except IndentationError, err:
        raise IndentationError (err.msg, rewrite_syntactic_frame (err.args[1]))
    except SyntaxError, err:
        raise SyntaxError (err.msg, rewrite_syntactic_frame (err.args[1]))

