import numpy as np

from sinek.experiments import odor_pair_check as pc


def test_side_bias_creature_gives_opposite_pairs_and_equal_counts():
    # yan yanlılığı: özgünde decoy (1), aynada gerçek (0); canlı başına 4 çift
    s = np.tile(np.array([1, 0] * 4), (6, 1))
    pt = pc.pair_table(s)
    assert pt["table"] == {"dr": 24}
    assert (s == 1).sum() == (s == 0).sum()
    obs, exp, p = pc.perm_test(pt["a"], pt["b"], n=200)
    assert obs == 1.0 and exp == 1.0              # tüm çiftler zıt: karıştırma da aynı kenar dağılımını verir (dejenere), oran 1


def test_independent_outcomes_have_no_excess():
    rng = np.random.default_rng(1)
    s = rng.choice([-1, 0, 1], size=(24, 16))
    pt = pc.pair_table(s)
    obs, exp, p = pc.perm_test(pt["a"], pt["b"], n=300)
    assert abs(obs - exp) < 0.08 and p > 0.01
