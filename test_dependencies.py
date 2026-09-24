import pytest
from fastapi import HTTPException

from app.dependencies import expand_percent
from app.schemas import ExpressionIn


def _expand(expr: str) -> str:
    """Helper: expand_percent is now a dependency that takes the request
    body model instead of a bare string, so tests build that model first.
    """
    return expand_percent(ExpressionIn(expr=expr))


def test_add_percent():
    """Test addition where B% means 'B percent of A'."""
    assert _expand("5 + 10%") == "5 + (5*10/100)"

def test_subtract_percent():
    """Test subtraction where B% means 'B percent of A'."""
    assert _expand("20 - 30%") == "20 - (20*30/100)"

def test_multiply_percent():
    """Test multiplication where B% means 'B divided by 100'."""
    assert _expand("15 * 25%") == "15 * (25/100)"

def test_divide_percent():
    """Test division where B% means 'B divided by 100'."""
    assert _expand("40 / 50%") == "40 / (50/100)"

def test_multiple_operations():
    """Test expressions with multiple A op B% operations."""
    assert _expand("3 * 4% + 2 / 1%") == "3 * (4/100) + 2 / (1/100)"

def test_standalone_100_percent():
    """Test standalone percentage (100%)."""
    assert _expand("100%") == "(100/100)"

def test_two_standalone_percents():
    """Test expression with two standalone percentages."""
    assert _expand("10% + 20%") == "(10/100) + (20/100)"

def test_empty_expr_raises_http_exception():
    """The dependency should surface an expansion failure as a 400."""
    with pytest.raises(HTTPException) as exc_info:
        _expand("")
    assert exc_info.value.status_code == 400