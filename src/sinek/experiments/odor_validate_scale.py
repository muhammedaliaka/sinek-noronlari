"""Ölçek ekseni DOĞRULAYICISI (docs/olcek_plani.md): topluluk okuması (anten başına K gürültülü kopya) + kısa okuma süresi (τ_valence) O1/O2'de kazanç sağlıyor mu?

    python -m sinek.experiments.odor_validate_scale --pre results/odor_val/pre_s200.npz --game O1a --seed 250 --out results/scale_val/O1a_s250

Kollar (CRN eşli, öğrenme KAPALI): frozen (taban beyin), ens (aynı beyin + EnsembleBrain(K, τ)), anosmic, anosmic_ens, reference.
Eşikler ve tasarım ön-kayıttadır; bu komut onları keşfetmez. Kol-kol kontrol noktası (V-03): biten kol yeniden koşulmaz.
`--pilot`: geliştirme tohumlarında (<200) deneme; doğrulayıcı tohumlar (≥200) `--pilot` olmadan.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..ensemble import EnsembleBrain
from ..games.protocol import hits, leak_check, make_game_creature, play
from .odor_eval import EVALUATORS, Thr
from .odor_validate import _git_head, _sha
from .odor_validate_s import _part

ARM_DEFS = {                      # kol → (oyun kolu, topluluk mu)
    "reference": ("reference", False), "anosmic": ("anosmic", False), "frozen": ("frozen", False),
    "anosmic_ens": ("anosmic", True), "ens": ("frozen", True),
}
KEYS = ("slot", "time", "path_len", "first_odor_step")


CHUNK_STRIDE = 1000               # parça c için dünya tohumu = seed + CHUNK_STRIDE·c (parça 0 = seed)


def _chunks(n_agents: int, chunks: int) -> list[list[int]]:
    if chunks < 1 or n_agents % chunks:
        raise ValueError("canlı sayısı parça sayısına bölünmeli")
    m = n_agents // chunks
    return [list(range(c * m, (c + 1) * m)) for c in range(chunks)]


def run_arms(pre, game: str, seed: int, agents: int, trials: int, seconds: float, k: int, tau: float, verbose=True,
             part_dir=None, key: str = "", chunks: int = 1) -> dict:
    """Her kol canlıların `chunks` eşit parçasında ayrı koşulur (parça başına dünya tohumu seed + 1000·c; TÜM kollarda aynı → CRN eşli kalır)
    ve parça başına kontrol noktasına yazılır: uzun topluluk kolları yeniden başlamalarda en fazla bir parça kaybeder (K-037).
    `chunks=1` önceki davranıştır."""
    ids_all = list(range(min(agents, pre.world.B)))
    parts, res, t0 = _chunks(len(ids_all), chunks), {}, time.time()
    for name, (arm, ens) in ARM_DEFS.items():
        pieces = []
        for ci, ids in enumerate(parts):
            path, z = _part(part_dir, f"sc_{name}_c{ci}", key)
            if z is not None:
                pieces.append({kk: z[kk] for kk in KEYS})
                if verbose:
                    print(f"[{time.time() - t0:6.0f}s] {game} {name:<12} parça {ci + 1}/{chunks} kontrol noktasından okundu", flush=True)
                continue
            c = make_game_creature(pre, game, arm, ids, trials, seed + CHUNK_STRIDE * ci)
            if ens:
                c.brain = EnsembleBrain(c.brain, k, tau_valence=tau)
            out = play(c, seconds, learn=False, test=True, n_agents=len(ids))
            pieces.append({kk: out[kk] for kk in KEYS})
            if path is not None:
                np.savez(path, key=key, **pieces[-1])
            if verbose:
                print(f"[{time.time() - t0:6.0f}s] {game} {name:<12} parça {ci + 1}/{chunks} p_hit={hits(out).mean():.3f}", flush=True)
        res[name] = {kk: np.concatenate([p[kk] for p in pieces], axis=0) for kk in KEYS}
        if verbose:
            print(f"[{time.time() - t0:6.0f}s] {game} {name:<12} p_hit={hits(res[name]).mean():.3f}", flush=True)
    return res


def evaluate(game: str, res: dict, thr: Thr) -> tuple[dict, dict]:
    h = {a: hits(res[a]) for a in res}
    leak = leak_check(res["frozen"], res["anosmic"])
    extra = {"sizinti_ihlali==0": leak["violations"] == 0}
    if game.startswith("O1"):
        extra["anosmik_pencerede"] = bool(thr.anos_lo <= np.mean(h["anosmic"]) <= thr.anos_hi)
    return EVALUATORS["SC"](h, thr, extra), leak


def report(game: str, seed: int, res: dict, ev: dict, leak: dict, thr: Thr, meta: dict) -> str:
    L = [f"# Ölçek ekseni doğrulayıcısı: {game} (oyun tohumu {seed})", "",
         f"{meta['stamp']} Ön-eğitim: `{meta['pre']}` (sha256[:16] {meta['pre_sha']}), kod commit `{meta['git']}`; topluluk K={meta['k']}, τ_valence={meta['tau']}.", "",
         f"δ={thr.delta}, δ_eq={thr.delta_eq}, α={thr.alpha}, referans kapısı ≥{thr.ref_min}.", "",
         "| kol | p_hit |", "|---|---|"] + [f"| {a} | {hits(res[a]).mean():.3f} |" for a in ARM_DEFS]
    L += ["", "## Kapılar", ""] + [f"- {'✔' if v else '✘'} {k}" for k, v in ev["gates"].items()]
    L += ["", f"Sızıntı (taban frozen/anosmic): denetlenen {leak['checked']} deneme, ihlal {leak['violations']}.", "", "## Ölçütler", ""]
    for k, c in ev["criteria"].items():
        p = f", p={c['p']:.4f}" if "p" in c else ""
        L.append(f"- {'✔' if c['passed'] else '✘'} {k}: fark {c['mean']:+.3f} [GA {c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}]{p}")
    for k, c in ev.get("descriptive", {}).items():
        L.append(f"- (betimsel, karar vermez) {k}: fark {c['mean']:+.3f} [GA {c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}], ±δ_eq içinde: {'evet' if c['passed'] else 'hayır'}")
    L += ["", f"**Karar (bu tohum): {'BAŞARILI' if ev['passed'] else 'BAŞARISIZ'}** (kapılar {'tamam' if ev['gates_ok'] else 'EKSİK'}).",
          "Tüm doğrulayıcı tohumlarda geçmedikçe başarılı sayılmaz; başarısızlık olduğu gibi raporlanır."]
    return "\n".join(L) + "\n"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", required=True, choices=["O1a", "O1b", "O2near"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--trials", type=int, default=16)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--chunks", type=int, default=4, help="canlılar bu sayıda parçaya bölünüp kol-kol-parça kontrol noktasıyla koşulur (K-037)")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--tau", type=float, default=0.04)
    ap.add_argument("--delta", type=float, default=0.15)
    ap.add_argument("--delta-eq", type=float, default=0.10)
    ap.add_argument("--ref-min", type=float, default=None, help="varsayılan: O1 0,80; O2-yakın 0,70 (K-024)")
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
    ref_min = a.ref_min if a.ref_min is not None else (0.80 if a.game.startswith("O1") else 0.70)
    thr = Thr(delta=a.delta, delta_eq=a.delta_eq, ref_min=ref_min, n_boot=a.boot, n_perm=a.boot)
    pre = checkpoint.load(a.pre)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    part_dir = out / "partial"
    part_dir.mkdir(exist_ok=True)
    key = json.dumps({"game": a.game, "seed": a.seed, "agents": a.agents, "trials": a.trials, "seconds": a.seconds, "k": a.k, "tau": a.tau,
                      "chunks": a.chunks, "pre_sha": _sha(a.pre)}, sort_keys=True)
    t0 = time.time()
    res = run_arms(pre, a.game, a.seed, a.agents, a.trials, a.seconds, a.k, a.tau, part_dir=part_dir, key=key, chunks=a.chunks)
    ev, leak = evaluate(a.game, res, thr)
    meta = {"stamp": "**PİLOT — kanıt değildir.**" if a.pilot else "Doğrulayıcı koşu.", "pre": a.pre, "pre_sha": _sha(a.pre), "git": _git_head(),
            "k": a.k, "tau": a.tau, "chunks": a.chunks}
    text = report(a.game, a.seed, res, ev, leak, thr, meta)
    (out / "summary.md").write_text(text, encoding="utf-8")
    (out / "results.json").write_text(json.dumps({"args": vars(a), "meta": meta, "eval": ev, "leak": leak,
                                                  "p_hit": {k: float(hits(v).mean()) for k, v in res.items()},
                                                  "wall_seconds": time.time() - t0}, indent=1, default=float), encoding="utf-8")
    print(text)
    return ev


if __name__ == "__main__":
    main()
