import pytest
from solution import fizzbuzz


@pytest.mark.sample
def test_three():
    assert fizzbuzz(3) == "fizz"


@pytest.mark.sample
def test_plain():
    assert fizzbuzz(7) == "7"


def test_fifteen():
    assert fizzbuzz(15) == "fizzbuzz"


@pytest.mark.trap("string-vs-int")
def test_returns_string_not_int():
    assert fizzbuzz(1) == "1"
