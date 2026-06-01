import ast
import operator


SUPPORTED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in SUPPORTED_OPERATORS:
        return SUPPORTED_OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in SUPPORTED_OPERATORS:
        return SUPPORTED_OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("unsupported expression.")


def calculator(expression: str) -> str:
    """
    Evaluate a simple math expression and return the result as text.
    """
    try:
        result = _evaluate(ast.parse(expression, mode="eval"))
        return str(result)
    except Exception as error:
        return f"Calculator error: {error}"


class Calculator:
    def calculate(self, expression: str) -> str:
        return calculator(expression)
