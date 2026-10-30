"""Elle kurulmuş referans karşılaştırıcı ve boş beyin (docs/dort_koku_oyunu_plani.md §3.1).

`ReferenceBrain`: öğrenmeyen, ödüllü kokunun glomerüllerindeki etkinliği toplayıp değer yapan beyin kuklası; aynı `Creature.motor`
kuralıyla birlikte "duyu–motor döngüsü bu alanı çözebilir mi" üst sınırını verir. **Elle yazılmıştır, biyolojik kontrol değildir** (R-11).
`NullBrain`: sıfır değer (yalnız hareket gürültüsü) — kör gezgin / dünya fiziği testleri için.
"""
from __future__ import annotations

import torch

from .world import GameWorld


class ReferenceBrain:
    def __init__(self, world: GameWorld, gain: float = 0.15):
        self.world, self.gain = world, gain

    def reset_state(self) -> None:
        pass

    def step(self, glom: torch.Tensor, taste: torch.Tensor, touch: torch.Tensor, learn: bool = True, vis=None) -> torch.Tensor:
        mask = self.world.reward_mask().unsqueeze(1)                   # (B,1,G)
        return self.gain * (glom * mask).sum(-1)                       # (B,2)


class NullBrain:
    def __init__(self, batch: int, device="cpu"):
        self.B, self.device = batch, torch.device(device)

    def reset_state(self) -> None:
        pass

    def step(self, glom, taste, touch, learn: bool = True, vis=None) -> torch.Tensor:
        return torch.zeros(self.B, 2, device=self.device)
