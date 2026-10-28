"""Evre 2b ön-kayıtlı istatistikleri: canlı-düzeyi (küme) bootstrap ve permütasyon, seçim sayısı ağırlıklı.

Birim canlıdır (aynı canlının denemeleri bağımsız sayılmaz). Bir canlı için `a` = A seçimi, `b` = B seçimi sayısıdır;
havuzlanmış A-oranı = Σa / Σ(a+b). Hiç seçim yapmayan canlı kendiliğinden ağırlıksızdır.

Bu dosya `evre2_posthoc.py`'den ayrıdır: o dosya Evre 2 v1 sonuç belgelerini yeniden üretmek için dondurulmuştur.
"""
from __future__ import annotations

from math import comb

import numpy as np


def pooled_fraction(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = a.sum() + b.sum()
    return float(a.sum() / t) if t > 0 else float("nan")


def cluster_bootstrap_ci(a, b, n: int = 10000, seed: int = 0, alpha: float = 0.05):
    """(havuzlanmış oran, alt, üst): canlılar yerine koyarak yeniden örneklenir, yüzdelik aralık."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = len(a)
    if a.sum() + b.sum() == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, m, size=(n, m))
    sa, sb = a[idx].sum(1), b[idx].sum(1)
    tot = sa + sb
    ok = tot > 0
    f = sa[ok] / tot[ok]
    return pooled_fraction(a, b), float(np.quantile(f, alpha / 2)), float(np.quantile(f, 1 - alpha / 2))


def cluster_permutation_p(g1, g2, n: int = 20000, seed: int = 0, alternative: str = "greater") -> float:
    """Havuzlanmış A-oranı farkı için canlı-düzeyi permütasyon p değeri.

    g1, g2 = (a_sayıları, b_sayıları), canlı başına. `alternative`: "greater" (grup1 > grup2) ya da "two-sided".
    Bir permütasyonda bir grubun hiç seçimi yoksa o grubun oranı 0.5 (yokluk değeri) sayılır.
    """
    a = np.concatenate([np.asarray(g1[0], float), np.asarray(g2[0], float)])
    b = np.concatenate([np.asarray(g1[1], float), np.asarray(g2[1], float)])
    n1, N = len(g1[0]), len(a)
    if np.asarray(g1[0]).sum() + np.asarray(g1[1]).sum() == 0 or np.asarray(g2[0]).sum() + np.asarray(g2[1]).sum() == 0:
        return float("nan")

    def frac(sa, sb):
        t = sa + sb
        return np.where(t > 0, sa / np.maximum(t, 1e-12), 0.5)

    obs = pooled_fraction(g1[0], g1[1]) - pooled_fraction(g2[0], g2[1])
    rng = np.random.default_rng(seed)
    ge = 0
    chunk = 5000
    done = 0
    while done < n:
        k = min(chunk, n - done)
        perm = np.argsort(rng.random((k, N)), axis=1)
        i1 = perm[:, :n1]
        sa1, sb1 = a[i1].sum(1), b[i1].sum(1)
        sa2, sb2 = a.sum() - sa1, b.sum() - sb1
        d = frac(sa1, sb1) - frac(sa2, sb2)
        ge += int((d >= obs - 1e-12).sum()) if alternative == "greater" else int((np.abs(d) >= abs(obs) - 1e-12).sum())
        done += k
    return (ge + 1) / (n + 1)


def binom_two_sided(k: int, n: int) -> float:
    """Tam iki yönlü iki terimli test, p0 = 0.5 (denemelerin bağımsız olduğu varsayımıyla; betimsel)."""
    if n == 0:
        return float("nan")
    pk = comb(n, k)
    return min(1.0, sum(comb(n, j) for j in range(n + 1) if comb(n, j) <= pk) / 2 ** n)


# ---------------------------------------------------------------- eşli (canlı içi) karşılaştırmalar: dört koku oyunu
# Birim canlıdır; her canlının iki kolu (aynı yerleşimler, ortak rastgele sayılar) vardır. Fark d_i = (x_i − y_i) / deneme sayısı.
# Bu işlevler docs/dort_koku_oyunu_plani.md §5.2'deki ön-kayıtlı istatistiktir; kullanılmadan önce null/bilinen-etki testleri (tests/test_stats_paired.py).
def _paired_diff(x, y, n_trials) -> np.ndarray:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.shape != y.shape:
        raise ValueError("eşli kollar aynı canlı sayısında olmalı")
    return (x - y) / float(n_trials)


def paired_cluster_ci(x, y, n_trials, n: int = 10000, seed: int = 0, alpha: float = 0.01):
    """(ortalama fark, alt, üst): canlılar yerine koyarak yeniden örneklenir; yüzdelik (1−alpha) aralığı."""
    d = _paired_diff(x, y, n_trials)
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, len(d), size=(n, len(d)))].mean(1)
    return float(d.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def paired_signflip_p(x, y, n_trials, n: int = 20000, seed: int = 0, alternative: str = "greater") -> float:
    """Eşli farkların ortalaması için işaret-çevirme permütasyonu p değeri (H0: fark dağılımı 0 etrafında simetrik)."""
    d = _paired_diff(x, y, n_trials)
    rng = np.random.default_rng(seed)
    flips = rng.choice([-1.0, 1.0], size=(n, len(d)))
    perm = (flips * d).mean(1)
    obs = d.mean()
    if alternative == "greater":
        ge = int((perm >= obs - 1e-12).sum())
    elif alternative == "less":
        ge = int((perm <= obs + 1e-12).sum())
    else:
        ge = int((np.abs(perm) >= abs(obs) - 1e-12).sum())
    return (ge + 1) / (n + 1)


def paired_equivalent(x, y, n_trials, delta: float, alpha: float = 0.01, n: int = 10000, seed: int = 0):
    """TOST benzeri eşdeğerlik: (1−2·alpha) bootstrap aralığı (−delta, delta) içinde mi? (mean, lo, hi, geçti)."""
    m, lo, hi = paired_cluster_ci(x, y, n_trials, n=n, seed=seed, alpha=2 * alpha)
    return m, lo, hi, bool(lo > -delta and hi < delta)
