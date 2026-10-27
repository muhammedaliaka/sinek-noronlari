"""Evre 2 beyni (gerçek mantar cismi bağlantısı): seyreklik, öğrenme, bölmeye özgü baskılanma, bellek."""
import numpy as np
import pytest
import torch

from sinek import Config, checkpoint
from sinek.brains import make_brain
from sinek.connectome import mbmodel
from sinek.experiments import protocol as P
from sinek.world import odor_patterns

try:
    mbmodel.resolve_dir(mbmodel.DEFAULT_DIR)
except FileNotFoundError:           # pragma: no cover
    pytest.skip("data/processed bulunamadı", allow_module_level=True)

torch.set_num_threads(2)


@pytest.fixture(scope="module")
def ccfg() -> Config:
    return mbmodel.connectome_config()


@pytest.fixture(scope="module")
def pat(ccfg):
    return odor_patterns(ccfg.world, 5000)


def present(brain, ccfg, odor_vec, secs, reward=None, learn=True, side=None):
    """Sabit koku; `reward` verilirse (0/1) tat+temas uygulanır. `side`: 0/1 ise yalnız o antene koku."""
    B = brain.B
    g = odor_vec.view(1, 1, -1).expand(B, 2, -1).clone()
    if side is not None:
        g[:, 1 - side] = 0
    z, o = torch.zeros(B), torch.ones(B)
    taste = z if reward is None else reward * o
    touch = z if reward is None else o
    vs = []
    for _ in range(int(secs / ccfg.world.dt)):
        brain.step(g, taste, touch, learn=learn)
        vs.append(brain.valence.view(B, 2).mean(1).clone())
    return torch.stack(vs[len(vs) // 2:]).mean(0)


def probe(brain, ccfg, odor_vec):
    brain.reset_state()
    return present(brain, ccfg, odor_vec, 1.0, learn=False).mean().item()


def teach(brain, ccfg, odor_vec, reward, secs=5.0):
    brain.reset_state()
    present(brain, ccfg, odor_vec, secs, reward=reward, learn=True)


def fresh(ccfg, batch=2, seed=0):
    return make_brain(ccfg, batch, seed)


def test_config_roundtrip_and_backward_compat(ccfg):
    r = Config.from_dict(ccfg.to_dict())
    assert r.brain_kind == "connectome" and r.cbrain == ccfg.cbrain and r.world == ccfg.world
    old = Config().to_dict()
    for k in ("cbrain", "brain_kind"):
        old.pop(k)                                    # Evre 1 zamanında yazılmış yapılandırma
    assert Config.from_dict(old).brain_kind == "synthetic"


def test_brain_uses_real_wiring_sizes(ccfg):
    b = fresh(ccfg)
    d = b.data
    assert (b.n_pn, b.n_kc, b.n_mbon, b.n_dan) == (123, 2045, 48, 161)
    assert b.W.shape == (4, 2045, 48)
    assert torch.equal(b.W[0], b.W0) and (b.W0[torch.as_tensor(d.kc_mbon == 0)] == 0).all()
    assert b.n_neurons() == 2 * (123 + 2045 + 1 + 48 + 161) + 3 * ccfg.cbrain.n_grn


def test_kc_code_is_sparse_and_driven_by_odor(ccfg, pat):
    b = fresh(ccfg)
    b.reset_state()
    g0 = torch.zeros(2, 2, ccfg.world.n_glom)
    z = torch.zeros(2)
    for _ in range(50):
        b.step(g0, z, z, learn=False)
    spont = b.kc_frac.mean().item()
    gA = pat[0].view(1, 1, -1).expand(2, 2, -1).contiguous()
    fr = []
    for _ in range(50):
        b.step(gA, z, z, learn=False)
        fr.append(b.kc_frac.mean().item())
    odor = float(np.mean(fr))
    assert odor > 10 * max(spont, 1e-5)               # koku KC'leri sürer
    assert odor < 0.02                                # alt adım başına KC'lerin <%2'si: seyrek
    assert abs(b.valence.mean().item()) < 0.5


def test_pairing_teaches_a_specific_odor_value(ccfg, pat):
    b = fresh(ccfg)
    a, o = pat[0], pat[1]
    v0 = probe(b, ccfg, a) - probe(b, ccfg, o)
    teach(b, ccfg, a, reward=1.0)
    va, vb = probe(b, ccfg, a), probe(b, ccfg, o)
    assert va - vb > v0 + 0.1                          # A, B'den belirgin daha değerli
    assert va > 0.1


def test_extinction_and_reversal(ccfg, pat):
    b = fresh(ccfg)
    a, o = pat[0], pat[1]
    teach(b, ccfg, a, 1.0)
    learned = probe(b, ccfg, a)
    for _ in range(3):
        teach(b, ccfg, a, 0.0)                         # ödülsüz temas: silinme
    assert probe(b, ccfg, a) < 0.5 * learned
    for _ in range(2):
        teach(b, ccfg, o, 1.0)                         # ödül B'ye taşındı
    assert probe(b, ccfg, o) > probe(b, ccfg, a)


def test_frozen_condition_changes_nothing(ccfg, pat):
    b = fresh(ccfg)
    b.eta_scale = torch.zeros(b.B)
    w = b.W.clone()
    teach(b, ccfg, pat[0], 1.0, secs=3.0)
    assert torch.equal(b.W, w)


def test_weights_only_fall_and_respect_the_wiring(ccfg, pat):
    b = fresh(ccfg)
    teach(b, ccfg, pat[0], 1.0)
    teach(b, ccfg, pat[0], 0.0)
    assert (b.W >= 0).all() and (b.W <= b.W0 + 1e-6).all()
    assert (b.W[:, torch.as_tensor(b.data.kc_mbon == 0)] == 0).all()     # olmayan sinaps oluşmaz
    assert (b.W < b.W0 - 1e-4).any()


def test_depression_is_compartment_specific(ccfg, pat):
    """Ödül (PAM) yalnız PAM bölmesindeki (kaçın sınıfı) MBON'ların KC girdisini baskılar."""
    b = fresh(ccfg)
    teach(b, ccfg, pat[0], 1.0)
    rel = (1 - b.W.sum(1) / b.W0.sum(0).unsqueeze(0)).mean(0).numpy()     # MBON başına bağıl kayıp
    u = b.data.mbon_u
    assert rel[u < -0.9].mean() > 5 * max(rel[u > 0.9].mean(), 1e-4)


def test_omission_depresses_approach_compartments(ccfg, pat):
    """Beklenen ödül gelmeyince (delta<0) PPL1 bölmesindeki (yaklaş sınıfı) MBON'lar baskılanır."""
    b = fresh(ccfg)
    teach(b, ccfg, pat[0], 1.0)
    before = b.W.sum(1).clone()
    teach(b, ccfg, pat[0], 0.0)
    drop = (1 - b.W.sum(1) / before).mean(0).numpy()
    u = b.data.mbon_u
    assert drop[u > 0.9].mean() > 5 * max(drop[u < -0.9].mean(), 1e-4)


def test_hemispheres_learn_independently(ccfg, pat):
    b = fresh(ccfg, batch=1)
    b.reset_state()
    present(b, ccfg, pat[0], 4.0, reward=1.0, learn=True, side=0)        # yalnız sol anten
    W = b.W.view(1, 2, b.n_kc, b.n_mbon)
    loss = [float(1 - W[0, h].sum() / b.W0.sum()) for h in (0, 1)]
    assert loss[0] > 0.01 and loss[0] > 4 * loss[1]       # koku almayan yarımküre yalnızca kendiliğinden KC etkinliğinden (çok daha az) öğrenir


def test_select_expand_and_state_dict(ccfg, pat):
    b = fresh(ccfg, batch=3)
    b.eta_scale = torch.tensor([1.0, 0.0, 1.0])
    teach(b, ccfg, pat[0], 1.0, secs=3.0)
    s = b.select([2, 0])
    Wb = b.W.view(3, 2, b.n_kc, b.n_mbon)
    assert torch.equal(s.W.view(2, 2, b.n_kc, b.n_mbon), Wb[[2, 0]]) and s.eta_scale.tolist() == [1.0, 1.0]
    e = b.expand(2)
    assert e.B == 6 and torch.equal(e.W.view(6, 2, b.n_kc, b.n_mbon)[2:4], Wb[[1, 1]])
    r = fresh(ccfg, batch=3)
    r.load_state_dict(b.state_dict())
    assert torch.equal(r.W, b.W)
    bad = b.state_dict(); bad["kc_ids"] = bad["kc_ids"].flip(0)
    with pytest.raises(ValueError):
        r.load_state_dict(bad)


def test_checkpoint_roundtrip_keeps_memory_and_odors(ccfg, pat, tmp_path):
    c = P.build(ccfg, ["plastic", "frozen"], seed=3, patterns=pat)
    teach(c.brain, ccfg, pat[0], 1.0, secs=3.0)
    path = checkpoint.save(c, tmp_path / "ck.npz")
    r = checkpoint.load(path)
    assert r.cfg.brain_kind == "connectome" and torch.equal(r.brain.W, c.brain.W)
    assert torch.equal(r.world.patterns, pat) and torch.equal(r.brain.eta_scale, c.brain.eta_scale)
    a = P.choice_test(c, trials=2, seconds=6.0, seed=99)
    b = P.choice_test(r, trials=2, seconds=6.0, seed=99)
    assert np.array_equal(a.n_a, b.n_a) and np.array_equal(a.n_b, b.n_b)


def test_creature_runs_in_the_world(ccfg, pat):
    c = P.build(ccfg, ["plastic", "random"], seed=1, patterns=pat)
    c.reset_episode("forage")
    c.run(2.0, learn=True)
    assert torch.isfinite(c.world.pos).all() and torch.isfinite(c.last_valence).all()


def test_class_shuffle_control_changes_only_the_readout(ccfg, pat):
    import copy

    real = fresh(ccfg)
    c2 = copy.deepcopy(ccfg)
    c2.cbrain.class_shuffle_seed = 1
    shuf = make_brain(c2, 2, 0)
    assert torch.equal(real.dan_mbon, shuf.dan_mbon) and torch.equal(real.W0, shuf.W0)   # bölme eşlemesi ve bağlantı aynı
    assert not torch.equal(real.cls_w, shuf.cls_w)
    gain = []
    for b in (real, shuf):
        teach(b, ccfg, pat[0], 1.0)
        gain.append(probe(b, ccfg, pat[0]) - probe(b, ccfg, pat[1]))
    assert gain[0] > gain[1]            # gerçek bölme-sınıf yapısı karıştırılmışa göre daha iyi öğrenir
