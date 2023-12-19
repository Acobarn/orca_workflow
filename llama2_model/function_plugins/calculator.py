# This is a simple calculator demo
from enum import Enum
class Trigo_Function(Enum):
    SIN = "sin("
    COS = "cos("
    TAN = "tan("
    COT = "cot("
    SEC = "sec("
    CSC = "csc("
    ARCSIN = "arcsin("
    ARCCOS = "arccos("
    ARCTAN = "arctan("

class Integral_Function(Enum):
    DEFINITE_INTEGRAL = "∫_"#∫_2^5 f(x) dx

class Arithmatics(Enum):
    PLUS = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVISION = "/"

class Power(Enum):
    POWER = "^"

class Constant(Enum):
    NATURAL_CONSTANT = "e"
    CIRCULAR_CONSTANT_1 = "pi"
    CIRCULAR_CONSTANT_2 = "π"


class Logarithm(Enum):
    LOGARITHM = "log_"#log_5(125)
    NATURAL_LOGARITHM = "ln"
    LOGARITHM_BASE_TEN = "lg"

class Permutation_Combination(Enum):
    COMBINATION = "C"#5C2
    PERMUTATION = "P"#5P2
    FACTORIAL = "!"

class Bracket(Enum):
    L_BRACKET = "("
    R_BRACKET = ")"

# Convert token to list[str] as input parameter
def notation_traversal(formula:list[str]) -> str:
    formula_stack:list[str] = []
    for i in formula:
        if i == Bracket.R_BRACKET.value:
            tmp_formula = []
            tmp = formula_stack.pop()
            trigo_list = [e.value for e in Trigo_Function.__members__.values()]
            while not (tmp in trigo_list or tmp == Bracket.L_BRACKET.value):
                tmp_formula.append(tmp)
                tmp = formula_stack.pop() 
            tmp_formula.reverse()
            result = compute(tmp_formula)
            formula_stack.append(result)
        else:
            formula_stack.append(i)
    return compute(formula_stack)

# TODO Support more calculation symbols
def compute(str_list:list[str]) -> str:
    compute_str:str = ''.join(str_list)
    result = eval(compute_str)
    return str(result)