"""Ölçek eğrisi, GELİŞTİRME (kanıt değildir): dondurulmuş canlının oyun başarısı, anten başına devre kopyası sayısı K ile nasıl değişir?

    python3 -I -m sinek.experiments.scale_dev --pre results/odor_games/pre_s100.npz --game O1a --seed 110 --ks 1,2,4 --out results/scale_dev/O1a_s110.md

Kollar CRN eşli: anosmik ve referans bir kez (K'den bağımsız), frozen her K için. K=1 sarmalayıcısı sarılmamış frozen kolla birebir aynı olmalıdır (denetlenir).
Sonuçlar tasarım ipucudur; doğrulayıcı tohumları (≥200) kullanılmaz (R-2).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..ensemble import EnsembleBrain
from ..games.protocol import hits, make_game_creature, play
from .stats import cluster_bootstrap_ci, paired_cluster_ci


def _hits(pre, game, arm, agents, trials, seed, seconds, k=0):
    c = make_game_creature(pre, game, arm, agents, trials, seed)
    if k:
        c.brain = EnsembleBrain(c.brain, k)
    out = play(c, seconds, learn=False, test=True)
    return hits(out).reshape(len(agents), trials), out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", default="O1a")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--ks", default="1,2,4")
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.seed >= 200:
        raise SystemExit("ölçek geliştirmesi doğrulayıcı tohumlarıyla (≥200) çalıştırılamaz")
    torch.set_num_threads(a.threads)
    pre = checkpoint.load(a.pre)
    agents = list(range(min(a.agents, pre.world.B)))
    t0 = time.time()
    h_an, _ = _hits(pre, a.game, "anosmic", agents, a.trials, a.seed, a.seconds)
    h_ref, _ = _hits(pre, a.game, "reference", agents, a.trials, a.seed, a.seconds)
    h_fr, o_fr = _hits(pre, a.game, "frozen", agents, a.trials, a.seed, a.seconds)
    print(f"[{time.time() - t0:5.0f}s] anosmik {h_an.mean():.3f} referans {h_ref.mean():.3f} frozen(sarmasız) {h_fr.mean():.3f}", flush=True)
    rows = []
    for k in [int(x) for x in a.ks.split(",")]:
        h, o = _hits(pre, a.game, "frozen", agents, a.trials, a.seed, a.seconds, k=k)
        if k == 1:
            same = bool(np.array_equal(h, h_fr) and np.array_equal(o["slot"], o_fr["slot"]))
            print(f"K=1 sarmalayıcı sarılmamış kolla birebir aynı: {same}", flush=True)
            if not same:
                raise SystemExit("K=1 sıfır-etki denetimi başarısız")
        m, lo, hi = paired_cluster_ci(h.sum(1), h_an.sum(1), a.trials, n=4000, alpha=0.01)
        rows.append(f"| {k} | {h.mean():.3f} | {m:+.3f} [{lo:+.3f}, {hi:+.3f}] | {np.mean(h_ref) - h.mean():+.3f} |")
        print(f"[{time.time() - t0:5.0f}s] K={k}: {rows[-1]}", flush=True)
    text = "\n".join([f"# Ölçek eğrisi (geliştirme; kanıt değildir): {a.game}, oyun tohumu {a.seed}", "",
                      f"{len(agents)} canlı × {a.trials} deneme; anosmik {h_an.mean():.3f}, referans {h_ref.mean():.3f}.", "",
                      "| K (anten başına kopya) | frozen p_hit | frozen − anosmik [%99 GA] | referansa uzaklık |", "|---|---|---|---|"] + rows) + "\n"
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
