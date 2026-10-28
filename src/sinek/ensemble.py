"""Test-zamanı topluluk okuması (ölçek ekseni, yol haritası 3.0): anten başına K bağımsız gürültülü devre kopyası, değerler ortalanır.

`EnsembleBrain`, `ConnectomeBrain`'i (öğrenmesi kapalı) K kez kopyalar: kopyalar AYNI ağırlıkları paylaşır (başlangıçta özdeş W) ama Poisson
gürültüsü bağımsızdır. Beyin arayüzü (`step`, `reset_state`, `gen`, `seed`) değişmez, böylece `Creature` ve oyun dünyaları olduğu gibi çalışır.
Amaç: değer sinyalinin gürültüsü (adım başına SNR ≈ 0,15) oyun başarısını sınırlıyorsa, K ile (yaklaşık √K) yükselmesi gerekir.
K=1 sarmalayıcısı sarılmamış beyinle birebir aynıdır (testli). Öğrenme bu sarmalayıcıda kapalıdır (dondurulmuş okuma).
"""
from __future__ import annotations

import torch


class EnsembleBrain:
    def __init__(self, brain, k: int):
        if k < 1:
            raise ValueError("k >= 1 olmalı")
        self.k, self.B = k, brain.B
        self.inner = brain.select(torch.arange(brain.B).repeat_interleave(k))      # eleman-major: indeks = b*k + j
        self.inner.eta_scale = torch.zeros_like(self.inner.eta_scale)
        self.seed = brain.seed

    @property
    def gen(self):
        return self.inner.gen

    @property
    def eta_scale(self):
        return self.inner.eta_scale[:: self.k]

    @eta_scale.setter
    def eta_scale(self, v) -> None:          # dondurulmuş okuma: öğrenme hep kapalı
        pass

    def reset_state(self) -> None:
        self.inner.reset_state()

    @torch.no_grad()
    def step(self, glom, taste, touch, learn: bool = False):
        k = self.k
        v = self.inner.step(glom.repeat_interleave(k, 0), taste.repeat_interleave(k, 0), touch.repeat_interleave(k, 0), learn=False)
        return v.view(self.B, k, -1).mean(1)
