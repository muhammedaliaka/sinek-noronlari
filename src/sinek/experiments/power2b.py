"""Evre 2b güç analizi: gerçek karar kodunu (`evre2b.evaluate2`) sentetik seçim sayılarıyla çalıştırır.

    python -m sinek.experiments.power2b --sims 300 --out docs/evre2b_guc_analizi.md

Model: canlıya özgü rol tercihi p_i ~ Beta(μκ, (1-μ)κ) (κ küçük = canlılar arası değişkenlik büyük); canlı başına deneme sayısı T,
her denemede seçim olasılığı r (koşul/aşama başına). Eğitimsiz ağda koku-kimliği yanlılığı b: canlıların yarısında A rolü koku 1
olduğundan p_naive = 0.5 ± b (rol dengelemesinin etkisi). Parametreler geliştirme gözlemlerinden gelir, ölçülmüş "doğru" değerler değildir.
"""
from __future__ import annotations

import argparse
import types
from dataclasses import dataclass, replace

import numpy as np

from . import evre2b


@dataclass(frozen=True)
class Scenario:
    name: str
    agents: int = 24
    trials: int = 8
    p_trained: float = 0.9          # eğitilmiş plastic rol-A oranı
    p_reversed: float = 0.15        # tersine çevirme sonrası
    kappa: float = 6.0              # Beta konsantrasyonu
    r_naive: float = 0.65
    r_trained: float = 0.8
    r_reversed: float = 0.7
    r_random: float = 0.7
    odor_bias: float = 0.10         # eğitimsiz ağın koku-0'a yanlılığı (rol dengelemeyle sönümlenir)
    swap: bool = True


def _group(rng, n, mu, kappa, r, T, bias_sign=None):
    """n canlı: p_i ~ Beta; seçim sayısı ~ Binom(T, r); A sayısı ~ Binom(seçim, p_i)."""
    mu = np.clip(mu, 1e-3, 1 - 1e-3)
    p = rng.beta(mu * kappa, (1 - mu) * kappa, n) if np.isfinite(kappa) else np.full(n, mu)
    tot = rng.binomial(T, r, n)
    a = rng.binomial(tot, p)
    return a, tot - a


def make_stages(s: Scenario, rng: np.random.Generator) -> list[dict]:
    n, T = s.agents, s.trials
    half = np.arange(n) >= n // 2 if s.swap else np.zeros(n, bool)

    def naive_group():
        # koku-0 yanlılığı: swap olmayan canlıda A=koku0 (p=0.5+b), swap olanda A=koku1 (p=0.5-b)
        mu = np.where(half, 0.5 - s.odor_bias, 0.5 + s.odor_bias)
        p = np.array([rng.beta(m * s.kappa, (1 - m) * s.kappa) for m in mu])
        tot = rng.binomial(T, s.r_naive, n)
        a = rng.binomial(tot, p)
        return a, tot - a

    def stage(phase, name, pl, fr, rn):
        return {"phase": phase, "name": name, "episode": 0,
                "n_a": np.concatenate([pl[0], fr[0], rn[0]]).tolist(), "n_b": np.concatenate([pl[1], fr[1], rn[1]]).tolist()}

    rnd = _group(rng, n, 0.5, s.kappa, s.r_random, T)
    fr = naive_group()
    return [
        stage("naive", "naif", naive_group(), fr, rnd),
        stage("A", "A12", _group(rng, n, s.p_trained, s.kappa, s.r_trained, T), fr, rnd),
        stage("B", "B24", _group(rng, n, s.p_reversed, s.kappa, s.r_reversed, T), fr, rnd),
    ]


def simulate(s: Scenario, sims: int, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    args = types.SimpleNamespace(agents=s.agents, trials=s.trials)
    keys = ["G", "A1", "A2", "A3", "B1", "B2"]
    hit = {k: 0 for k in keys + ["hepsi"]}
    for _ in range(sims):
        v = evre2b.evaluate2(make_stages(s, rng), args, None, True)
        ok = {}
        for k, x in v.items():
            code = k.split()[0]
            if code in keys:
                ok[code] = x["pass"]
        for k in keys:
            hit[k] += ok[k]
        hit["hepsi"] += all(ok.values())
    return {k: hit[k] / sims for k in hit}


SCENARIOS = [
    Scenario("sıfır (öğrenme yok)", p_trained=0.5, p_reversed=0.5),
    Scenario("güçlü (v1 benzeri: 0,90 → 0,15)", p_trained=0.90, p_reversed=0.15),
    Scenario("orta (0,80 → 0,30)", p_trained=0.80, p_reversed=0.30),
    Scenario("zayıf (0,70 → 0,40)", p_trained=0.70, p_reversed=0.40),
    Scenario("güçlü, canlılar arası değişkenlik yüksek (κ=2)", p_trained=0.90, p_reversed=0.15, kappa=2.0),
    Scenario("güçlü, eğitimsiz seçim oranı düşük (0,30; G kapısı)", p_trained=0.90, p_reversed=0.15, r_naive=0.30),
    Scenario("Evre 2 v1 tasarımı benzeri (16 canlı, 4 deneme, rol dengelemesi yok, eğitimsiz seçim 0,15), güçlü",
             agents=16, trials=4, r_naive=0.15, r_trained=0.78, r_reversed=0.69, swap=False, odor_bias=0.0,
             p_trained=0.90, p_reversed=0.20),
]


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sims", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    L = [f"| senaryo | G | A1 | A2 | A3 | B1 | B2 | **hepsi** |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s in SCENARIOS:
        r = simulate(s, a.sims, a.seed)
        L.append(f"| {s.name} | " + " | ".join(f"{r[k]:.2f}" for k in ["G", "A1", "A2", "A3", "B1", "B2"]) + f" | **{r['hepsi']:.2f}** |")
        print(L[-1], flush=True)
    md = "\n".join(L) + "\n"
    if a.out:
        from pathlib import Path
        Path(a.out).write_text(md)
    return md


if __name__ == "__main__":
    main()
