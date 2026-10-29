"""Ölçek eğrisi, GELİŞTİRME (kanıt değildir): dondurulmuş canlının oyun başarısı, anten başına devre kopyası sayısı K ile nasıl değişir?

    python3 -I -m sinek.experiments.scale_dev --pre results/odor_games/pre_s100.npz --game O1a --seed 110 --ks 1,2,4 --out results/scale_dev/O1a_s110.md

Kollar CRN eşli: anosmik ve referans bir kez (K'den bağımsız), frozen her K için. K=1 sarmalayıcısı sarılmamış frozen kolla birebir aynı olmalıdır (denetlenir).
Sonuçlar tasarım ipucudur; doğrulayıcı tohumları (≥200) kullanılmaz (R-2).
"""
from __future__ import annotations

import argparse
import dataclasses
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..ensemble import EnsembleBrain
from ..games.protocol import hits, make_game_creature, play
from .stats import cluster_bootstrap_ci, paired_cluster_ci


class LookupBrain:
    """K→∞ üst sınırı: öğrenilmiş değerin gürültüsüz beklentisi. V = f_canlı,yarımküre(s), s = ödüllü kokunun glomerül düzeyi.
    Tablo, dondurulmuş beynin sabit girdide uzun ortalamasından gelir (kayan zaman EMA gecikmesi ve nonlineer okuma ihmal edilir)."""

    def __init__(self, world, table, grid, trials):
        self.world, self.table, self.grid, self.trials = world, table, grid, trials
        self.cre = torch.arange(world.B) // trials

    def reset_state(self) -> None:
        pass

    def step(self, glom, taste, touch, learn: bool = False):
        mask = self.world.reward_mask().unsqueeze(1)
        s = ((glom * mask).sum(-1) / mask.sum(-1).clamp(min=1)).clamp(0, 1)          # (B,2)
        pos = s * (len(self.grid) - 1)
        lo = pos.floor().long().clamp(0, len(self.grid) - 2)
        f = pos - lo
        cre = self.cre.unsqueeze(1).expand_as(lo)
        h = torch.arange(2).view(1, 2).expand_as(lo)
        return self.table[lo, cre, h] * (1 - f) + self.table[lo + 1, cre, h] * f


def build_table(pre, c_ref, agents, trials, n_grid=21, steps=120, burn=40):
    brain = pre.brain.select(torch.as_tensor(agents, dtype=torch.long))
    brain.eta_scale = torch.zeros_like(brain.eta_scale)
    mask = c_ref.world.reward_mask()[::trials].unsqueeze(1)                          # (A,1,G)
    grid = torch.linspace(0, 1, n_grid)
    tab = torch.zeros(n_grid, len(agents), 2)
    z = torch.zeros(len(agents))
    for i, sv in enumerate(grid):
        brain.reset_state()
        g = (sv * mask).expand(len(agents), 2, -1).contiguous()
        acc = []
        for t in range(steps):
            v = brain.step(g, z, z, learn=False)
            if t >= burn:
                acc.append(v)
        tab[i] = torch.stack(acc).mean(0)
    return tab, grid


def set_motor(c, eps=None, gain=None):
    """Test anı motor kuralı geçersiz kılma (yalnız geliştirme): contrast_eps ve/veya turn_gain."""
    if eps is not None:
        c.cfg = dataclasses.replace(c.cfg, motor=dataclasses.replace(c.cfg.motor, contrast_eps=eps))
    if gain is not None:
        c.turn_gain = torch.full((c.world.B,), float(gain))


def _hits(pre, game, arm, agents, trials, seed, seconds, k=0, eps=None, gain=None):
    c = make_game_creature(pre, game, arm, agents, trials, seed)
    set_motor(c, eps, gain)
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
    ap.add_argument("--oracle", action="store_true", help="K→∞ üst sınırı: gürültüsüz değer tablosu ile frozen kol")
    ap.add_argument("--tau", type=float, default=None, help="tau_valence geçersiz kıl (okuma entegrasyon süresi, sn); yalnız geliştirme")
    ap.add_argument("--eps", type=float, default=None, help="contrast_eps geçersiz kıl (test anı motor; yalnız geliştirme)")
    ap.add_argument("--turn-gain", type=float, default=None, help="turn_gain geçersiz kıl (test anı motor; yalnız geliştirme)")
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
    if a.tau is not None:
        pre.brain.cfg.tau_valence = a.tau
    agents = list(range(min(a.agents, pre.world.B)))
    t0 = time.time()
    mo = dict(eps=a.eps, gain=a.turn_gain)
    h_an, _ = _hits(pre, a.game, "anosmic", agents, a.trials, a.seed, a.seconds, **mo)
    h_ref, _ = _hits(pre, a.game, "reference", agents, a.trials, a.seed, a.seconds, **mo)
    h_fr, o_fr = _hits(pre, a.game, "frozen", agents, a.trials, a.seed, a.seconds, **mo)
    print(f"[{time.time() - t0:5.0f}s] anosmik {h_an.mean():.3f} referans {h_ref.mean():.3f} frozen(sarmasız) {h_fr.mean():.3f}", flush=True)
    rows = []
    if a.oracle:
        c = make_game_creature(pre, a.game, "reference", agents, a.trials, a.seed)
        set_motor(c, a.eps, a.turn_gain)
        tab, grid = build_table(pre, c, agents, a.trials)
        c.brain = LookupBrain(c.world, tab, grid, a.trials)
        o = play(c, a.seconds, learn=False, test=True)
        h = hits(o).reshape(len(agents), a.trials)
        m, lo, hi = paired_cluster_ci(h.sum(1), h_an.sum(1), a.trials, n=4000, alpha=0.01)
        rows.append(f"| ∞ (gürültüsüz tablo) | {h.mean():.3f} | {m:+.3f} [{lo:+.3f}, {hi:+.3f}] | {np.mean(h_ref) - h.mean():+.3f} |")
        print(f"[{time.time() - t0:5.0f}s] K=∞: {rows[-1]}", flush=True)
    for k in [int(x) for x in a.ks.split(",") if x]:
        h, o = _hits(pre, a.game, "frozen", agents, a.trials, a.seed, a.seconds, k=k, **mo)
        if k == 1:
            same = bool(np.array_equal(h, h_fr) and np.array_equal(o["slot"], o_fr["slot"]))
            print(f"K=1 sarmalayıcı sarılmamış kolla birebir aynı: {same}", flush=True)
            if not same:
                raise SystemExit("K=1 sıfır-etki denetimi başarısız")
        m, lo, hi = paired_cluster_ci(h.sum(1), h_an.sum(1), a.trials, n=4000, alpha=0.01)
        rows.append(f"| {k} | {h.mean():.3f} | {m:+.3f} [{lo:+.3f}, {hi:+.3f}] | {np.mean(h_ref) - h.mean():+.3f} |")
        print(f"[{time.time() - t0:5.0f}s] K={k}: {rows[-1]}", flush=True)
    text = "\n".join([f"# Ölçek eğrisi (geliştirme; kanıt değildir): {a.game}, oyun tohumu {a.seed}", "",
                      f"{len(agents)} canlı × {a.trials} deneme; tau_valence={pre.brain.cfg.tau_valence}; motor ε={a.eps if a.eps is not None else pre.cfg.motor.contrast_eps:g}, turn_gain={a.turn_gain if a.turn_gain is not None else pre.cfg.motor.turn_gain:g}; anosmik {h_an.mean():.3f}, referans {h_ref.mean():.3f}.", "",
                      "| K (anten başına kopya) | frozen p_hit | frozen − anosmik [%99 GA] | referansa uzaklık |", "|---|---|---|---|"] + rows) + "\n"
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
