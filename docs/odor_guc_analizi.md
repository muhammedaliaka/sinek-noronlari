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
  sonuç olduğu gibi raporlanır (başarısızlık dâhil). O3 ve O4 için güç analizi ilgili pilotlardan sonra bu belgeye eklenecektir.
