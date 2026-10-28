"""DAN devresi varyantları (src/sinek/brain_dan.py): sıfır-etki regresyonu, kontrol ve kararlılık."""
import numpy as np
import pytest
import torch

from sinek.brain_connectome import ConnectomeBrain
from sinek.brain_dan import DanBrain, DanConfig, build_wiring, degree_preserving
from sinek.config import ConnectomeBrainConfig

torch.set_num_threads(1)


def test_degree_preserving_keeps_degrees_and_weights():
    rng = np.random.default_rng(0)
    w = (rng.random((30, 40)) < 0.2) * rng.integers(1, 9, (30, 40)).astype(float)
    s = degree_preserving(w, np.random.default_rng(1))
    assert ((w > 0).sum(0) == (s > 0).sum(0)).all() and ((w > 0).sum(1) == (s > 0).sum(1)).all()
    assert sorted(w[w > 0]) == sorted(s[s > 0])
    assert (w != s).any()


def test_wiring_shapes_and_signs():
    cfg = ConnectomeBrainConfig()
    a = build_wiring(cfg.data_dir, DanConfig(glu_sign=-1.0))
    b = build_wiring(cfg.data_dir, DanConfig(glu_sign=+1.0))
    assert a["kn"].shape[1] == a["M"].shape[1] == 161 and a["M"].shape[0] == a["L"].shape[0] == 48
    assert np.allclose(a["kn"].sum(0)[a["kn"].sum(0) > 0], 1.0, atol=1e-4)
    assert (a["M"] < 0).any() and (b["M"] > a["M"]).any()        # glutamat işareti M'yi değiştirir
    s = build_wiring(cfg.data_dir, DanConfig(wiring="shuffled", wiring_seed=3))
    assert ((a["M"] != 0).sum(0) == (s["M"] != 0).sum(0)).all()  # derece korunur


def _run(brain, steps=60, reward_from=20, reward_to=40, seed=0):
    g = torch.zeros(brain.B, 2, brain.n_glom)
    g[:, :, :8] = 0.9
    rng = torch.Generator().manual_seed(seed)
    taste, touch = torch.zeros(brain.B), torch.zeros(brain.B)
    for t in range(steps):
        on = reward_from <= t < reward_to
        taste[:] = 1.0 if on else 0.0
        touch[:] = 1.0 if on else 0.0
        brain.step(g, taste, touch, learn=True)
    return brain.W.clone(), brain.valence.clone()


@pytest.mark.parametrize("dcfg", [DanConfig("V0"), DanConfig("V1", g_kc=0.0), DanConfig("V2", g_kc=0.0, g_mbon=0.0, g_lat=0.0),
                                  DanConfig("V3", g_kc=0.0, g_mbon=0.0)])
def test_zero_gain_equals_connectome_brain(dcfg):
    """Sıfır-etki: tüm kazançlar 0 ise (V3 hariç, o zaten elle δ'yı bırakır) W ve değer birebir ConnectomeBrain'dir."""
    cfg = ConnectomeBrainConfig()
    base = ConnectomeBrain(cfg, 2, 5)
    dan = DanBrain(cfg, 2, 5, dcfg=dcfg)
    w0, v0 = _run(base)
    w1, v1 = _run(dan)
    if dcfg.mode == "V3":     # V3 öngörü terimini bırakır: aynı olmak zorunda değil, ama sonlu ve sınırlı olmalı
        assert torch.isfinite(w1).all()
        assert (w1 <= dan.W0 + 1e-6).all() and (w1 >= -1e-6).all()
    else:
        assert torch.equal(w0, w1) and torch.equal(v0, v1)


def test_v1_changes_plasticity_and_stays_bounded():
    cfg = ConnectomeBrainConfig()
    base = ConnectomeBrain(cfg, 2, 5)
    dan = DanBrain(cfg, 2, 5, dcfg=DanConfig("V1", g_kc=10.0))
    w0, _ = _run(base)
    w1, _ = _run(dan)
    assert not torch.equal(w0, w1)
    assert torch.isfinite(w1).all() and (w1 >= -1e-6).all() and (w1 <= dan.W0 + 1e-6).all()
    assert np.isfinite(dan.dan_max)


def test_select_and_expand_keep_class():
    cfg = ConnectomeBrainConfig()
    dan = DanBrain(cfg, 3, 5, dcfg=DanConfig("V2", g_mbon=1.0))
    sub = dan.select([0, 2])
    assert isinstance(sub, DanBrain) and sub.dcfg == dan.dcfg and sub.B == 2
    assert isinstance(dan.expand(2), DanBrain)
