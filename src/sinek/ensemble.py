"""Test-zamanı topluluk okuması (ölçek ekseni, yol haritası 3.0): anten başına K bağımsız gürültülü devre kopyası, değerler ortalanır.

`EnsembleBrain`, `ConnectomeBrain`'i (öğrenmesi kapalı) K kez kopyalar: kopyalar AYNI ağırlıkları paylaşır (başlangıçta özdeş W) ama Poisson
gürültüsü bağımsızdır. Beyin arayüzü (`step`, `reset_state`, `gen`, `seed`) değişmez, böylece `Creature` ve oyun dünyaları olduğu gibi çalışır.
Amaç: değer sinyalinin gürültüsü (adım başına SNR ≈ 0,15) oyun başarısını sınırlıyorsa, K ile (yaklaşık √K) yükselmesi gerekir.
K=1 sarmalayıcısı sarılmamış beyinle birebir aynıdır (testli). Öğrenme bu sarmalayıcıda kapalıdır (dondurulmuş okuma).
"""
from __future__ import annotations

import dataclasses

import torch


class EnsembleBrain:
    def __init__(self, brain, k: int, tau_valence: float | None = None):
        """`tau_valence`: yalnız bu topluluğun okuma entegrasyon süresi (sn); None: beyinin kendi değeri. Sarılan beynin yapılandırması değişmez."""
        if k < 1:
            raise ValueError("k >= 1 olmalı")
        self.k, self.B = k, brain.B
        self.inner = brain.select(torch.arange(brain.B).repeat_interleave(k))      # eleman-major: indeks = b*k + j
        if tau_valence is not None:
            self.inner.cfg = dataclasses.replace(self.inner.cfg, tau_valence=float(tau_valence))
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


class PlasticEnsembleBrain(EnsembleBrain):
    """Öğrenen topluluk (geliştirme; GPU devri 3b): K kopya BAĞIMSIZ öğrenir (her kopyanın kendi W'si ve kendi δ'sı), karar için değerler ortalanır.

    `EnsembleBrain`ın aksine öğrenme kapalı değildir: `eta_scale` kopyalara taşınır, `learn` iç beyne iletilir. Kopyalar yalnız Poisson gürültüsü ve ondan doğan
    δ/iz farkları kadar ayrışır; ortalama hem okuma gürültüsünü hem öğrenme gürültüsünü azaltmayı amaçlar. Maliyet ≈K× hesap ve bellek.
    K=1 sarmalayıcısı sarılmamış beyinle öğrenme AÇIKKEN de birebir aynıdır (testli).
    """

    def __init__(self, brain, k: int, tau_valence: float | None = None):
        super().__init__(brain, k, tau_valence)
        self.inner.eta_scale = brain.eta_scale.repeat_interleave(k).clone()

    @property
    def eta_scale(self):
        return self.inner.eta_scale[:: self.k]

    @eta_scale.setter
    def eta_scale(self, v) -> None:
        v = torch.as_tensor(v, dtype=self.inner.eta_scale.dtype, device=self.inner.eta_scale.device)
        self.inner.eta_scale = v.repeat_interleave(self.k).clone()

    @torch.no_grad()
    def step(self, glom, taste, touch, learn: bool = False):
        k = self.k
        v = self.inner.step(glom.repeat_interleave(k, 0), taste.repeat_interleave(k, 0), touch.repeat_interleave(k, 0), learn=learn)
        return v.view(self.B, k, -1).mean(1)
