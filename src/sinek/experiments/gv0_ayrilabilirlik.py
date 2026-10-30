"""Kapı G-V0 (docs/gorsel_koku_oyunu_plani.md §3): görsel desen X ile Y, mantar cismi KC yanıtında ÖĞRENMEDEN ayrılabiliyor mu? (geliştirme; kanıt değildir)

    python3 -I -m sinek.experiments.gv0_ayrilabilirlik --out results/gv0.md

Ölçü: tek deneme KC yanıt vektörü (uygunluk izi; iki yarımküre birleşik), en-yakın-sınıf-ortalaması sınıflandırıcısı, bir-dışarıda-bırak çapraz doğrulama doğruluğu (0,5 = ayrılamaz).
Pozitif kontrol: koku A vs B (aynı yöntem; öğrenmenin çalıştığı bilinen ayrım). Negatif kontrol: X vs X (aynı desen, farklı gürültü; ≈0,5 olmalı).
Girdi düzeyi: oyundaki tipik görünürlük (uzaklık 10 → ≈0,6; 25 → ≈0,2). Kapı (R-6'ya uygun, kodlamadan önce yazıldı): görsel X/Y doğruluğu ≥ 0,75 olmalı (düzey 0,6'da) VE negatif kontrol ≤ 0,60.
Geçmezse oyun koşmaz; "bu bağlantı verisiyle görsel desen ayrımı yetersiz" bir SONUÇTUR — ayar sürüsü yapılmaz (E-08).
"""
from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path

import numpy as np
import torch

from ..brain_connectome import ConnectomeBrain
from ..connectome import mbmodel
from ..games.world import vis_patterns
from ..world import odor_patterns


def kc_responses(cfg, glom: torch.Tensor, vis: torch.Tensor | None, n: int, steps: int, seed: int) -> np.ndarray:
    """n bağımsız deneme (eleman = deneme): (n, 2·n_kc) KC uygunluk izi. Girdiler (2, ...) tek göz/anten çifti, tüm denemelere aynı."""
    b = ConnectomeBrain(cfg.cbrain, n, seed)
    z = torch.zeros(n)
    g = glom.unsqueeze(0).expand(n, -1, -1).contiguous()
    v = None if vis is None else vis.unsqueeze(0).expand(n, -1, -1).contiguous()
    for _ in range(steps):
        b.step(g, z, z, learn=False, vis=v)
    return b.elig.view(n, 2 * b.n_kc).numpy().copy()


def loo_accuracy(a: np.ndarray, b: np.ndarray) -> float:
    """En-yakın-sınıf-ortalaması, bir-dışarıda-bırak. a, b: (n, d) iki sınıfın deneme yanıtları."""
    X = np.concatenate([a, b]); y = np.r_[np.zeros(len(a)), np.ones(len(b))]
    correct = 0
    for i in range(len(X)):
        m = np.ones(len(X), bool); m[i] = False
        c0, c1 = X[m & (y == 0)].mean(0), X[m & (y == 1)].mean(0)
        pred = 1.0 if np.linalg.norm(X[i] - c1) < np.linalg.norm(X[i] - c0) else 0.0
        correct += pred == y[i]
    return correct / len(X)


def run(levels=(0.2, 0.6, 1.0), n: int = 48, steps: int = 30, n_feat: int = 6, vis_seed: int = 0, brain_seed: int = 5) -> dict:
    cfg = mbmodel.connectome_config()
    cfg = dataclasses.replace(cfg, cbrain=dataclasses.replace(cfg.cbrain, n_vis_feat=n_feat, vis_tuning_seed=vis_seed))
    vp = vis_patterns(n_feat)
    pat = odor_patterns(cfg.world, 3)
    zero_g = torch.zeros(2, cfg.world.n_glom)
    out = {"levels": list(levels), "n": n, "steps": steps, "vis": {}, "odor": {}, "null": {}}
    for lv in levels:
        vx, vy = (vp[0] * lv).expand(2, -1).contiguous(), (vp[1] * lv).expand(2, -1).contiguous()
        x = kc_responses(cfg, zero_g, vx, n, steps, brain_seed + 1)
        y = kc_responses(cfg, zero_g, vy, n, steps, brain_seed + 2)
        x2 = kc_responses(cfg, zero_g, vx, n, steps, brain_seed + 3)
        out["vis"][lv] = loo_accuracy(x, y)
        out["null"][lv] = loo_accuracy(x, x2)
        ga = (1 - torch.exp(-cfg.world.odor_gain * pat[0] * lv)).expand(2, -1).contiguous()
        gb = (1 - torch.exp(-cfg.world.odor_gain * pat[1] * lv)).expand(2, -1).contiguous()
        no_vis = torch.zeros(2, n_feat)
        out["odor"][lv] = loo_accuracy(kc_responses(cfg, ga, no_vis, n, steps, brain_seed + 4), kc_responses(cfg, gb, no_vis, n, steps, brain_seed + 5))
    gate = out["vis"][0.6] >= 0.75 and out["null"][0.6] <= 0.60 if 0.6 in out["vis"] else None
    out["gate_pass"] = bool(gate) if gate is not None else None
    return out


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--vis-seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    r = run(n=a.n, steps=a.steps, vis_seed=a.vis_seed)
    L = ["# G-V0: görsel desen ayrılabilirliği (öğrenmesiz; geliştirme, kanıt değildir)", "",
         f"{r['n']} deneme/sınıf, {r['steps']} adım (×0,02 sn), tek-deneme KC izi, en-yakın-ortalama bir-dışarıda-bırak doğruluğu (0,5 = ayrılamaz). vis_tuning_seed={a.vis_seed}.", "",
         "| girdi düzeyi | görsel X vs Y | koku A vs B (pozitif kontrol) | X vs X (negatif kontrol) |", "|---|---|---|---|"]
    for lv in r["levels"]:
        L.append(f"| {lv} | {r['vis'][lv]:.3f} | {r['odor'][lv]:.3f} | {r['null'][lv]:.3f} |")
    L += ["", f"Kapı (düzey 0,6: görsel ≥0,75 ve negatif ≤0,60): **{'GEÇTİ' if r['gate_pass'] else 'GEÇMEDİ'}**"]
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
