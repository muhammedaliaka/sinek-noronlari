"""Canlı = beyin + hareket. Dünya ile döngüyü `Creature.step` kurar.

ŞEFFAFLIK: Hazır (öğrenilmemiş) parçalar şunlardır:
  - sabit ileri hız, yeme sırasında durma,
  - "daha yüksek değerli antene doğru dön" eşlemesi (kontrast x kazanç),
  - rastgele gezinme gürültüsü.
Öğrenilen parça yalnızca beynin verdiği değerdir (V): hangi kokuya yaklaşılacağı,
hangisinden kaçınılacağı KC->MBON ağırlıklarından gelir. Başlangıçta V ~ 0'dır,
yani canlının bir koku tercihi yoktur.
"""
from __future__ import annotations

import torch

from .brain import MushroomBodyBrain
from .config import Config
from .world import World


class Creature:
    def __init__(self, cfg: Config, brain: MushroomBodyBrain, world: World):
        self.cfg, self.brain, self.world = cfg, brain, world
        # eleman başına dönüş kazancı: 0 => rastgele politika kontrolü
        self.turn_gain = torch.full((world.B,), cfg.motor.turn_gain, device=world.device)
        self.last_valence = torch.zeros(world.B, 2, device=world.device)

    def reset_episode(self, mode: str) -> None:
        if mode == "forage":
            self.world.reset_forage()
        elif mode == "choice":
            self.world.reset_choice()
        else:
            raise ValueError(mode)
        self.brain.reset_state()

    def motor(self, valence: torch.Tensor) -> torch.Tensor:
        """(B,2) değer -> (B,) dönüş hızı (rad/s). Pozitif = sola."""
        m = self.cfg.motor
        v_l, v_r = valence[:, 0], valence[:, 1]
        contrast = (v_l - v_r) / (v_l.abs() + v_r.abs() + m.contrast_eps)
        noise = m.wander_sigma * torch.randn(
            self.world.B, generator=self.world.gen, device=self.world.device
        ) / self.cfg.world.dt ** 0.5
        return self.turn_gain * contrast + noise

    @torch.no_grad()
    def step(self, learn: bool = True) -> None:
        w = self.world
        glom = w.sense()
        taste, touch = w.taste_touch()
        valence = self.brain.step(glom, taste, touch, learn=learn)
        self.last_valence = valence
        w.step(self.motor(valence), self.cfg.motor.speed)

    def run(self, seconds: float, learn: bool = True, stop_when_done: bool = False) -> int:
        n = int(round(seconds / self.cfg.world.dt))
        for i in range(n):
            self.step(learn=learn)
            if stop_when_done and bool(self.world.done.all()):
                return i + 1
        return n
