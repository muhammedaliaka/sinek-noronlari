"""R-8 kuram kontrolü (kanıt değildir; beyin DEĞİL, soyut ödül öğrenici): hızlı + yavaş plastisite hız–gürültü ödünleşimini hafifletir mi?

    python3 -I -m sinek.experiments.kuram_iki_zaman --out results/kuram_iki_zaman.md

Model: O5 programı (iki kol, p 0,8/0,2, bölüm 21'de tersine çevirme, 40 bölüm); öğrenici kol değerlerini Q_a ← Q_a + α(r − Q_a) ile günceller
(yalnız seçilen kol gözlenir), kolu softmax((Q_1 − Q_2)/T) ile seçer. Ölçü: O5 bloklarında (geç faz-1 11-20, geçiş 21-30, geç faz-2 31-40) bölüm başına ödül.

ÖNCEDEN YAZILMIŞ TAHMİN (R-8, koşudan önce; belirsizliği açık):
 1. Tek EMA: durağan bloklar α küçüldükçe artar, geçiş bloğu α küçüldükçe düşer; (geç1+geç2) toplamı orta α'da (≈0,2–0,5) tepe yapar.
 2. Sabit karışım Q = ½(Q_hızlı + Q_yavaş) doğrusal bir süzgeçtir (iki üstel çekirdek): en iyi TEK α'dan farkı küçüktür (|fark| < 0,01 ödül/bölüm).
    Yanlışlanma: karışım en iyi tek α'yı ≥ 0,01 aşarsa "aynı ödünleşim eğrisi üzerinde" kuramım yanlıştır.
 3. Sürprizle kapılı α (kayıp/şaşırma biriktikçe hızlı) en iyi tek α'dan küçük, pozitif kazanç verir (0,01–0,03; geçiş bloğunda), çünkü Bernoulli 0,8/0,2 geri bildirimi
    değişimi bölüm başına zayıf işaretler; kazancın üst sınırı kanal gürültüsüyle kısıtlıdır.
Sonuç beyne aktarılırsa bile yalnız bir YÖN verir: gerçek beyinde okuma gürültüsü (K-028) ve yaklaşma gürültüsü ayrıca vardır.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

P_HI, P_LO = 0.8, 0.2
BLOCKS = {"geç faz-1 (11-20)": (10, 20), "geçiş (21-30)": (20, 30), "geç faz-2 (31-40)": (30, 40)}


def play(learner: str, par: dict, n: int, rng, episodes: int = 40, switch: int = 20, temp: float = 0.15) -> np.ndarray:
    """(yaşam, bölüm) ödül. learner: tek | karisim | kapili."""
    good = rng.integers(0, 2, n)                                            # ilk iyi kol
    q = {k: np.full((n, 2), 0.5) for k in ("f", "s")}
    surprise = np.zeros(n)
    out = np.zeros((n, episodes))
    for t in range(episodes):
        better = np.where(t < switch, good, 1 - good)
        if learner == "tek":
            Q = q["s"]
        elif learner == "karisim":
            Q = par["w"] * q["f"] + (1 - par["w"]) * q["s"]
        else:
            Q = q["s"]
        z = (Q[:, 1] - Q[:, 0]) / temp
        pick = (rng.random(n) < 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))).astype(int)
        p = np.where(pick == better, P_HI, P_LO)
        r = (rng.random(n) < p).astype(float)
        out[:, t] = r
        idx = np.arange(n)
        if learner == "kapili":
            pe = r - q["s"][idx, pick]
            surprise = (1 - par["beta"]) * surprise + par["beta"] * (np.abs(pe) > 0.5)      # durağan tabanı ≈0,2 (iyi kol 0,2 olasılıkla ödülsüz, kötü kol 0,2 ile ödüllü)
            alpha = par["a_slow"] + (par["a_fast"] - par["a_slow"]) * np.clip((surprise - 0.25) / par["theta"], 0.0, 1.0)
            q["s"][idx, pick] += alpha * pe
        else:
            for k, a in (("s", par["a_slow"]), ("f", par.get("a_fast", par["a_slow"]))):
                q[k][idx, pick] += a * (r - q[k][idx, pick])
    return out


def summarize(R: np.ndarray) -> dict:
    d = {k: float(R[:, a:b].mean()) for k, (a, b) in BLOCKS.items()}
    d["geç1+geç2 ortalama"] = (d["geç faz-1 (11-20)"] + d["geç faz-2 (31-40)"]) / 2
    d["üçü ortalama"] = float(np.mean([d[k] for k in BLOCKS]))
    return d


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=40000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(a.seed)
    rows = []
    for al in (0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0):
        rows.append((f"tek EMA α={al}", summarize(play("tek", {"a_slow": al}, a.n, rng))))
    for af, as_, w in ((0.8, 0.15, 0.5), (0.8, 0.1, 0.5), (0.5, 0.1, 0.5), (0.8, 0.15, 0.3), (0.8, 0.15, 0.7)):
        rows.append((f"karışım hızlı {af} / yavaş {as_}, w_hızlı={w}", summarize(play("karisim", {"a_fast": af, "a_slow": as_, "w": w}, a.n, rng))))
    for af, as_, beta, theta in ((0.8, 0.15, 0.3, 0.5), (0.8, 0.15, 0.5, 0.5), (0.8, 0.1, 0.3, 0.3), (1.0, 0.1, 0.3, 0.3)):
        rows.append((f"kapılı α {as_}→{af}, β={beta}, θ={theta}", summarize(play("kapili", {"a_fast": af, "a_slow": as_, "beta": beta, "theta": theta}, a.n, rng))))
    keys = list(BLOCKS) + ["geç1+geç2 ortalama", "üçü ortalama"]
    L = ["# İki zaman ölçekli plastisite — soyut kuram kontrolü (R-8; kanıt değildir)", "",
         f"{a.n} yaşam/öğrenici, T=0,15, p 0,8/0,2, 40 bölüm, tersine çevirme 21. bölümde. Hücre: bölüm başına ödül (en yüksek olası ≈0,8). Standart hata ≈ {np.sqrt(0.2 / a.n / 10):.4f} (blok).", "",
         "| öğrenici | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
    for name, d in rows:
        L.append(f"| {name} | " + " | ".join(f"{d[k]:.3f}" for k in keys) + " |")
    best_single = max((d["üçü ortalama"], n) for n, d in rows if n.startswith("tek"))
    best_mix = max((d["üçü ortalama"], n) for n, d in rows if n.startswith("karışım"))
    best_gate = max((d["üçü ortalama"], n) for n, d in rows if n.startswith("kapılı"))
    L += ["", f"En iyi tek EMA (üçü ortalama): {best_single[1]} → {best_single[0]:.3f}; en iyi karışım: {best_mix[1]} → {best_mix[0]:.3f} (fark {best_mix[0] - best_single[0]:+.3f}); "
          f"en iyi kapılı: {best_gate[1]} → {best_gate[0]:.3f} (fark {best_gate[0] - best_single[0]:+.3f})."]
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
