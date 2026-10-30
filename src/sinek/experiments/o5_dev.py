"""O5 (olasılıklı iki-kollu koku oyunu, tersine çevirmeli) GELİŞTİRME pilotu (kanıt değildir): hızlı öğrenme + gürültülü ödül + oturum içi tersine çevirme.

    python3 -I -m sinek.experiments.o5_dev --pre results/odor_games/pre_s100.npz --seed 120 --arms "naive_plastic@1,naive_plastic@0.3,naive@0" --out results/o5_dev/a.md

Her eleman bağımsız bir yaşam: ÖĞRENMEMİŞ ("naive") beyin, ardışık `--episodes` bölüm, ağırlıklar bölümler arasında korunur. İki kaynak: koku A (yuva 0) ve B (yuva 1), rastgele konumlar.
İlk `--switch` bölümde canlıya göre iyi koku (rol dengeli, `swap`) ödül olasılığı p_hi=0,8, diğeri p_lo=0,2; sonra roller tersine döner.
Ölçü: bloktaki ilk-temasların "o an iyi olan kokuya" oranı (temas yoksa sayılmaz; temas yok oranı ayrı), ödül oranı.
Kol belirtimi: `<kol>@<öğrenme ölçeği>[/k<K>][/t<τ_valence>][/r<reward_target>]`; `/k` ile `PlasticEnsembleBrain` (K bağımsız öğrenen kopya, karar için ortalama), `/t` okuma entegrasyon süresi, `/r` DAN hedefi (ödülün V karşılığı; varsayılan 0,6).
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

SONUÇ-3 (tohum 134, 48 yaşam, pre_s102; betimsel): geç blok seçiciliği (b3,b4,b7,b8) @1 0,655 / @2 0,660 / @4 0,623; geç blok temas-yok @1 0,30 / @2 0,37 / @4 0,42; ödül @1 0,39 / @2 0,37 / @4 0,33.
TAHMİN-3 tuttu (@2: Δ=+0,005; @4 daha iyi değil, −0,03) — ek bulgu: η büyüdükçe yaklaşma azalıyor (temas-yok artıyor). Ölçek kaldıraç değil. @2/k4/t0.04 kolu bu sürümde sonradan eklenen sonuç satırında.

TAHMİN-4 (2026-10-30, DAN hedefi `reward_target` T taraması, koşudan önce): denge değeri V* = T·p (iyi koku 0,8·T, kötü 0,2·T), yani öğrenilmiş V farkı 0,6·T ve gürültüden bağımsız; hareket kuralı KONTRAST = (v_l−v_r)/(|v_l|+|v_r|+0,05)
(normalize, ε=0,05 V) — küçük V'lerde gürültü kontrastı bozar. Seçicilik öğrenilen sinyalin genliği/gürültü oranıyla sınırlıysa T 0,6→1,5 geç blok seçiciliğini ≥ +0,05 artırır (≥0,70), T 2,5 doygunlukta (W ∈ [0,W0]) kalır ya da biraz bozulur;
T 0,4 ise bozulur (≤ −0,03) ve temas-yok artar. Seçicilik T'ye duyarsızsa (|Δ| <0,05 hem 1,5 hem 2,5'te): sınır genlik değil, normalize hareket kuralı/geometri/okuma yapısı → sıradaki iş hareket kuralı. Ayrıca T büyüdükçe temasın azalmayacağını bekliyorum (η'nın tersine
yaklaşma V'nin işaretiyle belirlenir, büyüklüğüyle değil).

SONUÇ-4 (tohum 134, pre_s102, 48 yaşam; betimsel; CRN-eşli dünyalar; geç blok = b3,b4,b7,b8): T=0,4: seçicilik 0,627 / temas-yok 0,367 / ödül 0,34; T=0,6: 0,655 / 0,295 / 0,39; T=1,5: 0,700 / 0,207 / 0,46; T=2,5: 0,715 / 0,165 / 0,48.
Tek yönlü monoton doz–yanıt. TAHMİN-4 değerlendirmesi (dürüst): T=1,5 seçicilik +0,045 (eşik +0,05'in hemen altı; mutlak ≥0,70 ✔), temas-yok azaldı (yaklaşma ARTTI; η'nın tersi ✔);
T=0,4: −0,028 (eşik −0,03'e yakın, yön ✔, temas-yok arttı ✔); **T=2,5 için "doygunluk/bozulma" tahminim YANLIŞ çıktı**: eğri düzleşiyor (0,6→1,5: +0,045, 1,5→2,5: +0,015) ama bozulmuyor.
T=2,5 ödül kazancı +0,09 (K=4 topluluğunun O5b ortalaması ≈+0,09) ama 1× hesap maliyetiyle. Tek popülasyon/tek tohum: yineleme gerekir.

TAHMİN-5 (2026-10-30, yineleme: tohum 135, FARKLI popülasyon pre_s100; kollar @1, @1/r2.5, @1/r4, koşudan önce): (a) @1/r2.5 − @1 ödül ≥ +0,05 ve geç seçicilik ≥ +0,03, temas-yok azalır; (b) @1/r4 ≈ r2.5 (ödül farkı |Δ| ≤ 0,03)
ya da hafif bozulma (seçicilik ≤ r2.5 − 0,02), çünkü ulaşılabilir V doygunluğunun üstünde δ > 0 kalıcı olur ve W iki koku için de tabana iner (ayırt etme zayıflar); temas artmaya devam eder.
Tutmazsa: (a) tutmazsa T bulgusu popülasyona özgü (ya da kazananın laneti); (b) bozulmazsa T doygunluğu henüz görülmemiş, tarama genişletilir.
"""
from __future__ import annotations

import argparse
import dataclasses
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..ensemble import PlasticEnsembleBrain
from ..games.protocol import bandit_schedule, make_game_creature, play_sequence


def parse_arm(tok: str) -> tuple[str, float | None, int, float | None, float | None]:
    head, *opts = tok.split("/")
    name, _, sc = head.partition("@")
    k, tau, rt = 1, None, None
    for o in opts:
        if o.startswith("k"):
            k = int(o[1:])
        elif o.startswith("t"):
            tau = float(o[1:])
        elif o.startswith("r"):
            rt = float(o[1:])
        else:
            raise ValueError(f"bilinmeyen kol seçeneği: {o}")
    return name, (float(sc) if sc else None), k, tau, rt


def run_arm(pre, arm: str, scale, seed: int, agents: int, copies: int, episodes: int, switch: int, seconds: float, p_hi: float, p_lo: float,
            k: int = 1, tau: float | None = None, reward_target: float | None = None) -> dict:
    ids = list(range(min(agents, pre.world.B)))
    c = make_game_creature(pre, "O5", arm, ids, copies, seed)
    if scale is not None:
        c.brain.eta_scale = torch.full((c.world.B,), float(scale))
    if reward_target is not None:                                                  # yalnız bu canlıların DAN hedefi (ödülün V karşılığı)
        c.brain.cfg = dataclasses.replace(c.brain.cfg, reward_target=float(reward_target))
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
        arm, sc, k, tau, rt = parse_arm(tok)
        r = run_arm(pre, arm, sc, a.seed, a.agents, a.copies, a.episodes, a.switch, a.seconds, a.p_hi, a.p_lo, k, tau, rt)
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
