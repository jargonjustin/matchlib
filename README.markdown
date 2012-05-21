## Python Pattern Matching Preprocessor

Matchlib is a Python pattern matching preprocessor that adds a ML-style pattern
matching syntax to Python inspired by Emir, Odersky and Williams' _[Matching
Objects with Patterns (PDF)][matching]_. The `mpyc` compiler converts files
using the `match` syntax to regular python source files.

### Basic Pattern Matching

The pattern matching syntax acts as a case statement, progressively comparing
the result of an expression with various patterns. For example:

    match expr with:
        case "testing":
            return "test string"
        case x if isinstance(x, str):
            return "string"
        case [1, 2, 3]:
            return "int list"
        case (1, x):
            return str(x)
        case { "foo": bar }:
            return "foo: %s" % bar

A match statement must include at least one case statement which tests a
pattern against the expression value. The pattern may consist of Python
literals (like strings and numbers), tuples, lists or dictionaries. Patterns
may include variables which will capture values from within a pattern. The
special variable `_` will match any value without introducing a variable
binding.

In addition to pattern matching, individual `case` statements may have a
trailing `if` clause which will be tested if the rest of the pattern matches.
This is useful for expressing predicates beyond those that may be captured
structurally.

### Extractor Objects

Pattern matching behavior may be customized for types by implementing a
`__match__` static method. Such types are called _extractor objects_ and will
be passed a value to match against. If the value matches, they should return a
tuple (which may be empty) of the extracted contents or `None` if they do not
match the value.

The `matchlib.extractors` package contains some utilities to assist in writing
extractor objects and simple structural types. The `@extractor` decorator may
be used to convert a function into an extractor object as in:

    @extractor
    def Twice(x):
        if isinstance(x, int):
            return (x/2,)

Which may then be used as:

    match 21 with:
        case Twice(x): print x # prints "42"

The resulting tuple will be matched against the pattern's arguments

    @extractor
    def seq(obj):
        try:
            return tuple ([ elm for elm in iter (obj) ])
        except TypeError:
            return None
    
    match value with:
        case seq (1, 1, 2, 3, 5, *rest):
            return 'fibonacci'

[matching] http://lampwww.epfl.ch/~emir/written/MatchingObjectsWithPatterns-TR.pdf
