"""Evre 2b E1 yapısal kontrolü: MBON yaklaş/kaçın sınıf etiketleri karıştırılmış koşular (ön-kayıt: docs/evre2b_plan.md §6).

    python -m sinek.experiments.evre2b_e1 --real results/evre2b_s30 \\
        --shuffle results/evre2b_s30_shuffle1 results/evre2b_s30_shuffle2 --out docs/evre2b_e1_s30.md

Karıştırılmış koşunun A eğitimi sonundaki `plastic` havuzlanmış A-oranı gerçek-etiketli koşudan düşük olmalıdır
(tek yönlü canlı-düzeyi permütasyon, p < 0.01). Karıştırılmış ağ neredeyse hiç seçim yapmıyorsa (seçim oranı < 0.40)
karşılaştırma değerlendirilemez ve E1 o karıştırma için GEÇMEZ (v1'deki "formel geçti ama veri yok" durumunu önlemek için).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .evre2b import ALPHA, GATE_MIN_RATE, STAT_SEED, agent_counts
from .stats import cluster_bootstrap_ci, cluster_permutation_p, pooled_fraction


def _last_a(r: dict) -> dict:
    return next(s for s in reversed(r["stages"]) if s["phase"] == "A")


DESIGN_KEYS = ("agents", "trials", "episodes", "reversal_episodes", "test_every", "test_seconds", "episode_seconds", "swap_roles")


def _check_same_design(real: dict, shuf: dict) -> None:
    """Farkın yalnızca sınıf karıştırmasından gelebilmesi için tasarım ve hareket okuması aynı olmalı (koku çifti hariç)."""
    bad = [k for k in DESIGN_KEYS if real["args"].get(k) != shuf["args"].get(k)]
    if real["config"].get("motor") != shuf["config"].get("motor"):
        bad.append("motor")
    if bad:
        raise ValueError(f"E1 karşılaştırması farklı tasarımlar arasında yapılamaz: {bad}")


def compare(real: dict, shuf: dict) -> dict:
    """Gerçek ve karıştırılmış sonuç sözlüğü (results.json içeriği) için E1 karşılaştırması."""
    _check_same_design(real, shuf)
    na, ns = real["args"]["agents"], shuf["args"]["agents"]
    g_r = agent_counts(_last_a(real), na, "plastic")
    g_s = agent_counts(_last_a(shuf), ns, "plastic")
    rate_s = float((g_s[0].sum() + g_s[1].sum()) / (ns * shuf["args"]["trials"]))
    f_r, f_s = pooled_fraction(*g_r), pooled_fraction(*g_s)
    p = cluster_permutation_p(g_r, g_s, seed=STAT_SEED)
    valid = rate_s >= GATE_MIN_RATE
    ok = bool(valid and f_r > f_s and p < ALPHA)
    return {"pass": ok, "valid": valid, "p": p, "real": (f_r, *cluster_bootstrap_ci(*g_r, seed=STAT_SEED)[1:]),
            "shuf": (f_s, *cluster_bootstrap_ci(*g_s, seed=STAT_SEED)[1:]), "shuf_rate": rate_s,
            "shuf_choices": int(g_s[0].sum() + g_s[1].sum())}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--real", required=True)
    ap.add_argument("--shuffle", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    real = json.loads((Path(a.real) / "results.json").read_text())
    L = ["# Evre 2b E1 — MBON sınıf etiketi karıştırma kontrolü", "",
         f"Gerçek-etiketli koşu: `{Path(a.real).name}` (tohum {real['args']['seed']}). Ölçüt: karıştırılmış `plastic` A-oranı gerçekten düşük "
         f"(p < {ALPHA}) VE karıştırılmış ağın seçim oranı >= {GATE_MIN_RATE}.", "",
         "| koşul | sınıf dengesi | eğitilmiş plastic A-oranı [GA] | seçim sayısı (oran) | p (gerçek > karıştırılmış) | E1 |", "|---|---:|---|---|---:|---|"]
    f, lo, hi = cluster_bootstrap_ci(*agent_counts(_last_a(real), real["args"]["agents"], "plastic"), seed=STAT_SEED)
    L.append(f"| gerçek etiketler | {real['balance']['class_balance']:.3f} | {f:.2f} [{lo:.2f}, {hi:.2f}] | — | — | — |")
    allok = True
    for p in a.shuffle:
        rr = json.loads((Path(p) / "results.json").read_text())
        c = compare(real, rr)
        allok &= c["pass"]
        s = c["shuf"]
        note = "" if c["valid"] else " (değerlendirilemez: seçim oranı düşük)"
        L.append(f"| karıştırma tohum {rr['config']['cbrain']['class_shuffle_seed']} (`{Path(p).name}`) | {rr['balance']['class_balance']:.3f} | "
                 f"{s[0]:.2f} [{s[1]:.2f}, {s[2]:.2f}] | {c['shuf_choices']} ({c['shuf_rate']:.2f}) | {c['p']:.4f} | "
                 f"{'PASS' if c['pass'] else 'FAIL'}{note} |")
    L += ["", f"**E1 genel: {'PASS' if allok else 'FAIL'}** (her karıştırma geçmeli). E1 bir yapısal kontroldür; Evre 2b ana karar kuralına girmez, "
          "ama FAIL ise 'gerçek sınıf yapısı işe yarıyor' iddiası kurulamaz.", ""]
    Path(a.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
