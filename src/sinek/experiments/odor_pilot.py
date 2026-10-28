"""Dört koku oyunu: PİLOT koşusu (kanıt değildir; docs/dort_koku_oyunu_plani.md K5/G3).

    python -m sinek.experiments.odor_pilot --pre results/odor_games/pre_s100.npz --game O1a --seed 101 \
        --arms frozen,anosmic,random,reference --agents 24 --trials 8 --seconds 25 --out results/odor_pilot/O1a_s101

Her kol aynı tohum/aynı canlı sırasıyla ayrı koşulur (CRN). Çıktı: kol başına isabet oranı (canlı-kümeli GA), eşli farklar (koku-açık − anosmik vb.)
ve sızıntı denetimi. Pilot sonuçları parametre seçimi/hata ayıklama içindir; doğrulayıcı sayılmaz (R-2).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import ARMS, hits, leak_check, make_game_creature, play
from ..games.spec import GAMES
from .stats import paired_cluster_ci, pooled_fraction, cluster_bootstrap_ci


def _rate(h: np.ndarray):
    """Canlı-kümeli oran ve %95 GA (havuzlanmış isabet / deneme)."""
    a, b = h.sum(1), (1 - h).sum(1)
    return cluster_bootstrap_ci(a, b, n=4000)


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", required=True, choices=sorted(GAMES))
    ap.add_argument("--seed", type=int, required=True, help="oyun (yerleşim/gürültü) tohumu; ön-eğitim tohumundan farklı olmalı")
    ap.add_argument("--arms", default="frozen,anosmic,random,reference")
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--set", action="append", default=[], metavar="YUVA.ALAN=DEĞER",
                    help="oyun parametresi geçersiz kılma, ör. target.width=3 (yalnız pilot; sonuç dosyasına yazılır)")
    ap.add_argument("--slot", type=int, default=None, help="isabet yuvası (varsayılan: O4 için 1=decoy, diğerleri 0=hedef)")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    slot = a.slot if a.slot is not None else (1 if a.game in ("O4a", "O4c") else 0)
    if a.threads:
        torch.set_num_threads(a.threads)
    t0 = time.time()
    pre = checkpoint.load(a.pre)
    spec = GAMES[a.game]
    for item in a.set:
        key, _, val = item.partition("=")
        slot, _, name = key.partition(".")
        cur = getattr(getattr(spec, slot), name)
        spec = spec.with_slot(slot, **{name: type(cur)(val)})
    agents = list(range(min(a.agents, pre.world.B)))
    arms = a.arms.split(",")
    res: dict[str, dict] = {}
    for arm in arms:
        c = make_game_creature(pre, a.game, arm, agents, a.trials, a.seed, spec=spec)
        res[arm] = play(c, a.seconds, learn=False, test=True, n_agents=len(agents))
        h = hits(res[arm], slot)
        print(f"[{time.time() - t0:6.0f}s] {a.game} {arm:<10} p_hit={h.mean():.3f}", flush=True)
    L = [f"# Pilot: {a.game} (tohum {a.seed}, ön-eğitim {a.pre})", "",
         f"Pilot — kanıt değildir. {len(agents)} canlı x {a.trials} deneme, süre sınırı {a.seconds:.0f} sn, kollar CRN eşli.", "",
         "| kol | p_hit [%95 GA] | koku alan (alan>0) | ort. süre (isabetler) | ort. yol (isabetler) |", "|---|---|---|---|---|"]
    summary = {}
    for arm in arms:
        o, h = res[arm], hits(res[arm], slot)
        m, lo, hi = _rate(h)
        seen = float((o["first_odor_step"] >= 0).mean())
        tm = float(np.nanmean(np.where(h == 1, o["time"], np.nan))) if h.any() else float("nan")
        pl = float(np.nanmean(np.where(h == 1, o["path_len"], np.nan))) if h.any() else float("nan")
        L.append(f"| {arm} | {m:.3f} [{lo:.3f}, {hi:.3f}] | {seen:.2f} | {tm:.1f} | {pl:.1f} |")
        summary[arm] = {"p_hit": m, "ci95": [lo, hi], "odor_seen": seen, "mean_time": tm, "mean_path": pl}
    L += ["", "## Eşli farklar (canlı-kümeli %99 GA)", ""]
    base = "anosmic" if "anosmic" in res else arms[0]
    paired = {}
    for arm in arms:
        if arm == base:
            continue
        m, lo, hi = paired_cluster_ci(hits(res[arm], slot).sum(1), hits(res[base], slot).sum(1), a.trials, n=4000, alpha=0.01)
        L.append(f"- {arm} − {base}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        paired[arm] = [m, lo, hi]
    leak = None
    odor_arms = [x for x in arms if x not in ("anosmic", "random") and ARMS[x].brain == "trained"]
    if "anosmic" in res and odor_arms:
        leak = leak_check(res[odor_arms[0]], res["anosmic"])
        L += ["", f"## Sızıntı denetimi ({odor_arms[0]} ve anosmik; koku alınmayan denemelerde sonuç bit-bit aynı olmalı)", "",
              f"- denetlenen deneme: {leak['checked']}, ihlal: **{leak['violations']}**, alan olayları aynı: {leak['events_identical']}"]
    # mirror yarıları (deneme çift/tek): duvar/yön yanlılığı kontrolü
    if "anosmic" in res:
        L += ["", "## Ayna yarıları (özgün / ayna) p_hit", ""]
        for arm in arms:
            h = hits(res[arm], slot)
            L.append(f"- {arm}: {h[:, 0::2].mean():.3f} / {h[:, 1::2].mean():.3f}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "results.json").write_text(json.dumps({"args": vars(a), "spec": dataclasses.asdict(spec), "summary": summary,
                                                  "paired_vs_" + base: paired, "leak": leak,
                                                  "wall_seconds": time.time() - t0}, indent=1, default=str), encoding="utf-8")
    np.savez_compressed(out / "outcomes.npz", **{f"{arm}__{k}": v for arm in arms for k, v in res[arm].items()})
    print("\n".join(L))
    return summary


if __name__ == "__main__":
    main()
