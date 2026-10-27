import numpy as np
import torch

from conftest import make_brain, present, probe


def test_neuron_count_in_phase1_range(cfg):
    n = make_brain(cfg, 1).n_neurons()
    assert 1000 <= n <= 5000


def test_kc_code_is_sparse(cfg):
    b = make_brain(cfg, 2)
    present(b, cfg, 0, 1.0, 2, learn=False)
    # her 2 ms'lik adımda KC'lerin yüzde 1'inden azı ateşler
    assert 0.0 < float(b.kc_frac.mean()) < 0.01


def test_naive_brain_has_no_preference(cfg):
    b = make_brain(cfg, 4)
    va = probe(b, cfg, 0, 4)
    vb = probe(b, cfg, 1, 4)
    assert float(va.abs().max()) < 0.08 and float(vb.abs().max()) < 0.08


def test_pairing_teaches_odor_specific_value(cfg):
    b = make_brain(cfg, 4)
    for _ in range(4):
        b.reset_state()
        present(b, cfg, 0, 1.0, 4, feed_from=0.4, reward=1.0)
    va, vb = probe(b, cfg, 0, 4), probe(b, cfg, 1, 4)
    assert float(va.mean()) > 0.25
    assert float(va.mean()) > 3 * float(vb.mean().abs()) + 0.1   # B'ye genelleme küçük


def test_punishment_teaches_avoidance(cfg):
    b = make_brain(cfg, 4)
    for _ in range(4):
        b.reset_state()
        present(b, cfg, 0, 1.0, 4, feed_from=0.4, reward=-1.0)
    assert float(probe(b, cfg, 0, 4).mean()) < -0.15


def test_extinction_when_reward_removed(cfg):
    b = make_brain(cfg, 4)
    for _ in range(4):
        b.reset_state()
        present(b, cfg, 0, 1.0, 4, feed_from=0.4, reward=1.0)
    learned = float(probe(b, cfg, 0, 4).mean())
    for _ in range(4):                       # temas var, ödül yok
        b.reset_state()
        present(b, cfg, 0, 1.0, 4, feed_from=0.4, reward=0.0)
    assert float(probe(b, cfg, 0, 4).mean()) < 0.5 * learned


def test_reversal_flips_preference(cfg):
    b = make_brain(cfg, 4)
    for _ in range(4):
        b.reset_state(); present(b, cfg, 0, 1.0, 4, feed_from=0.4, reward=1.0)
    for _ in range(6):
        b.reset_state(); present(b, cfg, 0, 1.0, 4, feed_from=0.4, reward=0.0)
        b.reset_state(); present(b, cfg, 1, 1.0, 4, feed_from=0.4, reward=1.0)
    assert float(probe(b, cfg, 1, 4).mean()) > float(probe(b, cfg, 0, 4).mean()) + 0.15


def test_no_learning_without_contact(cfg):
    b = make_brain(cfg, 2)
    w0 = b.W.clone()
    present(b, cfg, 0, 2.0, 2, feed_from=None, learn=True)     # koku var, ödül/temas yok
    assert torch.allclose(b.W, w0)


def test_frozen_agent_does_not_change_and_plastic_does(cfg):
    b = make_brain(cfg, 2)
    b.eta_scale = torch.tensor([1.0, 0.0])
    w0 = b.W.view(2, 2, -1, 2).clone()
    b.reset_state(); present(b, cfg, 0, 1.0, 2, feed_from=0.4, reward=1.0)
    w1 = b.W.view(2, 2, -1, 2)
    assert not torch.allclose(w1[0], w0[0]) and torch.allclose(w1[1], w0[1])


def test_weights_stay_bounded(cfg):
    b = make_brain(cfg, 2)
    for _ in range(10):
        b.reset_state(); present(b, cfg, 0, 1.0, 2, feed_from=0.2, reward=1.0)
    assert float(b.W.min()) >= 0.0 and float(b.W.max()) <= cfg.brain.w_max


def test_deterministic_given_seed(cfg):
    runs = []
    for _ in range(2):
        b = make_brain(cfg, 2, seed=5)
        b.reset_state(); present(b, cfg, 0, 0.6, 2, feed_from=0.2, reward=1.0)
        runs.append(b.W.clone())
    assert torch.equal(runs[0], runs[1])


def test_expand_and_select_keep_weights(cfg):
    b = make_brain(cfg, 3)
    b.reset_state(); present(b, cfg, 0, 0.6, 3, feed_from=0.2, reward=1.0)
    e = b.expand(2)
    assert e.B == 6
    W = b.W.view(3, 2, -1, 2); We = e.W.view(6, 2, -1, 2)
    assert torch.equal(We[0], W[0]) and torch.equal(We[1], W[0]) and torch.equal(We[4], W[2])
