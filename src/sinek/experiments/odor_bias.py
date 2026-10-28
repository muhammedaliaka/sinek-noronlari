"""Sıfır-koku dönüş yanlılığı tanısı (docs/dort_koku_oyunu_plani.md Z-16, G3): koku hiç yokken canlı bir yana mı dönüyor?

    python -m sinek.experiments.odor_bias --pre results/odor_games/pre_s100.npz --seed 101 --out results/odor_pilot/bias_s100

Anosmik kol (glom ≡ 0), öğrenme kapalı. Her (canlı, deneme) için "kontrast" = (v_sol − v_sağ)/(|v_sol|+|v_sağ|+eps) zaman ortalaması alınır
(motor kuralının dönüş girdisi; dönüş hızı = kazanç × kontrast + gürültü). Raporlanan: canlı başına ortalama kontrast, deneme-arası
standart hata, |z| > 2,58 olan canlı oranı (sıfır yanlılıkta ≈ %1), havuz ortalaması (işaretli: sola +). Yanlılık büyükse O3 gibi sıfır-koku
kontrollerinde kol farkları yanlılıktan çıkabilir (R-4). Tanı pilottur; kanıt değildir.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import make_game_creature


def measure(pre, game: str, seed: int, agents: int, trials: int, seconds: float, arm: str = "anosmic") -> dict:
    ids = list(range(min(agents, pre.world.B)))
    c = make_game_creature(pre, game, arm, ids, trials, seed)
    c.reset_episode("game", test=True)
    eps, n = c.cfg.motor.contrast_eps, int(round(seconds / c.cfg.world.dt))
    acc = torch.zeros(c.world.B)
    cnt = torch.zeros(c.world.B)
    for _ in range(n):
        alive = ~c.world.done
        c.step(learn=False)
        v = c.last_valence.cpu()
        con = (v[:, 0] - v[:, 1]) / (v[:, 0].abs() + v[:, 1].abs() + eps)
        acc += con * alive.cpu().float()
        cnt += alive.cpu().float()
        if bool(c.world.done.all()):
            break
    m = (acc / cnt.clamp(min=1)).numpy().reshape(len(ids), trials)
    per = m.mean(1)
    se = m.std(1, ddof=1) / np.sqrt(trials)
    z = per / np.maximum(se, 1e-9)
    return {"contrast_mean_per_creature": per.tolist(), "se": se.tolist(), "frac_abs_z_gt_2.58": float((np.abs(z) > 2.58).mean()),
            "pooled_mean": float(per.mean()), "pooled_abs_mean": float(np.abs(per).mean()),
            "turn_rate_bias_rad_s": float(np.abs(per).mean() * c.cfg.motor.turn_gain), "n_creatures": len(ids)}


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", default="O1a")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.threads:
        torch.set_num_threads(a.threads)
    pre = checkpoint.load(a.pre)
    r = measure(pre, a.game, a.seed, a.agents, a.trials, a.seconds)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"args": vars(a), **r}, indent=1), encoding="utf-8")
    print(f"sıfır-koku kontrast: havuz ort. {r['pooled_mean']:+.4f}, |ort.| {r['pooled_abs_mean']:.4f} "
          f"(≈ {r['turn_rate_bias_rad_s']:.3f} rad/s), |z|>2,58 canlı oranı {r['frac_abs_z_gt_2.58']:.2f} (sıfır yanlılıkta ≈ 0,01)")
    return r


if __name__ == "__main__":
    main()
