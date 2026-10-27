"""Evre 2 post-hoc ek analiz yardımcıları (sonuç dosyası gerektirmez)."""
import numpy as np

from sinek.experiments import evre2_posthoc as H


def test_binom_two_sided_known_values():
    assert H.binom_two_sided(5, 10) == 1.0
    assert abs(H.binom_two_sided(10, 10) - 2 / 1024) < 1e-12
    assert abs(H.binom_two_sided(4, 4) - 0.125) < 1e-12
    assert np.isnan(H.binom_two_sided(0, 0))


def test_pooled_pref():
    assert H.pooled_pref(np.array([3, 1]), np.array([1, 1])) == 4 / 6
    assert np.isnan(H.pooled_pref(np.zeros(2), np.zeros(2)))


def test_cluster_permutation_detects_a_clear_difference_and_not_a_null():
    g1 = (np.array([5, 4, 5, 6, 5, 4]), np.array([0, 1, 0, 0, 1, 0]))
    g2 = (np.array([1, 0, 1, 1, 0, 1]), np.array([4, 5, 4, 5, 5, 4]))
    assert H.cluster_permutation_p(g1, g2, n=4000) < 0.01
    assert H.cluster_permutation_p(g2, g1, n=4000) > 0.9  # yön tek yönlü
    rng = np.random.default_rng(0)
    h1 = (rng.integers(0, 4, 8), rng.integers(0, 4, 8))
    h2 = (rng.integers(0, 4, 8), rng.integers(0, 4, 8))
    assert H.cluster_permutation_p(h1, h2, n=4000) > 0.05


def test_cluster_permutation_returns_nan_without_choices():
    z = (np.zeros(3), np.zeros(3))
    assert np.isnan(H.cluster_permutation_p(z, (np.ones(3), np.ones(3)), n=100))


def test_one_sided_mean_p_ignores_nan_and_is_directional():
    a = np.array([0.9, 1.0, 0.8, np.nan, 0.9, 0.95, 0.85, 1.0, 0.9])
    b = np.array([0.2, 0.1, np.nan, 0.3, 0.2, 0.15, 0.25, 0.1, 0.3])
    assert H.one_sided_mean_p(a, b, n=4000) < 0.01
    assert H.one_sided_mean_p(b, a, n=4000) > 0.9
