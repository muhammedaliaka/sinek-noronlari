"""O5 (olasılıklı iki-kollu koku oyunu, tersine çevirmeli) GELİŞTİRME pilotu (kanıt değildir): hızlı öğrenme + gürültülü ödül + oturum içi tersine çevirme.

    python3 -I -m sinek.experiments.o5_dev --pre results/odor_games/pre_s100.npz --seed 120 --arms "naive_plastic@1,naive_plastic@0.3,naive@0" --out results/o5_dev/a.md

Her eleman bağımsız bir yaşam: ÖĞRENMEMİŞ ("naive") beyin, ardışık `--episodes` bölüm, ağırlıklar bölümler arasında korunur. İki kaynak: koku A (yuva 0) ve B (yuva 1), rastgele konumlar.
İlk `--switch` bölümde canlıya göre iyi koku (rol dengeli, `swap`) ödül olasılığı p_hi=0,8, diğeri p_lo=0,2; sonra roller tersine döner.
Ölçü: bloktaki ilk-temasların "o an iyi olan kokuya" oranı (temas yoksa sayılmaz; temas yok oranı ayrı), ödül oranı.
Kol belirtimi: `<kol>@<öğrenme ölçeği>[/k<K>][/t<τ_valence>]`; `/k` ile `PlasticEnsembleBrain` (K bağımsız öğrenen kopya, karar için ortalama), `/t` okuma entegrasyon süresi.
ÖNCEDEN YAZILMIŞ TAHMİN (R-8): öğrenmesiz kol (naive@0) ≈0,5; tek denemede öğrenen plastik kol (ölçek 1) bir "kazan-kal / kaybet-değiştir" benzeri davranır: durağan %80/%20 için
kuramsal denge ≈0,8 (ödül oranı ≈0,68), tersine çevirmeden sonra birkaç bölümde uyum; küçük ölçek (0,3) daha yüksek durağan başarı (ortalama alır) ama tersine çevirmede daha yavaş —
yani öğrenme oranı için gerçek bir hız–gürültü ödünleşimi görülmeli. Bu tahminlerden biri tutmazsa belgede "yanlış çıktı" olarak yazılır.

TAHMİN-2 (2026-10-29, plastik topluluk için, koşudan önce): `naive_plastic@1/k4/t0.04`, `naive_plastic@1`'e göre geç bloklarda (11-20, 31-40) ödül oranını ≥ +0,05 artırır
(K-038: O1a'da test-zamanı topluluk +0,26…+0,32; O5'te yaklaşma ve seçim aynı okuma gürültüsünden etkileniyor). Tersine çevirme sonrası ilk blok (b5) düşüşü değişmez ya da küçülür.
Tutmazsa: darboğaz okuma gürültüsü değil (öğrenme gürültüsü / elle yazılmış δ kuralı / yaklaşma), belgede "yanlış çıktı" yazılır ve plastik topluluk önceliği düşer.

TAHMİN-3 (2026-10-30, öğrenme hızı η ölçeği taraması, koşudan önce; O5b sonrası: topluluk seçiciliği artırmadı, seçicilik farkı +0,007…+0,058): soyut öğrenicide en iyi α yüksek (0,3–0,5;
`kuram_iki_zaman`), yani beyin etkin α'sı düşükse ölçek 2 seçiciliği artırmalıydı. AMA geliştirme verisi (tohum 120): ölçek 0,3 ile 1 geç blok seçiciliği ayırt edilemez (0,61–0,68 vs 0,63–0,68).
Bu veriden tahminim "duyarsızlık": naive_plastic@2 geç blok seçiciliği (b3,b4,b7,b8 ortalaması) @1'den en çok ±0,05 farklı; @4 en fazla @1 kadar iyi (temas kaybı/gürültü ile bozulma ≥0,03 olabilir).
Tutarsa: ölçek kaldıraç değildir; sınır elle yazılmış δ kuralı / ağırlık sınırları / değer okuması yapısındadır → sıradaki iş DAN yolu (sönüm, PPL1). Tutmazsa (|Δ| >0,05): hız ödünleşimi gerçek, η × K ızgarasına geçilir.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..ensemble import PlasticEnsembleBrain
from ..games.protocol import bandit_schedule, make_game_creature, play_sequence


def parse_arm(tok: str) -> tuple[str, float | None, int, float | None]:
    head, *opts = tok.split("/")
    name, _, sc = head.partition("@")
    k, tau = 1, None
    for o in opts:
        if o.startswith("k"):
            k = int(o[1:])
        elif o.startswith("t"):
            tau = float(o[1:])
        else:
            raise ValueError(f"bilinmeyen kol seçeneği: {o}")
    return name, (float(sc) if sc else None), k, tau


def run_arm(pre, arm: str, scale, seed: int, agents: int, copies: int, episodes: int, switch: int, seconds: float, p_hi: float, p_lo: float,
            k: int = 1, tau: float | None = None) -> dict:
    ids = list(range(min(agents, pre.world.B)))
    c = make_game_creature(pre, "O5", arm, ids, copies, seed)
    if scale is not None:
        c.brain.eta_scale = torch.full((c.world.B,), float(scale))
    if k > 1 or tau is not None:
        c.brain = PlasticEnsembleBrain(c.brain, k, tau)
    sch = bandit_schedule(c.world.swap.cpu(), episodes, switch, p_hi, p_lo)
    r = play_sequence(c, sch, seconds, learn=True)
    better = np.stack([(p[:, 1] > p[:, 0]).numpy().astype(int) for p in sch])           # (ep, B) o an iyi olan yuva (0=A,1=B)
    r["better"] = better
    return r


def blocks(r: dict, size: int) -> list[tuple[float, float, float]]:
    n = r["slot"].shape[0]
    out = []
    for s in range(0, n, size):
        sl = slice(s, s + size)
        ch = r["slot"][sl] >= 0
        good = (r["slot"][sl] == r["better"][sl]) & ch
        out.append((float(good.sum() / max(ch.sum(), 1)), float(1 - ch.mean()), float(r["got"][sl].mean())))
    return out


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arms", default="naive_plastic@1,naive_plastic@0.3,naive@0")
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--copies", type=int, default=2)
    ap.add_argument("--episodes", type=int, default=40)
    ap.add_argument("--switch", type=int, default=20)
    ap.add_argument("--block", type=int, default=5)
    ap.add_argument("--seconds", type=float, default=40.0)
    ap.add_argument("--p-hi", type=float, default=0.8)
    ap.add_argument("--p-lo", type=float, default=0.2)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.seed >= 200:
        raise SystemExit("geliştirme aracı: doğrulayıcı tohumları (≥200) yasak (R-2)")
    torch.set_num_threads(a.threads)
    pre = checkpoint.load(a.pre)
    t0 = time.time()
    nb = a.episodes // a.block
    L = ["# O5 geliştirme pilotu (kanıt değildir)", "",
         f"{a.agents} canlı × {a.copies} kopya, {a.episodes} bölüm × {a.seconds:g} sn, tersine çevirme bölüm {a.switch}; p_hi={a.p_hi}, p_lo={a.p_lo}; oyun tohumu {a.seed}.",
         "Hücre: iyi kokuyu seçme oranı (temas olanlar arasında) / temas-yok oranı. Son sütun: toplam ödül oranı (bölüm başına).", "",
         "| kol | " + " | ".join(f"b{i + 1} ({i * a.block + 1}-{(i + 1) * a.block})" for i in range(nb)) + " | ödül oranı |", "|---|" + "---|" * (nb + 1)]
    for tok in a.arms.split(","):
        arm, sc, k, tau = parse_arm(tok)
        r = run_arm(pre, arm, sc, a.seed, a.agents, a.copies, a.episodes, a.switch, a.seconds, a.p_hi, a.p_lo, k, tau)
        bl = blocks(r, a.block)
        L.append(f"| {tok} | " + " | ".join(f"{g:.2f} / {nc:.2f}" for g, nc, _ in bl) + f" | {r['got'].mean():.2f} |")
        print(f"[{time.time() - t0:5.0f}s] {L[-1]}", flush=True)
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
