"""Test-zamanı topluluk okuması (src/sinek/ensemble.py): K=1 sıfır-etki ve K>1 ortalama davranışı."""
import torch

from sinek.brain_connectome import ConnectomeBrain
from sinek.config import ConnectomeBrainConfig
from sinek.ensemble import EnsembleBrain

torch.set_num_threads(1)


def _inputs(b, n_glom, steps=30):
    g = torch.zeros(b, 2, n_glom)
    g[:, :, :8] = torch.tensor([0.6, 0.9])[None, :, None]
    z = torch.zeros(b)
    return g, z, steps


def test_k1_is_identical_to_unwrapped():
    cfg = ConnectomeBrainConfig()
    base = ConnectomeBrain(cfg, 3, 9)
    ens = EnsembleBrain(ConnectomeBrain(cfg, 3, 9), 1)
    g, z, steps = _inputs(3, base.n_glom)
    base.gen.manual_seed(5); ens.gen.manual_seed(5)
    for _ in range(steps):
        v0 = base.step(g, z, z, learn=False)
        v1 = ens.step(g, z, z)
        assert torch.equal(v0, v1)


def test_k_copies_average_independent_noise():
    cfg = ConnectomeBrainConfig()
    b = ConnectomeBrain(cfg, 2, 9)
    ens = EnsembleBrain(b, 4)
    g, z, steps = _inputs(2, b.n_glom)
    ens.gen.manual_seed(1)
    for _ in range(steps):
        v = ens.step(g, z, z)
    assert v.shape == (2, 2) and torch.isfinite(v).all()
    inner = ens.inner.valence.view(2, 4, 2)
    assert torch.allclose(v, inner.mean(1), atol=1e-6)
    assert inner[:, 0].ne(inner[:, 1]).any()          # kopyalar bağımsız gürültü görür (aynı W, farklı Poisson akışı)
    assert float(ens.inner.eta_scale.abs().sum()) == 0.0   # öğrenme kapalı


def test_ensemble_does_not_modify_source_weights():
    cfg = ConnectomeBrainConfig()
    b = ConnectomeBrain(cfg, 2, 9)
    w = b.W.clone()
    ens = EnsembleBrain(b, 2)
    g, z, steps = _inputs(2, b.n_glom, 10)
    for _ in range(steps):
        ens.step(g, z, z, learn=True)                 # learn istenmiş olsa bile kapalı
    assert torch.equal(b.W, w)
    iw = ens.inner.W.view(4, 2, b.n_kc, b.n_mbon)
    assert torch.equal(iw[1], w.view(2, 2, b.n_kc, b.n_mbon)[0]) and torch.equal(iw[2], w.view(2, 2, b.n_kc, b.n_mbon)[1])


def test_tau_override_is_local_and_none_is_noop():
    cfg = ConnectomeBrainConfig()
    b = ConnectomeBrain(cfg, 2, 9)
    ens = EnsembleBrain(b, 2, tau_valence=0.04)
    assert ens.inner.cfg.tau_valence == 0.04
    assert b.cfg.tau_valence == cfg.tau_valence == 0.15          # sarılan beynin yapılandırması değişmez
    same = EnsembleBrain(ConnectomeBrain(cfg, 2, 9), 2, tau_valence=None)
    assert same.inner.cfg.tau_valence == 0.15
    g, z, steps = _inputs(2, b.n_glom)
    ens.gen.manual_seed(3); same.gen.manual_seed(3)
    va = vb = None
    for _ in range(steps):
        va, vb = ens.step(g, z, z), same.step(g, z, z)
    assert not torch.equal(va, vb)                               # kısa τ değeri farklı kılar (sıfır-etki değil: bilinen etki)


def test_plastic_k1_identical_to_unwrapped_while_learning():
    from sinek.ensemble import PlasticEnsembleBrain
    cfg = ConnectomeBrainConfig()
    base = ConnectomeBrain(cfg, 3, 9)
    ens = PlasticEnsembleBrain(ConnectomeBrain(cfg, 3, 9), 1)
    g, z, steps = _inputs(3, base.n_glom)
    taste, touch = torch.ones(3), torch.ones(3)                               # tatlı ödül + temas kapısı
    base.gen.manual_seed(5); ens.gen.manual_seed(5)
    for _ in range(steps):
        v0 = base.step(g, taste, touch, learn=True)
        v1 = ens.step(g, taste, touch, learn=True)
        assert torch.equal(v0, v1)
    assert torch.equal(base.W, ens.inner.W) and not torch.equal(base.W, ConnectomeBrain(cfg, 3, 9).W)   # öğrendi (W değişti) ve birebir aynı


def test_plastic_k_copies_learn_independently_and_scale_passes_through():
    from sinek.ensemble import PlasticEnsembleBrain
    cfg = ConnectomeBrainConfig()
    b = ConnectomeBrain(cfg, 2, 9)
    w0 = b.W.clone()
    ens = PlasticEnsembleBrain(b, 3)
    ens.eta_scale = torch.tensor([1.0, 0.0])                                  # canlı 0 öğrenir, canlı 1 öğrenmez
    assert ens.eta_scale.tolist() == [1.0, 0.0] and ens.inner.eta_scale.tolist() == [1.0] * 3 + [0.0] * 3
    g, z, steps = _inputs(2, b.n_glom)
    taste, touch = torch.ones(2), torch.ones(2)
    ens.gen.manual_seed(2)
    for _ in range(steps):
        v = ens.step(g, taste, touch, learn=True)
    assert v.shape == (2, 2) and torch.isfinite(v).all()
    iw = ens.inner.W.view(2, 3, 2, b.n_kc, b.n_mbon)                           # (canlı, kopya, yarımküre, KC, MBON)
    assert not torch.equal(iw[0, 0], iw[0, 1])                                 # öğrenen kopyalar bağımsız gürültüyle ayrıştı
    assert torch.equal(iw[1, 0], w0.view(2, 2, b.n_kc, b.n_mbon)[1]) and torch.equal(iw[1, 2], iw[1, 0])   # eta_scale=0: hiç değişmedi
    assert torch.equal(b.W, w0)                                                # kaynak beyin bozulmadı
