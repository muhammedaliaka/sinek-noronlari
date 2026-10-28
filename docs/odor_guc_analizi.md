# Dört koku oyunu: güç ve yanlış-pozitif analizi (G4)

**Bu belge ön-kayıttan önce yazılır (R-6).** Benzetim, doğrulayıcıda kullanılacak **gerçek değerlendirici işlevlerle** (`src/sinek/experiments/odor_eval.py`)
koşar; ölçütler gevşetilmez, güç yetmezse tasarım (canlı/deneme sayısı, T) değişir. Komut: `python -m sinek.experiments.power_odor ...` (aşağıdaki parametrelerle).

## Model ve pilottan kalibrasyon

* Her (canlı, deneme) için kollar **ortak tekdüze sayıyı** paylaşır (CRN); `kol ayrışma oranı` kadar deneme kol başına bağımsız yeniden çekilir.
  Canlı başına ortak beceri sapması sd=0,08; canlıya özgü **etki yayılımı** `het`: kolun kör düzeyden sapması (1+h_i) ile çarpılır, h_i ~ N(0, het²).
  Referans karşılaştırıcı canlıdan bağımsızdır.
* **Kalibrasyon** (pilot, T=8 deneme/canlı, 24 canlı): frozen − anosmik farkının canlılar arası standart sapması gözlendi: O1a 0,254 · O1b 0,218 · O2-yakın 0,184 · O2-tam 0,155.
  Model (ayrışma 0,5): het=0,6 ile O1a 0,254'e uyar; O1b için het=0 (0,213); O2'de het=0 bile gözlenenden büyük (0,215 / 0,210). **Yani seçilen (ayrışma 0,5, het 0,6) O1b ve O2 için
  gözlenenden gürültülüdür → muhafazakâr.** Tek pilot tohumu ve 24 canlıyla bir sd'nin standart hatası ≈%15'tir; bu yüzden gözlenenin en kötü ucu alındı.
* Kör düzey pilottan: O1 anosmik 0,24; O2-yakın anosmik 0,42. Referans: O1 0,95; O2-yakın 0,83. Gözlenen etkiler: O1a +0,27, O1b +0,25, O2-yakın +0,32 (≈1,7–2,1 δ).
* 24 canlı × 16 deneme, T=25 sn, δ=0,15, α=0,01. Birincil kural (`odor_eval._superior`): eşli işaret-çevirme p<α **ve** eşli %99 küme-GA alt sınırı>0 **ve** ortalama fark ≥δ.
* **Yorum uyarısı:** gerçek etki tam δ iken "ortalama ≥ δ" kuralı yazı-turadır (güç ≈0,4-0,5, tablodaki satır). Güç hedefi **1,5δ'da ≥0,90**dır; pilotta gözlenen etkiler bunun üstündedir.

## Sonuçlar (500 benzetim/senaryo)

Koşu: O1 — gerçek değerlendirici işlevlerle (`odor_eval`), 500 benzetim/senaryo, 24 canlı × 16 deneme.
Girdi parametreleri (pilottan; yer tutucu olabilir): kör düzey p0=0.24, çekim p=0.7, referans=0.95, canlı sd=0.08, kol ayrışma oranı=0.5, etki yayılımı=0.6; δ=0.15, δ_eq=0.1, α=0.01, referans kapısı ≥0.8.

## O1

| senaryo | hepsi geçti | kapılar tamam | ölçüt başına geçme |
|---|---|---|---|
| sıfır etki | 0.00 | 1.00 | P1_frozen-anosmik 0.00, P2_frozen-random 0.00, P3_ayna_yarilari 0.20 |
| etki δ=0.15 | 0.36 | 1.00 | P1_frozen-anosmik 0.48, P2_frozen-random 0.47, P3_ayna_yarilari 1.00 |
| etki 1,5δ=0.225 | 0.94 | 1.00 | P1_frozen-anosmik 0.97, P2_frozen-random 0.96, P3_ayna_yarilari 1.00 |
| etki 2δ=0.3 | 1.00 | 1.00 | P1_frozen-anosmik 1.00, P2_frozen-random 1.00, P3_ayna_yarilari 1.00 |


Koşu: O2 — gerçek değerlendirici işlevlerle (`odor_eval`), 500 benzetim/senaryo, 24 canlı × 16 deneme.
Girdi parametreleri (pilottan; yer tutucu olabilir): kör düzey p0=0.42, çekim p=0.7, referans=0.83, canlı sd=0.08, kol ayrışma oranı=0.5, etki yayılımı=0.6; δ=0.15, δ_eq=0.1, α=0.01, referans kapısı ≥0.7.

## O2

| senaryo | hepsi geçti | kapılar tamam | ölçüt başına geçme |
|---|---|---|---|
| sıfır etki | 0.00 | 1.00 | P1_yakin_koku-anosmik 0.00 |
| etki δ=0.15 | 0.50 | 1.00 | P1_yakin_koku-anosmik 0.50 |
| etki 1,5δ=0.225 | 0.97 | 1.00 | P1_yakin_koku-anosmik 0.97 |
| etki 2δ=0.3 | 1.00 | 1.00 | P1_yakin_koku-anosmik 1.00 |

## Okuma

| oyun | sıfır etkide hepsi geçti | 1,5δ'da güç | 2δ'da güç | hedef (≥0,90 @1,5δ; sıfırda ≈0) |
|---|---|---|---|---|
| O1 (düz/dönüşlü iz, her biri ayrı) | 0,00 (0/500) | 0,94 | 1,00 | **karşılandı** |
| O2-yakın | 0,00 (0/500) | 0,97 | 1,00 | **karşılandı** |

* Yanlış-pozitif: 500 benzetimde 0 geçiş (%95 üst sınır ≈ %0,6). P3 (ayna yarıları) tek başına sıfır etkide 0,20 geçer, ama birincil P1/P2 sıfırda hiç geçmediği için karar kuralını etkilemez.
* "İki doğrulayıcı tohumda da hepsi" kuralı bağımsız tohumlarda 1,5δ gerçek etkide ≈0,94² ≈ 0,88 (O1) ve 0,97² ≈ 0,94 (O2) başarı olasılığı verir; gözlenen etkide (≈2δ) ≈1,0.
* **Sınırlar:** model pilotun tek tohumundan kalibre; ayrışma oranı ve het doğrudan ölçülmedi (yalnız yayılımla uyduruldu). Gerçek koşuda canlı sayısı aynıdır; doğrulayıcıda gözlenen sd modelden büyük çıkarsa bu belge tekrar yazılmaz,
  sonuç olduğu gibi raporlanır (başarısızlık dâhil). O3 ve O4 için güç analizi aşağıda (pilot G3 sonrası) eklenmiştir.

---

# O3 ve O4 (pilot G3 sonrası eklendi)


Koşu: O3 — gerçek değerlendirici işlevlerle (`odor_eval`), 500 benzetim/senaryo, 24 canlı × 64 deneme.
Girdi parametreleri (pilottan; yer tutucu olabilir): kör düzey p0=0.25, çekim p=0.7, referans=0.9, canlı sd=0.08, kol ayrışma oranı=0.7, etki yayılımı=0.0; δ=0.15, δ_eq=0.1, α=0.01, referans kapısı ≥0.8, çekim kapısı ≥2.0δ.

## O3

| senaryo | hepsi geçti | kapılar tamam | ölçüt başına geçme |
|---|---|---|---|
| sıfır sapma | 1.00 | 1.00 | E3_A~B 1.00, E3_A~C 1.00, E3_A~D 1.00, E3_A~F 1.00, E3_B~C 1.00, E3_B~D 1.00, E3_B~F 1.00, E3_C~D 1.00, E3_C~F 1.00, E3_D~F 1.00 |
| D sapması = δ_eq/2 (0.050) | 0.63 | 1.00 | E3_A~B 1.00, E3_A~C 1.00, E3_A~D 0.84, E3_A~F 1.00, E3_B~C 1.00, E3_B~D 0.85, E3_B~F 1.00, E3_C~D 0.85, E3_C~F 1.00, E3_D~F 0.84 |
| D sapması = δ_eq (0.1) | 0.00 | 1.00 | E3_A~B 1.00, E3_A~C 1.00, E3_A~D 0.01, E3_A~F 1.00, E3_B~C 1.00, E3_B~D 0.01, E3_B~F 1.00, E3_C~D 0.01, E3_C~F 1.00, E3_D~F 0.01 |
| D sapması = 2δ_eq (0.2) | 0.00 | 1.00 | E3_A~B 1.00, E3_A~C 1.00, E3_A~D 0.00, E3_A~F 1.00, E3_B~C 1.00, E3_B~D 0.00, E3_B~F 1.00, E3_C~D 0.00, E3_C~F 1.00, E3_D~F 0.00 |


Koşu: O4a,O4c — gerçek değerlendirici işlevlerle (`odor_eval`), 500 benzetim/senaryo, 24 canlı × 32 deneme.
Girdi parametreleri (pilottan; yer tutucu olabilir): kör düzey p0=0.25, çekim p=0.515, referans=0.9, canlı sd=0.08, kol ayrışma oranı=0.7, etki yayılımı=0.6; δ=0.15, δ_eq=0.1, α=0.01, referans kapısı ≥0.8, çekim kapısı ≥1.0δ.

## O4a

| senaryo | hepsi geçti | kapılar tamam | ölçüt başına geçme |
|---|---|---|---|
| sıfır etki (plastic=frozen) | 0.00 | 1.00 | P1_plastic<frozen 0.00 |
| etki δ=0.15 | 0.45 | 1.00 | P1_plastic<frozen 0.45 |
| etki 1,5δ=0.225 | 0.97 | 1.00 | P1_plastic<frozen 0.97 |
| yarım sönüm (−A/2=0.133) | 0.27 | 1.00 | P1_plastic<frozen 0.27 |
| TAM sönüm (plastic=anosmik düzey, −A=0.265) | 0.99 | 1.00 | P1_plastic<frozen 0.99 |
| çekim yok (G4 başarısız olmalı) | 0.00 | 0.00 | P1_plastic<frozen 0.23 |

## O4c

| senaryo | hepsi geçti | kapılar tamam | ölçüt başına geçme |
|---|---|---|---|
| sıfır etki (plastic=frozen) | 0.00 | 1.00 | P1_decoy_ilk_plastic<frozen 0.00, P2_gercek_ilk_asagi_tarafsiz 0.00 |
| etki δ=0.15, gerçek-ilk kör düzeye çıkar | 0.54 | 1.00 | P1_decoy_ilk_plastic<frozen 0.54, P2_gercek_ilk_asagi_tarafsiz 0.99 |
| etki 1,5δ=0.225, gerçek-ilk kör düzeye çıkar | 0.99 | 1.00 | P1_decoy_ilk_plastic<frozen 1.00, P2_gercek_ilk_asagi_tarafsiz 0.99 |
| TAM sönüm (decoy-ilk=anosmik düzey 0.25), gerçek-ilk kör düzey | 0.99 | 1.00 | P1_decoy_ilk_plastic<frozen 1.00, P2_gercek_ilk_asagi_tarafsiz 0.99 |
| tam sönüm ama gerçek-ilk çöker (0,0) | 0.00 | 1.00 | P1_decoy_ilk_plastic<frozen 1.00, P2_gercek_ilk_asagi_tarafsiz 0.00 |
| çekim yok (G4 başarısız olmalı) | 0.00 | 0.00 | P1_decoy_ilk_plastic<frozen 0.49, P2_gercek_ilk_asagi_tarafsiz 1.00 |


## O3/O4: kalibrasyon ve okuma

* **O3 kol ayrışması (pilot, ölçüldü):** kollar aynı yerleşim/gürültü ile koşar; aynı hücrede (canlı, kopya, deneme) farklı sonuç verme oranı 1. denemede 0,000 (özdeş başlangıç), 2.–4. denemelerde %6–12, son 4 denemede %19–35;
  kol çiftlerinde genel ≈0,09–0,27. Bağımsız kollarda beklenen 2p(1−p)≈0,385 → model parametresi "ayrışma" ≈0,6 genel, ≈0,8 son denemelerde. **Benzetimde 0,7 alındı (muhafazakâr).** Pilotta `eval_o3` pilot verisine uygulandığında 10 kol çiftinin hepsi ±0,10 içinde çıktı (en geniş %98 GA ±0,046) — bu pilottur, kanıt değildir.
* **O3 tasarımı:** 24 canlı × **4 kopya × 16 deneme = canlı başına 64 deneme**. 32 denemede (2 kopya) sıfır sapmada geçme 0,90 (10 çiftin hepsi aynı anda eşdeğer); 64 denemede **1,00**. Marj kadar (0,10) sapmayı eşdeğer sayma ≈0,01/çift (yanlış-eşdeğerlik yok); yarım marj (0,05) sapmayı 0,84/çift (hepsi birlikte 0,63) ayırt eder.
  Yani O3, "kollar arasında ≳0,05-0,10'luk bir fark yok" diyebilir; daha küçük farkları dışlayamaz.
* **O4 çekim ölçümü (geliştirme, frozen − anosmik decoy-ilk):** O4a: +0,253, +0,271 (n=384 deneme/kol/tohum); oturum pilotunda +0,290; O4c: +0,268, +0,260. **Birleşik ≈ +0,265 (≈1,8δ).** Plandaki geçici çekim kapısı "≥2δ=0,30" bu gerçek çekimde yaklaşık %25 olasılıkla geçerdi (yazı-tura ötesi, düşük) — kapı gerçek çekimi tanımadığı için **kapı yeniden tanımlandı (K-025):**
  *çekim kapısı = manipülasyon denetimi: frozen − anosmik decoy-ilk ortalama farkı ≥ δ (0,15), eşli p<0,01 ve %99 küme-GA alt sınırı >0.* Gerekçe: birincil ölçüt zaten plastic'in frozen'ın **en az δ altında** olmasını (anlamlı) ister; bunun fiziksel olarak mümkün olması için çekimin ≥δ olması gerekir; ek 2δ payı güç için gerekli değil (benzetim: çekim=0,265'te tam sönüm gücü 0,99). Kapı düşerse karar "DEĞERLENDİRİLEMEZ".
  Bu karar çekim ölçümü görüldükten SONRA ama ön-kayıt ve doğrulayıcı verisinden ÖNCE verildi; tarihçe karar defterinde (K-025).
* **O4 test örneği:** O4c'de P2 (gerçek-ilk aşağı-tarafsızlık, marj δ_eq=0,10) 16 denemede %82–89 güçle sınırlıydı; canlı başına **32 test denemesi** (2 kopya × 16 tekrar) ile 0,99. O4a/O4c: 12 aldatıcı eğitim bölümü × 2 kopya, ardından öğrenme kapalı 32 test denemesi/canlı/kol.
* **Hedefler:** sıfır etkide hepsi-geçti = 0,00 (0/500, tüm O4 senaryoları); 1,5δ'da güç O4a 0,97, O4c 0,99; "tam sönüm ama gerçek hedef bulma çöker" senaryosunda O4c **0,00** (yanlış-pozitif yok — P2 bunu yakalar).
  "Çekim yok" senaryosunda kapı 0,00 (doğru: değerlendirilemez). Gerçek etki tam δ iken kural yazı-turadır (0,45–0,54).
* **Sınırlar:** O4 modeli (ayrışma 0,7, het 0,6) O1 pilotundan miras; plastic–frozen arasındaki canlıya özgü yayılımı doğrudan ölçmedik. O3/O4 doğrulayıcı sonucu modelden daha gürültülü çıkarsa sonuç olduğu gibi raporlanır.
