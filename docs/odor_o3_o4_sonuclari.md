# O3 ve O4 doğrulayıcı sonuçları (ön-kayıtlı, bağımsız tohumlar)

Ön-kayıtlar: `docs/odor_o3_plani.md`, `docs/odor_o4_plani.md` (commit 5397b5d; ölçütler koşudan sonra değişmedi). Ham çıktı: `results/odor_val/<Oyun>_s<tohum>/{summary.md,results.json}` (git'te yok).
Canlılar: iki bağımsız ön-eğitim popülasyonu (tohum 200 ve 201; 24 canlı). **Koşu yolu notu:** konteyner/işçi süreci koşu sırasında dört kez yeniden başladı; kol-kol kontrol noktaları (K-029) sayesinde biten kollar yeniden koşulmadan okundu (hesaplama, tohumlar ve ölçütler aynı). Rapor "kod commit" alanı rapor yazıldığı andaki HEAD'dir.

## Durum

| oyun | popülasyon 200 | popülasyon 201 | hüküm |
|---|---|---|---|
| **O4a** (sönüm), tohum 240/241 | **BAŞARILI** (aşağıda) | **BAŞARILI** | **BAŞARILI** (iki popülasyonda G4 + P1) |
| **O4c** (decoy + kokusuz gerçek hedef), tohum 242/243 | **BAŞARILI** | **BAŞARILI** | **BAŞARILI** (iki popülasyonda G4 + P1 + P2) |
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

## O4c (decoy + kokusuz gerçek hedef)

| | pop. 200 (242) | pop. 201 (243) |
|---|---|---|
| çekim kapısı G4 (frozen − anosmik decoy-ilk, ≥ 0,15) | **+0,272** [%99 GA +0,194; +0,352] ✔ | **+0,250** [+0,135; +0,355] ✔ |
| P1 plastic − frozen decoy-ilk (≤ −0,15) | **−0,315** [−0,398; −0,237], p=0,0001 ✔ | **−0,297** [−0,408; −0,172], p=0,0001 ✔ |
| P2 gerçek-ilk, plastic − anosmik (%98 GA alt sınırı > −0,10) | −0,018 [−0,081; +0,038] ✔ | −0,013 [−0,073; +0,052] ✔ |
| decoy-ilk plastic / frozen / anosmik | 0,195 / 0,510 / 0,238 | 0,191 / 0,488 / 0,238 |
| gerçek-ilk plastic / frozen / anosmik | 0,208 / 0,135 / 0,227 | 0,238 / 0,120 / 0,251 |
| hiçbiri plastic / frozen / anosmik | 0,596 / 0,354 / 0,535 | 0,570 / 0,392 / 0,510 |

**Ne gösterildi:** O4a'daki sönüm, kokusuz gerçek hedefin bulunmasını kör düzeyin altına düşürmeden de oluyor: plastic'in decoy-ilk oranı frozen'a göre ≈0,30–0,32 azalıyor, gerçek-ilk oranı kör düzeyle eşdeğer (fark ≈ −0,015). Frozen canlıda gerçek-ilk oranının düşük olması (0,12–0,135) decoy'un hedeften önce yakalanmasının sonucudur; sönümle bu düzelip kör düzeye dönüyor.
**Sınırlar / betimsel not:** plastic'te "hiçbiri" oranı kör kola göre ≈6 puan yüksek (0,596 vs 0,535; 0,570 vs 0,510): sönümden sonra canlı kör gezgine göre biraz daha az ilk temas yapıyor. Ön-kayıtta ölçüt değildir; P2 yalnız gerçek-ilk oranına bakar. Canlı kokusuz gerçek hedefe *yönelmez* (kör); P2 "bozulmadı" der, "buldu" demez. Sönüm elle yazılmış hata terimiyle (O4a sınırlarındaki gibi). Tek ön-eğitim hattı, iki tohum.

### R-4: "decoy-ilk = gerçek-ilk" sayı eşitliği (pilot gözlemi) — kapatıldı
Pilotta (tohum 106) plastic için üç bölümde iki sayı birebir eşitti (9/9, 8/8, 10/10). Doğrulayıcıda **yinelenmedi**: bölüm 12'de plastic 0,195/0,208 (242) ve 0,191/0,238 (243); bölüm 3 ve 6'da da eşit değil. Aday açıklama olan ayna-çifti yan yanlılığı (`odor_pair_check`) da desteklenmedi: (decoy, gerçek)/(gerçek, decoy) ayna-çifti oranı çiftler karıştırılınca beklenenle aynı (plastic bölüm 3/6/12, iki popülasyon: p = 0,46; 0,54; 0,037; 0,61; 0,68; 0,48; frozen p = 0,64; 0,96; anosmik p = 0,78; 0,12; çoklu karşılaştırma düzeltmesi yapılmadı, tek sınırda p=0,037 var, genel olarak aşırı yan yanlılığı yok). Pilot ön-kaydındaki kural gereği (yinelenmiyorsa rastlantı sayılır) **rastlantı olarak kayıtlı kalır**; kod hatası belirtisi yok.

## Genel hüküm

Dört oyunun ön-kayıtlı doğrulayıcıları iki bağımsız popülasyonda tamamlandı: **O1a, O1b, O2-yakın, O4a, O4c BAŞARILI; O3 eşdeğerlik geçti (olumsuz kontrol); O2-tam betimsel.** Bu "canlı akıllı" demek değildir:
* Koku izini izleme başarısı referansın yaklaşık yarısıdır (frozen ≈0,47–0,54 vs referans ≈0,97–0,98, O1); sınırlayıcı etken değer okumasının Poisson gürültüsüdür (K-028), devre/öğrenme kuralı değil.
* Sönüm (O4) elle yazılmış hata terimine dayanır; hata sinyalini bağlantı verisinden türetme kapısı (3.3) karşılanmadı.
* O3'te canlının konum belleği yoktur (kör düzey); bu bir eksiklik olarak kayıtlıdır, M1 (bellek modülü) ayrı bir kapıdır.

