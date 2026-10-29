# O3 ve O4 doğrulayıcı sonuçları (ön-kayıtlı, bağımsız tohumlar)

Ön-kayıtlar: `docs/odor_o3_plani.md`, `docs/odor_o4_plani.md` (commit 5397b5d; ölçütler koşudan sonra değişmedi). Ham çıktı: `results/odor_val/<Oyun>_s<tohum>/{summary.md,results.json}` (git'te yok).
Canlılar: iki bağımsız ön-eğitim popülasyonu (tohum 200 ve 201; 24 canlı). **Koşu yolu notu:** konteyner/işçi süreci koşu sırasında dört kez yeniden başladı; kol-kol kontrol noktaları (K-029) sayesinde biten kollar yeniden koşulmadan okundu (hesaplama, tohumlar ve ölçütler aynı). Rapor "kod commit" alanı rapor yazıldığı andaki HEAD'dir.

## Durum

| oyun | popülasyon 200 | popülasyon 201 | hüküm |
|---|---|---|---|
| **O4a** (sönüm), tohum 240/241 | **BAŞARILI** (aşağıda) | **BAŞARILI** | **BAŞARILI** (iki popülasyonda G4 + P1) |
| O4c (decoy + kokusuz gerçek hedef), tohum 242/243 | koşuyor | koşuyor | bekleniyor |
| **O3** (yalnız temas, eşdeğerlik), tohum 230/231 | **GEÇTİ** (G3 + 10/10 E3) | **GEÇTİ** (G3 + 10/10 E3) | **EŞDEĞERLİK GEÇTİ** (olumsuz kontrol; zeka iddiası yok) |

## O4a

| | pop. 200 (240) | pop. 201 (241) |
|---|---|---|
| çekim kapısı G4 (frozen − anosmik decoy-ilk, ≥ δ=0,15) | **+0,311** [%99 GA +0,217; +0,397] ✔ | **+0,281** [+0,173; +0,387] ✔ |
| P1 plastic − frozen decoy-ilk (≤ −0,15; p<0,01; GA üst sınırı <0) | **−0,348** [−0,427; −0,259], p=0,0001 ✔ | **−0,322** [−0,439; −0,197], p=0,0001 ✔ |
| decoy-ilk oranı: plastic / frozen / anosmik (bölüm 12) | 0,212 / 0,560 / 0,249 | 0,191 / 0,513 / 0,232 |
| plastic eğilim (bölüm 3 → 6 → 12) | 0,289 → 0,190 → 0,212 | 0,214 → 0,168 → 0,191 |

**Ne gösterildi:** Öğrenme açıkken decoy'un ödülsüz tüketilmesi, canlının decoy'a gidişini öğrenme kapalı kopyasına göre ≈0,32–0,35 azaltıyor ve oran kör (anosmik) düzeye iniyor. Etki ön-kayıt eşiğinin (0,15) iki katından fazla. Sönüm 3 bölümde büyük ölçüde oluşuyor.
**Ne gösterilmedi / sınırlar:**
* Plastic decoy-ilk oranı kör düzeyin (anosmik 0,249/0,232) hafifçe **altına** iniyor (0,212/0,191): bu "tam sönüm"den fazlası olabilir (decoy kokusundan kaçınma ya da kısmi tüketim sonrası koku yönelimi azalması); ön-kayıtta bu fark ölçüt değildir ve ayrı yorumlanmadı.
* Sönüm kuralı elle yazılmış hata terimine dayanıyor (`δ = kapı·(hedef·ödül − valence)`; K-026): ödülsüz tüketimde δ negatif olur ve ağırlıklar bastırılır. Yani sonuç "öğrenme kuralı sönümü üretiyor" der, "veriden gelen hata devresi sönümü üretiyor" **demez** (kapı 3.3 karşılanmadı, `docs/evre3_dan_plani.md` §5).
* Hızlı öğrenme/unutma (tek denemede sönüm) sorusu bu oyunda ölçülmedi; 12 bölümlük sonuç sınandı. Kimlik değişimi ve transfer ertelendi (ön-kayıt §6).
* Tek ön-eğitim hattı, iki tohum.

## O3 (olumsuz kontrol: koku alanı yok, hedef yalnız temasta algılanır)

| kol (p_hit) | pop. 200 (230) | pop. 201 (231) |
|---|---|---|
| plastic A (ödül+koku) | 0,219 | 0,254 |
| plastic B (ödül, koku yok) | 0,225 | 0,256 |
| plastic C (ödülsüz, koku var) | 0,247 | 0,248 |
| plastic D (ikisi de yok) | 0,255 | 0,266 |
| frozen A (öğrenme kapalı) | 0,243 | 0,266 |

* **G3:** koşu boyunca alan görülen deneme 0 / 0 (ön-temas `glom ≡ 0`) ✔ iki popülasyonda.
* **E3:** 10 kol çiftinin hepsinde eşli fark %98 küme-GA'sı (−0,10; +0,10) içinde ✔ iki popülasyonda. En uç GA: pop. 200'de plastic:A~plastic:D −0,036 [−0,062; −0,008] (sıfırı dışlar ama marjın içinde), frozen:A~plastic:A +0,025 [+0,003; +0,045]; pop. 201'de en uç −0,042.
* **Dürüst cümle (ön-kayıt §1):** Koku alanı olmadan bu canlı **kör arama düzeyinde (≈0,22–0,27) kalıyor**; ödül öğrenmesi konum belleği vermiyor ve oyun dünyasında ön-temas bilgi sızıntısı yok (|Δp| < 0,10). Bu bir **başarı değil, olumsuz kontroldür**: canlının "yeri hatırlama" gibi bir yeteneği yok ve sınanan şey bunu bulmak değildi.
* **Sınırlar:** 0,05'ten küçük farklar dışlanamaz (güç analizi); O3'te sıfır dışlayan iki küçük fark (≈0,03) raporlanmıştır, yorumlanmamıştır. Konum belleği/sistematik keşif istenirse ayrı devre kapısıdır (M1).
