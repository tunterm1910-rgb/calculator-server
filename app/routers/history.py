from collections import deque

from fastapi import APIRouter, Depends, Query

from app.dependencies import HISTORY_MAX, get_history
from app.schemas import ExpressionOut

router = APIRouter()


@router.get("/history", response_model=list[ExpressionOut])
def read_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=HISTORY_MAX,
        description="",
    ),
    history: "deque[ExpressionOut]" = Depends(get_history),
):
    return list(history)[-limit:][::-1]


@router.delete("/history")
def delete_history(history: "deque[ExpressionOut]" = Depends(get_history)):
    history.clear()
    return {"ok": True, "cleared": True}