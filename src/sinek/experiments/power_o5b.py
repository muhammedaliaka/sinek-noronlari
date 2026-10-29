"""O5b güç ve yanlış-pozitif analizi (R-6; E-15 dersi): parametrik benzetim yerine GERÇEK ham yaşam verisinden yeniden örnekleme.

    python -m sinek.experiments.power_o5b --panels results/o5_val/s260,results/o5_val/s261,results/o5_val/dev_s132,results/o5_val/dev_s133 --sims 300 --out results/power_o5b.md

Her panel bir popülasyondur (kol başına 48 yaşam, CRN eşli, ham kontrol noktaları `partial/`). Senaryolar (her panel için, `eval_o5b` gerçek değerlendiricisiyle):
  sıfır etki     plastic↔frozen (ve ens↔plastic) etiketleri yaşam başına rastgele değiştirilir (eşli kolların değiş-tokuşa duyarlı olması H0'dır)
  bilinen etki   yaşamlar yerine koyarak yeniden örneklenir (gözlenen etki sabit; ölçüt kuralının örnekleme gücü)
  yarım etki     her yaşam için plastic kaydı olasılık ½ ile frozen kaydıyla değiştirilir (etkinin ≈yarısı)
  yalnız yaklaşma plastic'in temas örüntüsü korunur, iyi/kötü seçimi yazı-tura (N ölçütleri başarısız olmalı)
Popülasyon başına geçme olasılıkları, 4 popülasyon için Poisson-binom ile "≥k/4 popülasyon" karar kurallarına çevrilir. ÖLÇÜT/EŞİK KEŞFETMEZ.
"""
from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import numpy as np

from .odor_eval import EVALUATORS, Thr, O5_BLOCKS
from .odor_validate_o5 import to_h

ARMS = ("plastic", "frozen", "reference", "plastic_ens")
KEYS = ("slot", "got", "better")


def load_panel(d: Path) -> dict:
    res = {}
    for arm in ARMS:
        parts = sorted((d / "partial").glob(f"o5_{arm}_c*.npz"), key=lambda p: int(p.stem.rsplit("_c", 1)[1]))
        if parts:
            res[arm] = {k: np.concatenate([np.load(p)[k] for p in parts], axis=1) for k in KEYS}
    return res


def lives(res: dict) -> dict:
    """(yaşam, bölüm) biçiminde ödül ve net tercih; kol → dizi."""
    return to_h(res)


def resample(h: dict, idx: np.ndarray) -> dict:
    return {k: v[idx] for k, v in h.items()}


def swap(h: dict, a: str, b: str, mask: np.ndarray) -> dict:
    out = dict(h)
    for pre in ("", "net_"):
        x, y = h[pre + a].copy(), h[pre + b].copy()
        x[mask], y[mask] = h[pre + b][mask], h[pre + a][mask]
        out[pre + a], out[pre + b] = x, y
    return out


def approach_only(h: dict, rng, arm: str = "plastic") -> dict:
    """arm'ın temas örüntüsü korunur; iyi/kötü seçimi yazı-tura; ödül p_hi/p_lo ile yeniden çekilir (net tercih ≈0)."""
    out = dict(h)
    contact = h["net_" + arm] != 0
    sign = np.where(rng.random(contact.shape) < 0.5, 1, -1)
    out["net_" + arm] = np.where(contact, sign, 0)
    out[arm] = (contact & (rng.random(contact.shape) < np.where(sign > 0, 0.8, 0.2))).astype(int)
    return out


def replace_arm(h: dict, dst: str, src: str, mask: np.ndarray) -> dict:
    """mask olan yaşamlarda dst kolunun kaydı src kolununkiyle değiştirilir (yarım etki: dst etkisi ≈yarıya iner)."""
    out = dict(h)
    for pre in ("", "net_"):
        out[pre + dst] = np.where(mask[:, None], h[pre + src], h[pre + dst])
    return out


def run_panel(h: dict, sims: int, thr: Thr, rng) -> dict:
    """senaryo → ölçüt → geçme olasılığı; her senaryo yalnız ilgili ölçüt ailesini (N: plastic−frozen, E: ens−plastic) raporlar."""
    n = h["plastic"].shape[0]
    has_ens = "plastic_ens" in h
    def rate(make, fam):
        rows = []
        for _ in range(sims):
            ev = EVALUATORS["O5b"](make(), thr)
            rows.append({k: c["passed"] for k, c in (ev["criteria"] | ev["descriptive"]).items() if k[0] in fam} | {"kapı": ev["gates_ok"]})
        return {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
    sc = {
        "sıfır etki N (plastic↔frozen değişimi)": (lambda: swap(h, "plastic", "frozen", rng.random(n) < 0.5), "N"),
        "bilinen etki (gözlenen; yeniden örnekleme)": (lambda: resample(h, rng.integers(0, n, n)), "NE"),
        "yarım etki N (plastic kaydı ½ olasılıkla frozen)": (lambda: replace_arm(h, "plastic", "frozen", rng.random(n) < 0.5), "N"),
        "yalnız yaklaşma N (plastic temas örüntüsü, seçim yazı-tura)": (lambda: approach_only(h, rng, "plastic"), "N"),
    }
    if has_ens:
        sc |= {
            "sıfır etki E (ens↔plastic değişimi)": (lambda: swap(h, "plastic_ens", "plastic", rng.random(n) < 0.5), "E"),
            "yarım etki E (ens kaydı ½ olasılıkla plastic)": (lambda: replace_arm(h, "plastic_ens", "plastic", rng.random(n) < 0.5), "E"),
            "yalnız yaklaşma E (ens temas örüntüsü, seçim yazı-tura)": (lambda: approach_only(h, rng, "plastic_ens"), "E"),
        }
    return {name: rate(mk, fam) for name, (mk, fam) in sc.items()}


def at_least(ps: list[float], k: int) -> float:
    """Bağımsız Bernoulli(p_i) toplamı ≥ k olasılığı (Poisson-binom, tam sayım)."""
    tot = 0.0
    for r in range(k, len(ps) + 1):
        for S in combinations(range(len(ps)), r):
            tot += np.prod([ps[i] if i in S else 1 - ps[i] for i in range(len(ps))])
    return float(tot)


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--panels", required=True)
    ap.add_argument("--sims", type=int, default=300)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--delta-np", type=float, default=0.10)
    ap.add_argument("--delta-r", type=float, default=0.08)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    thr = Thr(delta=a.delta_np, ref_min=0.60, n_boot=a.boot, n_perm=a.boot)
    rng = np.random.default_rng(a.seed)
    names = [Path(p).name for p in a.panels.split(",")]
    all_res = {}
    L = ["# O5b güç ve yanlış-pozitif analizi (R-6; gerçek ham veriden yeniden örnekleme)", "",
         f"{a.sims} yeniden örnekleme/senaryo/panel; δ_np={a.delta_np}, δ_r={a.delta_r}, α={thr.alpha}, referans kapısı ≥{thr.ref_min}. Hücre: ölçütün geçme olasılığı.", ""]
    for p in a.panels.split(","):
        res = load_panel(Path(p))
        h = lives(res)
        # eval_o5b her iki E ölçütünü yalnız plastic_ens varsa hesaplar
        all_res[Path(p).name] = run_panel(h, a.sims, thr, rng)
        print(f"{Path(p).name} bitti", flush=True)
    crits = sorted({k for r in all_res.values() for sc in r.values() for k in sc if k != "kapı"})
    scen = list(dict.fromkeys(sc for r in all_res.values() for sc in r))
    for sc in scen:
        cs = [c for c in crits if any(c in r.get(sc, {}) for r in all_res.values())]
        L += [f"## {sc}", "", "| panel | kapı | " + " | ".join(cs) + " |", "|---|---|" + "---|" * len(cs)]
        for nm, r in all_res.items():
            if sc in r:
                L.append(f"| {nm} | {r[sc]['kapı']:.2f} | " + " | ".join(f"{r[sc][c]:.2f}" if c in r[sc] else "—" for c in cs) + " |")
        L.append("")
    L += ["## Karar kuralı adayları (panelleri popülasyon örnekleri sayarak; bağımsız Poisson-binom)", "",
          "Popülasyon başına geçme olasılığı = yukarıdaki tablo. Sıfır-etki satırlarında 'P(hepsi)' kuralın yanlış-pozitif oranı, bilinen-etki satırlarında gücüdür.", "",
          "| senaryo | ölçüt | popülasyon sayısı | P(hepsi) | P(≥ n−1) |", "|---|---|---|---|---|"]
    for sc in scen:
        for c in crits:
            ps = [r[sc][c] for r in all_res.values() if sc in r and c in r[sc]]
            if ps:
                L.append(f"| {sc} | {c} | {len(ps)} | {at_least(ps, len(ps)):.3f} | {at_least(ps, max(len(ps) - 1, 1)):.3f} |")
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
