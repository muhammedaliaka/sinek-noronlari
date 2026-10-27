# Evre 2 — gerçek mantar cismi bağlantısıyla öğrenme: plan, varsayımlar, önceden yazılmış ölçütler

Bu belge, **doğrulayıcı koşulardan önce** yazılıp commit edilmiştir. Ölçütler koşular başladıktan sonra değiştirilmez;
başarısızlık da raporlanır. Sonuçlar `docs/evre2_sonuclar.md` içinde olacaktır. Veri denetimi: `docs/evre2_veri_denetimi.md`.

## 1. Amaç

Evre 1'de sentetik (rastgele kablolu) mantar cismi (MB) ile koku/ödül öğrenme, silinme, bellek kalıcılığı ve ödül
tersine çevirme gösterilmişti. Evre 2 aynı soruyu **gerçek bağlantı haritasından** (MaleCNS v1.0, sağ yarımküre MB) çıkarılan
alt ağla sorar: PN → KC → MBON ve DAN bölmeleri veriden gelirken aynı protokol ve aynı başarı ölçütleri geçerli mi?

Evre 2 **gerçek bir sineğin davranışını** modellediğini iddia etmez; "gerçek kablolama, basit öğrenme kuralı, sanal ortam" sorusunun cevabıdır.

## 2. Ne veriden, ne varsayımdan geliyor

| Öğe | Kaynak |
|---|---|
| Hangi nöronlar MB alt ağında (PN 123, KC 2045, APL 1, MBON 48, DAN 161) | **veri** (seçim kuralları `connectome/malecns.py`, denetim: `evre2_veri_denetimi.md`) |
| PN→KC, KC→APL, APL→KC, KC→MBON sinaps sayıları | **veri** |
| PN→glomerül ataması (58 kanal); 3 GABAerjik PN'nin işareti | **veri** (nörotransmitter *tahmini*) |
| Bölme eşlemesi: bir MBON hangi DAN'lardan ne kadar sinaps alıyor | **veri** |
| Sinaps sayısı → göreli sinaptik ağırlık (ortalamaya bölme, tek genel ölçek) | **varsayım** |
| MBON "yaklaş / kaçın" sınıfı = DAN bölme payından türetilir (PPL1 → yaklaş, PAM → kaçın) | **varsayım** (Aso & Rubin çerçevesi; nörotransmitterle tam örtüşmez, bkz. denetim §5) |
| Tüm PAM = ödül, tüm PPL1 = ceza / ödül yokluğu sinyali | **varsayım** (gerçekte bazı PAM'ler cezalandırıcı olabilir) |
| Tat/temas → DAN sinyali (delta = temas·(hedef·ödül − V)) | **model** (tat girdisi bağlantıdan alınmadı) |
| LIF parametreleri, hızlar, eşikler, öğrenme hızı | **model** |
| Her MBON'un toplam KC girdisi eşitlenir (`kc_mbon_norm="mbon"`) | **varsayım** (mutlak sinaps gücü bilinmiyor) |
| Hareket kuralı (sabit hız, "değeri yüksek antene dön", gezinme gürültüsü) | **elle yazılmış**; öğrenilen yalnızca değer V |
| Kapsam dışı: KC→KC, MBON→MBON, MBON→DAN, DAN→KC, DPM, sol yarımküre | **çıkarıldı** (sol anten de sağ yarımküre bağlantısını kullanır) |

## 3. Model

Her yarımküre için, `R = canlı·2`; PN spike'ları Poisson (taban 3 Hz + 120 Hz·glomerül aktivasyonu):

- KC: LIF, `v ← a v + Σ_pn spike·w_pn,kc·j − apl_gain·apl·u_kc`, eşik 1; APL `apl ← a apl + Σ_kc spike·v_kc,apl / n_kc`
  (hız birimi; ağırlıklar gerçek sinaps sayılarının ortalamaya bölünmüşü).
- MBON: LIF, tonik sürüş + `j_kc_mb · Σ_kc spike·W_kc,m + gürültü`; W başlangıçta gerçek KC→MBON sayıları (MBON başına toplam eşitlenmiş).
- Değer: `V = (class_balance·r_yaklaş − r_kaçın)/valence_gain`; sınıf ağırlığı `|u_m|`, `u_m = PPL1 payı − PAM payı`.
- Dopamin: `delta = temas·(0.6·ödül − V)`; PAM etkinliği `max(delta,0)`, PPL1 etkinliği `max(−delta,0)` (DAN→MBON sinaps payıyla bölmelere dağıtılır).
- Plastisite (KC izi `e_k` ile, W ∈ [0, W0] içinde kalır):
  `W_km ← W_km·exp(−η dt e_k D_m)` (kendi bölmesinin DAN'ı etkinken baskılanma),
  `W_km ← W_km + (W0_km − W_km)(1 − exp(−η dt e_k R_m))` (karşı sınıf DAN etkinken geri yükleme).
  Sonuç: `delta>0` kaçın sınıfını baskılar ve yaklaş sınıfını geri yükler; `delta<0` tersi.

## 4. Geliştirme geçmişi (dürüst kayıt)

Geliştirme tohumları **0 ve 1**; doğrulayıcı koşular **20 ve 21** (geliştirmede hiç kullanılmadı). Önceden yazılmış ölçütler değişmedi;
aşağıdakiler model/ortam ayarlarıdır ve geliştirme tohumlarında seçilmiştir.

1. **İlk deneme** (Evre 1 dünyası σ=8, doygunluk 4; `valence_gain=40`; yalnız baskılanma; tek aşamalı koku seçimi; tohum 0, 10 canlı/koşul, 6+6 bölüm):
   A-tercihi naif 0.68 → 0.61 → 0.57 → 0.47 (A eğitimi), ölçütlerin 3'ü başarısız. Eğitilmiş ağın doğrudan sondalanması: V(A)=+0.065, V(B)=+0.060
   (frozen: −0.051 / −0.066) — **öğrenme koku-özgül değildi**.
2. **Tanılar:**
   (a) Arenada iki koku birbirine karışıyor: bir A kaynağına temas anında yalnız-A glomerülleri 0.99, yalnız-B glomerülleri 0.76 aktif (fark 0.23),
   yani KC kodu A ve B teması için neredeyse aynı. σ=6 ve doygunluk 2'de fark 0.49.
   (b) Yalnız baskılanma ile öğrenilen A−B farkı eğitimle **eriyor** (σ=6, kazanç 15, tohum 0: ΔV 0.16 → 0.09 → 0.06, bölüm 2/4/6);
   iki yönlü sınırlı kuralla erimedi (0.14 → 0.24 → 0.24 → 0.22).
   (c) Koku çifti seçimi "kazananın laneti"ne uğradı: seçilen çiftin ilk-geçiş skoru 0.018 iken ikinci, daha çok tekrarlı ölçümde 0.091 çıktı.
   (d) Sınıf boyutları ve bağlantı yoğunluğu farklı olduğundan eğitimsiz ağ tüm kokulara hafif negatif değer veriyor (V ≈ −0.23, `valence_gain=10` ile).
3. **Yapılan değişiklikler:** dünya σ=6, doygunluk 2; iki yönlü sınırlı plastisite; `valence_gain=10`; **dönüş kazancı 40**
   (aynı eğitilmiş 16 canlıda 10/20/40 → A-tercihi 0.70/0.78/0.90 — *örneklem içi* seçim); `class_balance` eğitimsiz ağdan ölçülür;
   koku çifti iki aşamalı seçilir; eğitim 12 + 12 bölüme çıkarıldı (ΔV 8. bölümde hâlâ yükseliyordu).
4. **Son geliştirme ölçümü** (nihai varsayılanlar, 16 canlı, yalnız plastic, 8 bölüm, 6 deneme/canlı): tohum 0: ΔV(yakın) 0.21, A-tercihi 0.68;
   tohum 1: ΔV 0.15, A-tercihi 0.81. Eğitimsiz tercih 0.32 ve 0.43 (seçim oranı 0.19 / 0.15: az seçim, gürültülü).

## 5. Doğrulayıcı koşular

Üç koşul aynı batch'te (Evre 1 ile aynı): `plastic` (öğrenen), `frozen` (aynı deneyim, öğrenme kapalı), `random` (dönüş kazancı 0).
Protokol: naif test → A için 12 bölüm (A ödüllü) → bellek kalıcılığı (kaydet/yeniden yükle) → ödül tersine çevirme 12 bölüm (B ödüllü);
her 3 bölümde seçim testi (ilk temas = seçim; kaynaklar tüketilmez; öğrenme kapalı).

```
python -m sinek.experiments.evre2 --agents 16 --episodes 12 --reversal-episodes 12 --test-every 3 --trials 4 --seed 20 --out results/evre2_s20
python -m sinek.experiments.evre2 --agents 16 --episodes 12 --reversal-episodes 12 --test-every 3 --trials 4 --seed 21 --out results/evre2_s21
```

Her koşu kendi koku çiftini aday aralığı `5000 + 100·tohum` içinden **yalnızca eğitimsiz ağın iç eğilimine göre** seçer (öğrenme/davranış sonucu kullanılmaz).
Sınıf dengesi de eğitimsiz ağdan ölçülür. Tüm kalibrasyon değerleri `results.json` içine yazılır.

Not: "canlı"lar **aynı bağlantının** gürültü / yol / başlangıç tekrarlarıdır (tek erkek sinek haritası). Bu nedenle sonuçlar "bu bağlantı ve bu model"
için geçerlidir; sinekler arası değişkenliği temsil etmez.

## 6. Başarı ölçütleri (koşu başına; hepsi iki doğrulayıcı koşuda da sağlanmalı)

Evre 1 ile birebir aynı tanımlar (`experiments/evre1.py: evaluate`):

- **A1** eğitilmiş `plastic` A-tercihi %95 bootstrap GA alt sınırı > 0.5
- **A2** `plastic` > `frozen` ve > `random` (permütasyon p < 0.01, ortalamalar da sıralı)
- **A3** eğitimsiz `plastic` tercihinin GA'sı 0.5'i kapsar (kalibrasyonun ve bağlantının içsel yan etkisi yok)
- **C** kaydedilip yeniden yüklenen canlı birebir aynı ağırlıklara ve aynı test sonuçlarına sahip
- **B1** ödül tersine çevrildikten sonra `plastic` A-tercihi anlamlı düşer (p < 0.01)
- **B2** tersine çevirme sonrası A-tercihi GA üst sınırı < 0.5 (B artık tercih ediliyor)

**Yapısal kontrol E1 (yalnız tohum 20 kurulumuyla, aynı koku çifti `--pattern-seed`):** MBON yaklaş/kaçın sınıf etiketleri MBON'lar arasında
karıştırılır (`--set cbrain.class_shuffle_seed=1`, ikinci bir koşuda `=2`); bağlantı ve bölme eşlemesi aynı kalır.
Ölçüt: A eğitimi sonunda `plastic` A-tercihi gerçek-etiketli koşudan **düşüktür** (tek yönlü permütasyon p < 0.01). Bu, gerçek bölme/sınıf yapısının
modelde işe yaradığının kontrolüdür. Sonuç ne olursa raporlanır; "etiketlerin önemi yok" çıkarsa bu da bir bulgudur.

**Betimsel ablasyon (ölçütsüz):** yalnız baskılanma (`--set cbrain.restore=false`) — geliştirmede gözlenen erimenin tam protokolde de görülüp görülmediği.

## 7. Bilinen sınırlamalar

- Tek bağlantı haritası (tek erkek sinek, tek yarımküre); iki anten aynı yarımküre kablolamasını kullanır.
- Sinaps sayısı → ağırlık dönüşümü ve MBON sınıf türetimi varsayımdır; sonuçlar bunlara bağlıdır (E1 yalnızca sınıf türetimini sınar).
- Nörotransmitter değerleri sınıflandırıcı tahminidir; DPM yanlış tahmin edildiği için kullanılmadı.
- KC→KC, MBON→MBON, MBON→DAN geri beslemeleri modelde yok; bu yüzden gerçek sineğin ödül-tahmin hatası devresi tam temsil edilmiyor (delta modelde yazılı).
- Dönüş kazancı geliştirme tohumunda örneklem içi seçildi; hareket kuralı elle yazılmıştır.
- Sanal ortam 2B ve basittir; CUDA yolu bu ortamda sınanmadı (yalnız CPU).
