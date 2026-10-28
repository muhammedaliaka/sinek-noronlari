"""Dört koku oyunu için ön-eğitimli canlı kümesi (docs/dort_koku_oyunu_plani.md Z-22): tohum başına BİR kez.

    python -m sinek.experiments.odor_pretrain --seed 100 --out results/odor_games/pre_s100.npz

Evre 2b'nin A fazıyla aynı kurulum: bağlantı-tabanlı beyin, `V2_SET` hareket okuması (donmuş), eğitimsiz ağdan sınıf dengesi ve koku çifti
kalibrasyonu, rol dengeli yarı yarıya, 12 bölüm x 60 sn, ödül = koku A. Çıktı bir checkpoint'tir (ağırlıklar, koku desenleri, rol maskesi).
Geliştirme tohumları 100-149; doğrulayıcı ön-eğitim tohumları ön-kayıtta yazılır (R-2).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..connectome import mbmodel
from ..games.protocol import pretrain
from ..world import odor_patterns
from . import evre2


def main(argv=None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--episodes", type=int, default=12)
    ap.add_argument("--episode-seconds", type=float, default=60.0)
    ap.add_argument("--calib-candidates", type=int, default=40)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--data-dir", default=mbmodel.DEFAULT_DIR)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.threads:
        torch.set_num_threads(a.threads)
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:6.0f}s] {m}", flush=True)    # noqa: E731
    cfg = mbmodel.connectome_config(a.data_dir)
    for item in evre2.V2_SET:
        evre2.apply_override(cfg, item)
    bal = evre2.calibrate_balance(cfg, device=a.device)
    cfg.cbrain.class_balance = bal["class_balance"]
    log(f"sınıf dengesi {bal['class_balance']:.3f}")
    patterns, info = evre2.calibrate_odors(cfg, a.calib_candidates, seed0=5000 + 100 * a.seed, device=a.device)
    log(f"koku çifti: tohum {info['pattern_seed']}, iç fark skoru {info['chosen_score']:.3f}")
    creature = pretrain(cfg, patterns, a.agents, a.seed, a.episodes, a.episode_seconds, a.device, log=log)
    out = checkpoint.save(creature, a.out, extra={"phase": "odor_games_pretrain", "calibration": info, "balance": bal,
                                                   "episodes": a.episodes, "seed": a.seed})
    Path(str(out) + ".json").write_text(json.dumps({"calibration": info, "balance": bal, "args": vars(a),
                                                     "wall_seconds": time.time() - t0}, indent=1, default=str))
    log(f"kaydedildi: {out}")
    return out


if __name__ == "__main__":
    main()
