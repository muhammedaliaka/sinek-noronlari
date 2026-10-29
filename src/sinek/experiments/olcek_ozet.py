"""Ölçek ekseni doğrulayıcı sonuçlarını toplar ve docs/olcek_plani.md §4 hüküm kuralını uygular (ölçüt/eşik KEŞFETMEZ).

    python -m sinek.experiments.olcek_ozet --dir results/scale_val [--out results/scale_val/ozet.md]

Oyun hükmü: iki popülasyonun ikisinde de (kapılar tamam ∧ P1 ∧ P2) geçerse BAŞARILI. Ölçek iddiası: O1a ve O1b ikisi de BAŞARILI.
Eksik (bitmemiş) koşu varsa hüküm "BEKLİYOR" olur; sessizce atlanmaz.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

GAMES = {"O1a": (250, 251), "O1b": (252, 253)}      # docs/olcek_plani.md §2
ARMS = ("reference", "anosmic", "frozen", "anosmic_ens", "ens")


def load(d: Path, game: str, seed: int) -> dict | None:
    f = d / f"{game}_s{seed}" / "results.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def verdict(runs: dict[tuple[str, int], dict | None]) -> dict:
    """runs: (oyun, tohum) → results.json içeriği ya da None (bitmedi). Dönen: oyun → 'BAŞARILI'|'BAŞARISIZ'|'BEKLİYOR', 'ölçek' → aynı."""
    out = {}
    for game, seeds in GAMES.items():
        rs = [runs.get((game, s)) for s in seeds]
        if any(r is None for r in rs):
            # bir koşu başarısızsa hüküm artık değişemez; yine de bitmeyen koşular açıkça işaretlenir
            out[game] = "BAŞARISIZ" if any(r is not None and not r["eval"]["passed"] for r in rs) else "BEKLİYOR"
        else:
            out[game] = "BAŞARILI" if all(r["eval"]["passed"] for r in rs) else "BAŞARISIZ"
    vals = list(out.values())
    out["ölçek"] = "BAŞARILI" if all(v == "BAŞARILI" for v in vals) else ("BAŞARISIZ" if "BAŞARISIZ" in vals else "BEKLİYOR")
    return out


def table(runs: dict[tuple[str, int], dict | None]) -> str:
    L = ["| oyun | tohum | " + " | ".join(ARMS) + " | P1 ens−frozen [%99 GA] | P2 ens−anosmic_ens [%99 GA] | P3 (betimsel) | kapılar | sızıntı | karar |",
         "|---|---|" + "---|" * (len(ARMS) + 6)]
    for (game, seed), r in runs.items():
        if r is None:
            L.append(f"| {game} | {seed} | " + " | ".join("—" for _ in ARMS) + " | — | — | — | — | — | BEKLİYOR |")
            continue
        e, c = r["eval"], r["eval"]["criteria"]
        fmt = lambda k: f"{c[k]['mean']:+.3f} [{c[k]['ci'][0]:+.3f}; {c[k]['ci'][1]:+.3f}] p={c[k]['p']:.4f} {'✔' if c[k]['passed'] else '✘'}"   # noqa: E731
        d = e.get("descriptive", {}).get("P3_anosmic_ens~anosmic")
        p3 = f"{d['mean']:+.3f} [{d['ci'][0]:+.3f}; {d['ci'][1]:+.3f}] {'±δ_eq içinde' if d['passed'] else 'dışında'}" if d else "—"
        gates = "tamam" if e["gates_ok"] else "EKSİK: " + ", ".join(k for k, v in e["gates"].items() if not v)
        L.append(f"| {game} | {seed} | " + " | ".join(f"{r['p_hit'][a]:.3f}" for a in ARMS) + f" | {fmt('P1_ens-frozen')} | {fmt('P2_ens-anosmic_ens')} | {p3} | {gates} | "
                 f"{r['leak']['violations']}/{r['leak']['checked']} | {'BAŞARILI' if e['passed'] else 'BAŞARISIZ'} |")
    return "\n".join(L)


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="results/scale_val")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    runs = {(g, s): load(d, g, s) for g, seeds in GAMES.items() for s in seeds}
    v = verdict(runs)
    text = ["# Ölçek ekseni doğrulayıcısı — özet (otomatik; `olcek_ozet`)", "", table(runs), "",
            "**Hükümler (docs/olcek_plani.md §4):** " + "; ".join(f"{g}: {v[g]}" for g in GAMES) + f"; **ölçek iddiası: {v['ölçek']}**", ""]
    text = "\n".join(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
