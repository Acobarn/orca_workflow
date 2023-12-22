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

class Equals_Sign(Enum):
    EQUALS_SIGN = "="

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

class Function_Variable(Enum):
    FUNC = "f"
    A = "a"
    B = "b"
    C = "c"
    X = "x"
    Y = "y"
    Z = "z"

class Non_Metric_Units_Conversion(Enum):
    

    pass

class Calculator():

    TEMPLATE_PROMPT:str = "Assistant,you can call calculator function in the following format. "
    # TODO Add call method in format to support more handling of formulas.
    "<calculator><equation>x=arcsin(1/2)</equation></calculator>. "
    "This function helps you to compute one-dimensional equations and simplify formulas.\n"
    "For example :\n"
    "\"user:I have a 25 hectares of farmland and this year I plan to plant corn. The yield of this variety of corn is 2.2 tonnes per acre. Due to technical problems, 57% of my farm is effectively planted. What is the expected corn harvest from my farmland this year?\"",
    "\"assistant:To calculate the expected corn harvest from your farmland this year, you need to follow these steps:\n\""
    "Find the total area of your farmland. Since you have 25 hectares, "
    "you can use this conversion factor: 1 hectare = 2.47105 acres. So, 25 hectares = <calculator><equation>25 * 2.47105</equation></calculator> = 61.780875 acres.\n"
    "Find the area of your farm that is effectively planted. Since 57% of your farm is planted, you can multiply the total area by 0.57. So, <calculator><equation>61.780875 * 0.57</equation></calculator> = 35.1932625 acres.\n"
    "Find the expected yield per  acre of your corn variety. You have 2.2 tonnes per acre.\n"
    "Multiply the yield per acre by the area that is effectively planted. So, <calculator><equation>35.1932625 * 2.2</equation></calculator> = 77.4166875 tonnes.\n"
    "Therefore, the expected corn harvest from your farmland this year is about 77.4166875 tonnes."

    # Add a stop token, when llm generates this token, it will interrupt the generation,
    # get the formula in the specified format, complete the simplification and calculation,
    # finally replace the formula in the original output and let llm continue generation.
    EXTRA_STOP_TOKEN:str = "</calculator>"

    START_TOKEN:str = "<calculator>"

    def __init__(self) -> None:
        pass

    # Convert token to list[str] as input parameter
    def notation_traversal(self,formula:list[str]) -> str:
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
                result = self.compute(tmp_formula)
                formula_stack.append(result)
            else:
                formula_stack.append(i)
        return self.compute(formula_stack)

    # TODO Support more calculation symbols
    def compute(self,str_list:list[str]) -> str:
        compute_str:str = ''.join(str_list)
        result = eval(compute_str)
        return str(result)