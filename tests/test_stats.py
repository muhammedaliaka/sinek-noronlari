"""Evre 2b istatistikleri: küme bootstrap / permütasyon (sonuç dosyası gerektirmez)."""
import numpy as np

from sinek.experiments import stats as S


def test_pooled_fraction_and_empty():
    assert S.pooled_fraction([3, 1], [1, 1]) == 4 / 6
    assert np.isnan(S.pooled_fraction([0, 0], [0, 0]))


def test_bootstrap_ci_contains_estimate_and_is_narrower_with_more_data():
    rng = np.random.default_rng(1)
    a1, b1 = rng.binomial(8, 0.8, 12), None
    b1 = 8 - a1
    a2, b2 = np.tile(a1, 4), np.tile(b1, 4)
    m1, lo1, hi1 = S.cluster_bootstrap_ci(a1, b1, n=4000)
    m2, lo2, hi2 = S.cluster_bootstrap_ci(a2, b2, n=4000)
    assert lo1 <= m1 <= hi1 and lo2 <= m2 <= hi2
    assert (hi2 - lo2) < (hi1 - lo1)
    assert all(np.isnan(x) for x in S.cluster_bootstrap_ci([0, 0], [0, 0]))


def test_cluster_permutation_detects_effect_and_is_directional():
    g1 = (np.array([5, 4, 5, 6, 5, 4]), np.array([0, 1, 0, 0, 1, 0]))
    g2 = (np.array([1, 0, 1, 1, 0, 1]), np.array([4, 5, 4, 5, 5, 4]))
    assert S.cluster_permutation_p(g1, g2, n=4000) < 0.01
    assert S.cluster_permutation_p(g2, g1, n=4000) > 0.9
    assert S.cluster_permutation_p(g1, g2, n=4000, alternative="two-sided") < 0.01


def test_cluster_permutation_nan_without_choices():
    z = (np.zeros(3), np.zeros(3))
    assert np.isnan(S.cluster_permutation_p(z, (np.ones(3), np.ones(3)), n=100))


def test_type_one_error_is_controlled_under_null_with_agent_heterogeneity():
    """H0: iki grup aynı dağılımdan (canlılar arası tercih farkı var, denemeler canlı içinde korelasyonlu)."""
    rng = np.random.default_rng(7)
    rej = 0
    n_sim = 300
    for s in range(n_sim):
        def group(m):
            p = rng.beta(2, 2, m)                      # canlıya özgü tercih
            tot = rng.integers(0, 9, m)                # canlı başına seçim sayısı 0..8
            a = rng.binomial(tot, p)
            return a, tot - a
        g1, g2 = group(12), group(12)
        rej += S.cluster_permutation_p(g1, g2, n=500, seed=s) < 0.05
    assert rej / n_sim < 0.10   # ~%5 beklenir; Monte Carlo gürültüsü için gevşek sınır


def test_bootstrap_ci_coverage_under_heterogeneity():
    rng = np.random.default_rng(11)
    hit, n_sim = 0, 200
    true = 0.5   # Beta(2,2) ortalaması
    for s in range(n_sim):
        m = 20
        p = rng.beta(2, 2, m)
        tot = rng.integers(4, 9, m)
        a = rng.binomial(tot, p)
        _, lo, hi = S.cluster_bootstrap_ci(a, tot - a, n=500, seed=s)
        hit += lo <= true <= hi
    assert hit / n_sim > 0.88   # nominal 0.95; küçük örneklemde hafif liberal olabilir


def test_binom_two_sided_known_values():
    assert S.binom_two_sided(5, 10) == 1.0
    assert abs(S.binom_two_sided(4, 4) - 0.125) < 1e-12
