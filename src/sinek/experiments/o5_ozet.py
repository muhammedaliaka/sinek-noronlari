"""O5 doğrulayıcı sonuçlarını toplar ve docs/odor_o5_plani.md §5 karar kuralını uygular (ölçüt/eşik KEŞFETMEZ).

    python -m sinek.experiments.o5_ozet --dir results/o5_val [--out results/o5_val/ozet.md]

Hüküm: iki tohumun (260, 261) İKİSİ de (kapı G ∧ P1 ∧ P2 ∧ P3) geçerse BAŞARILI. Biri geçip diğeri geçmezse KISMİ (iddia yok; BAŞARISIZ sayılır).
Eksik (bitmemiş) koşu varsa ve henüz başarısızlık yoksa hüküm "BEKLİYOR" olur; sessizce atlanmaz.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SEEDS = (260, 261)      # docs/odor_o5_plani.md §2
ARMS = ("plastic", "frozen", "reference")
CRIT = ("P1_odul_gec_faz1", "P2_odul_gec_faz2", "P3_ozgullukte_net_tercih")


def load(d: Path, seed: int) -> dict | None:
    f = d / f"s{seed}" / "results.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def verdict(runs: dict[int, dict | None]) -> str:
    rs = [runs.get(s) for s in SEEDS]
    done = [r for r in rs if r is not None]
    passed = [r["eval"]["passed"] for r in done]
    if len(done) == len(SEEDS):
        return "BAŞARILI" if all(passed) else ("KISMİ (iddia yok)" if any(passed) else "BAŞARISIZ")
    return "BAŞARISIZ" if not all(passed) else "BEKLİYOR"       # bir tohum geçemediyse karar artık değişemez (iki tohum da gerekir)


def table(runs: dict[int, dict | None]) -> str:
    L = ["| tohum | ödül oranı: plastic / frozen / reference | P1 geç faz-1 [%99 GA] | P2 geç faz-2 [%99 GA] | P3 özgüllük [%99 GA] | kapı G | karar |", "|---|---|---|---|---|---|---|"]
    for seed in SEEDS:
        r = runs.get(seed)
        if r is None:
            L.append(f"| {seed} | — | — | — | — | — | BEKLİYOR |")
            continue
        e, c = r["eval"], r["eval"]["criteria"]
        fmt = lambda k: f"{c[k]['mean']:+.3f} [{c[k]['ci'][0]:+.3f}; {c[k]['ci'][1]:+.3f}] p={c[k]['p']:.4f} {'✔' if c[k]['passed'] else '✘'}"   # noqa: E731
        gates = "tamam" if e["gates_ok"] else "EKSİK: " + ", ".join(k for k, v in e["gates"].items() if not v)
        L.append(f"| {seed} | " + " / ".join(f"{r['reward_rate'][a]:.3f}" for a in ARMS) + " | " + " | ".join(fmt(k) for k in CRIT) + f" | {gates} | {'BAŞARILI' if e['passed'] else 'BAŞARISIZ'} |")
    return "\n".join(L)


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="results/o5_val")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    runs = {s: load(d, s) for s in SEEDS}
    text = "\n".join(["# O5 doğrulayıcısı — özet (otomatik; `o5_ozet`)", "", table(runs), "",
                      f"**Hüküm (docs/odor_o5_plani.md §5): {verdict(runs)}**", ""])
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
