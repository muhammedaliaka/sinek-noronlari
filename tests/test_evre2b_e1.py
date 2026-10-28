"""Evre 2b E1 karşılaştırması (sonuç dosyası gerektirmez)."""
import numpy as np

from sinek.experiments import evre2b_e1


def _run(a_counts, b_counts, trials=8):
    n = len(a_counts)
    z = [0] * n
    st = {"phase": "A", "n_a": [0] * n + list(a_counts) + [0] * n, "n_b": [0] * n + list(b_counts) + [0] * n}
    # koşul sırası P.CONDITIONS = plastic, frozen, random; plastic ilk n canlı
    st["n_a"] = list(a_counts) + z + z
    st["n_b"] = list(b_counts) + z + z
    return {"args": {"agents": n, "trials": trials}, "config": {"motor": {"turn_gain": 60}}, "stages": [st]}


def test_real_better_than_shuffled_passes():
    real = _run([6, 7, 6, 7, 6, 7, 6, 7, 6, 7, 6, 7], [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    shuf = _run([3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4], [4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3])
    c = evre2b_e1.compare(real, shuf)
    assert c["valid"] and c["pass"] and c["p"] < 0.01


def test_shuffled_with_almost_no_choices_is_not_evaluable():
    real = _run([6, 7, 6, 7, 6, 7, 6, 7, 6, 7, 6, 7], [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    shuf = _run([0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
    c = evre2b_e1.compare(real, shuf)
    assert not c["valid"] and not c["pass"]


def test_equal_runs_fail():
    r = _run([5, 4, 6, 5, 4, 5, 6, 4, 5, 5, 4, 6], [3, 4, 2, 3, 4, 3, 2, 4, 3, 3, 4, 2])
    assert not evre2b_e1.compare(r, r)["pass"]


def test_different_design_is_rejected():
    import pytest

    r = _run([5] * 12, [3] * 12)
    s = _run([5] * 12, [3] * 12, trials=4)
    with pytest.raises(ValueError):
        evre2b_e1.compare(r, s)
    s2 = _run([5] * 12, [3] * 12)
    s2["config"]["motor"]["turn_gain"] = 40
    with pytest.raises(ValueError):
        evre2b_e1.compare(r, s2)
