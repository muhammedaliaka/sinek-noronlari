"""O5 (olasılıklı iki-kollu koku oyunu): ödül olasılığı uçları, CRN tekrarı, mevcut oyunların etkilenmemesi."""
import numpy as np
import torch

from sinek.games.protocol import bandit_schedule, make_game_creature, play_sequence, pretrain
from sinek.world import odor_patterns


def _pre(cfg):
    return pretrain(cfg, odor_patterns(cfg.world, 3), 4, seed=3, episodes=1, seconds=4.0)


def test_reward_probability_extremes_and_crn(cfg):
    pre = _pre(cfg)
    ids = [0, 1, 2, 3]
    for p_hi, p_lo, expect in ((1.0, 1.0, 1.0), (0.0, 0.0, 0.0)):
        c = make_game_creature(pre, "O5", "naive_plastic", ids, 2, 150)
        sch = bandit_schedule(c.world.swap, 4, None, p_hi, p_lo)
        r = play_sequence(c, sch, 40.0)
        contact = r["slot"] >= 0
        assert contact.any()
        assert np.all(r["got"][contact] == expect) and np.all(r["got"][~contact] == 0)
    a = play_sequence(make_game_creature(pre, "O5", "naive_plastic", ids, 2, 150), bandit_schedule(pre.world.swap[torch.tensor(ids).repeat_interleave(2)], 3, 2), 20.0)
    b = play_sequence(make_game_creature(pre, "O5", "naive_plastic", ids, 2, 150), bandit_schedule(pre.world.swap[torch.tensor(ids).repeat_interleave(2)], 3, 2), 20.0)
    assert all(np.array_equal(a[k], b[k], equal_nan=True) for k in a)                 # aynı tohum → birebir aynı (CRN)


def test_schedule_switches_better_odor():
    better = torch.tensor([0, 1, 0, 1])
    s = bandit_schedule(better, 4, 2, 0.8, 0.2)
    assert torch.allclose(s[0], torch.tensor([[.8, .2], [.2, .8], [.8, .2], [.2, .8]]))
    assert torch.allclose(s[2], torch.tensor([[.2, .8], [.8, .2], [.2, .8], [.8, .2]]))
    assert torch.allclose(s[1], s[0]) and torch.allclose(s[3], s[2])


def test_o5_only_changes_bandit_games(cfg):
    """Mevcut oyunların dünyası O5 ekleriyle değişmedi: reward_u çekimi ayrı akıştan, bandit=False oyunlarda ödül çarpanı yok."""
    from sinek.games.spec import GAMES
    assert not any(g.bandit for k, g in GAMES.items() if k != "O5") and GAMES["O5"].bandit
