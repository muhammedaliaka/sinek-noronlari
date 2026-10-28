"""Altın koşu + cihaz duman testi (GPU devri, docs/birlestirme_risk_analizi.md §9 madde 2 ve 6).

    python3 -I -m sinek.experiments.altin_kosu --device cpu --write-ref docs/altin_kosu_referans.json   # referansı üret (CPU)
    python3 -I -m sinek.experiments.altin_kosu --device cuda --check docs/altin_kosu_referans.json     # yeni makinede denetle

Küçük ve belirlenimcidir: gerçek MaleCNS mantar cismi alt ağı, 16 canlı, koku A + tatlı ödül (4 edinim), A/B testi (öğrenme kapalı).
Ölçüler: seçicilik sel = V_A − V_B (canlılar üzerinden ortalama), son edinim sonrası ortalama |ΔW|, KC gerilimi>0 oranı (son adım; kaba bir etkinlik göstergesi), adım/sn.

İki denetim:
  (1) AYNI cihazda tekrar: bit-bit aynı olmak ZORUNDA (belirlenimcilik).
  (2) CPU↔GPU: Poisson akışı cihaza özgüdür (torch.Generator CPU ve CUDA'da farklı sayı üretir), yani nokta nokta eşleşme beklenmez.
      Karşılaştırma İSTATİSTİKSELDİR: referans dosyası CPU'da 8 farklı beyin tohumunun ölçü ortalaması ve ayrıkları (SD) ile gelir;
      kontrol edilen ölçü, referans ortalamasının ±4·SD (en az mutlak tolerans `MIN_TOL`) içinde olmalıdır. Tolerans koşudan ÖNCE yazılmıştır.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from ..connectome import mbmodel
from ..brains import make_brain
from ..world import odor_patterns

CLASS_BALANCE = 1.215          # evre2.calibrate_balance(n_patterns=8) çıktısı (geliştirme tohumları), burada sabit: koşu kalibrasyondan bağımsız
N_CREAT, ACQ, STEPS, REW = 16, 4, 50, (20, 40)
REF_SEEDS = tuple(range(8))
MIN_TOL = {"sel": 0.02, "dw": 0.002, "kc_active": 0.002}
K_SD = 4.0


def _present(brain, odor, learn: bool, reward: bool) -> torch.Tensor:
    brain.reset_state()
    g = odor.view(1, 1, -1).expand(brain.B, 2, -1).contiguous().to(brain.device)
    z = torch.zeros(brain.B, device=brain.device)
    taste, touch = z.clone(), z.clone()
    vals = []
    for t in range(STEPS):
        win = REW[0] <= t < REW[1]
        taste[:] = 1.0 if (reward and win) else 0.0
        touch[:] = 1.0 if (reward and win) else 0.0
        v = brain.step(g, taste, touch, learn=learn)
        if t >= STEPS // 2:
            vals.append(v.mean(1))
    return torch.stack(vals).mean(0)


def one_run(device: str, seed: int) -> dict:
    cfg = mbmodel.connectome_config()
    cfg.cbrain.class_balance = CLASS_BALANCE
    pat = odor_patterns(cfg.world, 7001)
    A, B = pat[0], pat[1]
    brain = make_brain(cfg, N_CREAT, seed, device)
    w0 = brain.W.clone()
    t0 = time.time()
    for _ in range(ACQ):
        _present(brain, A, True, True)
        _present(brain, B, True, False)
    eta = brain.eta_scale.clone()
    brain.eta_scale = torch.zeros_like(eta)
    va, vb = _present(brain, A, False, False), _present(brain, B, False, False)
    if device != "cpu":
        torch.cuda.synchronize()
    dt = time.time() - t0
    n_steps = (2 * ACQ + 2) * STEPS
    return {"sel": float((va - vb).mean()), "dw": float((brain.W - w0).abs().mean()),
            "kc_active": float((brain.v_kc > 0).float().mean()), "steps_per_s": n_steps / dt}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--seed", type=int, default=0, help="denetlenen koşunun beyin tohumu (referans tohumlarından biri)")
    ap.add_argument("--write-ref", default=None, help="CPU'da 8 tohumlu referansı yaz")
    ap.add_argument("--check", default=None, help="referans dosyasına karşı denetle")
    ap.add_argument("--threads", type=int, default=1)
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    if a.device.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("CUDA yok: --device cuda kullanılamaz")
    r1 = one_run(a.device, a.seed)
    r2 = one_run(a.device, a.seed)
    same = all(r1[k] == r2[k] for k in ("sel", "dw", "kc_active"))
    print(f"[{a.device}] tohum {a.seed}: sel {r1['sel']:+.4f} dW {r1['dw']:.5f} KC etkin {r1['kc_active']:.4f} ({r1['steps_per_s']:.0f} adım/sn)")
    print(f"aynı cihazda tekrar bit-bit aynı: {same}")
    if not same:
        raise SystemExit("belirlenimcilik denetimi BAŞARISIZ")
    if a.write_ref:
        if a.device != "cpu":
            raise SystemExit("referans yalnız CPU'da yazılır")
        runs = [one_run("cpu", s) for s in REF_SEEDS]
        ref = {k: {"mean": float(np.mean([r[k] for r in runs])), "sd": float(np.std([r[k] for r in runs], ddof=1)),
                   "by_seed": [r[k] for r in runs]} for k in MIN_TOL}
        ref["_meta"] = {"torch": torch.__version__, "class_balance": CLASS_BALANCE, "n_creat": N_CREAT, "acq": ACQ, "ref_seeds": list(REF_SEEDS),
                        "k_sd": K_SD, "min_tol": MIN_TOL}
        Path(a.write_ref).parent.mkdir(parents=True, exist_ok=True)
        Path(a.write_ref).write_text(json.dumps(ref, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"referans yazıldı: {a.write_ref}")
    if a.check:
        ref = json.loads(Path(a.check).read_text(encoding="utf-8"))
        ok = True
        for k, tol0 in MIN_TOL.items():
            tol = max(K_SD * ref[k]["sd"], tol0)
            d = abs(r1[k] - ref[k]["mean"])
            good = d <= tol
            ok &= good
            print(f"  {k}: {r1[k]:.5f} referans {ref[k]['mean']:.5f} ±{tol:.5f}  {'GEÇTİ' if good else 'KALDI'}")
        print("ALTIN KOŞU:", "GEÇTİ" if ok else "KALDI")
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
