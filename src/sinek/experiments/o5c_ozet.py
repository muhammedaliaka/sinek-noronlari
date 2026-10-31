"""O5c doğrulayıcı sonuçlarını toplar ve docs/odor_o5c_plani.md §5 karar kuralını uygular (ölçüt/eşik KEŞFETMEZ).

    python -m sinek.experiments.o5c_ozet --dir results/o5_val [--out results/o5_val/ozet_o5c.md]

Tek iddia (C: DAN hedefi T=2,5, tek öğrenici): dört popülasyonda kapı G ∧ T1, T2, T3 her biri en az üç popülasyonda.
Eksik (bitmemiş) koşu varsa ve kural henüz çürütülmediyse hüküm "BEKLİYOR"; sessizce atlanmaz.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SEEDS = (274, 275, 276, 277)       # docs/odor_o5c_plani.md §2
N_POP = len(SEEDS)
CRITS = ("T1_secicilik_kazanci", "T2_odul_kazanci", "T3_secicilik_mutlak")
NEED = N_POP - 1


def load(d: Path, seed: int) -> dict | None:
    f = d / f"c_s{seed}" / "results.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def verdict(runs: dict[int, dict | None]) -> str:
    done = [r for r in runs.values() if r is not None]
    if any(not r["eval"]["gates_ok"] for r in done):
        return "BAŞARISIZ"                                                # kapı eksik → iddia yapılamaz
    ok = True
    for crit in CRITS:
        passes = sum(1 for r in done if r["eval"]["criteria"][crit]["passed"])
        if len(done) - passes > N_POP - NEED:
            return "BAŞARISIZ"
        ok &= passes >= NEED
    return "BAŞARILI" if (ok and len(done) == N_POP) else "BEKLİYOR"


def table(runs: dict[int, dict | None]) -> str:
    L = ["| tohum | ödül: plastic_t / plastic / frozen / reference | " + " | ".join(CRITS) + " | kapı G |", "|---|---|" + "---|" * (len(CRITS) + 1)]
    fmt = lambda x: f"{x['mean']:+.3f} [{x['ci'][0]:+.3f}; {x['ci'][1]:+.3f}] p={x['p']:.4f} {'✔' if x['passed'] else '✘'}"   # noqa: E731
    for seed in SEEDS:
        r = runs.get(seed)
        if r is None:
            L.append(f"| {seed} | — | " + " | ".join("—" for _ in CRITS) + " | — |")
            continue
        e, c = r["eval"], r["eval"]["criteria"]
        L.append(f"| {seed} | " + " / ".join(f"{r['reward_rate'][a]:.3f}" for a in ("plastic_t", "plastic", "frozen", "reference")) + " | " + " | ".join(fmt(c[k]) for k in CRITS)
                 + f" | {'tamam' if e['gates_ok'] else 'EKSİK'} |")
    return "\n".join(L)


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="results/o5_val")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    runs = {s: load(Path(a.dir), s) for s in SEEDS}
    text = "\n".join(["# O5c doğrulayıcısı — özet (otomatik; `o5c_ozet`)", "", table(runs), "",
                      f"**Hüküm (docs/odor_o5c_plani.md §5), C (DAN hedefi T=2,5, tek öğrenici): {verdict(runs)}**", ""])
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
