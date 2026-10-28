"""Dört koku oyunu: güç ve yanlış-pozitif benzetimi — GERÇEK değerlendirici işlevlerle (`odor_eval`; R-6, CLAUDE.md kural 3).

    python -m sinek.experiments.power_odor --games O1,O2,O3,O4a,O4c --sims 200 --agents 24 --trials 16 \
        --p0 0.30 --p-attract 0.70 --creature-sd 0.08 --indep 0.2 --out docs/odor_guc_analizi.md

Model: her (canlı, deneme) için kollar ORTAK bir tekdüze sayı paylaşır (CRN); `--indep` oranında deneme kol başına bağımsız yeniden çekilir
(kollar o denemede ayrışmıştır). Canlı başına ortak beceri sapması `--creature-sd`. Bu parametreler **pilottan** (odor_pilot/odor_session
çıktılarından) alınır; varsayılanlar yalnız yer tutucudur ve çıktı belgesine yazılır. Senaryolar: sıfır etki (yanlış-pozitif), δ ve 2δ etki,
O3 için marj kadar sapma. Benzetim ölçütleri gevşetmez: güç < 0,90 ya da sıfır-etkide geçme > α çıkarsa tasarım (canlı/deneme/T) değişir.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from .odor_eval import EVALUATORS, Thr


def _shared(rng, A: int, T: int, indep: float):
    u = rng.random((A, T))
    def draw():
        return np.where(rng.random((A, T)) < indep, rng.random((A, T)), u)
    return draw


def sim_hits(rng, p_by_arm: dict, A: int, T: int, creature_sd: float, indep: float) -> dict:
    dev = creature_sd * rng.standard_normal(A)
    draw = _shared(rng, A, T, indep)
    return {k: (draw() < np.clip(p + dev, 0.01, 0.99)[:, None]).astype(int) for k, p in p_by_arm.items()}


def sim_slots(rng, pd_by_arm: dict, A: int, T: int, indep: float) -> dict:
    """O4c: kol → (decoy-ilk olasılığı, gerçek-ilk olasılığı); ilk-temas yuvası 1/0/−1."""
    draw = _shared(rng, A, T, indep)
    out = {}
    for k, (pd, pr) in pd_by_arm.items():
        u = draw()
        out[k] = np.where(u < pd, 1, np.where(u < pd + pr, 0, -1))
    return out


def scenarios(game: str, thr: Thr, p0: float, pa: float, ref: float) -> list[tuple[str, dict]]:
    d, e = thr.delta, thr.delta_eq
    if game in ("O1", "O2"):
        base = {"anosmic": p0, "random": p0, "reference": ref}
        return [("sıfır etki", {**base, "frozen": p0}), (f"etki δ={d}", {**base, "frozen": p0 + d}),
                (f"etki 1,5δ={1.5 * d:.3f}", {**base, "frozen": p0 + 1.5 * d}), (f"etki 2δ={2 * d}", {**base, "frozen": p0 + 2 * d})]
    if game == "O3":
        eq = {k: p0 for k in "ABCD"}
        return [("sıfır sapma", eq), (f"D sapması = δ_eq/2 ({e / 2:.3f})", {**eq, "D": p0 + e / 2}),
                (f"D sapması = δ_eq ({e})", {**eq, "D": p0 + e}), (f"D sapması = 2δ_eq ({2 * e})", {**eq, "D": p0 + 2 * e})]
    if game == "O4a":
        base = {"frozen": pa, "anosmic": p0}
        return [("sıfır etki (plastic=frozen)", {**base, "plastic": pa}), (f"etki δ={d}", {**base, "plastic": pa - d}),
                (f"etki 1,5δ={1.5 * d:.3f}", {**base, "plastic": pa - 1.5 * d}), (f"etki 2δ={2 * d}", {**base, "plastic": pa - 2 * d}),
                ("çekim yok (G4 başarısız olmalı)", {"frozen": p0, "anosmic": p0, "plastic": p0 - d})]
    if game == "O4c":
        pr = 0.15
        base = {"anosmic": (p0, pr), "frozen": (pa, 0.05)}
        return [("sıfır etki (plastic=frozen)", {**base, "plastic": (pa, 0.05)}),
                (f"etki δ={d}, gerçek-ilk korunur", {**base, "plastic": (pa - d, pr)}),
                (f"etki 2δ={2 * d}, gerçek-ilk korunur", {**base, "plastic": (pa - 2 * d, pr)}),
                ("etki 2δ ama gerçek-ilk çöker", {**base, "plastic": (pa - 2 * d, 0.0)})]
    raise ValueError(game)


def run(game: str, thr: Thr, sims: int, A: int, T: int, p0: float, pa: float, ref: float, creature_sd: float, indep: float, seed: int = 0):
    rng = np.random.default_rng(seed)
    ev = EVALUATORS[game]
    rows = []
    for name, spec in scenarios(game, thr, p0, pa, ref):
        n_ok, per, gates = 0, {}, 0
        for _ in range(sims):
            h = sim_slots(rng, spec, A, T, indep) if game == "O4c" else sim_hits(rng, spec, A, T, creature_sd, indep)
            r = ev(h, thr)
            n_ok += r["passed"]
            gates += r["gates_ok"]
            for k, c in r["criteria"].items():
                per[k] = per.get(k, 0) + int(c["passed"])
        rows.append({"senaryo": name, "geçti": n_ok / sims, "kapılar": gates / sims, "ölçüt": {k: v / sims for k, v in per.items()}})
    return rows


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--games", default="O1,O2,O3,O4a,O4c")
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--trials", type=int, default=16)
    ap.add_argument("--p0", type=float, default=0.30, help="kör düzey (anosmik/kontrol) isabet olasılığı — pilottan")
    ap.add_argument("--p-attract", type=float, default=0.70, help="O4: frozen kolun decoy'a isabeti — pilottan")
    ap.add_argument("--ref", type=float, default=0.90, help="referans karşılaştırıcı isabeti — pilottan")
    ap.add_argument("--creature-sd", type=float, default=0.08)
    ap.add_argument("--indep", type=float, default=0.2, help="kolların bağımsız ayrıştığı deneme oranı — pilottan")
    ap.add_argument("--delta", type=float, default=0.15)
    ap.add_argument("--delta-eq", type=float, default=0.10)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    thr = Thr(delta=a.delta, delta_eq=a.delta_eq, n_boot=a.boot, n_perm=a.boot)
    t0 = time.time()
    L = ["# Dört koku oyunu: güç ve yanlış-pozitif benzetimi", "",
         f"Gerçek değerlendirici işlevlerle (`odor_eval`), {a.sims} benzetim/senaryo, {a.agents} canlı × {a.trials} deneme.",
         f"Girdi parametreleri (pilottan; yer tutucu olabilir): kör düzey p0={a.p0}, çekim p={a.p_attract}, referans={a.ref}, "
         f"canlı sd={a.creature_sd}, kol ayrışma oranı={a.indep}; δ={a.delta}, δ_eq={a.delta_eq}, α={thr.alpha}.", ""]
    for g in a.games.split(","):
        L += [f"## {g}", "", "| senaryo | hepsi geçti | kapılar tamam | ölçüt başına geçme |", "|---|---|---|---|"]
        for r in run(g, thr, a.sims, a.agents, a.trials, a.p0, a.p_attract, a.ref, a.creature_sd, a.indep):
            L.append(f"| {r['senaryo']} | {r['geçti']:.2f} | {r['kapılar']:.2f} | " + ", ".join(f"{k} {v:.2f}" for k, v in r["ölçüt"].items()) + " |")
        L.append("")
        print(f"[{time.time() - t0:5.0f}s] {g} tamam", flush=True)
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
