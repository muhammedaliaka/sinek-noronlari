"""O5 doğrulayıcısı: değerlendirici (sıfır-etki / bilinen etki / yalnız-yaklaşma artefaktı), parçalı devam, sıfır-etki (öğrenme ölçeği 0 ⇒ frozen), tohum koruması."""
import numpy as np
import pytest

from sinek.experiments import odor_validate_o5 as V5
from sinek.experiments.odor_eval import EVALUATORS, Thr
from sinek.experiments.power_odor import O5_PILOT, sim_o5
from sinek.games.protocol import pretrain
from sinek.world import odor_patterns


def test_eval_o5_zero_known_and_approach_only():
    rng = np.random.default_rng(0)
    thr = Thr(delta=0.10, ref_min=0.60, n_boot=800, n_perm=800)
    fr = O5_PILOT["frozen"][0]
    ref = O5_PILOT["reference"]
    def rate(spec, n=60):
        return float(np.mean([EVALUATORS["O5"](sim_o5(rng, spec, 48), thr)["passed"] for _ in range(n)]))
    # yanlış-pozitif oranı P3'ün nominal boyutuna (α=0,01) bağlıdır: 400 benzetimde yalnız-yaklaşma artefaktı 3/400 geçti (hepsi P3 yanlış-pozitifi), 0 değil
    assert rate({"plastic": [fr] * 4, "frozen": [fr] * 4, "reference": ref}) <= 0.05                                 # sıfır etki
    assert rate({"plastic": O5_PILOT["plastic"], "frozen": [fr] * 4, "reference": ref}) >= 0.9                         # beklenen etki
    approach = [(pc, fr[1]) for pc, _ in O5_PILOT["plastic"]]
    assert rate({"plastic": approach, "frozen": [fr] * 4, "reference": ref}) <= 0.05                                  # yalnız yaklaşma → P3 yakalar (P1/P2 tek başına 0,6-0,8 geçer)


def test_validator_chunked_resume_zero_effect_and_guards(cfg, tmp_path):
    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 4, seed=3, episodes=1, seconds=4.0)
    kw = dict(seed=150, agents=4, copies=2, episodes=4, switch=2, seconds=20.0, p_hi=0.8, p_lo=0.2, chunks=2, verbose=False)
    a = V5.run_arms(pre, plastic_scale=0.0, part_dir=tmp_path, key="k", **kw)
    assert set(a) == set(V5.ARM_DEFS) and a["frozen"]["slot"].shape == (4, 8)
    assert all(np.array_equal(a["plastic"][k], a["frozen"][k]) for k in V5.KEYS)                                       # öğrenme ölçeği 0 ⇒ frozen ile birebir aynı
    assert len(list(tmp_path.glob("o5_*_c*.npz"))) == 3 * 2
    (tmp_path / "o5_reference_c1.npz").unlink()
    b = V5.run_arms(pre, plastic_scale=0.0, part_dir=tmp_path, key="k", **kw)
    assert all(np.array_equal(a[k][kk], b[k][kk]) for k in a for kk in V5.KEYS)
    assert V5.blocks_for(40, 20) == V5.O5_BLOCKS and V5.blocks_for(8, 4) == ((2, 4), (6, 8))
    h = V5.to_h(a)
    assert h["plastic"].shape == (8, 4) and set(h["net_plastic"].ravel()) <= {-1, 0, 1}
    for bad in (["--seed", "150"], ["--seed", "260", "--pilot"]):
        with pytest.raises(SystemExit):
            V5.main(["--pre", "yok.npz", "--out", str(tmp_path / "o"), *bad])
