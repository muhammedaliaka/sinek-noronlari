"""Dört koku oyunu: DOĞRULAYICI koşu — alan-rehberliği oyunları O1 (O1a/O1b) ve O2 (O2near; O2full yalnız betimsel).

    python -m sinek.experiments.odor_validate --pre results/odor_games/pre_s200.npz --game O1a --seed 210 --out results/odor_val/O1a_s210

Eşikler ve tasarım ön-kayıt belgesindedir (docs/odor_o1_plani.md, docs/odor_o2_plani.md); bu komut onları KEŞFETMEZ, komut satırından alır ve
sonuç dosyasına yazar. Ön-kayıt commit'inden önce doğrulayıcı tohumlarla (200-serisi) çalıştırılmamalıdır; `--pilot` bayrağı geliştirme
tohumlarında (<200) denemek içindir ve sonuca "pilot" damgası basar (R-2).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import hits, leak_check, make_game_creature, play
from .odor_eval import EVALUATORS, Thr

ARMS = ("frozen", "anosmic", "random", "reference")


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "bilinmiyor"


def _sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def validate(pre, game: str, seed: int, agents: int, trials: int, seconds: float, thr: Thr, threads: int | None = None,
             verbose: bool = True) -> dict:
    ids = list(range(min(agents, pre.world.B)))
    res, t0 = {}, time.time()
    for arm in ARMS:
        c = make_game_creature(pre, game, arm, ids, trials, seed)
        res[arm] = play(c, seconds, learn=False, test=True, n_agents=len(ids))
        if verbose:
            print(f"[{time.time() - t0:6.0f}s] {game} {arm:<9} p_hit={hits(res[arm]).mean():.3f}", flush=True)
    h = {a: hits(res[a]) for a in ARMS}
    leak = leak_check(res["frozen"], res["anosmic"])
    extra = {"sizinti_ihlali==0": leak["violations"] == 0}
    ev = EVALUATORS["O1" if game.startswith("O1") else "O2"](h, thr, extra)
    seen = {a: float((res[a]["first_odor_step"] >= 0).mean()) for a in ARMS}
    return {"game": game, "seed": seed, "agents": len(ids), "trials": trials, "seconds": seconds, "p_hit": {a: float(h[a].mean()) for a in ARMS},
            "odor_seen": seen, "leak": leak, "eval": ev, "mirror_halves": {a: [float(h[a][:, 0::2].mean()), float(h[a][:, 1::2].mean())] for a in ARMS},
            "wall_seconds": time.time() - t0}


def report(r: dict, thr: Thr, meta: dict) -> str:
    ev = r["eval"]
    L = [f"# Doğrulayıcı koşu: {r['game']} (oyun tohumu {r['seed']})", "",
         f"{meta['stamp']} Ön-eğitim: `{meta['pre']}` (sha256[:16] {meta['pre_sha']}), kod commit `{meta['git']}`.", "",
         f"{r['agents']} canlı × {r['trials']} deneme, T={r['seconds']:.0f} sn; δ={thr.delta}, α={thr.alpha}, referans kapısı ≥{thr.ref_min}, "
         f"anosmik penceresi [{thr.anos_lo}, {thr.anos_hi}] (yalnız O1).", "",
         "| kol | p_hit | koku görülen deneme | ayna yarıları (özgün/ayna) |", "|---|---|---|---|"]
    for a in ARMS:
        L.append(f"| {a} | {r['p_hit'][a]:.3f} | {r['odor_seen'][a]:.2f} | {r['mirror_halves'][a][0]:.3f} / {r['mirror_halves'][a][1]:.3f} |")
    L += ["", "## Kapılar", ""] + [f"- {'✔' if v else '✘'} {k}" for k, v in ev["gates"].items()]
    L += ["", f"Sızıntı: denetlenen {r['leak']['checked']} deneme, ihlal {r['leak']['violations']}.", "", "## Ölçütler", ""]
    for k, c in ev["criteria"].items():
        if "halves" in c:
            L.append(f"- {'✔' if c['passed'] else '✘'} {k}: yarılar " + ", ".join(f"{x['mean']:+.3f} [{x['ci'][0]:+.3f}, {x['ci'][1]:+.3f}]" for x in c["halves"]))
        else:
            L.append(f"- {'✔' if c['passed'] else '✘'} {k}: fark {c['mean']:+.3f} [%99 GA {c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}], p={c['p']:.4f}")
    L += ["", f"**Karar (bu tohum): {'BAŞARILI' if ev['passed'] else 'BAŞARISIZ'}** (kapılar {'tamam' if ev['gates_ok'] else 'EKSİK'}).",
          "Tüm doğrulayıcı tohumlarda geçmedikçe oyun başarılı sayılmaz; başarısızlık olduğu gibi raporlanır."]
    return "\n".join(L) + "\n"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", required=True, choices=["O1a", "O1b", "O2near", "O2full"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--trials", type=int, default=16)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--delta", type=float, default=0.15)
    ap.add_argument("--ref-min", type=float, default=0.80)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--pilot", action="store_true", help="geliştirme tohumu: sonuca pilot damgası")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.seed >= 200 and a.pilot:
        raise SystemExit("--pilot yalnız geliştirme tohumlarıyla (<200)")
    if a.seed < 200 and not a.pilot:
        raise SystemExit("200 altı tohum doğrulayıcı olamaz: --pilot ekleyin (R-2)")
    if a.threads:
        torch.set_num_threads(a.threads)
    thr = Thr(delta=a.delta, ref_min=a.ref_min, n_boot=a.boot, n_perm=a.boot)
    pre = checkpoint.load(a.pre)
    r = validate(pre, a.game, a.seed, a.agents, a.trials, a.seconds, thr)
    meta = {"stamp": "**PİLOT — kanıt değildir.**" if a.pilot else "Doğrulayıcı koşu.", "pre": a.pre, "pre_sha": _sha(a.pre), "git": _git_head()}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(report(r, thr, meta), encoding="utf-8")
    (out / "results.json").write_text(json.dumps({"args": vars(a), "meta": meta, **r}, indent=1, default=float), encoding="utf-8")
    print(report(r, thr, meta))
    return r


if __name__ == "__main__":
    main()
