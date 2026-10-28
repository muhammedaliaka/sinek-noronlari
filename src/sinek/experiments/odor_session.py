"""Dört koku oyunu: OTURUM koşusu — ardışık denemeler, öğrenme açık (docs/dort_koku_oyunu_plani.md §3.3, §3.4, §4).

    # O3 çarpanlı kollar (koku yalnız temasta): plastic A/B/C/D + frozen
    python -m sinek.experiments.odor_session --pre results/odor_games/pre_s100.npz --game O3 --seed 102 \
        --arms plastic:A,plastic:B,plastic:C,plastic:D,frozen:A --trials 16 --out results/odor_pilot/O3_s102
    # O4a aldatıcı eğitim + öğrenme kapalı anlık testler (6., 12. bölümde)
    python -m sinek.experiments.odor_session --pre ... --game O4a --seed 103 --arms plastic,frozen,anosmic \
        --trials 12 --snapshots 0,3,6,12 --out results/odor_pilot/O4a_s103

Kol sözdizimi `kol[:o3]`; `kol` = protocol.ARMS anahtarı (plastic, frozen, random, anosmic, naive, naive_plastic, reference), `o3` = A|B|C|D.
Her canlı `--copies` (çift) kopya olarak koşar (ayna çifti); canlı = küme birimi. Pilot sonuçları kanıt değildir (R-2).
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
from ..games.protocol import ARMS, make_game_creature, play, snapshot
from ..games.spec import GAMES
from .stats import paired_cluster_ci


def _parse_arm(token: str) -> tuple[str, str | None]:
    arm, _, o3 = token.partition(":")
    if arm not in ARMS:
        raise SystemExit(f"bilinmeyen kol: {arm}")
    return arm, (o3 or None)


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", required=True, choices=sorted(GAMES))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arms", required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--copies", type=int, default=2, help="canlı başına paralel kopya (çift: ayna çifti)")
    ap.add_argument("--trials", type=int, default=16, help="ardışık deneme/bölüm sayısı")
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--snapshots", default="", help="öğrenme kapalı anlık test yapılacak bölüm sayıları, ör. 0,3,6,12")
    ap.add_argument("--test-copies", type=int, default=8)
    ap.add_argument("--slot", type=int, default=None, help="isabet yuvası (varsayılan: O4 için 1=decoy, diğerleri 0=hedef)")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.threads:
        torch.set_num_threads(a.threads)
    t0 = time.time()
    pre = checkpoint.load(a.pre)
    spec = GAMES[a.game]
    slot = a.slot if a.slot is not None else (1 if a.game in ("O4a", "O4c") else 0)
    agents = list(range(min(a.agents, pre.world.B)))
    snaps = [int(x) for x in a.snapshots.split(",") if x != ""]
    res: dict[str, dict] = {}
    for token in a.arms.split(","):
        arm, o3 = _parse_arm(token)
        c = make_game_creature(pre, a.game, arm, agents, a.copies, a.seed, spec=spec, o3=o3)
        learn = ARMS[arm].eta > 0
        hits, ep_contacts, snap_hits = [], [], {}
        for ep in range(a.trials + 1):
            if ep in snaps:      # öğrenme kapalı anlık test (ayrı dünya, ayrı tohum)
                t = snapshot(c, a.seed + 5000 + ep)
                t.world.set_anosmic(c.world.anosmic)
                out = play(t, a.seconds, learn=False, test=True)
                snap_hits[ep] = {"decoy": (out["slot"] == 1).astype(int).reshape(len(agents), -1).tolist(),
                                 "target": (out["slot"] == 0).astype(int).reshape(len(agents), -1).tolist()}
            if ep == a.trials:
                break
            out = play(c, a.seconds, learn=learn, test=False)
            hits.append((out["slot"] == slot).astype(int).reshape(len(agents), -1))
            ep_contacts.append(out["contacts"].reshape(len(agents), -1, 2).sum(1))
        h = np.stack(hits, axis=-1)                       # (canlı, kopya, bölüm)
        res[token] = {"hits": h, "decoy_contacts": np.stack(ep_contacts, -1), "snap": snap_hits}
        print(f"[{time.time() - t0:6.0f}s] {a.game} {token:<14} p(slot {slot})={h.mean():.3f} "
              f"(ilk yarı {h[..., :a.trials // 2].mean():.3f}, ikinci yarı {h[..., a.trials // 2:].mean():.3f})", flush=True)
    toks = list(res)
    L = [f"# Oturum pilotu: {a.game} (tohum {a.seed}, ön-eğitim {a.pre})", "",
         f"Pilot — kanıt değildir. {len(agents)} canlı x {a.copies} kopya x {a.trials} ardışık deneme, sınır {a.seconds:.0f} sn.",
         f"Ölçü: ilk temas yuva {slot} ({'decoy' if slot == 1 else 'hedef'}).", "",
         "| kol | p_hit (tümü) | ilk yarı | ikinci yarı | deneme-başına eğilim (ilk→son 4'lü) |", "|---|---|---|---|---|"]
    for tk in toks:
        h = res[tk]["hits"]
        k4 = max(1, a.trials // 4)
        L.append(f"| {tk} | {h.mean():.3f} | {h[..., :a.trials // 2].mean():.3f} | {h[..., a.trials // 2:].mean():.3f} | "
                 f"{h[..., :k4].mean():.3f} → {h[..., -k4:].mean():.3f} |")
    L += ["", f"## Eşli farklar ({toks[-1]} tabanına karşı, canlı-kümeli %99 GA; kopya+bölüm ortalaması)", ""]
    base = res[toks[-1]]["hits"].reshape(len(agents), -1)
    paired = {}
    for tk in toks[:-1]:
        x = res[tk]["hits"].reshape(len(agents), -1)
        m, lo, hi = paired_cluster_ci(x.sum(1), base.sum(1), x.shape[1], n=4000, alpha=0.01)
        L.append(f"- {tk} − {toks[-1]}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        paired[tk] = [m, lo, hi]
    if snaps:
        L += ["", "## Anlık testler (öğrenme kapalı, ilk temas): decoy p_hit / hedef p_hit", "",
              "| kol | " + " | ".join(f"bölüm {s}" for s in snaps) + " |", "|---|" + "---|" * len(snaps)]
        for tk in toks:
            cells = []
            for s in snaps:
                sh = res[tk]["snap"][s]
                cells.append(f"{np.mean(sh['decoy']):.3f} / {np.mean(sh['target']):.3f}")
            L.append(f"| {tk} | " + " | ".join(cells) + " |")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "results.json").write_text(json.dumps({
        "args": vars(a), "spec": dataclasses.asdict(spec), "wall_seconds": time.time() - t0, "paired": paired,
        "arms": {tk: {"hits": res[tk]["hits"].tolist(), "decoy_contacts": res[tk]["decoy_contacts"].tolist(),
                      "snap": res[tk]["snap"]} for tk in toks}}, indent=1), encoding="utf-8")
    print("\n".join(L))
    return res


if __name__ == "__main__":
    main()
