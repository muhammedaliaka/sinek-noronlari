import math

import torch

from sinek import World
from sinek.world import odor_patterns


def test_odor_patterns_overlap(cfg):
    pat = odor_patterns(cfg.world, 0)
    assert pat.shape == (2, cfg.world.n_glom)
    assert int(pat[0].sum()) == cfg.world.glom_per_odor
    assert int((pat[0] * pat[1]).sum()) == cfg.world.odor_overlap


def test_sense_range_and_gradient(cfg):
    w = World(cfg.world, 4, seed=0)
    g = w.sense()
    assert g.shape == (4, 2, cfg.world.n_glom)
    assert float(g.min()) >= 0 and float(g.max()) < 1
    # bir kaynağın hemen yanında koku, uzaktakinden güçlüdür
    w.src_pos[:] = torch.tensor([20.0, 20.0])
    w.src_kind[:] = 0
    w.pos[0] = torch.tensor([20.0, 22.0])
    w.pos[1] = torch.tensor([20.0, 38.0])
    g = w.sense()
    assert g[0].sum() > g[1].sum()


def test_contact_rewards_and_respawns(cfg):
    w = World(cfg.world, 2, seed=1)
    w.reset_forage()
    w.src_pos[0, 0] = w.pos[0] + torch.tensor([0.5, 0.0])   # A kaynağı, temas menzilinde
    w.heading[:] = 0.0
    before = w.src_pos[0, 0].clone()
    w.step(torch.zeros(2), 0.0)
    assert w.n_contacts[0, 0] == 1 and w.feed_timer[0] > 0
    assert w.feed_reward[0] == 1.0                           # A ödüllü
    assert not torch.equal(w.src_pos[0, 0], before)          # tüketildi, yeniden doğdu
    taste, touch = w.taste_touch()
    assert taste[0] == 1.0 and touch[0] == 1.0


def test_unrewarded_odor_gives_touch_but_no_taste(cfg):
    w = World(cfg.world, 1, seed=1)
    w.reset_forage()
    b_index = int(torch.nonzero(w.src_kind[0] == 1)[0])
    w.src_pos[0, b_index] = w.pos[0] + torch.tensor([0.5, 0.0])
    w.step(torch.zeros(1), 0.0)
    taste, touch = w.taste_touch()
    assert w.n_contacts[0, 1] == 1 and touch[0] == 1.0 and taste[0] == 0.0


def test_creature_stops_while_eating(cfg):
    w = World(cfg.world, 1, seed=1)
    w.reset_forage()
    w.src_pos[0, 0] = w.pos[0] + torch.tensor([0.5, 0.0])
    w.step(torch.zeros(1), 8.0)
    p = w.pos.clone()
    w.step(torch.zeros(1), 8.0)
    assert torch.equal(p, w.pos)


def test_choice_trial_ends_at_first_contact(cfg):
    w = World(cfg.world, 64, seed=2)
    w.reset_choice()
    # A ve B simetrik ve merkezden eşit uzaklıkta
    c = cfg.world.arena / 2
    da = (w.src_pos[:, 0] - c).norm(dim=-1)
    db = (w.src_pos[:, 1] - c).norm(dim=-1)
    assert torch.allclose(da, db, atol=1e-4) and torch.allclose(da, torch.tensor(cfg.world.choice_distance), atol=1e-4)
    # A'ya doğru yürüt: seçim 0 (A) olmalı
    for _ in range(300):
        d = w.src_pos[:, 0] - w.pos
        target = torch.atan2(d[:, 1], d[:, 0])
        w.heading = target
        w.step(torch.zeros(64), cfg.motor.speed)
    assert bool(w.done.all()) and bool((w.choice == 0).all())


def test_stays_in_arena(cfg):
    w = World(cfg.world, 32, seed=3)
    w.reset_forage()
    for _ in range(2000):
        w.step(5.0 * torch.randn(32), cfg.motor.speed)
    assert float(w.pos.min()) >= 0 and float(w.pos.max()) <= cfg.world.arena


def test_batch_elements_are_independent(cfg):
    w = World(cfg.world, 3, seed=4)
    w.reset_forage()
    p1 = w.pos[1].clone()
    w.step(torch.tensor([1.0, 0.0, 0.0]), 8.0)
    q1 = w.pos[1].clone()
    w2 = World(cfg.world, 3, seed=4)
    w2.reset_forage()
    w2.step(torch.tensor([-3.0, 0.0, 2.0]), 8.0)
    assert torch.allclose(w2.pos[1], q1) and math.isclose(float((q1 - p1).norm()), 8.0 * cfg.world.dt, rel_tol=1e-4)
