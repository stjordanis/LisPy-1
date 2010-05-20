#! /usr/bin/env python

"""
interpreter.py
Author: Kemal Eren

A minimal implementation of a LISP interpreter.

"""

import re
import sys
import copy

#some useful regexes:
ATOM_regex = re.compile("^[0-9a-zA-Z%*\-\+/=<>]+$")
INT_regex = re.compile("^-?[0-9]+$")
WHITESPACE_regex = re.compile("^\s+$")

#TODO: experiment with my own tail-recursion stack, to avoid recursion depth of python

class LispException(Exception):
    pass

primitives_string = "T NIL CAR CDR CONS ATOM EQ NULL INT PLUS MINUS TIMES QUOTIENT REMAINDER LESS GREATER COND QUOTE DEFUN + - % * / = < >"
primitives = [i for i in primitives_string.split()]

help_string = "Available primitives:\n{0}\n\nFurther help not currently available.".format(primitives_string)

class SExp(object):
    def __init__(self, left, right=None):
        """Create an S-expression (left . right). If 'right' is not provided,
        'left' should be atomic.

        """
        if right is None:
            if not isinstance(left, str):
                raise LispException("trying to create an S-expression from {0}".format(str(left)))
            if ATOM_regex.match(left) is None:
                raise LispException("not a valid atomic S-expression: {0}".format(left))
            self.val = left.upper()
        else:
            if not isinstance(left, SExp) or not isinstance(right, SExp):
                raise LispException("not an S-expression")
            self.val = (left, right)
        self.bool_sexps = {True: "T", False: "NIL"}


    def atom(self, sexp=False):
        result = type(self.val) == type("")
        if sexp: return SExp(self.bool_sexps[result])
        return result

    def __eq__(self, other):
        if not self.atom(): raise LispException("not an atomic S-expression: {0}".format(self))
        if not other.atom(): raise LispException("not an atomic S-expression: {0}".format(other))
        return self.val == other.val

    def __ne__(self, other):
        return not self.__eq__(other)

    def eq(self, other, sexp=False):
        result = False
        if self.__eq__(other): result = True
        if sexp: return SExp(self.bool_sexps[result])
        return result

    def null(self, sexp=False):
        result = False
        if self.atom():
            if self.val == "NIL": result = True
        if sexp: return SExp(self.bool_sexps[result])
        return result

    def int(self, sexp=False):
        result = False
        if self.atom():
            if INT_regex.match(self.val) is not None:
                result = True
        if sexp: return SExp(self.bool_sexps[result])
        return result

    def car(self):
        if self.atom(): raise LispException("cannot call CAR on atomic s-expression: {0}".format(self))
        return self.val[0]

    def cdr(self):
        if self.atom():
            raise LispException("cannot call CDR on atomic s-expression: {0}".format(self))
        return self.val[1]

    def _arithmetic(self, other, op):
        if not self.int(): raise LispException("not an int: {0}".format(self))
        if not other.int(): raise LispException("not an int: {0}".format(other))
        return SExp(str(op(int(self.val),
                           int(other.val))))

    def plus(self, other):
        return self._arithmetic(other, lambda a,b: a+b)

    def minus(self, other):
        return self._arithmetic(other, lambda a,b: a-b)

    def times(self, other):
        return self._arithmetic(other, lambda a,b: a*b)

    def quotient(self, other):
        return self._arithmetic(other, lambda a,b: a/b)

    def remainder(self, other):
        return self._arithmetic(other, lambda a,b: a%b)

    def _compare(self, other, op):
        if not self.int(): raise LispException("not an int: {0}".format(self))
        if not other.int(): raise LispException("not an int: {0}".format(other))
        if op(int(self.val), int(other.val)): return SExp("T")
        return SExp("NIL")

    def greater(self, other):
        return self._compare(other, lambda a,b: a>b)

    def less(self, other):
        return self._compare(other, lambda a,b: a<b)

    def is_list(self):
        if self.null(): return True
        if self.atom(): return False
        if self.val[1].is_list(): return True
        return False

    def length(self):
        if not self.is_list():
            raise LispException("calling length on non-list {0}".format(self))
        if self.null(): return 0
        return 1+self.val[1].length()

    def non_int_atom(self):
        if not self.atom(): return False
        if INT_regex.match(self.val) is not None: return False
        return True

    def _repr_helper(self):
        if self.null():
            return ""
        return " {0}{1}".format(self.val[0], self.val[1]._repr_helper())

    def __repr__(self):
        if self.atom():
            return self.val
        else:
            if self.is_list():
                return "({0}{1})".format(self.val[0], self.val[1]._repr_helper())
            return "({0} . {1})".format(self.val[0], self.val[1])

    def copy(self, other):
        self.val = other.val

#basic S-expressions
#TODO: do this using the 'primitives' string above!!! Also integrate into a help system.
T = (SExp("T"),)
NIL = (SExp("NIL"),)

CAR = (SExp("CAR"), SExp("FIRST"),)
CDR = (SExp("CDR"), SExp("REST"),)
CONS = (SExp("CONS"),)
ATOM = (SExp("ATOM"),)
NULL = (SExp("NULL"),)
EQ = (SExp("EQ"), SExp("="),)
INT = (SExp("INT"),)
PLUS = (SExp("PLUS"), SExp("+"),)
MINUS = (SExp("MINUS"), SExp("-"),)
TIMES = (SExp("TIMES"), SExp("*"),)
QUOTIENT = (SExp("QUOTIENT"), SExp("/"),)
REMAINDER = (SExp("REMAINDER"), SExp("%"),)
LESS = (SExp("LESS"), SExp("<"),)
GREATER = (SExp("GREATER"), SExp(">"),)
QUIT = (SExp("QUIT"),)
HELP = (SExp("HELP"),)
QUOTE = (SExp("QUOTE"),)
COND = (SExp("COND"),)
DEFUN = (SExp("DEFUN"),)

primitive_sexps = [SExp(i) for i in primitives]


def lex(myinput):
    """A generator for tokens in myinput"""
    my_atom = ""
    for char in myinput:
        if not my_atom == "":
            if ATOM_regex.match(char):
                my_atom += char
                continue
            else:
                yield my_atom
                my_atom = ""
        if WHITESPACE_regex.match(char):
            continue
        elif char in "().'": yield char
        elif ATOM_regex.match(char):
            my_atom += char
        else:
            raise LispException("bad token: {0}".format(char))
    if not my_atom == "":
        yield my_atom


def get_tokens(myinput):
    return [i for i in lex(myinput)]


def balanced(tokens):
    count = 0
    for token in tokens:
        if token == "(": count += 1
        if token == ")": count -= 1
        if count < 0: raise LispException("imbalanced parens")
    return count == 0


def process_list_tokens(tokens):
    """Parses tokens in list form into an s-expression"""
    if len(tokens) == 0: raise LispException("parse error: missing tokens")
    if tokens[0] == ")":
        tokens.pop(0)
        return SExp("NIL")
    first = process_tokens(tokens)
    if len(tokens) == 0: raise LispException("parse error: missing tokens")
    if tokens[0] == ".": raise LispException("mixed notation not supported")
    second = process_list_tokens(tokens)
    return SExp(first, second)


def process_tokens(tokens):
    """Parses tokens into an s-expression"""
    if len(tokens) == 0: raise LispException("parse error: missing tokens")
    if ATOM_regex.match(tokens[0]):
        sexp = SExp(tokens.pop(0))
        return sexp
    if tokens[0] == "(" and tokens[1] == ")":
        tokens.pop(0)
        tokens.pop(0)
        return SExp("NIL")
    #recursively continue
    if not tokens.pop(0) == "(": raise LispException("missing open parentheses")
    first = process_tokens(tokens)
    if len(tokens) == 0: raise LispException("parse error: missing tokens")
    second = []
    if tokens[0] == ".":
        tokens.pop(0)
        second = process_tokens(tokens)
        if len(tokens) == 0: raise LispException("parse error: missing tokens")
        if not tokens.pop(0) == ")": raise LispException("missing close parentheses")
    else:
        second = process_list_tokens(tokens)
    sexp  = SExp(first, second)
    return sexp


def parse(tokens):
    """Parses tokens and returns an s-expression"""
    sexp = process_tokens(tokens)
    return sexp


def parse_gen(tokens):
    """A generator that parses tokens and returns as many s-expressions as possible"""
    while (len(tokens) > 0):
        yield process_tokens(tokens)


def in_pairlist(exp, pairlist):
    if pairlist.null(): return False
    if pairlist.car().atom(): raise LispException("a-list or d-list in wrong format")
    if exp == pairlist.car().car(): return True
    return in_pairlist(exp, pairlist.cdr())


def getval(exp, from_list):
    if from_list.null(): return SExp("NIL")
    if from_list.car().atom(): raise LispException("a-list or d-list in wrong format")
    if exp == from_list.car().car(): return from_list.car().cdr()
    return getval(exp, from_list.cdr())


def addpairs(params, cur_args, to_list):
    if params.null() and cur_args.null(): return to_list
    if params.atom() or cur_args.atom(): raise LispException("pairs cannot be atoms")
    pair = SExp(params.car(), cur_args.car())
    return addpairs(params.cdr(), cur_args.cdr(), SExp(pair, to_list))


def check_args(f, sexp, exp_len):
    real_len = sexp.length()
    if not real_len == exp_len:
        raise LispException("{0} expects {1} argument; got {2}".format(f, exp_len, real_len))
    

def myeval(exp, aList, dList):
    if exp.atom():
        if exp.int(): return exp
        if exp in T: return SExp("T")
        if exp.null(): return SExp("NIL")
        if in_pairlist(exp, aList): return getval(exp, aList)
        raise LispException("unbound variable: {0}".format(exp))
    if exp.car().atom():
        if not exp.car().non_int_atom: raise LispException("'{0}' is not a valid function name or special form".format(exp.car()))
        #cdar because cdr only would give (quote 5) evaluating to (5), not 5. only takes one argument.
        if exp.car() in QUOTE:
            check_args(exp.car(), exp.cdr(), 1)
            return exp.cdr().car() 
        if exp.car() in COND: return evcond(exp.cdr(), aList, dList)
        if exp.car() in DEFUN:
            f = exp.cdr().car()
            if not f.non_int_atom(): raise LispException("'{0}' is not a valid function name".format(f))
            if f in primitive_sexps: raise LispException("cannot redefine primitive '{0}'".format(f))
            args = exp.cdr().cdr().car()
            body = exp.cdr().cdr().cdr().car()
            check_args(f, exp.cdr(), 3)
            return defun(f, args, body, dList)
        return my_apply(exp.car(), evlis(exp.cdr(), aList, dList), aList, dList)
    raise LispException("eval called with invalid expression")


def evlis(targetlist, aList, dList):
    if targetlist.null(): return SExp("NIL")
    return SExp(myeval(targetlist.car(), aList, dList),
                evlis(targetlist.cdr(), aList, dList))


def my_apply(f, x, aList, dList):
    """
    f: a special form, primitive function, or a function in the dlist.
    x: a list of function arguments.
    aList: a list of (variable . binding) pairs.
    dList: a list of (fname . (arglist . body)) pairs.

    """
    if not f.atom(): raise LispException("error: cannot call non-atom {0} as a function".format(f))
    #TODO: integrate the check_args call with the other primitives definitions + help.
    if f in CAR:
        check_args(f, x, 1)
        return x.car().car() #caar, because only have one argument: a list
    if f in CDR:
        check_args(f, x, 1)
        return x.car().cdr() #cadr
    if f in CONS:
        check_args(f, x, 2)
        return SExp(x.car(), x.cdr()) #two arguments
    if f in ATOM:
        check_args(f, x, 1)
        return x.car().atom(sexp=True)
    if f in NULL:
        check_args(f, x, 1)
        return x.car().null(sexp=True)
    if f in EQ:
        check_args(f, x, 2)
        return x.car().eq(x.cdr().car(), sexp=True)

    if f in INT:
        check_args(f, x, 1)
        return x.car().int(sexp=True)
    if f in PLUS:
        check_args(f, x, 2)
        return x.car().plus(x.cdr().car())
    if f in MINUS:
        check_args(f, x, 2)
        return x.car().minus(x.cdr().car())
    if f in TIMES:
        check_args(f, x, 2)
        return x.car().times(x.cdr().car())
    if f in QUOTIENT:
        check_args(f, x, 2)
        return x.car().quotient(x.cdr().car())
    if f in REMAINDER:
        check_args(f, x, 2)
        return x.car().remainder(x.cdr().car())
    if f in LESS:
        check_args(f, x, 2)
        return x.car().less(x.cdr().car())
    if f in GREATER:
        check_args(f, x, 2)
        return x.car().greater(x.cdr().car())
    if f in HELP:
        check_args(f, x, 0)
        print help_string
        return SExp("T")
    if f in QUIT:
        check_args(f, x, 0)
        exit()
    if not in_pairlist(f, dList): raise LispException("function {0} not found".format(f))
    params = getval(f, dList).car()
    check_args(f, params, x.length())
    return myeval(getval(f,dList).cdr(), addpairs(params, x, aList), dList)


def defun(f, args, body, dList):
    new_dList = SExp(SExp(f, SExp(args, body)), copy.copy(dList))
    dList.copy(new_dList)
    return f


def evcond(be, aList, dList):
    if be.null(): raise LispException("boolean expression cannot be NIL")
    if not (myeval(be.car().car(), aList, dList)).null():
        return myeval(be.car().cdr().car(), aList, dList)
    return evcond(be.cdr(), aList, dList)


class bcolors:
    PROMPT = '\033[92m'
    OKBLUE = '\033[94m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


def interpreter(dList):
    print ""
    print bcolors.OKBLUE + "Welcome to LISP" + bcolors.ENDC
    print "Call (help) to see available primitives"
    print "Type 'Control+c' to cancel the current input"
    print "Call (quit) or type 'Control-d' to quit"
    print ""
    try:
        import readline
    except:
        print bcolors.WARNING + "warning: " + bcolors.ENDC + "loading readline library failed. Advanced editing features will not be available"
        print ""

    while True:
        try:
            entry = raw_input(bcolors.PROMPT + "LISP: " + bcolors.ENDC)
            tokens = get_tokens(entry)

            while not balanced(tokens):
                entry = raw_input("")
                tokens += get_tokens(entry)

            #read. parse(tokens) #parse the tokens and build an S-Expression
            if len(tokens) > 0: raise LispException("extra tokens found: {0}".format(tokens))

            #eval and print. the heart of the interpreter!
            print bcolors.OKBLUE + " OUT: " + bcolors.ENDC + str(myeval(sexp, SExp("NIL"), dList))
            print ""
        except KeyboardInterrupt:
            print ""
            print "keyboard interrupt"
            print ""
        except LispException as inst:
            print bcolors.FAIL + " ERR: " + bcolors.ENDC + inst.args[0]
            print ""


if __name__ == "__main__":
    dList = copy.copy(SExp("NIL"))

    if len(sys.argv) == 1:
        try:
            interpreter(dList)
        except EOFError:
            print ""
    elif len(sys.argv) == 2:
        infile = file(sys.argv[1], "r")
        tokens = get_tokens(infile.read())
        for sexp in parse_gen(tokens):
            try:
                print str(myeval(sexp, SExp("NIL"), dList))
            except LispException as inst:
                print "error: " + inst.args[0]
        infile.close()
    else:
        print "Usage: interpreter.py [input file]"
        print ""
        print "Note that [input file] is optional. If provided, all LISP expressions in the file"
        print "will be read, eval'd and printed in order. Otherwise, the interpreter starts."""
        print ""
        print ""
