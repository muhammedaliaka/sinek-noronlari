import numpy as np
import pytest
import torch

from conftest import make_brain, present
from sinek import Creature, World, checkpoint
from sinek.experiments import protocol as P


def test_motor_turns_toward_higher_value_and_flips_for_negative(cfg):
    w = World(cfg.world, 1, seed=0)
    c = Creature(cfg, make_brain(cfg, 1), w)
    c.cfg.motor.wander_sigma, old = 0.0, c.cfg.motor.wander_sigma
    try:
        left = c.motor(torch.tensor([[0.5, 0.1]]))
        right = c.motor(torch.tensor([[0.1, 0.5]]))
        avoid_left = c.motor(torch.tensor([[-0.5, -0.1]]))
        zero = c.motor(torch.tensor([[0.0, 0.0]]))
    finally:
        c.cfg.motor.wander_sigma = old
    assert left > 0 and right < 0           # yüksek değere doğru dön
    assert avoid_left < 0                   # sol daha kötüyse sağa (uzaklaş)
    assert abs(float(zero)) < 1e-6          # öğrenilmiş değer yoksa yönelim yok


def test_random_policy_has_zero_gain(cfg):
    c = P.build(cfg, ["plastic", "random"], seed=0)
    assert float(c.turn_gain[0]) > 0 and float(c.turn_gain[1]) == 0.0
    assert float(c.brain.eta_scale[0]) == 1.0


def test_checkpoint_roundtrip_is_exact(cfg, tmp_path):
    c = P.build(cfg, ["plastic", "frozen"], seed=3)
    c.brain.reset_state(); present(c.brain, cfg, 0, 1.0, 2, seed=3, feed_from=0.4, reward=1.0)
    path = checkpoint.save(c, tmp_path / "ck.npz")
    r = checkpoint.load(path)
    assert torch.equal(r.brain.W, c.brain.W)
    assert torch.equal(r.brain.eta_scale, c.brain.eta_scale) and torch.equal(r.turn_gain, c.turn_gain)
    # davranış birebir aynı
    a = P.choice_test(c, trials=2, seconds=8.0, seed=99)
    b = P.choice_test(r, trials=2, seconds=8.0, seed=99)
    assert np.array_equal(a.n_a, b.n_a) and np.array_equal(a.n_b, b.n_b)


def test_checkpoint_rejects_mismatched_wiring(cfg, tmp_path):
    c = P.build(cfg, ["plastic"], seed=3)
    other = make_brain(cfg, 1, seed=4)
    with pytest.raises(ValueError):
        other.load_state_dict(c.brain.state_dict())


def test_choice_test_shapes_and_counts(cfg):
    c = P.build(cfg, ["plastic", "random", "frozen"], seed=1)
    r = P.choice_test(c, trials=3, seconds=6.0, seed=5)
    assert r.n_a.shape == (3,) and np.all(r.n_a + r.n_b + r.n_none == 3)
    assert np.all((r.choice_rate >= 0) & (r.choice_rate <= 1))


def test_stats_helpers():
    rng = np.random.default_rng(0)
    hi, lo = rng.normal(0.8, 0.05, 30), rng.normal(0.5, 0.05, 30)
    m, ci_lo, ci_hi = P.bootstrap_ci(hi)
    assert ci_lo <= m <= ci_hi and 0.75 < m < 0.85
    assert P.permutation_p(hi, lo, n=2000) < 0.01
    assert P.permutation_p(hi, rng.normal(0.8, 0.05, 30), n=2000) > 0.05
    assert np.isnan(P.bootstrap_ci(np.array([np.nan]))[0])


# ---- Regresyon: test dünyası, canlının eğitim kokularını kullanmalı -----------------
def test_choice_world_uses_the_trained_odor_patterns(cfg):
    """Hata: test dünyası desenleri test tohumundan üretiyordu; 'A' ve 'B' öğrenilen kokular değildi."""
    c = P.build(cfg, ["plastic", "frozen"], seed=1)
    for test_seed in (12346, 5, 99):
        t = P.make_test_creature(c, torch.tensor([0, 1, 1]), test_seed)
        assert torch.equal(t.world.patterns, c.world.patterns)


def test_loaded_checkpoint_keeps_training_odors(cfg, tmp_path):
    c = P.build(cfg, ["plastic"], seed=2)
    r = checkpoint.load(checkpoint.save(c, tmp_path / "ck.npz"), world_seed=777)
    assert torch.equal(r.world.patterns, c.world.patterns)


@pytest.mark.parametrize("seed", [1, 2])
def test_taught_creature_prefers_its_rewarded_odor_in_choice_test(cfg, seed):
    """Davranış testi: A+ödül öğretilmiş canlı, FARKLI test tohumunda A'yı seçmeli."""
    B = 4
    c = P.build(cfg, ["plastic"] * B, seed=seed)
    for _ in range(4):
        c.brain.reset_state()
        present(c.brain, cfg, 0, 1.0, B, seed=seed, feed_from=0.4, reward=1.0)
    r = P.choice_test(c, trials=6, seconds=30.0, seed=424242 + seed)
    pref = r.n_a.sum() / (r.n_a.sum() + r.n_b.sum())
    assert pref > 0.65, f"A tercihi {pref:.2f} (A={r.n_a.sum()}, B={r.n_b.sum()})"
