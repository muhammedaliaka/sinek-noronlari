"""Verim eğrisi (GPU devri, yol haritası 3.0; geliştirme ölçümü, bilimsel iddia değildir): beyin adımı/sn ve bellek, toplu iş boyutuna göre.

    python3 -I -m sinek.experiments.olcek_egrisi --device cpu --batches 8,32,128 --out results/olcek/cpu.md
    python3 -I -m sinek.experiments.olcek_egrisi --device cuda --batches 64,256,1024,4096 --out results/olcek/cuda.md

Ağ boyutu sabittir (MaleCNS mantar cismi alt ağı, ~4,8 bin nöron/yarımküre); değişen şey `batch` = canlı sayısı (topluluk K ile çarpılırsa canlı·K).
Tam-CNS (160 bin nöron) seyrek yolu bu depoda YOKTUR; bu betik onu ölçmez (risk analizi R-H1).
Bellek: CPU'da süreç tepe RSS'i (MB), CUDA'da `max_memory_allocated` (MB). Her ölçüde ısınma adımları atılır.
"""
from __future__ import annotations

import argparse
import resource
import time
from pathlib import Path

import torch

from ..brains import make_brain
from ..connectome import mbmodel
from ..world import odor_patterns


def measure(device: str, batch: int, steps: int = 30, warm: int = 5) -> dict:
    cfg = mbmodel.connectome_config()
    cfg.cbrain.class_balance = 1.215
    brain = make_brain(cfg, batch, 0, device)
    odor = odor_patterns(cfg.world, 7001)[0]
    g = odor.view(1, 1, -1).expand(batch, 2, -1).contiguous().to(brain.device)
    z = torch.zeros(batch, device=brain.device)
    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    for _ in range(warm):
        brain.step(g, z, z, learn=True)
    if device.startswith("cuda"):
        torch.cuda.synchronize()
    t0 = time.time()
    for _ in range(steps):
        brain.step(g, z, z, learn=True)
    if device.startswith("cuda"):
        torch.cuda.synchronize()
    dt = time.time() - t0
    mem = (torch.cuda.max_memory_allocated() if device.startswith("cuda") else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024) / 2**20
    return {"batch": batch, "n_neurons": batch * 2 * (brain.n_kc + brain.n_mbon), "steps_per_s": steps / dt, "creature_steps_per_s": batch * steps / dt, "mem_mb": mem}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batches", default="8,32,128")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    if a.device.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("CUDA yok")
    rows = ["| toplu iş (canlı) | nöron-örneği (KC+MBON, 2 yarımküre) | adım/sn | canlı·adım/sn | bellek (MB) |", "|---|---|---|---|---|"]
    for b in [int(x) for x in a.batches.split(",") if x]:
        try:
            r = measure(a.device, b)
        except RuntimeError as e:                      # CUDA OOM vb.: sınırı belgele
            rows.append(f"| {b} | — | — | — | HATA: {str(e).splitlines()[0][:60]} |")
            print(rows[-1], flush=True)
            break
        rows.append(f"| {r['batch']} | {r['n_neurons']:,} | {r['steps_per_s']:.1f} | {r['creature_steps_per_s']:.0f} | {r['mem_mb']:.0f} |")
        print(rows[-1], flush=True)
    text = "\n".join([f"# Verim eğrisi ({a.device}, torch {torch.__version__}, {a.threads} iş parçacığı)", "", *rows]) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
