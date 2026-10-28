"""Rol dengelemesi (Evre 2b): A/B rolü canlı başına koku 0/1 olabilir; sonuçlar rol cinsinden raporlanır."""
import numpy as np
import torch

from sinek import World, checkpoint
from sinek.experiments import protocol as P


def test_set_swap_remaps_rewards_per_role(cfg):
    w = World(cfg.world, 4, seed=0)
    w.set_swap(torch.tensor([False, True, False, True]))
    w.set_rewards(1.0, 0.0)                       # A rolü ödüllü
    assert w.reward_by_odor.tolist() == [[1, 0], [0, 1], [1, 0], [0, 1]]
    w.set_rewards(0.0, 1.0)                       # tersine çevirme: B rolü ödüllü
    assert w.reward_by_odor.tolist() == [[0, 1], [1, 0], [0, 1], [1, 0]]
    w.set_swap(torch.zeros(4, dtype=torch.bool))  # eşleme yeniden uygulanır
    assert w.reward_by_odor.tolist() == [[0, 1]] * 4


def test_default_world_unchanged_by_roles(cfg):
    w = World(cfg.world, 3, seed=0)
    assert not bool(w.swap.any()) and w.reward_by_odor[:, 0].tolist() == [1.0] * 3


def test_choice_counts_are_reported_by_role(cfg):
    """Aynı canlı + aynı rastgele sayılar: swap yalnızca etiketi çevirir (A <-> B sayıları yer değiştirir)."""
    c = P.build(cfg, ["random", "random"], seed=1)
    c0 = P.choice_test(c, trials=6, seconds=10.0, seed=5)
    c.world.set_swap(torch.tensor([True, True]))
    c1 = P.choice_test(c, trials=6, seconds=10.0, seed=5)
    assert np.array_equal(c0.n_a, c1.n_b) and np.array_equal(c0.n_b, c1.n_a)
    c.world.set_swap(torch.tensor([True, False]))
    c2 = P.choice_test(c, trials=6, seconds=10.0, seed=5)
    assert c2.n_a[0] == c0.n_b[0] and c2.n_a[1] == c0.n_a[1]


def test_checkpoint_keeps_swap_and_behaviour(cfg, tmp_path):
    c = P.build(cfg, ["plastic", "plastic", "frozen", "frozen"], seed=3)
    c.world.set_swap(torch.tensor([False, True, False, True]))
    path = checkpoint.save(c, tmp_path / "ck.npz")
    r = checkpoint.load(path)
    assert torch.equal(r.world.swap, c.world.swap)
    a = P.choice_test(c, trials=2, seconds=8.0, seed=99)
    b = P.choice_test(r, trials=2, seconds=8.0, seed=99)
    assert np.array_equal(a.n_a, b.n_a) and np.array_equal(a.n_b, b.n_b)


def test_swap_mask_is_balanced_and_requires_even_agents():
    import pytest
    from sinek.experiments.evre1 import _swap_mask

    m = _swap_mask(4, 3, True).reshape(3, 4)
    assert m.sum(1).tolist() == [2, 2, 2] and not m[:, :2].any() and m[:, 2:].all()
    assert not _swap_mask(5, 3, False).any()
    with pytest.raises(ValueError):
        _swap_mask(5, 3, True)
