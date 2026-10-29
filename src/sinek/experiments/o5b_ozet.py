"""O5b doğrulayıcı sonuçlarını toplar ve docs/odor_o5b_plani.md §5 karar kurallarını uygular (ölçüt/eşik KEŞFETMEZ).

    python -m sinek.experiments.o5b_ozet --dir results/o5_val [--out results/o5_val/ozet_o5b.md]

İki ayrı iddia (her biri kendi hükmü):
  A (seçicilik / öğrenme):  dört popülasyonda kapı G ∧ N1 (4/4 popülasyon) ∧ N2 (≥3/4 popülasyon)
  B (topluluk):             dört popülasyonda kapı G ∧ E1 (≥3/4 popülasyon)
Eksik (bitmemiş) koşu varsa ve kural henüz çürütülmediyse hüküm "BEKLİYOR"; sessizce atlanmaz.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SEEDS = (270, 271, 272, 273)       # docs/odor_o5b_plani.md §2
N_POP = len(SEEDS)


def load(d: Path, seed: int) -> dict | None:
    f = d / f"b_s{seed}" / "results.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def _status(runs: dict[int, dict | None], rules: dict[str, int]) -> str:
    """rules: ölçüt → gereken en az geçen popülasyon sayısı. Kapı her popülasyonda tamam olmalı."""
    done = [r for r in runs.values() if r is not None]
    if any(not r["eval"]["gates_ok"] for r in done):
        return "BAŞARISIZ"                                                # kapı eksik → iddia yapılamaz
    undecided = N_POP - len(done)
    ok = True
    for crit, need in rules.items():
        passes = sum(1 for r in done if r["eval"]["criteria"][crit]["passed"])
        fails = len(done) - passes
        if fails > N_POP - need:
            return "BAŞARISIZ"
        ok &= passes >= need
    return "BAŞARILI" if (ok and undecided == 0) else "BEKLİYOR"


def verdicts(runs: dict[int, dict | None]) -> dict[str, str]:
    return {"A (seçicilik/öğrenme)": _status(runs, {"N1_secicilik_toplam": N_POP, "N2_yeniden_ogrenme_faz2": N_POP - 1}),
            "B (topluluk)": _status(runs, {"E1_topluluk_odul": N_POP - 1})}


def table(runs: dict[int, dict | None]) -> str:
    cols = ("N1_secicilik_toplam", "N2_yeniden_ogrenme_faz2", "E1_topluluk_odul")
    L = ["| tohum | ödül: plastic_ens / plastic / frozen / reference | " + " | ".join(cols) + " | E2 (betimsel) | kapı G |", "|---|---|" + "---|" * (len(cols) + 2)]
    for seed in SEEDS:
        r = runs.get(seed)
        if r is None:
            L.append(f"| {seed} | — | " + " | ".join("—" for _ in cols) + " | — | — |")
            continue
        e, c = r["eval"], r["eval"]["criteria"]
        fmt = lambda x: f"{x['mean']:+.3f} [{x['ci'][0]:+.3f}; {x['ci'][1]:+.3f}] p={x['p']:.4f} {'✔' if x['passed'] else '✘'}"   # noqa: E731
        d = e.get("descriptive", {}).get("E2_topluluk_net_tercih")
        L.append(f"| {seed} | " + " / ".join(f"{r['reward_rate'][a]:.3f}" for a in ("plastic_ens", "plastic", "frozen", "reference")) + " | " + " | ".join(fmt(c[k]) for k in cols)
                 + f" | {fmt(d) if d else '—'} | {'tamam' if e['gates_ok'] else 'EKSİK'} |")
    return "\n".join(L)


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="results/o5_val")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    runs = {s: load(d, s) for s in SEEDS}
    v = verdicts(runs)
    text = "\n".join(["# O5b doğrulayıcısı — özet (otomatik; `o5b_ozet`)", "", table(runs), "",
                      "**Hükümler (docs/odor_o5b_plani.md §5):** " + "; ".join(f"{k}: **{x}**" for k, x in v.items()), ""])
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
