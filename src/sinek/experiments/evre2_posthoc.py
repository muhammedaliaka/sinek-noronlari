"""Evre 2 ek analizleri: ön-kayıtlı OLMAYAN (post-hoc) betimsel kontroller ve E1 karıştırma kontrolü.

Ön-kayıtlı ölçütlerin hükmünü değiştirmez; yalnızca *neden* geçti/kaldığını anlamak içindir.

    python -m sinek.experiments.evre2_posthoc --runs results/evre2_s20 results/evre2_s21 \
        --shuffle results/evre2_s20_shuffle1 results/evre2_s20_shuffle2 --out docs/evre2_ek_analiz.md
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

import numpy as np

CONDS = ("plastic", "frozen", "random")


def _stage(r: dict, phase: str, last: bool = True) -> dict:
    ss = [s for s in r["stages"] if s["phase"] == phase]
    return ss[-1] if last else ss[0]


def counts(r: dict, stage: dict, cond: str) -> tuple[np.ndarray, np.ndarray]:
    """Canlı başına A ve B ilk-temas sayıları (stage['n_a'], ['n_b'] koşullara sırayla bölünmüştür)."""
    n = r["args"]["agents"]
    i = CONDS.index(cond)
    return np.array(stage["n_a"])[i * n:(i + 1) * n], np.array(stage["n_b"])[i * n:(i + 1) * n]


def pooled_pref(a: np.ndarray, b: np.ndarray) -> float:
    t = a.sum() + b.sum()
    return float(a.sum() / t) if t else float("nan")


def cluster_permutation_p(g1, g2, n: int = 20000, seed: int = 0, alternative: str = "greater") -> float:
    """Havuzlanmış A-oranı farkı için canlı-düzeyinde permütasyon: canlılar birim, etiketleri karıştırılır.
    g1, g2 = (a_sayıları, b_sayıları). Hiç seçim yapmayan canlılar ağırlıksızdır (toplam 0)."""
    a = np.concatenate([g1[0], g2[0]]).astype(float)
    b = np.concatenate([g1[1], g2[1]]).astype(float)
    n1 = len(g1[0])
    if g1[0].sum() + g1[1].sum() == 0 or g2[0].sum() + g2[1].sum() == 0:
        return float("nan")

    def stat(idx1, idx2):
        return a[idx1].sum() / max(a[idx1].sum() + b[idx1].sum(), 1e-9) - a[idx2].sum() / max(a[idx2].sum() + b[idx2].sum(), 1e-9)

    idx = np.arange(len(a))
    obs = stat(idx[:n1], idx[n1:])
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(n):
        rng.shuffle(idx)
        s = stat(idx[:n1], idx[n1:])
        ge += (s >= obs - 1e-12) if alternative == "greater" else (abs(s) >= abs(obs) - 1e-12)
    return (ge + 1) / (n + 1)


def binom_two_sided(k: int, n: int) -> float:
    """Tam iki yönlü iki terimli test, p0 = 0.5."""
    if n == 0:
        return float("nan")
    pk = comb(n, k)
    return min(1.0, sum(comb(n, j) for j in range(n + 1) if comb(n, j) <= pk) / 2 ** n)


def pref_per_agent(stage: dict, cond: str) -> np.ndarray:
    return np.array([np.nan if v is None else v for v in stage["summary"][cond]["pref_A_per_agent"]])


def one_sided_mean_p(a: np.ndarray, b: np.ndarray, n: int = 20000, seed: int = 0) -> float:
    """H1: mean(a) > mean(b); canlı başına tercih (NaN'ler atılır) üzerinde permütasyon."""
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(n):
        rng.shuffle(pool)
        ge += pool[: len(a)].mean() - pool[len(a):].mean() >= obs - 1e-12
    return (ge + 1) / (n + 1)


def run_table(path: Path) -> tuple[list[str], dict]:
    r = json.loads((path / "results.json").read_text())
    nv, ta, tb = _stage(r, "naive"), _stage(r, "A"), _stage(r, "B")
    L = [f"### {path.name} (tohum {r['args']['seed']})", "",
         "| aşama | koşul | seçim yapan canlı | A / B ilk-temas | havuzlanmış A-oranı |", "|---|---|---:|---|---:|"]
    n = r["args"]["agents"]
    for st, nm in ((nv, "naif"), (ta, f"A sonrası bölüm {ta['episode']}"), (tb, f"B sonrası bölüm {tb['episode']}")):
        for c in CONDS:
            a, b = counts(r, st, c)
            L.append(f"| {nm} | {c} | {int(((a + b) > 0).sum())}/{n} | {a.sum()} / {b.sum()} | {pooled_pref(a, b):.2f} |")
    L.append("")
    return L, r


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True, help="doğrulayıcı koşu klasörleri")
    ap.add_argument("--shuffle", nargs="*", default=[], help="E1 karıştırma koşuları (gerçek-etiketli koşu = ilk --runs)")
    ap.add_argument("--out", default="docs/evre2_ek_analiz.md")
    a = ap.parse_args(argv)

    L = ["# Evre 2 — ek analizler (ön-kayıtlı DEĞİL)", "",
         "Bu belge `python -m sinek.experiments.evre2_posthoc` ile üretilir. **Ön-kayıtlı ölçütlerin hükmünü değiştirmez**; koşular",
         "bittikten sonra, ölçütlerin neden geçtiği/kaldığını anlamak için yapılmış betimsel çözümlemelerdir.", "",
         "## 1. Seçim sayıları (A ve B ilk-temas toplamları)", ""]
    runs = {}
    for p in a.runs:
        t, r = run_table(Path(p))
        L += t
        runs[Path(p).name] = r

    L += ["## 2. Post-hoc karşılaştırmalar (havuzlanmış A-oranı, canlı-düzeyi permütasyon)", "",
          "Ağırlık = canlının yaptığı seçim sayısı; birim = canlı (denemeler aynı canlı içinde bağımsız sayılmaz). Tek yönlü: ilk grup > ikinci grup.", "",
          "| koşu | karşılaştırma | grup 1 | grup 2 | p |", "|---|---|---|---|---:|"]
    for name, r in runs.items():
        nv, ta, tb = _stage(r, "naive"), _stage(r, "A"), _stage(r, "B")
        pa, fa = counts(r, ta, "plastic"), counts(r, ta, "frozen")
        pn, fn = counts(r, nv, "plastic"), counts(r, nv, "frozen")
        naive_pool = (np.concatenate([pn[0], fn[0]]), np.concatenate([pn[1], fn[1]]))
        pb = counts(r, tb, "plastic")

        def row(label, g1, g2, alt="greater"):
            L.append(f"| {name} | {label} | {g1[0].sum()}A/{g1[1].sum()}B ({pooled_pref(*g1):.2f}) | "
                     f"{g2[0].sum()}A/{g2[1].sum()}B ({pooled_pref(*g2):.2f}) | {cluster_permutation_p(g1, g2, alternative=alt):.4f} |")

        row("eğitilmiş plastic > frozen (A2'nin havuzlanmış karşılığı)", pa, fa)
        row("eğitilmiş plastic > naif (plastic+frozen, aynı ağ)", pa, naive_pool)
        row("eğitilmiş A-plastic > B-plastic (tersine çevirme)", pa, pb)
        k, n = int(naive_pool[0].sum()), int((naive_pool[0] + naive_pool[1]).sum())
        L.append(f"| {name} | naif ağ (plastic+frozen) tercihi = 0.5? (tam iki terimli, denemeler bağımsız varsayılır) | {k}A/{n - k}B | — | {binom_two_sided(k, n):.4f} |")
    L.append("")

    if a.shuffle:
        base = next(iter(runs.values()))
        base_a = _stage(base, "A")
        L += ["## 3. E1 — MBON yaklaş/kaçın etiketlerinin karıştırılması (tohum-20 kurulumu)", "",
              "Ön-kayıtlı ölçüt: A eğitimi sonunda `plastic` A-tercihi gerçek-etiketli koşudan düşüktür (tek yönlü permütasyon, canlı başına tercih, p < 0.01).", "",
              "| koşu | sınıf dengesi | naif plastic A-tercihi | eğitilmiş plastic A-tercihi [GA] | seçim yapan canlı | p (gerçek > karıştırılmış) | E1 |", "|---|---:|---|---|---:|---:|---|"]
        s = base_a["summary"]["plastic"]
        lo, hi = s["pref_A_ci95"]
        nvb = _stage(base, "naive")["summary"]["plastic"]
        L.append(f"| gerçek etiketler ({next(iter(runs))}) | {base['balance']['class_balance']:.3f} | {nvb['pref_A_mean']:.2f} | "
                 f"{s['pref_A_mean']:.2f} [{lo:.2f}, {hi:.2f}] | {int(np.sum(~np.isnan(pref_per_agent(base_a, 'plastic'))))}/16 | — | — |")
        for p in a.shuffle:
            rr = json.loads((Path(p) / "results.json").read_text())
            sa, sn = _stage(rr, "A"), _stage(rr, "naive")
            ss = sa["summary"]["plastic"]
            lo, hi = ss["pref_A_ci95"]
            pv = one_sided_mean_p(pref_per_agent(base_a, "plastic"), pref_per_agent(sa, "plastic"))
            L.append(f"| karıştırma tohum {rr['config']['cbrain']['class_shuffle_seed']} ({Path(p).name}) | {rr['balance']['class_balance']:.3f} | "
                     f"{sn['summary']['plastic']['pref_A_mean']:.2f} | {ss['pref_A_mean']:.2f} [{lo:.2f}, {hi:.2f}] | "
                     f"{int(np.sum(~np.isnan(pref_per_agent(sa, 'plastic'))))}/16 | {pv:.4f} | {'PASS' if pv < 0.01 else 'FAIL'} |")
        L.append("")
    Path(a.out).write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
