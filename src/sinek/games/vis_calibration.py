"""Görsel nötrlük kalibrasyonu (E-17, K-051): eğitimsiz ağın görsel girdiye verdiği ortalama değer (V) sıfır-girdideki değere eşit olsun.

Neden: bağlantıdan gelen KC->MBON sinapsları görsel KC'leri (VPN girdili γd, α/β-p) büyük ölçüde 'kaçın' sınıfı MBON'lara bağlar ve `class_balance` yalnız
koku için kalibre edildi; kalibrasyonsuz eğitimsiz ağda görsel girdi V'yi −0,2…−0,5 yapar (koku kaynaklı V ≈ ±0,1) → yaratık görsel kaynaktan kaçar, hiç temas
etmez, hiç öğrenemez (O6b ilk pilot: temas-yok 1,00). Kalibrasyon KOKU için zaten yapılan `calibrate_balance` ile aynı pratiktir ve ÖNCEDEN SABİTLENMİŞ ölçüte bağlıdır:
  ölçüt: iki görsel desen X ve Y'nin ortalaması, tipik girdi düzeyi 0,6, iki gözde de: |V_ort(X,Y) − V(girdi yok)| ≤ tol (0,01 V).
  yöntem: 'kaçın' sınıfı MBON sinapslarına (VPN girdili KC'lerden) çarpan κ ∈ (0,1]; V(κ), κ ile tekdüze azalan; ikili arama.
Görev bilgisi (hangi desen ödül/ısı) kullanılmaz; X ile Y arasındaki kalan fark gerçek innate fark olarak kalır (rol dengelemesi `vis_swap` ile dengelenir).
"""
from __future__ import annotations

import dataclasses

import torch

from ..brain_connectome import ConnectomeBrain
from .world import vis_patterns

_CACHE: dict = {}


def _mean_v(cbrain_cfg, level: float, n: int, steps: int, seed: int, with_vis: bool) -> float:
    b = ConnectomeBrain(cbrain_cfg, n, seed)
    z, g = torch.zeros(n), torch.zeros(n, 2, b.n_glom)
    vp = vis_patterns(cbrain_cfg.n_vis_feat)
    out = []
    for name in ("X", "Y"):
        b.reset_state()
        p = vp[0 if name == "X" else 1]
        v = (p * level).expand(n, 2, -1).contiguous() if with_vis else torch.zeros(n, 2, cbrain_cfg.n_vis_feat)
        vs = []
        for t in range(steps):
            val = b.step(g, z, z, learn=False, vis=v)
            if t >= steps // 2:
                vs.append(val.clone())
        out.append(torch.stack(vs).mean().item())
    return sum(out) / 2


def neutral_scale(cbrain_cfg, level: float = 0.6, tol: float = 0.01, n: int = 64, steps: int = 40, seed: int = 12345, iters: int = 14) -> float:
    """κ: 'kaçın' sınıfı görsel-KC->MBON çarpanı; ikili arama, sonuç (yapılandırma → κ) önbelleğe alınır."""
    key = (cbrain_cfg.data_dir, cbrain_cfg.n_vis_feat, cbrain_cfg.vis_gain, cbrain_cfg.vis_tuning_seed, cbrain_cfg.vis_tuning_density, cbrain_cfg.vis_kc_gain, cbrain_cfg.vis_innate_flat, level, cbrain_cfg.class_balance)
    if key in _CACHE:
        return _CACHE[key]
    base = dataclasses.replace(cbrain_cfg, vis_avoid_scale=1.0)
    lo, hi = 0.0, 1.0

    def f(k: float) -> float:                            # ölçüt AYNI κ'da: V(görsel girdi) − V(girdi yok) (VPN taban ateşlemesi de κ'dan etkilenir; E-19)
        c = dataclasses.replace(base, vis_avoid_scale=k)
        return _mean_v(c, level, n, steps, seed, with_vis=True) - _mean_v(c, level, n, steps, seed, with_vis=False)
    if f(1.0) >= -tol:                                   # zaten nötr ya da pozitif
        _CACHE[key] = 1.0
        return 1.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        if f(mid) < 0:                                   # V(κ) κ ile AZALIR (κ küçük ⇒ daha az kaçınma): V hâlâ sıfırın altındaysa κ'yi küçült
            hi = mid
        else:
            lo = mid
    k = (lo + hi) / 2
    _CACHE[key] = k
    return k
