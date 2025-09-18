from cxx11bindings import increment


def test_int():
    assert increment(3) == 4


def test_float():
    assert increment(3.0) == 4.0
