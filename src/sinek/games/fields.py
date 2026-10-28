"""Koku alanı fonksiyonları (docs/dort_koku_oyunu_plani.md §3).

Sonlu destekli alanlar (`bump`, `trail`) destek dışında **tam 0.0** döndürür (Gauss kuyruğu gibi sızıntı yok, R01).
Hepsi saf torch fonksiyonudur; hiçbirinde rastgelelik yoktur.
"""
from __future__ import annotations

import torch


def gauss(d: torch.Tensor, sigma: float, amp: float = 1.0) -> torch.Tensor:
    """Evre 1/2'deki yarı-sonsuz Gauss profili (yalnız çapa oyunu O1-R ve O4 decoy'u için)."""
    return amp * torch.exp(-(d**2) / (2 * sigma**2))


def bump(d: torch.Tensor, radius: float, amp: float = 1.0) -> torch.Tensor:
    """d<R için amp·(1−(d/R)²)³ (C² sürekli), d≥R için TAM 0.0."""
    u = (1.0 - (d / radius) ** 2).clamp(min=0.0)
    return torch.where(d < radius, amp * u**3, torch.zeros_like(d))


def polyline_geometry(p: torch.Tensor, poly: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """p (B,N,2), poly (B,K,2) -> (n, s_kalan), ikisi (B,N): çokgene en yakın uzaklık ve hedefe (son köşe) kalan yay uzunluğu."""
    seg = poly[:, 1:] - poly[:, :-1]                                   # (B,K-1,2)
    seg_len = seg.norm(dim=-1)                                         # (B,K-1)
    tail = torch.flip(torch.cumsum(torch.flip(seg_len, [1]), 1), [1]) - seg_len   # Σ_{j>k} uzunluk_j
    a = poly[:, :-1].unsqueeze(1)                                      # (B,1,K-1,2)
    ab = seg.unsqueeze(1)
    ap = p.unsqueeze(2) - a                                            # (B,N,K-1,2)
    len2 = (seg_len**2).clamp(min=1e-12).unsqueeze(1)                  # (B,1,K-1)
    t = ((ap * ab).sum(-1) / len2).clamp(0.0, 1.0)                     # (B,N,K-1)
    n_seg = (p.unsqueeze(2) - (a + t.unsqueeze(-1) * ab)).norm(dim=-1)
    best = n_seg.argmin(-1)                                            # (B,N)
    n = n_seg.gather(-1, best.unsqueeze(-1)).squeeze(-1)
    t_b = t.gather(-1, best.unsqueeze(-1)).squeeze(-1)
    rem = (1.0 - t_b) * seg_len.gather(1, best) + tail.gather(1, best)
    return n, rem


def trail(p: torch.Tensor, poly: torch.Tensor, width: float, lam: float, amp: float = 1.0) -> torch.Tensor:
    """İz: yanal `bump(n, W)` × hedefe doğru artan boylamsal terim `exp(−s_kalan/λ)`; tüp dışı TAM 0.0."""
    n, rem = polyline_geometry(p, poly)
    return amp * bump(n, width, 1.0) * torch.exp(-rem / lam)
