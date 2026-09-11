import re
from pydantic import BaseModel


class Expression(BaseModel):
    """Request body for the /calculate API."""
    expr: str

    def expand_percent(self) -> str:
        """
        Expand '%' symbols in the expression into explicit arithmetic.

        Rules:
          - "<number>%" on its own      -> "(<number>/100)"
          - "<a> - <number>%"           -> "<a> - (<a>*<number>/100)"
          - "<a> + <number>%"           -> "<a> + (<a>*<number>/100)"

        Falls back to a standalone percent expansion for any other
        "<number>%" occurrence in the expression.
        """
        code = self.expr

        # "<a> +/- <number>%" -> percentage of <a>
        pattern = r"([\w\.\)]+)\s*([+-])\s*(\d+(?:\.\d+)?)\s*%"

        def repl(match: "re.Match") -> str:
            base, sign, pct = match.group(1), match.group(2), match.group(3)
            return f"{base} {sign} ({base}*{pct}/100)"

        code = re.sub(pattern, repl, code)

        # Any remaining standalone "<number>%" -> "(<number>/100)"
        code = re.sub(r"(\d+(?:\.\d+)?)%", r"(\1/100)", code)

        return code


class CalculatorLog(BaseModel):
    """Response body item for the /history API."""
    timestamp: str
    expr: str
    result: float


class CalculateResponse(BaseModel):
    """Response body for the /calculate API."""
    ok: bool
    expr: str
    result: float | str = ""
    error: str = ""