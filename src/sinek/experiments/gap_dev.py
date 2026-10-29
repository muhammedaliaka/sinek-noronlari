"""Kalan boşluk ayrıştırması, GELİŞTİRME (kanıt değildir; docs/evre3_dan_plani.md §6.3): gürültüsüz öğrenilmiş değer tablosu (K→∞) ile
hangi bileşen referansa (0,98) ulaşmayı engelliyor?

    python3 -I -m sinek.experiments.gap_dev --pre results/odor_games/pre_s100.npz --game O1a --seed 110 --out results/gap_dev/O1a_s110.md

Varyantlar (hepsi aynı CRN dünyalarında, öğrenme kapalı, gürültüsüz tablo — `scale_dev.LookupBrain`):
  tablo        öğrenilmiş V_{canlı,yarımküre}(s) olduğu gibi
  simetrik     V_L = V_R = canlı başına iki yarımkürenin ortalaması (sol–sağ kazanç asimetrisi YOK; mekanizma değil, tanı)
  ortak_dogru  simetrik + canlı başına V(s) = a·s en küçük kareler doğrusu (ofset/eğrilik YOK; tanı)
  referans     ReferenceBrain (elle kurulmuş), aynı motor kuralıyla
Motor kuralı taraması (ε, turn_gain) yalnız `tablo` ve `referans` için. Doğrulayıcı tohumları (≥200) yasaktır (R-2).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import hits, make_game_creature, play
from .scale_dev import LookupBrain, build_table, set_motor


def _play(pre, game, arm, agents, trials, seed, seconds, table=None, grid=None, eps=None, gain=None) -> float:
    c = make_game_creature(pre, game, arm, agents, trials, seed)
    if table is not None:
        c.brain = LookupBrain(c.world, table, grid, trials)
    set_motor(c, eps, gain)
    return float(hits(play(c, seconds, learn=False, test=True)).mean())


def variants(tab: torch.Tensor, grid: torch.Tensor) -> dict[str, torch.Tensor]:
    sym = tab.mean(dim=2, keepdim=True).expand_as(tab).contiguous()                 # (grid, canlı, 2)
    s = grid.view(-1, 1)
    a = (sym[:, :, 0] * s).sum(0) / (s * s).sum()                                    # (canlı,) V = a·s
    lin = (a.view(1, -1) * s).unsqueeze(2).expand_as(tab).contiguous()
    return {"tablo": tab, "simetrik": sym, "ortak_dogru": lin}


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", default="O1a")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--eps", default="0.02,0.1,0.5,2,8")
    ap.add_argument("--gains", default="10,20,40,60,120")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.seed >= 200:
        raise SystemExit("geliştirme aracı doğrulayıcı tohumlarıyla (≥200) çalıştırılamaz")
    torch.set_num_threads(a.threads)
    pre = checkpoint.load(a.pre)
    agents = list(range(min(a.agents, pre.world.B)))
    t0 = time.time()
    c = make_game_creature(pre, a.game, "reference", agents, a.trials, a.seed)
    tab, grid = build_table(pre, c, agents, a.trials)
    kw = dict(pre=pre, game=a.game, agents=agents, trials=a.trials, seed=a.seed, seconds=a.seconds)
    an = _play(arm="anosmic", **kw)
    rows = [f"anosmik {an:.3f}"]
    L = [f"# Boşluk ayrıştırması (geliştirme; kanıt değildir): {a.game}, oyun tohumu {a.seed}", "",
         f"{len(agents)} canlı × {a.trials} deneme, ön-eğitim `{a.pre}`; anosmik {an:.3f}.", "",
         f"## Değer tablosu varyantları (kontrol noktasındaki motor: ε={pre.cfg.motor.contrast_eps:g}, turn_gain={pre.cfg.motor.turn_gain:g}, wander_σ={pre.cfg.motor.wander_sigma:g})", "", "| değer kaynağı | p_hit |", "|---|---|"]
    ref = _play(arm="reference", **kw)
    L.append(f"| referans (elle) | {ref:.3f} |")
    for name, t in variants(tab, grid).items():
        v = _play(arm="reference", table=t, grid=grid, **kw)
        L.append(f"| {name} | {v:.3f} |")
        print(f"[{time.time() - t0:4.0f}s] {name}: {v:.3f}", flush=True)
    L += ["", "## Motor kuralı taraması (satır ε, sütun turn_gain)", ""]
    gains = [float(x) for x in a.gains.split(",")]
    for who, table in (("tablo", tab), ("referans", None)):
        L += [f"**{who}**", "", "| ε \\ turn_gain | " + " | ".join(f"{g:g}" for g in gains) + " |", "|---|" + "---|" * len(gains)]
        for e in [float(x) for x in a.eps.split(",")]:
            cells = []
            for g in gains:
                cells.append(f"{_play(arm='reference', table=table, grid=grid if table is not None else None, eps=e, gain=g, **kw):.3f}")
            L.append(f"| {e:g} | " + " | ".join(cells) + " |")
            print(f"[{time.time() - t0:4.0f}s] {who} ε={e:g}: {cells}", flush=True)
        L.append("")
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
