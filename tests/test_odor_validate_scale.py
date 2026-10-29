"""Ölçek ekseni doğrulayıcısı: değerlendirici (sıfır-etki / bilinen-etki / kayma), kol-kol devam ve tohum koruması."""
import numpy as np
import pytest

from sinek.experiments import odor_validate_scale as VSC
from sinek.experiments.odor_eval import EVALUATORS, Thr
from sinek.games.protocol import pretrain
from sinek.world import odor_patterns


def _h(rng, A, T, p_by_arm, dev_sd=0.05):
    dev = dev_sd * rng.standard_normal(A)
    return {k: (rng.random((A, T)) < np.clip(p + (0.0 if k == "reference" else dev), 0.01, 0.99)[:, None]).astype(int) if k != "reference" else
            (rng.random((A, T)) < p).astype(int) for k, p in p_by_arm.items()}


def test_eval_scale_zero_effect_known_effect_and_bias():
    thr = Thr(n_boot=300, n_perm=300)
    ev = EVALUATORS["SC"]
    base = {"frozen": 0.5, "anosmic": 0.28, "anosmic_ens": 0.28, "reference": 0.97}
    null_pass, known_pass = 0, 0
    for s in range(20):
        rng = np.random.default_rng(s)
        null_pass += ev(_h(rng, 24, 16, {**base, "ens": 0.5}), thr)["passed"]
        known_pass += ev(_h(rng, 24, 16, {**base, "ens": 0.8}), thr)["passed"]
    assert null_pass == 0 and known_pass >= 18                       # sıfır etkide geçme yok, büyük etkide çoğu geçer
    rng = np.random.default_rng(99)
    shifted = ev(_h(rng, 24, 16, {**base, "ens": 0.8, "anosmic_ens": 0.28 + 0.2}), thr)       # topluluk kör düzeyi +0,20 kaydırıyor
    assert not shifted["descriptive"]["P3_anosmic_ens~anosmic"]["passed"]                    # betimsel kayma raporlanır
    assert "P3_anosmic_ens~anosmic" not in shifted["criteria"]                               # ama karar vermez


def test_scale_validator_resumes_and_guards(cfg, tmp_path):
    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 2, seed=3, episodes=1, seconds=4.0)
    kw = dict(game="O1a", seed=150, agents=2, trials=2, seconds=4.0, k=2, tau=0.04, verbose=False)
    a = VSC.run_arms(pre, part_dir=tmp_path, key="k1", **kw)
    assert set(a) == set(VSC.ARM_DEFS)
    b = VSC.run_arms(pre, part_dir=tmp_path, key="k1", **kw)                       # hepsi kontrol noktasından
    assert all(np.array_equal(a[k][kk], b[k][kk], equal_nan=True) for k in a for kk in VSC.KEYS)
    for bad in (["--seed", "150"], ["--seed", "250", "--pilot"]):
        with pytest.raises(SystemExit):
            VSC.main(["--pre", "yok.npz", "--game", "O1a", "--out", str(tmp_path / "o"), *bad])
