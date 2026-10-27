"""Evre 2b ölçüt değerlendiricisi: sentetik seçim sayılarıyla (simülasyon gerektirmez)."""
import types

import numpy as np

from sinek.experiments import evre2b


def _args(n=12, trials=8):
    return types.SimpleNamespace(agents=n, trials=trials)


def _stage(phase, name, a_counts, b_counts, episode=0):
    """a_counts/b_counts: koşul başına (plastic, frozen, random) canlı-başı sayı dizileri."""
    return {"phase": phase, "name": name, "episode": episode,
            "n_a": np.concatenate(a_counts).tolist(), "n_b": np.concatenate(b_counts).tolist()}


def _rng_counts(rng, n, p, total):
    t = rng.binomial(8, total, n)
    a = rng.binomial(t, p)
    return a, t - a


def _scenario(seed, p_naive, rate_naive, p_trained, rate_trained, p_rev, rate_rev=0.7, n=12):
    rng = np.random.default_rng(seed)

    def stage(phase, name, pl, fr, rn):
        a, b = zip(pl, fr, rn)
        return _stage(phase, name, a, b)

    naive = stage("naive", "naif", _rng_counts(rng, n, p_naive, rate_naive), _rng_counts(rng, n, p_naive, rate_naive),
                  _rng_counts(rng, n, 0.5, 0.7))
    fr, rn = _rng_counts(rng, n, p_naive, rate_naive), _rng_counts(rng, n, 0.5, 0.7)
    sa = stage("A", "A12", _rng_counts(rng, n, p_trained, rate_trained), fr, rn)
    sb = stage("B", "B24", _rng_counts(rng, n, p_rev, rate_rev), fr, rn)
    return [naive, sa, sb]


def test_strong_effect_with_good_data_passes_everything():
    v = evre2b.evaluate2(_scenario(1, 0.5, 0.6, 0.9, 0.8, 0.15, n=24), _args(24), None, True)
    assert all(x["pass"] for x in v.values()), {k: x for k, x in v.items() if not x["pass"]}


def test_low_naive_choice_rate_fails_gate_and_makes_a2_a3_not_evaluable():
    v = evre2b.evaluate2(_scenario(2, 0.5, 0.15, 0.9, 0.8, 0.15, n=24), _args(24), None, True)
    gate = [x for k, x in v.items() if k.startswith("G ")][0]
    a2 = [x for k, x in v.items() if k.startswith("A2")][0]
    a3 = [x for k, x in v.items() if k.startswith("A3")][0]
    assert not gate["pass"] and not a2["pass"] and not a3["pass"]
    assert "değerlendirilemez" in a2["detail"]


def test_no_learning_fails_a1_a2_and_reversal_criteria():
    v = evre2b.evaluate2(_scenario(3, 0.5, 0.6, 0.5, 0.6, 0.5, n=24), _args(24), None, True)
    for k in v:
        if k[:2] in ("A1", "A2", "B1", "B2"):
            assert not v[k]["pass"], k


def test_naive_role_bias_fails_a3_and_persistence_flag_is_respected():
    v = evre2b.evaluate2(_scenario(4, 0.8, 0.6, 0.9, 0.8, 0.15, n=24), _args(24), None, False)
    a3 = [x for k, x in v.items() if k.startswith("A3")][0]
    c = [x for k, x in v.items() if k.startswith("C ")][0]
    assert not a3["pass"] and not c["pass"]


def test_kind0_counts_undo_role_swap():
    stage = {"n_a": [3, 1, 0, 0, 0, 0], "n_b": [1, 3, 0, 0, 0, 0]}
    k0, k1 = evre2b.kind0_counts(stage, 2, "plastic", [False, True, False, False, False, False])
    assert k0.tolist() == [3, 3] and k1.tolist() == [1, 1]   # ikinci canlıda roller yer değiştirmişti


def test_render_summary_smoke():
    st = _scenario(5, 0.5, 0.6, 0.9, 0.8, 0.2, n=12)
    from sinek.experiments import protocol as P
    stages = []
    for s in st:
        res = P.ChoiceResult(np.array(s["n_a"]), np.array(s["n_b"]), 8, np.zeros(36))
        stages.append({**s, "summary": P.summarize(res, ["plastic"] * 12 + ["frozen"] * 12 + ["random"] * 12)})
    r = {"args": {"agents": 12, "trials": 8, "swap_roles": True, "episodes": 12, "reversal_episodes": 12, "episode_seconds": 60.0,
                  "seed": 1}, "neurons_per_creature": 4780, "wall_seconds": 60.0, "swap": [0] * 36, "stages": stages,
         "verdict": evre2b.evaluate2(stages, _args(12), None, True), "title": "Evre 2b"}
    md = evre2b.render_summary2(r)
    assert "Ölçütler" in md and "koku-0 oranı" in md and "A1" in md
