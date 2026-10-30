"""O5 doğrulayıcısı POST-HOC çözümleme (hükmü DEĞİŞTİRMEZ; docs/odor_o5_plani.md §5 hükmü ön-kayıtlıdır).

    python -m sinek.experiments.o5_posthoc --dir results/o5_val [--out results/o5_val/posthoc.md]

Ham kontrol noktalarından (results/o5_val/s<tohum>/partial/*.npz) geç bloklarda (bölüm 11-20, 31-40) kol başına: temas oranı, temasta iyi kokuyu seçme oranı, ödül oranı;
ve `plastic − frozen` ödül farkının "temas" ve "seçim" bileşenlerine ayrışması: ödül = temas × P(ödül | temas), P(ödül | temas) = p_lo + (p_hi − p_lo)·P(iyi | temas).
Yaşam birimli eşli küme bootstrap %99 GA yalnız betimsel amaçlıdır (karar vermez).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .stats import paired_cluster_ci
from .odor_eval import O5_BLOCKS

P_HI, P_LO = 0.8, 0.2
ARMS = ("plastic", "frozen", "reference", "plastic_ens")


def load(d: Path, seed: int, prefix: str = "s") -> dict:
    out = {}
    for arm in ARMS:
        parts = sorted((d / f"{prefix}{seed}" / "partial").glob(f"o5_{arm}_c*.npz"), key=lambda p: int(p.stem.rsplit("_c", 1)[1]))
        if parts:                                                                                                      # plastic_ens yalnız O5b/geliştirme panellerinde var
            out[arm] = {k: np.concatenate([np.load(p)[k] for p in parts], axis=1) for k in ("slot", "got", "better")}      # (bölüm, yaşam)
    return out


def late(r: dict) -> dict:
    cols = np.r_[O5_BLOCKS[0][0]:O5_BLOCKS[0][1], O5_BLOCKS[1][0]:O5_BLOCKS[1][1]]
    slot, got, better = (r[k][cols].T for k in ("slot", "got", "better"))                # (yaşam, geç bölüm)
    contact = slot >= 0
    good = contact & (slot == better)
    return {"contact": contact.astype(float), "good": good.astype(float), "got": got.astype(float)}


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="results/o5_val")
    ap.add_argument("--seeds", default="260,261")
    ap.add_argument("--prefix", default="s", help="klasör öneki: O5 'o5_val/s<tohum>', O5b 'o5_val/b_s<tohum>'")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    L = ["# O5 POST-HOC çözümleme (hükmü değiştirmez)", "",
         "Geç bloklar (bölüm 11-20 ve 31-40). Hücreler yaşam ortalaması; ödül ≈ temas × [p_lo + (p_hi − p_lo) × P(iyi | temas)].", "",
         "| tohum | kol | temas oranı | temasta iyi koku seçme | ödül oranı |", "|---|---|---|---|---|"]
    dec = ["", "## `plastic − frozen` ödül farkının ayrışması (yaşam birimli eşli küme bootstrap %99 GA; betimsel)", "",
           "| tohum | ödül farkı | temas farkı | iyi-koku-seçme farkı (temaslı bölümler) | net tercih farkı (P3 ölçüsü) |", "|---|---|---|---|---|"]
    dec_e = ["", "## `plastic_ens − plastic` ayrışması (aynı yöntem; betimsel)", "",
             "| tohum | ödül farkı | temas farkı | iyi-koku-seçme farkı (temaslı bölümler) | net tercih farkı |", "|---|---|---|---|---|"]
    for seed in [int(s) for s in a.seeds.split(",")]:
        res = {arm: late(r) for arm, r in load(Path(a.dir), seed, a.prefix).items()}
        for arm in res:
            m = res[arm]
            L.append(f"| {seed} | {arm} | {m['contact'].mean():.3f} | {m['good'].sum() / max(m['contact'].sum(), 1):.3f} | {m['got'].mean():.3f} |")
        pl, fr = res["plastic"], res["frozen"]
        n = pl["got"].shape[1]
        ci = lambda x, y: paired_cluster_ci(x.sum(1), y.sum(1), n, n=4000, seed=1, alpha=0.01)       # noqa: E731
        net = lambda m: m["good"] - (m["contact"] - m["good"])                                          # noqa: E731
        cells = []
        for x, y in ((pl["got"], fr["got"]), (pl["contact"], fr["contact"]), (net(pl), net(fr))):
            mn, lo, hi = ci(x, y)
            cells.append(f"{mn:+.3f} [{lo:+.3f}; {hi:+.3f}]")
        gp, gf = pl["good"].sum() / max(pl["contact"].sum(), 1), fr["good"].sum() / max(fr["contact"].sum(), 1)
        dec.append(f"| {seed} | {cells[0]} | {cells[1]} | {gp - gf:+.3f} ({gp:.3f} − {gf:.3f}) | {cells[2]} |")
        if "plastic_ens" in res:
            en = res["plastic_ens"]
            ce = []
            for x, y in ((en["got"], pl["got"]), (en["contact"], pl["contact"]), (net(en), net(pl))):
                mn, lo, hi = ci(x, y)
                ce.append(f"{mn:+.3f} [{lo:+.3f}; {hi:+.3f}]")
            ge = en["good"].sum() / max(en["contact"].sum(), 1)
            dec_e.append(f"| {seed} | {ce[0]} | {ce[1]} | {ge - gp:+.3f} ({ge:.3f} − {gp:.3f}) | {ce[2]} |")
    text = "\n".join(L + dec + (dec_e if len(dec_e) > 5 else [])) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
