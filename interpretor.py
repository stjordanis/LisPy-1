import re
import sys
import copy

#some useful regexes:
ATOM = re.compile("^\w+$|^-[0-9]+$")
INT = re.compile("^-?[0-9]+$")
WHITESPACE = re.compile("^\s+$")

NULL_VALUE = "NIL"

#write eval, apply, defun, cond, quote

#experiment with my own tail-recursion stack, to avoid recursion depth of python
    
class SExp:
    def __init__(self, left, right=None):
        """Create an S-expression (left . right). If 'right' is not provided,
        'left' should be atomic.

        """
        if right is None:
            if not isinstance(left, str):
                raise Exception("trying to create an S-expression from {0}".format(str(left)))
            if ATOM.match(left) is None:
                raise Exception("not a valid atomic S-expression: {0}".format(left))
            self.val = left
        else:
            if not isinstance(left, SExp) or not isinstance(right, SExp):
                raise Exception("not an S-expression")
            self.val = (left, right)

    def _atom(self):
        return type(self.val) == type("")

    #todo: replace this repetition of code
    def atom(self):
        if self._atom(): return T_sexp
        return NIL_sexp

    def _eq(self, other):
        if not self._atom(): raise Exception("not an atomic S-expression: {0}".format(self))
        if not other._atom(): raise Exception("not an atomic S-expression: {0}".format(other))
        return self.val == other.val

    def eq(self, other):
        if self._eq(other): return T_sexp
        return NIL_sexp

    def _null(self):
        if self._atom():
            if self.val == NULL_VALUE: return True
        return False

    def null(self):
        if self._null(): return T_sexp
        return NIL_sexp
    
    def _int(self):
        if not self._atom() or INT.match(self.val) is None: return False
        return True

    def int(self):
        if self._int(): return T_sexp
        return NIL_sexp

    def car(self):
        if self._atom(): raise Exception("cannot call CAR on atomic s-expression: {0}".format(self))
        return self.val[0]

    def cdr(self):
        if self._atom(): raise Exception("cannot call CDR on atomic s-expression: {0}".format(self))
        return self.val[1]

    def _arithmetic(self, other, op):
        if not self._int(): raise Exception("not an int: {0}".format(self))
        if not other._int(): raise Exception("not an int: {0}".format(other))
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
        if not self._int(): raise Exception("not an int: {0}".forat(self))
        if not other._int(): raise Exception("not an int: {0}".format(other))
        if op(int(self.val), int(other.val)): return T_sexp
        return NIL_sexp
        
    def greater(self, other):
        return self._compare(other, lambda a,b: a>b)

    def less(self, other):
        return self._compare(other, lambda a,b: a<b)

    def _is_list(self):
        if self._null(): return True
        if self._atom(): return False
        if self.val[1]._is_list(): return True
        return False

    def _repr_helper(self):
        if self._null():
            return ""
        return " {0}{1}".format(self.val[0], self.val[1]._repr_helper())

    def __repr__(self):
        if self._atom():
            return self.val
        else:
            if self._is_list():
                return "({0}{1})".format(self.val[0], self.val[1]._repr_helper())
            return "({0} . {1})".format(self.val[0], self.val[1])

#basic S-expressions
T_sexp = SExp("T")
NIL_sexp = SExp(NULL_VALUE)

def lex(myinput):
    """A generator for tokens in myinput"""
    my_atom = ""
    for char in myinput:
        if not my_atom == "":
            if ATOM.match(char):
                my_atom += char
                continue
            else:
                yield my_atom
                my_atom = ""
        if WHITESPACE.match(char):
            continue
        elif char in "().": yield char
        elif ATOM.match(char) or (char == "-" and my_atom == ""): #FIXME: a horrible hack for negative numbers!!!
            my_atom += char
        else:
            raise Exception("bad token: {0}".format(char))
    if not my_atom == "":
        yield my_atom


def process_list_tokens(tokens):
    """Parses tokens in list form into an s-expression"""
    if len(tokens) == 0: raise Exception("parse error: missing tokens")
    if tokens[0] == ")":
        tokens.pop(0)
        return NIL_sexp
    first = process_tokens(tokens)
    if len(tokens) == 0: raise Exception("parse error: missing tokens")
    if tokens[0] == ".": raise Exception("mixed notation not supported")
    second = process_list_tokens(tokens)
    return SExp(first, second)


def process_tokens(tokens):
    """Parses tokens into an s-expression"""
    if len(tokens) == 0: raise Exception("parse error: missing tokens")
    if ATOM.match(tokens[0]):
        return SExp(tokens.pop(0))
    if tokens[0] == "(" and tokens[1] == ")":
        tokens.pop(0)
        tokens.pop(0)
        return NIL_sexp
    #recursively continue
    if not tokens.pop(0) == "(": raise Exception("missing open parentheses")
    first = process_tokens(tokens)
    if len(tokens) == 0: raise Exception("parse error: missing tokens")
    second = []
    if tokens[0] == ".":
        tokens.pop(0)
        second = process_tokens(tokens)
        if len(tokens) == 0: raise Exception("parse error: missing tokens")
        if not tokens.pop(0) == ")": raise Exception("missing close parentheses")
    else:
        second = process_list_tokens(tokens)
    return SExp(first, second)
        
        
def parse(myinput):
    """Parses in input and returns it as an s-expression"""
    tokens = [i for i in lex(myinput)]
    sexp = process_tokens(tokens)
    if len(tokens) > 0: raise Exception("extra tokens found: {0}".format(", ".join(tokens)))
    return sexp


def in_pairlist(exp, pairlist):
    if pairlist._null(): return False
    if pairlist.car()._atom(): raise Exception("a-list or d-list in wrong format")
    if exp._eq(pairlist.car().car()): return True
    return in_pairlist(exp, pairlist.cdr())
    

def getval(exp, from_list):
    if from_list._null(): return NIL_sexp
    if from_list.car()._atom(): raise Exception("a-list or d-list in wrong format")
    if exp._eq(from_list.car().car()): return from_list.car().cdr()
    return getval(exp, from_list.cdr())


def addpairs(params, cur_args, to_list):
    if params._null() and cur_args._null(): return to_list
    if params._atom() or cur_args._atom(): raise Exception("pairs cannot be atoms")
    pair = SExp(params.car(), cur_args.car())
    return addpairs(params.cdr(), cur_args.cdr(), SExp(pair, to_list))


def myeval(exp, aList, dList):
    if exp._atom():
        if exp._int(): return exp
        if exp._eq(T_sexp): return T_sexp
        if exp._null(): return NIL_sexp
        if in_pairlist(exp, aList): return getval(exp, aList)
        raise Exception("unbound variable: {0}".format(exp.val))
    if exp.car()._atom():
        if exp.car().val == "QUOTE": return exp.cdr().car()
        if exp.car().val == "COND": return evcond(exp.cdr(), aList, dList)
        if exp.car().val == "DEFUN": 
            f = exp.cdr().car()
            args = exp.cdr().cdr().car()
            body = exp.cdr().cdr().cdr().car()
            return defun(f, args, body, dList)
        return my_apply(exp.car(), evlis(exp.cdr(), aList, dList), aList, dList)
    raise Exception("eval called with invalid expression")
        
    
def evlis(targetlist, aList, dList):
    if targetlist._null(): return NIL_sexp
    return SExp(myeval(targetlist.car(), aList, dList),
                evlis(targetlist.cdr(), aList, dList))

def my_apply(f, x, aList, dList):
    if not f._atom(): raise Exception("error: {0} is not a known function".format(f))
    if f.val == "CAR": return x.car().car()
    if f.val == "CDR": return x.car().cdr()
    if f.val == "CONS": return SExp(x.car(), x.cdr())
    if f.val == "ATOM": return x.car.atom()
    if f.val == "NULL": return x.null()
    if f.val == "EQ": return x.car().eq(x.car().cdr())

    if f.val == "INT": return x.car().int()
    if f.val == "PLUS": return x.car().plus(x.cdr().car())
    if f.val == "MINUS": return x.car().minus(x.cdr().car())
    if f.val == "TIMES": return x.car().times(x.cdr().car())
    if f.val == "QUOTIENT": return x.car().quotient(x.cdr().car())
    if f.val == "REMAINDER": return x.car().remainder(x.cdr().car())
    if f.val == "LESS": return x.car().less(x.cdr().car())
    if f.val == "GREATER": return x.car().greater(x.cdr().car())
    
    return myeval(getval(f,dList).cdr(), addpairs(getval(f, dList).car(), x, aList), dList)


def defun(f, args, body, dList):
    new_dList = SExp(SExp(f, SExp(args, body)), copy.copy(dList))
    dList.val = new_dList.val
    return f
    

def evcond(be, aList, dList):
    if be._null(): raise Exception("boolean expression cannot be NIL")
    if not (myeval(be.car().car(), aList, dList))._null():
        return myeval(be.car().cdr().car(), aList, dList)
    return evcond(be.cdr(), aList, dList)


def interpreter(dList):
    while True:
        expression = raw_input("LISP>")
        try:
            print myeval(parse(expression), NIL_sexp, dList)
        except Exception as inst:
            print "error: " + inst.args[0]
            

if __name__ == "__main__":
    dList = copy.copy(NIL_sexp)
    if len(sys.argv) == 1: interpreter(dList)
    else:
        print "error - command-line options not yet supported."
