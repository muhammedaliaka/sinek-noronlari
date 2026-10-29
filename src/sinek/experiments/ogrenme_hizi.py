"""Öğrenme HIZI, GELİŞTİRME (kanıt değildir; docs/evre3_dan_plani.md §7): edinim / sönüm / tersine çevirme için "ölçüte kaç denemede ulaştı".

    python3 -I -m sinek.experiments.ogrenme_hizi --scales 0.03,0.1,0.3,1 --variants "V0;V2/-:g_mbon=0.03" --out results/ogrenme_hizi/a.md

`dan_dev` protokolü (oyun dünyası yok; doğrudan beyin; koku A + tatlı ödül 0,4 sn × her deneme, ödülsüz B), ama her denemeden sonra öğrenmesi kapalı test yapılır ve
canlı başına İLK ölçüt geçişi alınır (geçmeyen = sansürlü, `--max` + 1):
  edinim      sel = V_A − V_B ≥ theta_acq (0,20)
  sönüm       A temaslı ama tatsız (decoy tüketimi); sel ≤ 0,5 · sönüm öncesi sel
  tersine çev. B ödüllü, A ödülsüz; sel_BA = V_B − V_A ≥ theta_acq
Öğrenme hızı `brain.eta_scale` (öğrenme oranı çarpanı) ile taranır; 1,0 = ön-kayıtlı doğrulayıcı beyni.
ÖNCEDEN YAZILMIŞ TAHMİN (R-8, koşudan önce): W ← W·exp(−η·iz·D·dt) olduğundan her denemedeki seçicilik artışı ≈ ölçekle doğru orantılı ve plato (okuma tavanı) ölçekten bağımsızdır;
bu yüzden edinim süresi küçük ölçeklerde ≈ 1/ölçek, ölçek ≥ 1'de ise tavan etkisiyle 1 denemede kalır; sönüm de benzer; tersine çevirme edinimden YAVAŞ
(önce A'nın baskılanmış ağırlıklarının geri yüklenmesi gerekir). Büyük ölçeklerde (≥3) aşırı genelleme (ödülsüz B'nin de baskılanması) ve sahte öğretmen artabilir.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from ..brain_dan import DanBrain
from ..connectome import mbmodel
from ..world import odor_patterns
from .dan_dev import _present, parse_variant
from .evre2 import calibrate_balance


def _sel(brain, X, Y) -> np.ndarray:
    vx, _ = _present(brain, X, False, False)
    vy, _ = _present(brain, Y, False, False)
    return (vx - vy).numpy()


def _first(hist: list[np.ndarray], ok, maxn: int) -> np.ndarray:
    """hist[n-1] = n. denemeden sonraki canlı başına ölçü; ok(ölçü) → bool; ilk geçiş (yoksa maxn+1)."""
    h = np.stack(hist)                                   # (n, canlı)
    passed = ok(h)
    first = np.where(passed.any(0), passed.argmax(0) + 1, maxn + 1)
    return first


def run(cfg, dcfg, scale: float, seed: int, creatures: int, patterns: int, maxn: int, theta: float) -> dict:
    acq, ext, rev, spur, peak = [], [], [], [], []
    for ps in range(patterns):
        pat = odor_patterns(cfg.world, 7001 + ps)
        A, B = pat[0], pat[1]
        brain = DanBrain(cfg.cbrain, creatures, seed + ps, dt_world=cfg.world.dt, substeps=cfg.substeps, dcfg=dcfg)
        brain.eta_scale = torch.full((creatures,), float(scale))
        h = []
        for _ in range(maxn):
            _present(brain, A, True, True); _present(brain, B, True, False)
            h.append(_sel(brain, A, B))
        acq.append(_first(h, lambda x: x >= theta, maxn)); pk = np.stack(h)[-1]; peak.append(pk)
        h = []
        for _ in range(maxn):
            _present(brain, A, True, False, contact=True)
            h.append(_sel(brain, A, B))
        ext.append(_first(h, lambda x: x <= 0.5 * np.maximum(pk, 1e-9), maxn))
        h = []
        for _ in range(maxn):
            _present(brain, B, True, True); _present(brain, A, True, False)
            h.append(-_sel(brain, A, B))                 # sel_BA = V_B − V_A
        rev.append(_first(h, lambda x: x >= theta, maxn))
        _, (p0, q0) = _present(brain, B, False, False, record=True)
        spur.append(float(p0.mean() + q0.mean()))
    f = lambda xs: np.concatenate(xs)
    return {"acq": f(acq), "ext": f(ext), "rev": f(rev), "spur": np.mean(spur), "plato": float(np.mean(f(peak))), "dan_max": brain.dan_max}


def cell(x: np.ndarray, maxn: int) -> str:
    cens = float((x > maxn).mean())
    return f"{np.median(x):.0f} ({np.mean(np.minimum(x, maxn + 1)):.1f}; sansür {cens:.0%})"


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scales", default="0.03,0.1,0.3,1")
    ap.add_argument("--variants", default="V0")
    ap.add_argument("--creatures", type=int, default=6)
    ap.add_argument("--patterns", type=int, default=3)
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--theta", type=float, default=0.20)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.seed >= 150:
        raise SystemExit("geliştirme aracı: tohum < 150 (R-2)")
    torch.set_num_threads(a.threads)
    cfg = mbmodel.connectome_config()
    t0 = time.time()
    cfg.cbrain.class_balance = calibrate_balance(cfg, n_patterns=8)["class_balance"]
    L = ["# Öğrenme hızı (geliştirme; kanıt değildir)", "",
         f"{a.creatures} canlı × {a.patterns} koku çifti, ölçüt θ={a.theta}, en çok {a.max} deneme; hücre: ortanca (ortalama; sansürlü oranı). Sansürlü = ölçüte {a.max} denemede ulaşmadı (değer {a.max + 1} sayıldı).", "",
         "| varyant | öğrenme ölçeği | edinim | sönüm | tersine çevirme | plato sel | sahte öğretmen | DAN tepe |", "|---|---|---|---|---|---|---|---|"]
    for v in a.variants.split(";"):
        name, dcfg = parse_variant(v)
        for s in [float(x) for x in a.scales.split(",")]:
            r = run(cfg, dcfg, s, a.seed, a.creatures, a.patterns, a.max, a.theta)
            L.append(f"| {name} | {s:g} | {cell(r['acq'], a.max)} | {cell(r['ext'], a.max)} | {cell(r['rev'], a.max)} | {r['plato']:+.2f} | {r['spur']:.3f} | {r['dan_max']:.1f} |")
            print(f"[{time.time() - t0:5.0f}s] {L[-1]}", flush=True)
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
