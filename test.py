from __future__ import with_statement
from popen2 import popen3
# Match-Python Test Harness
#   For each source file in tests/, pipes it through the compiler and into
#   a python interpreter in a seperate process, and compares standard output
#   to an expected result.
#

import difflib, site, os, glob, sys, traceback

ROOTPATH = os.path.abspath(os.path.dirname(__file__))
TESTPATH = os.path.join(ROOTPATH, 'tests')

site.addsitedir(ROOTPATH)
import matchlib

def run_mpython(filename):
    with open(filename) as source_file:
        (stdout, stdin, stderr) = popen3('python -')
        try:
            matchlib.compiler.compile_piped(source_file, stdin, filename)
            stdin.close()
        except Exception, err:
            return (False, err)
        errors = stderr.read()
        if errors:
            return (False, errors)
        return (True, stdout.read())

def run_tests(tests, out=None):
    if out is None:
        out = sys.stdout
    
    failures = list()
    for source_filename, expected_filename in tests:
        (success, details) = run_mpython(source_filename)
        if not success:
            out.write("E")
            failures.append((source_filename, details))
        else:
            with open(expected_filename) as expected_file:
                expected = expected_file.read()
                if details != expected:
                    out.write("F")
                    failures.append((source_filename, (expected, details)))
                else:
                    out.write(".")
        out.flush()
    out.write("\n")
    
    if failures:
        for filename, details in failures:
            if isinstance(details, tuple):
                out.write("\nFAILURE: %s\n" % filename)
            elif isinstance(details, Exception):
                out.write("\nERROR: %s\n" % filename)
                traceback.print_exception (details.__class__, details, tb=None, file=out)
            else:
                out.write("\nERROR: %s\n" % filename)
                out.write(details)
        return 1
    else:
        return 0

def main(argv=None):
    global TESTPATH
    
    if argv is None:
        argv = sys.argv
    
    if len(argv) > 1:
        return run_tests([
            (os.path.join(TESTPATH,test)+'.mpy', os.path.join(TESTPATH, test)+'.out')
            for test in argv[1:]
        ])
    else:
        return run_tests([
            (source_filename, os.path.splitext(source_filename)[0]+'.out')
            for source_filename in glob.glob(os.path.join(TESTPATH, '*.mpy'))
        ])

if __name__ == '__main__':
    sys.exit(main(sys.argv))
