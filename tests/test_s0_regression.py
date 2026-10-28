"""G0/S0: `Creature` değişiklikleri (noise_gen getattr, reset_episode kwargs) eski `World` davranışını değiştirmez.

Mutlak bit-bit altın değerler makineye bağlıdır (BLAS sırası); bu yüzden test, aynı süreçte iki yolu karşılaştırır:
`noise_gen` tanımsız (eski yol) ve `noise_gen = gen` (takma ad) -> birebir aynı yörünge. Ayrıca eski modda `reset_episode` kipleri çalışır.
"""
import pytest
import torch

from sinek import Config, MushroomBodyBrain, World
from sinek.agent import Creature


def _run(cfg, alias: bool):
    w = World(cfg.world, 4, 5)
    if alias:
        w.noise_gen = w.gen
    c = Creature(cfg, MushroomBodyBrain(cfg.brain, 4, 5, "cpu", cfg.world.dt, cfg.substeps), w)
    c.reset_episode("forage")
    c.run(3.0, learn=True)
    c.reset_episode("choice")
    c.run(3.0, learn=False, stop_when_done=True)
    return w.pos.clone(), w.heading.clone(), c.brain.W.clone()


def test_noise_gen_alias_is_bit_identical(cfg):
    a, b = _run(cfg, False), _run(cfg, True)
    for x, y in zip(a, b):
        assert torch.equal(x, y)


def test_reset_episode_rejects_unknown_mode_and_game_needs_game_world(cfg):
    w = World(cfg.world, 2, 1)
    c = Creature(cfg, MushroomBodyBrain(cfg.brain, 2, 1, "cpu", cfg.world.dt, cfg.substeps), w)
    with pytest.raises(ValueError):
        c.reset_episode("bilinmeyen")
    with pytest.raises(AttributeError):
        c.reset_episode("game")      # eski World'de oyun kipi yok
