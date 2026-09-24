import re
from pydantic import BaseModel


class BaseExpression(BaseModel):
    """Fields shared by every expression-related schema."""
    expr: str


class ExpressionIn(BaseExpression):
    """Request body for the /calculate API. (previously `Expression`)"""
    pass


class ExpressionOut(BaseExpression):
    """Response body item for the /history API. (previously `CalculatorLog`)"""
    timestamp: str
    result: float


class CalculateResponse(BaseModel):
    """Response body for the /calculate API."""
    ok: bool
    expr: str
    result: float | str = ""
    error: str = ""