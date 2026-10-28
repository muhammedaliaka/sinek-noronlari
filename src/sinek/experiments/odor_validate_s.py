"""Dört koku oyunu: DOĞRULAYICI koşu — oturum oyunları O3 (koku yalnız temasta), O4a (sönüm), O4c (decoy + kokusuz gerçek hedef).

    python -m sinek.experiments.odor_validate_s --pre results/odor_val/pre_s200.npz --game O3 --seed 230 --out results/odor_val/O3_s230

Eşikler ve tasarım ön-kayıt belgelerindedir (docs/odor_o3_plani.md, docs/odor_o4_plani.md); komut onları keşfetmez. 200 altı tohum yalnız `--pilot` ile.

* O3: kollar plastic:A/B/C/D ve frozen:A; her canlı `copies` kopya x `trials` ardışık deneme (öğrenme plastic'te açık, tüketimli eğitim kipi);
  ölçü ilk temasın hedef olması; değerlendirici `eval_o3` (eşdeğerlik). Kapı: koşu boyunca alan hiç görülmedi (ön-temas glom ≡ 0).
* O4a/O4c: plastic aldatıcı eğitim görür (`trials` bölüm x `copies` kopya); frozen ve anosmic öğrenmediği için eğitim görmez (ağırlıkları değişmez);
  eğitim sonunda öğrenmesi kapalı bağımsız test (her eleman `test_reps` kez kopyalanır, ayrı tohum, tüm kollar için aynı yerleşimler).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import ARMS, make_game_creature, play, snapshot
from .odor_eval import EVALUATORS, Thr
from .odor_validate import _git_head, _sha

import json

O3_TOKENS = ("plastic:A", "plastic:B", "plastic:C", "plastic:D", "frozen:A")


def _parse(token: str):
    arm, _, o3 = token.partition(":")
    return arm, (o3 or None)


def run_o3(pre, seed: int, agents: int, copies: int, trials: int, seconds: float, verbose=True) -> dict:
    ids = list(range(min(agents, pre.world.B)))
    hits, seen, t0 = {}, 0, time.time()
    for tok in O3_TOKENS:
        arm, o3 = _parse(tok)
        c = make_game_creature(pre, "O3", arm, ids, copies, seed, o3=o3)
        learn = ARMS[arm].eta > 0
        slots = []
        for _ in range(trials):
            out = play(c, seconds, learn=learn, test=False)
            slots.append(out["slot"].reshape(len(ids), copies))
            seen += int((out["first_odor_step"] >= 0).sum())
        h = (np.stack(slots, -1) == 0).astype(int).reshape(len(ids), -1)       # (canlı, kopya*deneme)
        hits[tok] = h
        if verbose:
            print(f"[{time.time() - t0:6.0f}s] O3 {tok:<10} p_hit={h.mean():.3f}", flush=True)
    return {"hits": hits, "field_seen_trials": seen, "n_creatures": len(ids)}


def run_o4(pre, game: str, seed: int, agents: int, copies: int, trials: int, seconds: float, test_reps: int, snap_eps=(3, 6),
           verbose=True) -> dict:
    ids = list(range(min(agents, pre.world.B)))
    out, t0 = {}, time.time()
    for arm in ("plastic", "frozen", "anosmic"):
        c = make_game_creature(pre, game, arm, ids, copies, seed)
        learn = ARMS[arm].eta > 0
        snaps = {}
        for ep in range(trials + 1):
            if (learn and ep in snap_eps) or ep == trials:
                t = snapshot(c, seed + 5000 + ep, reps=test_reps)
                o = play(t, seconds, learn=False, test=True)
                snaps[ep] = o["slot"].reshape(len(ids), -1)
            if ep == trials:
                break
            if learn:
                play(c, seconds, learn=True, test=False)
        out[arm] = snaps
        if verbose:
            s = snaps[trials]
            print(f"[{time.time() - t0:6.0f}s] {game} {arm:<8} test(ep {trials}): decoy-ilk {np.mean(s == 1):.3f} gerçek-ilk {np.mean(s == 0):.3f}", flush=True)
    return {"slots": out, "n_creatures": len(ids)}


def evaluate(game: str, run: dict, trials: int, thr: Thr) -> dict:
    if game == "O3":
        extra = {"G3_on_temas_alan_yok": run["field_seen_trials"] == 0}
        return EVALUATORS["O3"](run["hits"], thr, extra)
    slots = {arm: run["slots"][arm][trials] for arm in ("plastic", "frozen", "anosmic")}
    if game == "O4a":
        return EVALUATORS["O4a"]({k: (v == 1).astype(int) for k, v in slots.items()}, thr)
    return EVALUATORS["O4c"](slots, thr)


def report(game: str, seed: int, ev: dict, run: dict, trials: int, thr: Thr, meta: dict) -> str:
    L = [f"# Doğrulayıcı koşu: {game} (oyun tohumu {seed})", "",
         f"{meta['stamp']} Ön-eğitim: `{meta['pre']}` (sha256[:16] {meta['pre_sha']}), kod commit `{meta['git']}`.", "",
         f"δ={thr.delta}, δ_eq={thr.delta_eq}, α={thr.alpha}, çekim kapısı ≥{thr.attract_mult}δ.", ""]
    if game == "O3":
        L += ["| kol | p_hit |", "|---|---|"] + [f"| {k} | {v.mean():.3f} |" for k, v in run["hits"].items()]
        L += ["", f"Koşu boyunca alan görülen deneme: {run['field_seen_trials']} (0 olmalı)."]
    else:
        L += ["| kol | decoy-ilk | gerçek-ilk | hiçbiri |", "|---|---|---|---|"]
        for arm, snaps in run["slots"].items():
            s = snaps[trials]
            L.append(f"| {arm} (test, bölüm {trials}) | {np.mean(s == 1):.3f} | {np.mean(s == 0):.3f} | {np.mean(s == -1):.3f} |")
        tr = [ep for ep in run["slots"]["plastic"] if ep != trials]
        if tr:
            L += ["", "Plastic eğilim (öğrenme kapalı testler): " + ", ".join(
                f"bölüm {ep}: decoy-ilk {np.mean(run['slots']['plastic'][ep] == 1):.3f}" for ep in sorted(tr)) + f", bölüm {trials}: {np.mean(run['slots']['plastic'][trials] == 1):.3f}"]
    L += ["", "## Kapılar", ""] + [f"- {'✔' if v else '✘'} {k}" for k, v in ev["gates"].items()]
    if "attraction" in ev:
        a = ev["attraction"]
        L.append(f"- çekim odası (frozen − anosmik decoy-ilk): {a['mean']:+.3f} [%99 GA {a['ci'][0]:+.3f}, {a['ci'][1]:+.3f}]")
    L += ["", "## Ölçütler", ""]
    for k, c in ev["criteria"].items():
        extra = f", p={c['p']:.4f}" if "p" in c else ""
        L.append(f"- {'✔' if c['passed'] else '✘'} {k}: fark {c['mean']:+.3f} [GA {c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}]{extra}")
    L += ["", f"**Karar (bu tohum): {'BAŞARILI' if ev['passed'] else 'BAŞARISIZ'}** (kapılar {'tamam' if ev['gates_ok'] else 'EKSİK'}).",
          "Tüm doğrulayıcı tohumlarda geçmedikçe oyun başarılı sayılmaz; başarısızlık olduğu gibi raporlanır."]
    return "\n".join(L) + "\n"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", required=True, choices=["O3", "O4a", "O4c"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--copies", type=int, default=None, help="O3 için 4, O4 için 2 (varsayılan)")
    ap.add_argument("--trials", type=int, default=None, help="O3: ardışık deneme (varsayılan 16); O4: aldatıcı eğitim bölümü (varsayılan 12)")
    ap.add_argument("--test-reps", type=int, default=8, help="O4 testinde eleman başına kopya (çift)")
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--delta", type=float, default=0.15)
    ap.add_argument("--delta-eq", type=float, default=0.10)
    ap.add_argument("--attract-mult", type=float, default=1.0)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.seed >= 200 and a.pilot:
        raise SystemExit("--pilot yalnız geliştirme tohumlarıyla (<200)")
    if a.seed < 200 and not a.pilot:
        raise SystemExit("200 altı tohum doğrulayıcı olamaz: --pilot ekleyin (R-2)")
    if a.threads:
        torch.set_num_threads(a.threads)
    copies = a.copies if a.copies is not None else (4 if a.game == "O3" else 2)
    trials = a.trials if a.trials is not None else (16 if a.game == "O3" else 12)
    thr = Thr(delta=a.delta, delta_eq=a.delta_eq, attract_mult=a.attract_mult, n_boot=a.boot, n_perm=a.boot)
    pre = checkpoint.load(a.pre)
    t0 = time.time()
    run = run_o3(pre, a.seed, a.agents, copies, trials, a.seconds) if a.game == "O3" else \
        run_o4(pre, a.game, a.seed, a.agents, copies, trials, a.seconds, a.test_reps)
    ev = evaluate(a.game, run, trials, thr)
    meta = {"stamp": "**PİLOT — kanıt değildir.**" if a.pilot else "Doğrulayıcı koşu.", "pre": a.pre, "pre_sha": _sha(a.pre), "git": _git_head()}
    text = report(a.game, a.seed, ev, run, trials, thr, meta)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text, encoding="utf-8")
    raw = ({"hits": {k: v.tolist() for k, v in run["hits"].items()}, "field_seen_trials": run["field_seen_trials"]} if a.game == "O3"
           else {"slots": {arm: {str(ep): v.tolist() for ep, v in s.items()} for arm, s in run["slots"].items()}})
    (out / "results.json").write_text(json.dumps({"args": vars(a), "meta": meta, "copies": copies, "trials": trials, "eval": ev, "raw": raw,
                                                  "wall_seconds": time.time() - t0}, indent=1, default=float), encoding="utf-8")
    print(text)
    return ev


if __name__ == "__main__":
    main()
