import math
from collections import deque
from datetime import datetime

from asteval import Interpreter
from fastapi import APIRouter, Depends

from app.dependencies import expand_percent, get_history
from app.schemas import CalculateResponse, ExpressionIn, ExpressionOut

router = APIRouter()

# Safe evaluator
aeval = Interpreter(minimal=True, usersyms={"pi": math.pi, "e": math.e})


@router.post("/calculate", response_model=CalculateResponse)
def calculate(
    expression: ExpressionIn,
    code: str = Depends(expand_percent),
    history: "deque[ExpressionOut]" = Depends(get_history),
):
    expr = expression.expr
    try:
        result = aeval(code)
        if aeval.error:
            msg = "; ".join(str(e.get_error()) for e in aeval.error)
            aeval.error.clear()
            return CalculateResponse(ok=False, expr=expr, result="", error=msg)

        history.append(ExpressionOut(
            expr=expr,
            timestamp=datetime.now().isoformat(),
            result=result,
        ))
        return CalculateResponse(ok=True, expr=expr, result=result, error="")
    except Exception as e:
        return CalculateResponse(ok=False, expr=expr, result="", error=str(e))