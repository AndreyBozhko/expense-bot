from datetime import date, timedelta

import pytest

from expense_bot.utils import all_subclasses, parse_date


def test_all_subclasses():
    class A:
        pass

    class B(A):
        pass

    class C(A):
        pass

    class D(B):
        pass

    class E(D):
        pass

    assert set(all_subclasses(A)) == set([B, C, D, E])
    assert set(all_subclasses(B)) == set([D, E])
    assert set(all_subclasses(C)) == set()
    assert set(all_subclasses(D)) == set([E])
    assert set(all_subclasses(E)) == set()

    class BC(B, C):
        pass

    assert set(all_subclasses(A)) == set([B, C, BC, D, E])
    assert set(all_subclasses(B)) == set([BC, D, E])
    assert set(all_subclasses(C)) == set([BC])
    assert set(all_subclasses(D)) == set([E])
    assert set(all_subclasses(E)) == set()
    assert set(all_subclasses(BC)) == set()


@pytest.mark.parametrize(
    "dt_str, result",
    [
        ("2022-07-11", date(2022, 7, 11)),
        ("20220711", date(2022, 7, 11)),
        ("2022711", date(2022, 7, 11)),
        ("7/11/22", date(2022, 7, 11)),
        ("07/11/22", date(2022, 7, 11)),
        ("7/11/2022", date(2022, 7, 11)),
        ("07/11/2022", date(2022, 7, 11)),
        ("today", date.today()),
        ("yesterday", date.today() - timedelta(days=1)),
    ],
)
def test_parse_date_succeeds(dt_str, result):
    assert parse_date(dt_str) == result


@pytest.mark.parametrize(
    "dt_str",
    [
        "2022_07_11",
        "2022-0711",
        "07/11",
        "22-07-11",
        "tomorrow",
    ],
)
def test_parse_date_raises(dt_str):
    with pytest.raises(ValueError):
        parse_date(dt_str)
