"""Oyun yerleşimleri: başlangıç, hedef, decoy, iz köşeleri (docs/dort_koku_oyunu_plani.md §2.6).

Yerleşimler AYNA ÇİFTLERİ halinde üretilir: eleman 2k özgün, 2k+1 onun x→L−x aynasıdır (yön π−yön). Böylece sabit yön/konum kazancı
(duvar yansımasının gizli işaret olması dahil, Z-04) paired analizde dengelenir. Rastgelelik yalnız `gen` (layout_gen) akışından gelir.
"""
from __future__ import annotations

import math

import torch

from ..config import WorldConfig
from .spec import GameSpec

FAR = -1000.0   # etkin olmayan yuvanın konumu (temas/alan hesabına girmez)


def _unif(gen, n: int, lo: float, hi: float, device) -> torch.Tensor:
    return lo + (hi - lo) * torch.rand(n, 2, generator=gen, device=device)


def _reject(draw, ok, max_iter: int = 500):
    out = draw()
    good = ok(*out)
    for _ in range(max_iter):
        if bool(good.all()):
            return out
        new = draw()
        take = ~good & ok(*new)
        out = tuple(torch.where(take.view(-1, *([1] * (o.dim() - 1))), nw, o) for o, nw in zip(out, new))
        good = good | take
    raise RuntimeError("yerleşim kuralları sağlanamadı (kural çok sıkı?)")


def make_layout(spec: GameSpec, cfg: WorldConfig, batch: int, gen: torch.Generator, device) -> dict[str, torch.Tensor]:
    if batch % 2:
        raise ValueError("ayna çiftleri için batch çift olmalı")
    n, L = batch // 2, cfg.arena
    ms, mt = spec.start_margin, spec.src_margin
    t_on, d_on = spec.target.active, spec.decoy.active

    def draw():
        start = _unif(gen, n, ms, L - ms, device)
        tgt = _unif(gen, n, mt, L - mt, device)
        dec = _unif(gen, n, mt, L - mt, device)
        ang = torch.rand(n, generator=gen, device=device) * 2 * math.pi
        head = torch.rand(n, generator=gen, device=device) * 2 * math.pi
        sign = torch.where(torch.rand(n, generator=gen, device=device) < 0.5, -1.0, 1.0)
        if spec.start == "ring":      # başlangıç hedef bölgesinin dışında R+gap halkasında
            r = spec.target.radius + spec.ring_gap
            start = tgt + r * torch.stack([torch.cos(ang), torch.sin(ang)], -1)
        return start, tgt, dec, head, sign

    def waypoint(start, tgt, sign):
        mid, d = (start + tgt) / 2, tgt - start
        perp = torch.stack([-d[:, 1], d[:, 0]], -1) / d.norm(dim=-1, keepdim=True).clamp(min=1e-9)
        return mid + (spec.bend or 0.0) * sign.unsqueeze(-1) * perp

    def ok(start, tgt, dec, head, sign):
        good = ((start >= ms) & (start <= L - ms)).all(-1)
        if spec.start != "ring":
            if t_on:
                good &= (start - tgt).norm(dim=-1) >= spec.dmin
            if d_on:
                good &= (start - dec).norm(dim=-1) >= spec.dmin
        if t_on and d_on:
            good &= (tgt - dec).norm(dim=-1) >= spec.dmin
        if spec.bend is not None:
            wp = waypoint(start, tgt, sign)
            good &= ((wp >= 2.0) & (wp <= L - 2.0)).all(-1)
        return good

    start, tgt, dec, head, sign = _reject(draw, ok)
    wp = waypoint(start, tgt, sign)

    def mirror(x):
        out = x.clone()
        out[..., 0] = L - out[..., 0]
        return out

    def inter(a, b):       # (n,...) ve aynası -> (2n,...) [özgün, ayna] sıralı
        return torch.stack([a, b], 1).reshape(2 * n, *a.shape[1:])

    far = torch.full((n, 2), FAR, device=device)
    s0 = tgt if t_on else far
    s1 = dec if d_on else far
    src = torch.stack([s0, s1], 1)                                     # (n,2,2)
    src_m = mirror(src)
    for k, on in enumerate((t_on, d_on)):                              # etkin olmayan yuva aynada da uzakta kalır
        if not on:
            src_m[:, k] = FAR
    poly = torch.stack([start, wp, tgt], 1)                            # (n,3,2)
    return {
        "start": inter(start, mirror(start)),
        "heading": inter(head, math.pi - head),
        "src_pos": inter(src, src_m),
        "poly": inter(poly, mirror(poly)),
    }
