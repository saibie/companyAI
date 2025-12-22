from langchain_core.tools import tool
from sympy import sympify, N

@tool
def calculator_tool(expression: str) -> str:
    """
    Calculate mathematical expressions safely using SymPy.
    Useful for precise calculations (budgeting, growth rates, etc.).
    Args:
        expression: Mathematical expression (e.g., '200 * 1.5 / 10', 'sqrt(25)').
    """
    try:
        # sympify는 eval보다 안전하게 수식을 파싱합니다.
        # N()은 결과를 소수점 숫자로 평가합니다.
        result = N(sympify(expression))
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation Error: {str(e)}"