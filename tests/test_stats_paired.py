"""Eşli (canlı içi) istatistikler: null'da yanlış-pozitif, bilinen etkide güç, kapsama (R-6)."""
import numpy as np
import pytest

from sinek.experiments import stats as S


def _sim(rng, m=24, trials=16, p0=0.3, shift=0.0, het=20.0, rho=0.7):
    """Canlıya özgü taban olasılık (Beta), kol farkı `shift`, kollar arasında ortak-rastgele-sayı bağı rho."""
    pb = rng.beta(p0 * het, (1 - p0) * het, m)
    py, px = pb, np.clip(pb + shift, 0, 1)
    u = rng.random((m, trials))
    v = np.where(rng.random((m, trials)) < rho, u, rng.random((m, trials)))
    return (u < px[:, None]).sum(1), (v < py[:, None]).sum(1)


def test_paired_ci_covers_true_difference_and_signflip_is_directional():
    rng = np.random.default_rng(0)
    x, y = _sim(rng, shift=0.25)
    m, lo, hi = S.paired_cluster_ci(x, y, 16, n=4000, alpha=0.01)
    assert lo < m < hi and lo > 0
    assert S.paired_signflip_p(x, y, 16, n=4000) < 0.01
    assert S.paired_signflip_p(y, x, 16, n=4000) > 0.9


def test_paired_type_one_error_under_null_with_heterogeneity():
    rng = np.random.default_rng(1)
    n_sim, rej = 400, 0
    for s in range(n_sim):
        x, y = _sim(rng, shift=0.0)
        rej += S.paired_signflip_p(x, y, 16, n=400, seed=s) < 0.05
    assert rej / n_sim < 0.09        # ~%5 beklenir; Monte Carlo gürültüsü için gevşek sınır


def test_paired_ci_coverage():
    rng = np.random.default_rng(2)
    cover, n_sim = 0, 300
    for s in range(n_sim):
        x, y = _sim(rng, shift=0.15)
        _, lo, hi = S.paired_cluster_ci(x, y, 16, n=600, seed=s, alpha=0.05)
        cover += lo <= 0.15 <= hi
    assert 0.88 < cover / n_sim < 0.99


def test_paired_power_at_design_size_for_known_effect():
    rng = np.random.default_rng(3)
    n_sim, ok = 200, 0
    for s in range(n_sim):
        x, y = _sim(rng, m=24, trials=16, shift=0.30)
        _, lo, _ = S.paired_cluster_ci(x, y, 16, n=600, seed=s, alpha=0.01)
        ok += lo > 0
    assert ok / n_sim > 0.90


def test_paired_equivalence_passes_for_null_and_fails_for_large_shift():
    rng = np.random.default_rng(4)
    x, y = _sim(rng, m=48, trials=16, shift=0.0, het=40.0, rho=0.9)
    assert S.paired_equivalent(x, y, 16, delta=0.10)[3]
    x, y = _sim(rng, m=48, trials=16, shift=0.20, het=40.0, rho=0.9)
    assert not S.paired_equivalent(x, y, 16, delta=0.10)[3]


def test_paired_shape_mismatch_raises():
    with pytest.raises(ValueError):
        S.paired_cluster_ci([1, 2], [1, 2, 3], 16)
