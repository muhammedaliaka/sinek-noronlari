"""Ayna-çifti yapı denetimi (R-4; geliştirme/tanı aracı, ölçüt değil).

    python3 -I -m sinek.experiments.odor_pair_check results/odor_val/O4a_s240/partial/plastic.npz

Soru: "decoy-ilk" ve "gerçek-ilk" sayıları neden birebir eşit çıkabiliyor? Aday: ardışık kopyalar ayna çiftidir (2k özgün, 2k+1 aynası); odordan
bağımsız bir yan yanlılığı olan canlı özgünde decoy'a, aynada gerçek hedefe çarpar. Bu araç her ayna çiftinin (özgün, ayna) sonuç çiftini
sayar (d=decoy, r=gerçek, n=hiçbiri) ve (d,r)+(r,d) çift oranını, çiftler karıştırılınca beklenenle karşılaştırır (permütasyon, 2000).
Girdi: kontrol noktası .npz (anahtarlar ep0, ep3, ... ; her biri (canlı, test_reps) yuva dizisi: 0 gerçek, 1 decoy, -1 hiçbiri).
"""
from __future__ import annotations

import sys

import numpy as np


def pair_table(slots: np.ndarray) -> dict:
    s = np.asarray(slots)
    if s.shape[1] % 2:
        raise ValueError("test_reps çift olmalı")
    a, b = s[:, 0::2].ravel(), s[:, 1::2].ravel()
    code = {1: "d", 0: "r", -1: "n"}
    tab = {}
    for x, y in zip(a, b):
        k = code[int(x)] + code[int(y)]
        tab[k] = tab.get(k, 0) + 1
    return {"table": tab, "a": a, "b": b}


def opposite_fraction(a: np.ndarray, b: np.ndarray) -> float:
    return float((((a == 1) & (b == 0)) | ((a == 0) & (b == 1))).mean())


def perm_test(a: np.ndarray, b: np.ndarray, n: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Gözlenen (d,r)/(r,d) çift oranı, çiftler karıştırılınca (aynı kenar dağılımı) beklenen ve tek-yönlü p."""
    rng = np.random.default_rng(seed)
    obs = opposite_fraction(a, b)
    null = np.array([opposite_fraction(a, rng.permutation(b)) for _ in range(n)])
    return obs, float(null.mean()), float((1 + (null >= obs).sum()) / (n + 1))


def main(argv=None) -> None:
    for path in (argv if argv is not None else sys.argv[1:]):
        z = np.load(path)
        for k in sorted(z.files, key=lambda x: (len(x), x)):
            if not k.startswith("ep"):
                continue
            pt = pair_table(z[k])
            obs, exp, p = perm_test(pt["a"], pt["b"])
            s = z[k]
            print(f"{path} {k}: decoy-ilk {np.mean(s == 1):.3f} gerçek-ilk {np.mean(s == 0):.3f} | çiftler {pt['table']} | (d,r)/(r,d) oranı {obs:.3f} beklenen {exp:.3f} p={p:.4f}")


if __name__ == "__main__":
    main()
