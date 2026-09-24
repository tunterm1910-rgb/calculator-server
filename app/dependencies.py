import re
from collections import deque

from fastapi import HTTPException

from app.schemas import ExpressionIn, ExpressionOut

HISTORY_MAX = 1000

# In-memory history store, shared across requests via the get_history
history: deque[ExpressionOut] = deque(maxlen=HISTORY_MAX)

# "<a> +/- <number>%" -> percentage of <a>
_PERCENT_ADD_SUB = re.compile(r"([\w\.\)]+)\s*([+-])\s*(\d+(?:\.\d+)?)\s*%")
# any remaining standalone "<number>%"
_PERCENT_STANDALONE = re.compile(r"(\d+(?:\.\d+)?)%")


def _expand(expr: str) -> str:
    """Pure string transformation: expand '%' into explicit arithmetic.

    Rules:
      - "<a> - <number>%"  -> "<a> - (<a>*<number>/100)"
      - "<a> + <number>%"  -> "<a> + (<a>*<number>/100)"
      - any other "<number>%" -> "(<number>/100)"
    """
    if not expr or not expr.strip():
        raise ValueError("expr must not be empty")

    def repl(match: "re.Match") -> str:
        base, sign, pct = match.group(1), match.group(2), match.group(3)
        return f"{base} {sign} ({base}*{pct}/100)"

    code = _PERCENT_ADD_SUB.sub(repl, expr)
    code = _PERCENT_STANDALONE.sub(r"(\1/100)", code)
    return code


def expand_percent(expression: ExpressionIn) -> str:
    """FastAPI dependency: expand '%' syntax in the request body's `expr`.

    Shares the same `ExpressionIn` body as the path operation function, so
    the request is only parsed once. Raises an HTTPException(400) if the
    expression can't be expanded.
    """
    try:
        return _expand(expression.expr)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not expand expression: {exc}",
        )


def get_history() -> "deque[ExpressionOut]":
    """FastAPI dependency returning the shared in-memory history store."""
    return history