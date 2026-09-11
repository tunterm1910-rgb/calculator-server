import math
from collections import deque
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from asteval import Interpreter

from models import Expression, CalculatorLog

HISTORY_MAX = 1000
# HISTORY (in-memory for now)
history: deque[CalculatorLog] = deque(maxlen=HISTORY_MAX)

app = FastAPI(title="Mini Calculator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Safe evaluator ----------
aeval = Interpreter(minimal=True, usersyms={"pi": math.pi, "e": math.e})


@app.post("/calculate")
def calculate(expression: Expression):
    expr = expression.expr
    try:
        code = expression.expand_percent()
        result = aeval(code)
        if aeval.error:
            msg = "; ".join(str(e.get_error()) for e in aeval.error)
            aeval.error.clear()
            return {"ok": False, "expr": expr, "result": "", "error": msg}
        # Add history
        history.append(CalculatorLog(
            timestamp=datetime.now().isoformat(),
            expr=expr,
            result=result,
        ))
        return {"ok": True, "expr": expr, "result": result, "error": ""}
    except Exception as e:
        return {"ok": False, "expr": expr, "result": "", "error": str(e)}


@app.get("/history", response_model=list[CalculatorLog])
def get_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=HISTORY_MAX,
        description="",
    )
):
    return list(history)[-limit:][::-1]


@app.delete("/history")
def delete_history():
    history.clear()
    return {"ok": True, "cleared": True}