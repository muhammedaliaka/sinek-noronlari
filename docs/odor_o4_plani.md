# O4 — yanıltıcı koku (sönüm): ÖN-KAYIT (doğrulayıcı koşulardan önce)

Bağlayıcı üst belge: `docs/dort_koku_oyunu_plani.md` (§3.4, §5, Z-10/Z-11). Güç ve çekim kapısı gerekçesi: `docs/odor_guc_analizi.md` (O3/O4 bölümü), K-025. Ortak kurallar `docs/odor_o1_plani.md` §2 ve §8.
**Commit edilmeden doğrulayıcı koşu (tohum ≥200) başlamaz.** Kapsam: **O4a** (decoy, gerçek hedef yok) ve **O4c** (decoy + kokusuz gerçek hedef). O4b, kimlik değişimi ve transfer ertelendi.

## 1. Soru ve dürüst cümleler

* **O4a:** *Ön-eğitimde ödüllü olan kokunun kaynağı artık ödül vermiyorsa (sönüm), öğrenme açık canlı o kaynağa gidişi, öğrenmesi kapalı kopyasına göre azaltır mı?*
  Evet ise: **"Bu canlı koku-ödül ilişkisini ödülsüz tüketimle söndürüyor (öğrenmenin sonucu davranış değişiyor)."** Hayır ise: **"Bu tasarımda sönüm görülmedi."**
* **O4c:** O4a'ya ek olarak *gerçek ödül kokusuz bir hedefte*: canlı decoy'dan kaçarken **gerçek hedefi bulmayı da kaybetmiyor** mu? Sağlanırsa: **"Sönüm decoy'a özgü; gerçek hedefi arama bozulmuyor (aşağı-tarafsız)."** Canlı gerçek hedefi *aktif bulmaya yönelmez* (kokusuz, kör); beklenen gerçek-ilk oranı kör düzeydir.
Zeka/planlama iddiası yoktur.

## 2. Tasarım (donduruldu)
* **Alan:** decoy = canlının ödüllü kokusu, Gauss σ=8, ödül 0; T=25 sn; O4c'de gerçek hedef kokusuz (`src_odor=−1`), ödül 1.
* **Kollar (CRN eşli):** `plastic` (aldatıcı eğitim görür: **12 bölüm × 2 kopya**, decoy tüketilir, öğrenme açık), `frozen` ve `anosmic` (öğrenmeyen; ağırlıkları eğitimle değişmez, bu yüzden eğitim bölümü koşturulmaz — başlangıç ağırlıklarıyla test edilir). Anosmik kol `glom ≡ 0`.
* **Test:** eğitim sonunda **öğrenmesi kapalı**, ayrı tohumlu (`oyun tohumu + 5012`), tüm kollar için **aynı yerleşimler**; her eğitim elemanı **16 kez** kopyalanır → canlı başına **32 test denemesi**/kol. Ölçü: ilk temas decoy mu / gerçek hedef mi / hiçbiri.
* **Popülasyonlar ve tohumlar:** ön-eğitim 200 ve 201; oyun tohumları O4a **240** (pop. 200), **241** (pop. 201); O4c **242**, **243**. Betimsel: plastic 3. ve 6. bölümde de test edilir (eğilim).
* **Komut:** `python3 -I -m sinek.experiments.odor_validate_s --pre results/odor_val/pre_s{200|201}.npz --game {O4a|O4c} --seed {tohum} --test-reps 16 --attract-mult 1.0 --out results/odor_val/{oyun}_s{tohum}`

## 3. Kapı (manipülasyon denetimi, K-025)
* **G4 çekim:** frozen − anosmik decoy-ilk oranı: eşli işaret-çevirme p<0,01, %99 küme-GA alt sınırı >0 ve ortalama fark ≥ δ (0,15). Sağlanmazsa karar "DEĞERLENDİRİLEMEZ" (sönüm ölçülecek çekim yok).
  Geliştirmede çekim ≈+0,265 (O4a +0,253/+0,271; O4c +0,268/+0,260). **Eşik tarihçesi:** plandaki geçici ≥2δ, bu çekimi ≈%25 olasılıkla geçeceğinden, pilot çekim görüldükten sonra ve doğrulayıcı verisinden önce ≥δ'ya çekildi; gerekçe K-025'te.

## 4. Birincil ölçütler (her popülasyonda)
* **O4a P1:** plastic − frozen decoy-ilk: ortalama fark ≤ −δ (−0,15), eşli işaret-çevirme (azalma yönünde) p<0,01 ve %99 küme-GA üst sınırı <0.
* **O4c P1:** aynı kural decoy-ilk oranı üzerinde. **O4c P2 (aşağı-tarafsızlık):** plastic gerçek-ilk oranı − anosmik (kör) gerçek-ilk oranı için %98 küme-GA alt sınırı > −0,10.
* **Karar:** "O4a başarılı" = iki popülasyonda G4 ve P1. "O4c başarılı" = iki popülasyonda G4, P1 ve P2. Aksi: "başarısız" ya da (kapı düştüyse) "değerlendirilemez".

## 5. Güç (`odor_guc_analizi.md`)
Sıfır etkide hepsi geçti 0/500; 1,5δ gerçek etkide O4a 0,97, O4c 0,99; tam sönümde 0,99; "sönüm var ama gerçek hedefi bulma çöküyor" senaryosunda O4c 0,00 (P2 yakalar). Gerçek etki tam δ iken kural yazı-turadır (≈0,5). Geliştirme pilotunda plastic decoy-ilk oranı 0,56'dan 0,17-0,21'e indi (frozen 0,50): beklenen etki ≈2δ'nın üstünde, ama bu pilottur.

## 6. Sınırlar (peşin)
Sönüm **hızlı** öğrenme ve unutma sorusunu çözmez: yalnız 12 bölümlük sonuç sınanır, bölüm eğilimi betimseldir. "Kimlik değişimi" (kokunun ödül eşleşmesi tersine döndü) ve transfer ertelendi. Hedef kokusuz olduğu için O4c'de canlı gerçek hedefe *yönelemez*; P2 yalnız "bozulmadı" der. Hareket kuralı ve ödül/dopamin hatası elle yazılmıştır (`dort_koku_oyunu_plani.md` §6). Tek ön-eğitim hattı, iki tohum.
