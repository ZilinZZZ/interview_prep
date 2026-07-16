import pytest
from solution import add


@pytest.mark.sample
def test_add_small():
    assert add(1, 2) == 3


def test_add_negative():
    assert add(-1, 1) == 0


@pytest.mark.trap("silent-none")
def test_add_returns_value_not_none():
    assert add(0, 0) == 0
