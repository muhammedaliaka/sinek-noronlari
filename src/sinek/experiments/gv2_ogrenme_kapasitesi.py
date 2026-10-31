"""G-V2 (geliştirme, kanıt değildir): navigasyonsuz ÖĞRENME KAPASİTESİ — zorunlu temas: her denemede ipucu (koku ve/veya görsel) + ±1 tat, sonra ipucu-yalnız okuma.

    python3 -I -m sinek.experiments.gv2_ogrenme_kapasitesi

Δ = V(+ipucu) − V(−ipucu). Kontroller: koku A/B (pozitif), boş (aynı ipucu hem + hem −; Δ≈0). K-054: görsel Δ +0,83, koku +0,44, boş +0,01 (tohum 3, 32 yaşam, 12 deneme/desen).
"""
import dataclasses
import numpy as np
import torch
from sinek import checkpoint
from sinek.brain_connectome import ConnectomeBrain
from sinek.games.vis_calibration import neutral_scale
from sinek.games.world import vis_patterns
from sinek.world import odor_patterns
pre = checkpoint.load("results/odor_games/pre_s102.npz")
cb = dataclasses.replace(pre.cfg.cbrain, n_vis_feat=6)
cb = dataclasses.replace(cb, vis_avoid_scale=neutral_scale(cb))
vp = vis_patterns(6); pat = odor_patterns(pre.cfg.world, 3)
B, NG = 32, cb.n_vis_feat
def cue(kind, which, n):
    g = torch.zeros(n, 2, pre.cfg.world.n_glom); v = torch.zeros(n, 2, 6)
    if kind in ("odor", "both_odor"):
        g[:] = (pat[which] * 0.6) if kind == "odor" else (pat[0] * 0.6)
    if kind in ("vis", "both_odor"):
        v[:] = vp[which] * 0.6
    return g, v
def run(kind, trials=12, seed=3, null=False):
    b = ConnectomeBrain(cb, B, seed)
    rng = np.random.default_rng(seed)
    z = torch.zeros(B)
    for t in range(trials):
        for which in rng.permutation([0, 1]):
            if null: which_cue = 0
            else: which_cue = which
            g, v = cue(kind, which_cue, B)
            b.reset_state()
            sgn = 1.0 if which == 0 else -1.0
            for s in range(45):
                taste = z + sgn if s >= 30 else z
                touch = (z + 1.0) if s >= 30 else z
                b.step(g, taste, touch, learn=True, vis=v if kind != "odor" else None)
    out = []
    for which in (0, 1):
        g, v = cue(kind, which if not null else 0, B); b.reset_state(); vs = []
        for s in range(40):
            val = b.step(g, z, z, learn=False, vis=v if kind != "odor" else None)
            if s >= 20: vs.append(val.mean(-1))
        out.append(torch.stack(vs).mean(0))
    return out
def main():
    for name, kind, null in (("koku A(+) vs B(−)", "odor", False), ("görsel X(+) vs Y(−), kokusuz", "vis", False), ("görsel X vs Y + ortak koku A (O6b)", "both_odor", False), ("null: X hem + hem −", "vis", True)):
        a, bb = run(kind, null=null)
        d = a - bb
        print(f"{name}: V(+)={a.mean():+.3f} V(−)={bb.mean():+.3f}  Δ={d.mean():+.3f} (sd {d.std():.3f}, Δ>0 oranı {float((d>0).float().mean()):.2f})", flush=True)


if __name__ == "__main__":
    torch.set_num_threads(2)
    main()
