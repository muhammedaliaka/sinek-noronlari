"""Evre 3.3 GELİŞTİRME harness'ı (kanıt değildir): DAN devresi varyantlarının koşullama özellikleri, tam spiking beyinde.

    python3 -I -m sinek.experiments.dan_dev --variants V0,V1:g_kc=3 --out results/dan_dev/a.md

Protokol (oyun dünyası yok, doğrudan beyin): koku A + tatlı ödül (0,4 sn temas) × `acq` deneme, her denemede ödülsüz koku B;
sonra koku A temaslı ama ödülsüz (decoy tüketimi: touch=1, tat=0) × `ext` sönüm denemesi. Öğrenmesi kapalı testlerle A ve B değeri ölçülür (son 0,5 sn ortalaması).
Ölçüler: seçicilik sel = V_A − V_B, tahmin indeksi (PAM yanıtı son/ilk ödüllü deneme), ödülsüz sunumda sahte öğretmen etkinliği, DAN tepe değeri.
Kokular: `odor_patterns` desen tohumları 7001..7000+n_pat (geliştirme; oyun/doğrulayıcı tohumlarıyla ilgisi yok).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from ..brain_dan import DanBrain, DanConfig
from ..connectome import mbmodel
from ..world import odor_patterns
from .evre2 import calibrate_balance

DT_STEPS = 50          # 1,0 sn @ 0,02 sn
REW = (20, 40)         # ödül penceresi (0,4 sn temas)


def parse_variant(s: str) -> tuple[str, DanConfig]:
    name, _, kv = s.partition(":")
    kw = {}
    for item in filter(None, kv.split(",")):
        k, v = item.split("=")
        kw[k] = v if k == "wiring" else float(v) if k != "wiring_seed" else int(v)
    mode = name.split("/")[0]
    return s, DanConfig(mode=mode, **kw)


def _present(brain, odor, learn: bool, reward: bool, record: bool = False, contact: bool = False):
    brain.reset_state()
    g = odor.view(1, 1, -1).expand(brain.B, 2, -1).contiguous()
    taste, touch = torch.zeros(brain.B), torch.zeros(brain.B)
    pam, ppl, vals = [], [], []
    for t in range(DT_STEPS):
        win = REW[0] <= t < REW[1]
        taste[:] = 1.0 if (reward and win) else 0.0
        touch[:] = 1.0 if ((reward or contact) and win) else 0.0     # contact: temas var, tat yok (O4 decoy tüketimi)
        v = brain.step(g, taste, touch, learn=learn)
        if record:
            own = brain._own if hasattr(brain, "_own") else None
            if own is not None:
                pam.append(own[:, ~brain.dan_is_ppl].mean().item()); ppl.append(own[:, brain.dan_is_ppl].mean().item())
        if t >= DT_STEPS // 2:
            vals.append(v.mean(1))
    val = torch.stack(vals).mean(0)                      # (B,)
    return val, (np.array(pam), np.array(ppl))


def run_variant(cfg, dcfg: DanConfig, seed: int, n_creat: int, n_pat: int, acq: int, ext: int,
                tests_acq=(1, 2, 4, 8, 12), tests_ext=(2, 4, 8)) -> dict:
    out = {"acq": {n: [] for n in tests_acq}, "ext": {n: [] for n in tests_ext}, "naive": [], "pam_first": [], "pam_last": [], "spur": [], "dan_max": 0.0}
    for ps in range(n_pat):
        pat = odor_patterns(cfg.world, 7001 + ps)
        A, B = pat[0], pat[1]
        brain = DanBrain(cfg.cbrain, n_creat, seed + ps, dt_world=cfg.world.dt, substeps=cfg.substeps, dcfg=dcfg)
        va, _ = _present(brain, A, False, False); vb, _ = _present(brain, B, False, False)
        out["naive"].append((va - vb).mean().item())
        for n in range(1, acq + 1):
            _, (pam, ppl) = _present(brain, A, True, True, record=True)
            _present(brain, B, True, False)
            if n == 1:
                out["pam_first"].append(float(pam[REW[0]:REW[1]].mean()))
            if n == acq:
                out["pam_last"].append(float(pam[REW[0]:REW[1]].mean()))
            if n in tests_acq:
                va, _ = _present(brain, A, False, False); vb, _ = _present(brain, B, False, False)
                out["acq"][n].append((va - vb).mean().item())
        _, (pam0, ppl0) = _present(brain, A, False, False, record=True)
        out["spur"].append(float(pam0.mean() + ppl0.mean()))
        for n in range(1, ext + 1):
            _present(brain, A, True, False, contact=True)
            if n in tests_ext:
                va, _ = _present(brain, A, False, False); vb, _ = _present(brain, B, False, False)
                out["ext"][n].append((va - vb).mean().item())
        out["dan_max"] = max(out["dan_max"], brain.dan_max)
    return out


def summarize(name: str, r: dict) -> str:
    m = lambda x: np.mean(x)
    sd = lambda x: np.std(x)
    acq = " | ".join(f"{m(v):+.3f}" for v in r["acq"].values())
    ext = " | ".join(f"{m(v):+.3f}" for v in r["ext"].values())
    pi = m(r["pam_last"]) / max(m(r["pam_first"]), 1e-9)
    return f"| {name} | {m(r['naive']):+.3f} | {acq} | {ext} | {pi:.2f} | {m(r['spur']):.3f} | {r['dan_max']:.2f} |"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--variants", default="V0")
    ap.add_argument("--creatures", type=int, default=6)
    ap.add_argument("--patterns", type=int, default=3)
    ap.add_argument("--acq", type=int, default=12)
    ap.add_argument("--ext", type=int, default=8)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    cfg = mbmodel.connectome_config()
    t0 = time.time()
    bal = calibrate_balance(cfg, n_patterns=8)
    cfg.cbrain.class_balance = bal["class_balance"]
    print(f"[{time.time() - t0:5.0f}s] class_balance={bal['class_balance']:.3f}", flush=True)
    head = ["# DAN devresi geliştirme harness'ı (kanıt değildir)", "",
            f"{a.creatures} canlı × {a.patterns} koku çifti, {a.acq} edinim + {a.ext} sönüm denemesi; class_balance={bal['class_balance']:.3f}; tohum {a.seed}.", "",
            "| varyant | naif sel | " + " | ".join(f"edinim {n}" for n in (1, 2, 4, 8, 12)) + " | " + " | ".join(f"sönüm {n}" for n in (2, 4, 8)) + " | tahmin idx | sahte öğretmen | DAN tepe |",
            "|---|---|" + "---|" * 11]
    rows = []
    for v in a.variants.split(";"):
        name, dcfg = parse_variant(v)
        r = run_variant(cfg, dcfg, a.seed, a.creatures, a.patterns, a.acq, a.ext)
        rows.append(summarize(name, r))
        print(f"[{time.time() - t0:5.0f}s] {rows[-1]}", flush=True)
    text = "\n".join(head + rows) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
