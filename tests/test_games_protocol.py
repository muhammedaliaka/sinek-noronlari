"""Oyun protokolü: kol kurulumu, CRN sızıntı denetimi, ön-eğitimli canlıdan kopya (küçük, sentetik beyin)."""
import numpy as np
import torch

from sinek import Config
from sinek.games import protocol as GP
from sinek.games.protocol import ARMS, hits, leak_check, make_game_creature, play, pretrain
from sinek.world import odor_patterns


def _pre(cfg, agents=4):
    return pretrain(cfg, odor_patterns(cfg.world, 3), agents, seed=3, episodes=1, seconds=4.0)


def test_pretrain_balances_roles_and_copies_agents(cfg):
    pre = _pre(cfg)
    assert pre.world.swap.tolist() == [False, False, True, True]
    c = make_game_creature(pre, "O2near", "frozen", [0, 3], trials=4, seed=7)
    assert c.world.B == 8 and c.world.swap.tolist() == [False] * 4 + [True] * 4
    assert float(c.brain.eta_scale.max()) == 0.0 and float(c.turn_gain.min()) == cfg.motor.turn_gain
    r = make_game_creature(pre, "O2near", "random", [0], trials=2, seed=7)
    assert float(r.turn_gain.max()) == 0.0


def test_crn_leak_check_on_pretrained_creatures(cfg):
    pre = _pre(cfg)
    o = play(make_game_creature(pre, "O2near", "frozen", [0, 1, 2, 3], 4, seed=11), 8.0, n_agents=4)
    a = play(make_game_creature(pre, "O2near", "anosmic", [0, 1, 2, 3], 4, seed=11), 8.0, n_agents=4)
    chk = leak_check(o, a)
    assert chk["events_identical"] and chk["violations"] == 0
    assert chk["checked"] < o["slot"].size                         # bazı denemelerde koku alındı (test boş değil)
    assert o["slot"].shape == (4, 4)


def test_reference_arm_beats_blind_in_o1a(cfg):
    pre = _pre(cfg, agents=2)
    ref = play(make_game_creature(pre, "O1a", "reference", [0, 1], 40, seed=5), 25.0, n_agents=2)
    rnd = play(make_game_creature(pre, "O1a", "random", [0, 1], 40, seed=5), 25.0, n_agents=2)
    assert hits(ref).mean() > hits(rnd).mean() + 0.3


def test_arms_table_is_complete():
    assert {"plastic", "frozen", "random", "anosmic", "reference", "naive"} <= set(ARMS)
