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


def test_scale_validator_resumes_chunked_zero_effect_and_guards(cfg, tmp_path):
    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 4, seed=3, episodes=1, seconds=4.0)
    kw = dict(game="O1a", seed=150, agents=4, trials=2, seconds=4.0, verbose=False, chunks=2)
    a = VSC.run_arms(pre, k=1, tau=cfg.brain.tau_valence, part_dir=tmp_path, key="k1", **kw)
    assert set(a) == set(VSC.ARM_DEFS) and a["frozen"]["slot"].shape[0] == 4
    assert all(np.array_equal(a["ens"][kk], a["frozen"][kk], equal_nan=True) for kk in VSC.KEYS)     # sıfır-etki: K=1, varsayılan τ → taban kolla birebir aynı
    assert all(np.array_equal(a["anosmic_ens"][kk], a["anosmic"][kk], equal_nan=True) for kk in VSC.KEYS)
    assert len(list(tmp_path.glob("sc_*_c*.npz"))) == len(VSC.ARM_DEFS) * 2                         # kol × parça kontrol noktası
    (tmp_path / "sc_ens_c1.npz").unlink()                                                           # yarım kalmış kol: yalnız eksik parça yeniden koşulur
    b = VSC.run_arms(pre, k=1, tau=cfg.brain.tau_valence, part_dir=tmp_path, key="k1", **kw)
    assert all(np.array_equal(a[k][kk], b[k][kk], equal_nan=True) for k in a for kk in VSC.KEYS)
    # parçalar bağımsız yerleşim alır (aynı tohumla kopyalanmaz): iki parçanın yol uzunlukları özdeş olmamalı
    f = a["anosmic"]["path_len"]
    assert not np.array_equal(f[:2], f[2:])
    with pytest.raises(ValueError):
        VSC.run_arms(pre, k=1, tau=0.04, **{**kw, "chunks": 3})
    for bad in (["--seed", "150"], ["--seed", "250", "--pilot"]):
        with pytest.raises(SystemExit):
            VSC.main(["--pre", "yok.npz", "--game", "O1a", "--out", str(tmp_path / "o"), *bad])


def test_olcek_ozet_verdict_rules_and_table(tmp_path):
    from sinek.experiments import olcek_ozet as OZ
    rng = np.random.default_rng(0)
    thr = Thr(n_boot=500, n_perm=500)

    def fake(gain):
        h = _h(rng, 24, 16, {"reference": 0.97, "anosmic": 0.27, "frozen": 0.5, "anosmic_ens": 0.27, "ens": 0.5 + gain})
        ev = EVALUATORS["SC"](h, thr, {"sizinti_ihlali==0": True, "anosmik_pencerede": True})
        return {"eval": ev, "leak": {"violations": 0, "checked": 5}, "p_hit": {k: float(np.mean(v)) for k, v in h.items()}}

    ok, bad = fake(0.3), fake(0.0)
    assert ok["eval"]["passed"] and not bad["eval"]["passed"]
    allok = {(g, s): ok for g, ss in OZ.GAMES.items() for s in ss}
    assert OZ.verdict(allok)["ölçek"] == "BAŞARILI"
    one_bad = {**allok, ("O1b", 253): bad}
    v = OZ.verdict(one_bad)
    assert v["O1a"] == "BAŞARILI" and v["O1b"] == "BAŞARISIZ" and v["ölçek"] == "BAŞARISIZ"
    missing = {**allok, ("O1b", 253): None}
    v = OZ.verdict(missing)
    assert v["O1b"] == "BEKLİYOR" and v["ölçek"] == "BEKLİYOR"
    missing_and_bad = {**one_bad, ("O1a", 251): None}
    assert OZ.verdict(missing_and_bad)["ölçek"] == "BAŞARISIZ"                  # bir başarısızlık varken eksik koşu hükmü değiştiremez
    assert "BEKLİYOR" in OZ.table(missing) and "P1 ens−frozen" in OZ.table(allok)
