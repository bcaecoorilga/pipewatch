"""Tests for pipewatch.correlation."""
import pytest
from unittest.mock import MagicMock
from pipewatch.correlation import correlate, _pearson, _interpret, CorrelationResult


def _rec(name, ts, value):
    m = MagicMock()
    m.name = name
    m.timestamp = ts
    m.value = value
    return m


@pytest.fixture
def history():
    h = MagicMock()
    return h


def test_pearson_perfect_positive():
    assert _pearson([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_pearson_perfect_negative():
    assert _pearson([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_pearson_insufficient_data():
    assert _pearson([1], [1]) is None


def test_pearson_zero_variance():
    assert _pearson([2, 2, 2], [1, 2, 3]) is None


def test_interpret_strong():
    assert _interpret(0.9) == "strong"
    assert _interpret(-0.85) == "strong"


def test_interpret_moderate():
    assert _interpret(0.6) == "moderate"


def test_interpret_negligible():
    assert _interpret(0.1) == "negligible"


def test_interpret_none():
    assert _interpret(None) == "insufficient data"


def test_correlate_no_overlap(history):
    history.for_name.side_effect = lambda n: [
        _rec(n, 1, 10.0)
    ] if n == "a" else [_rec(n, 2, 20.0)]
    result = correlate(history, "a", "b")
    assert result.n == 0
    assert result.coefficient is None


def test_correlate_with_overlap(history):
    history.for_name.side_effect = lambda n: [
        _rec(n, 1, 1.0), _rec(n, 2, 2.0), _rec(n, 3, 3.0)
    ] if n == "a" else [
        _rec(n, 1, 2.0), _rec(n, 2, 4.0), _rec(n, 3, 6.0)
    ]
    result = correlate(history, "a", "b")
    assert result.n == 3
    assert result.coefficient == pytest.approx(1.0)
    assert result.interpretation == "strong"


def test_correlate_to_dict(history):
    history.for_name.return_value = []
    result = correlate(history, "x", "y")
    d = result.to_dict()
    assert "metric_a" in d
    assert "coefficient" in d
    assert "interpretation" in d
