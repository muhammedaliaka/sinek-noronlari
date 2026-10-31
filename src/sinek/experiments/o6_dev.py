"""O6 (görsel + koku, ısı tuzağı) GELİŞTİRME pilotu (kanıt değildir; tohum <200): ardışık bölümlerde öğrenme eğrisi.

    python3 -I -m sinek.experiments.o6_dev --pre results/odor_games/pre_s102.npz --game O6b --seed 140 --arms naive_plastic,naive_plastic_blind,naive --out results/o6_dev/b140.md

Her eleman bağımsız bir yaşam (ÖĞRENMEMİŞ "naive" beyin; ağırlıklar bölümler arasında korunur). Yuva 0 = güvenli (ödül +1), yuva 1 = ısı tuzağı (−1); herhangi bir temas bölümü bitirir.
Çıktı (bloklar): güvenli ilk temas oranı / tuzak ilk temas oranı / temas-yok oranı ve NET TERCİH NP = güvenli − tuzak (temas yoksa 0; yaklaşmadan arındırılmış, E-15).
Kollar: naive_plastic (öğrenen; O6b/c'de görsel açık), naive_plastic_blind (görsel girdi sıfır; aynı beyin ve RNG tüketimi), naive (öğrenme kapalı). Görsel ön uç yalnız O6b/O6c oyunlarında açıktır (O6a koku-yalnız).

ÖNCEDEN YAZILMIŞ TAHMİN (R-8, 2026-10-30, koşudan önce; belirsizliği açık):
 O6a (yalnız koku; yuva 0 koku A ödül, yuva 1 koku B ısı): öğrenen kolda NP son blokta ≥ +0,30 (O5'te 0,8/0,2 olasılıkla ≈ +0,2…0,3 görülmüştü; burada ödül/ısı kesin olduğundan daha yüksek beklenir); naive (öğrenmesiz) ≈ 0 (|NP| < 0,10).
 O6b (iki yuvada AYNI koku; ayrım yalnız görsel X/Y): naive_plastic_blind NP ≈ 0 (|NP| < 0,10; bilgi yok); naive_plastic (görsel) NP son blokta pozitif ama O6a'dan DÜŞÜK (görsel girdili KC ≈%8, VPN→KC bağlantıları PN'den ≈2× zayıf): NP ∈ [+0,10, +0,30].
 Yanlışlanma: görsel NP < +0,10 ise "görsel yol bu hâliyle yetersiz" (G-V0 ayrılabilirlik gösterse bile öğrenilen MBON okuması çok zayıf); NP ≥ O6a ise tahminim (görsel girdi daha zayıf) yanlış.
 Her iki durumda ayar sürüsü YAPILMAZ (E-08); önce kuram kontrolü ve karar defteri kaydı.

SONUÇ-1 (O6b, tohum 140, kalibrasyonsuz): TAHMİN YANLIŞ — görsel kolda temas-yok 1,00 (blok 1'den), NP 0; kör kolda öğrenme var. Neden: eğitimsiz ağın görsel girdiye innate değeri V ≈ −0,2…−0,5
(`class_balance` yalnız koku için kalibre; avoid-sınıfı MBON hızı artıyor) → yaratık görsel kaynaktan kaçıyor, hiç temas etmiyor, hiç öğrenemiyor. Kod hatası değil, kalibrasyon eksiği (E-17).
ÇÖZÜM (K-051): `games.vis_calibration.neutral_scale` — görsel-KC→avoid-MBON çarpanı κ, ön-tanımlı ölçüt |V_ort(X,Y) − V(girdi yok)| ≤ 0,01 (düzey 0,6); görev bilgisi kullanılmaz. κ = 0,704 (pre_s102); düzey 0,2/0,6/1,0'da kalan sapma +0,018/−0,006/−0,016.

SONUÇ-2 (O6b, tohum 140, κ=0,704): TAHMİN-2 YANLIŞ — naive_plastic NP −0,03/−0,01/+0,05/+0,01/−0,01/0,00 (temas-yok 0,78→1,00); kör ≈0; naive ≈0. Teşhis: ısı dersi iki desene de genelleşiyor (V güvenli −0,09 / tuzak −0,14);
görsel KC kodu çok seyrek ve çok örtüşük (X/Y KC kosinüsü 0,84, eşik üstü KC 3–4; koku A/B 0,44 ve 20 KC) → K-052 (G-V1 seçicilik ölçütü, vis_tuning_density ızgarası).

K-053 (seçilen tasarım, KC kodu ölçütüyle; oyun yok): vis_tuning_density 0,10, vis_kc_gain 8 (m=4: PR 78/72 eşiği 80'i kıl payı kaçırdı, m=8: PR 118/103, cos 0,40).
TAHMİN-3 (koşudan önce, aynı tohum 140, κ yeniden kalibre): naive_plastic NP son 3 blokta ort. ∈ [+0,05, +0,30] ve son blokta temas-yok < 0,90 (çöküş yok); kör kol |NP| < 0,10.
Yanlışlanma: NP < +0,05 ya da temas-yok ≥ 0,95 → "görsel öğrenme bu tasarımda çalışmıyor"; ayar sürüsü yapılmaz, mekanizma yeniden teşhis edilir (E-08).

SONUÇ-3 (O6b, tohum 140, K-053 tasarımı + düzeltilmiş κ=0,6115): TAHMİN-3 YANLIŞ — naive_plastic NP ≈0 (−0,03…+0,01), temas-yok 0,87→0,97; kör kol temas-yok ≈0,68; **öğrenmesiz görsel-açık kol (naive) temas-yok 0,84** (kör 0,68): görsel
girdi, öğrenme olmadan da ilk temas oranını yarıya indiriyor → öğrenme olayı yok (K-054). G-V2 (zorunlu temas) görsel öğrenme kapasitesini sağlam gösterdi (Δ +0,83 vs koku +0,44, boş +0,01). Göz başına valans kontrastı ölçümü: görsel kontrast ±0,02, koku kontrastıyla (±0,02) aynı büyüklükte
ama KC'ye özgü rastgele işaretli (örn. Y sol göz +0,021) → odor yaklaşmasını bozuyor.
K-055 (uygulanan): `vis_innate_flat` — görsel KC'lerin doğuştan KC→MBON ağırlıkları görsel-KC ortalamasına eşitlenir (desene bağlı rastgele yönlendirme kalkar; öğrenme üstüne kurulur; κ yeniden kalibre).
TAHMİN-4 (koşudan önce, tohum 140): (a) naive (öğrenmesiz, görsel açık) temas-yok ≤ 0,75 (kör ≈0,68'e yaklaşır); (b) naive_plastic NP son 3 blokta ort. ∈ [+0,05, +0,30], son blokta temas-yok < 0,90.
Yanlışlanma: (a) temas-yok > 0,80 ise yönlendirme hipotezi yanlış; (b) NP < +0,05 → görsel yol bu hâliyle O6b'yi çözmüyor; ayar sürüsü yapılmaz (E-08).

SONUÇ-4 (K-055, tohum 140, 24 yaşam×2, 8 bölüm, ÖĞRENMESİZ, `vis_innate_flat` açık): temas-yok görsel 0,833 vs kör 0,620 → TAHMİN-4(a) YANLIŞ (≤0,75 beklenmişti); KC'ye özgü doğuştan ağırlık yönlendirmesi nedeni DEĞİL.
`vis_innate_flat` bu yüzden varsayılan kapalı ve fabrika tarafından AÇILMAZ (seçenek olarak kodda kalır). O6b'de görsel açıkken temas oranını neyin yarıya indirdiği AÇIK SORU (K-055).

K-058 tanıları (öğrenmesiz, tohum 140): temas-yok kör 0,67 | görsel X/Y 0,84 | her iki kaynak X 0,68 | her iki kaynak Y 0,74 | görsel ölçeği 0,5: 0,72 (doz-yanıt monoton) → düşüş, iki farklı desenin birlikte bulunmasına bağlı (X–Y doğuştan değer farkı |ΔX−ΔY| ≈0,05–0,09 → yanal kontrast çatışması).
`vis_kc_balance` (her görsel KC için doğuştan yaklaş/kaçın katkısını eşitleme) X–Y farkını 0,05→0,17'ye ÇIKARDI → çözüm değil, varsayılan kapalı (seçenek olarak kodda).
TAHMİN-5 (olay kıtlığı hipotezi; koşudan önce): `--seconds 90` (3× uzun bölüm), 12 canlı×2, 16 bölüm: olay kıtlığı asıl neden ise naive_plastic NP son 2 blokta ∈ [+0,10, +0,40] ve son blokta temas-yok < 0,6;
öğrenme dinamiği asıl neden ise NP ≈0 ve temas-yok ≥0,9'a çöküş sürer. Kör kol NP ≈0.

SONUÇ-5 (TAHMİN-5 YANLIŞ; seconds=90, tohum 141, 12×2, 16 bölüm): naive_plastic NP −0,10/−0,01/−0,01/−0,02, temas-yok 0,73→0,98; kör kol temas-yok 0,25–0,34 (NP ≈0) → olay kıtlığı neden DEĞİL: görsel açıkken yaratık 90 sn'de bile kaynaklara gitmiyor.
Kör kolun temasları rastgele gezinmeden (naive beyin koku A'ya doğuştan hafif kaçıngan/nötr: V(koku) 0,067 < V(yok) 0,091); görsel girdinin desenle işaretli yanal kontrastı (±0,02–0,03, koku kontrastıyla aynı büyüklükte) bu gezinmeyi bozuyor.
K-058 müdahalesi: desenden bağımsız, öğrenilmemiş görsel yaklaşma refleksi `motor.vis_taxis_gain` (göz şiddeti kontrastı yönünde dönüş; sinek nesne çekiciliği; elle yazılmış R-11). Öğrenmesiz naive, tohum 140, 24×2, 4 bölüm: temas-yok 0,844 (refleks 0) → 0,167 (kazanç 2) → 0,0 (5, 10); güvenli/tuzak ≈ eşit (0,41/0,42 @2).
TAHMİN-6 (koşudan önce; tek kazanç = 2, tarama yok): naive_plastic (refleks 2) NP son 2 blokta ort. ≥ +0,20 ve temas-yok < 0,3 (olay bolluğu); kör kol |NP| < 0,10. Yanlışlanma: NP < +0,10 → öğrenme dinamiği/okuma de sorunlu (ayrı teşhis).

SONUÇ-6 (TAHMİN-6 YANLIŞ; refleks 2, tohum 142, 24×2): naive_plastic NP −0,01/+0,01/−0,01/−0,01/+0,01/0,00, temas-yok 0,62→0,97 (blok 1 temas %38: yalnız birkaç olaydan sonra yaratık görselden uzaklaşıyor); kör kol NP ≈0.
Zorunlu-temas ölçümü (tek desen, 8 deneme; K-058): koku +0,30/−0,25 (T=0,6), görsel +0,37/−0,66 (T=0,6) ve +2,54/−3,19 (T=2,5) → görsel yol koku yolundan 1–7× daha sert öğreniyor ve cezaya doğru asimetrik; ortak KC'ler (cos 0,4) yüzünden ceza X'e de yayılıp ortak negatif değer üretiyor,
yanal kontrast (v_l−v_r) bunu görselden KAÇMA olarak okuyor (tek kaynak tek gözde) ve refleks 2'yi yeniyor.
TAHMİN-7 (koşudan önce; tek değer, tarama yok): refleks kazancı 10 (temas bolluğu korunur; öğrenilmiş yanal kontrast ~0,2×60=12 rad/s mertebesinde): naive_plastic NP son 2 blokta ort. ≥ +0,10 ve temas-yok < 0,5. Yanlışlanma: NP < +0,05 → refleks çözüm değil; sorun öğrenmenin sertliği/yayılması (görsel kazanç `vis_kc_gain`, ayrı teşhis).

SONUÇ-7 (TAHMİN-7 YANLIŞ; refleks 10, tohum 143, 24×2): NP −0,04/+0,02/+0,05/−0,01/+0,01/+0,01, temas-yok 0,30→0,89 (temas başta bol, 4-8 bölümde çöküyor) → öğrenilen kaçınma refleks 10'u da yeniyor. Yakın-uzak aktarım ölçümü (12 deneme X+/Y−): Δ 0,86 (0,9) → 0,52 (0,3) → 0,34 (0,15): aktarım kısmi, sıfır değil;
V(X) neredeyse hiç yükselmiyor (+0,17), V(Y) −0,69: öğrenme ağırlıklı olarak CEZA öğrenmesi; ortak KC'ler yoluyla ceza X'e de yayılıp ortak negatif değer → "görselden kaç". (Not: 8 canlılık tanılarda rol dengelemesi yoktu; pilotlar 24 canlıyla dengeli.)
TAHMİN-8 (koşudan önce; T ve refleks birleşik, tek koşu): `--reward-target 2.5 --vis-taxis 10`: T=2,5 zorunlu temasta ödül/ceza oranını 0,56→0,80'e getiriyor (+2,54/−3,19) → ödüllü X güçlü pozitif, ceza yayılımı dengelenir: naive_plastic NP son 2 blokta ≥ +0,10, temas-yok < 0,6. Yanlışlanma: NP < +0,05 → T de çözüm değil.

SONUÇ-8 (TAHMİN-8 YANLIŞ; T=2,5 + refleks 10, tohum 144, 24×2): NP −0,24/−0,04/−0,01/+0,02/−0,01/0,00, temas-yok 0,45→1,00; İLK BLOKTA YANLIŞ İŞARET (tuzak 0,40 > güvenli 0,15) → T=2,5 çözüm değil, durumu kötüleştirdi.
Dürüst durum (K-058): O6b hâlâ ÇÖZÜLMEDİ. Çürütülen hipotezler: iç değer nötrlüğü (κ, K-051), kod darlığı/örtüşme (K-053), KC'ye özgü doğuştan ağırlıklar (K-055), olay kıtlığı (SONUÇ-5), doğuştan görsel yönlendirme bozukluğu tek başına (refleks, SONUÇ-6/7), ödül/ceza asimetrisi tek başına (T, SONUÇ-8).
Açık ipuçları: (i) zorunlu temasta görsel yol koku yolundan 1–7× sert ve cezaya asimetrik; (ii) kapalı çevrimde öğrenme ortak negatif görsel değer üretiyor ve yaratık görselden uzaklaşıyor; (iii) T=2,5 ilk blokta yanlış işaret veriyor (işaret/zamanlama hatası şüphesi: temas anı uygunluk izi vs yaklaşma anı kodu, `play_sequence` öğrenme zamanlaması) — henüz kod düzeyinde denetlenmedi.

TAHMİN-2 (nötrleştirilmiş görsel, aynı tohum 140; koşudan önce): görsel yaratık artık temas edebilir; naive_plastic NP son blokta ∈ [+0,05, +0,30] (belirsizlik geniş: kalan innate fark X≠Y ve VPN→KC zayıflığı);
kör kol |NP| < 0,10. Görsel NP < +0,05 ise "görsel öğrenme bu hâliyle yetersiz" — ayar sürüsü yapılmaz (E-08).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import ARMS, make_game_creature, play

VIS_GAMES = ("O6b", "O6c")


def run_arm(pre, game: str, arm: str, seed: int, agents: int, copies: int, episodes: int, seconds: float, n_vis: int = 6, vis_taxis: float = 0.0, reward_target: float | None = None) -> np.ndarray:
    """(bölüm, eleman) ilk temas yuvası (−1 yok)."""
    ids = list(range(min(agents, pre.world.B)))
    c = make_game_creature(pre, game, arm, ids, copies, seed, vis_feat=n_vis if game in VIS_GAMES else 0, vis_taxis=vis_taxis if game in VIS_GAMES else 0.0, reward_target=reward_target)
    learn = ARMS[arm].eta > 0
    return np.stack([play(c, seconds, learn=learn, test=False)["slot"] for _ in range(episodes)])


def block_table(slot: np.ndarray, block: int) -> list[tuple[float, float, float, float]]:
    """Blok başına (güvenli, tuzak, temas-yok, NP)."""
    out = []
    for s in range(0, slot.shape[0], block):
        b = slot[s:s + block]
        safe, trap, none = float((b == 0).mean()), float((b == 1).mean()), float((b < 0).mean())
        out.append((safe, trap, none, safe - trap))
    return out


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", required=True, choices=["O6a", "O6b", "O6c"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arms", default="naive_plastic,naive_plastic_blind,naive")
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--copies", type=int, default=2)
    ap.add_argument("--episodes", type=int, default=24)
    ap.add_argument("--block", type=int, default=4)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--n-vis", type=int, default=6)
    ap.add_argument("--reward-target", type=float, default=None, help="GELİŞTİRME (K-048/K-058): DAN hedefi T (varsayılan yapılandırma 0,6)")
    ap.add_argument("--vis-taxis", type=float, default=0.0, help="GELİŞTİRME (K-058): görsel yaklaşma refleksi kazancı (rad/s); 0 = kapalı")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.seed >= 200:
        raise SystemExit("geliştirme aracı: doğrulayıcı tohumları (≥200) yasak (R-2)")
    torch.set_num_threads(a.threads)
    pre = checkpoint.load(a.pre)
    t0 = time.time()
    nb = -(-a.episodes // a.block)
    L = [f"# {a.game} geliştirme pilotu (kanıt değildir)", "",
         f"{a.agents} canlı × {a.copies} kopya, {a.episodes} bölüm × {a.seconds:g} sn, oyun tohumu {a.seed}; kollar aynı dünyalarda (CRN).",
         "Hücre: güvenli / tuzak / temas-yok oranı → NP (= güvenli − tuzak). Bloklar bölüm sırasıyla.", "",
         "| kol | " + " | ".join(f"b{i + 1} ({i * a.block + 1}-{min((i + 1) * a.block, a.episodes)})" for i in range(nb)) + " |", "|---|" + "---|" * nb]
    for arm in a.arms.split(","):
        slot = run_arm(pre, a.game, arm, a.seed, a.agents, a.copies, a.episodes, a.seconds, a.n_vis, a.vis_taxis, a.reward_target)
        bl = block_table(slot, a.block)
        L.append(f"| {arm} | " + " | ".join(f"{s:.2f} / {t:.2f} / {n:.2f} → **{np_:+.2f}**" for s, t, n, np_ in bl) + " |")
        print(f"[{time.time() - t0:5.0f}s] {L[-1]}", flush=True)
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
