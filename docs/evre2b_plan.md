# Evre 2b — ölçüt gücü artırılmış doğrulama: plan, yöntem denetimi, önceden yazılmış ölçütler

> **DURUM: TASLAK.** Bu sürüm, geliştirme provası sonuçlarını görmeden önce yazıldı ve commit edildi; böylece §4.4'teki seçim kuralı
> sonuçlardan önce sabitlenmiş olur. Prova bitince yalnızca "{{...}}" ile işaretli yerler ve §4.5 doldurulacak, belge **yeniden commit edilerek
> kesinleşecek**; **doğrulayıcı koşular (tohum 30 ve 31) kesinleşmiş sürüm commit edilmeden başlamayacak.**
> Kesinleşmeden sonra ölçütler değiştirilmez; başarısızlık da raporlanır.

## 1. Neden Evre 2b?

Evre 2 (v1, `evre2_plan.md`, `evre2_sonuclar.md`) iki doğrulayıcı koşuda **5/6 ve 4/6** ölçüt geçti; ön-kayıtlı hüküm "Evre 2 ölçütü başarısız"dır ve bu hüküm
değişmez. Öğrenmenin kendisi büyüktü (eğitilmiş A-tercihi 0,92 ve 0,90; tersine çevirmede 0,27 ve 0,14), ama iki ölçüt **ölçüm gücü** yüzünden kaldı:
eğitimsiz ağ kaynaklara nadiren ulaşıyordu (seçim oranı 0,15–0,19; dönüş kazancı 0 olan rastgele politika 0,69), dolayısıyla `frozen` karşılaştırması ve naif tercih
birkaç gözleme dayanıyordu. Evre 2b, **aynı soruyu** (gerçek mantar cismi alt ağıyla koku/ödül öğrenme, silinmeme, bellek, tersine çevirme) daha güçlü bir
ölçümle yeniden sorar. Evre 2 sonuçlarına dokunmaz; yeni tohumlar (30, 31) ve yeni ön-kayıt kullanır.

## 2. Teşhis (yalnız geliştirme tohumlarında)

* Hareket kuralı `turn = turn_gain · (V_sol − V_sağ) / (|V_sol| + |V_sağ| + ε) + gezinme gürültüsü` idi, ε = 0,05.
  Eğitimsiz ağda sol/sağ değerin farkındaki gürültü sd(V_sol − V_sağ) ≈ 0,145, yani ε'dan çok büyüktür. Bu durumda oran işaret fonksiyonuna benzer, gürültüyü
  **büyütür**: eğitimsiz canlı kendi etrafında dönüp durur ve kaynağa varamaz (seçim oranı 0,17–0,20; dönüş kazancı 0 olan rastgele politika 0,69).
* Zamansal yumuşatma (düşük geçiren filtre) denendi ve **atıldı**: yönelim difüzyonu sıfır-frekans gürültü gücüne bağlıdır, yumuşatma bunu azaltmaz (kuram ve ızgara aramayla doğrulandı).
* Çözüm: ε'u büyütüp okumayı **yaklaşık doğrusal** yapmak (`contrast_eps = 2,0`). Böylece gürültü büyütülmez, öğrenilen ortalama fark ise korunur.
* Eğitimsiz ağ koku 0/1'e farklı değer verebilir (koku-kimliği yanlılığı). v1'de A rolü hep koku 0 idi: bu yanlılık A-tercihine karışıyordu.

## 3. Evre 2b'de ne değişti (özet tablo)

| Öğe | Evre 2 (v1) | Evre 2b |
|---|---|---|
| Hareket okuması | ε = 0,05, kazanç 40 | **ε = 2,0**, kazanç {{GAIN}} (§4.4 kuralıyla seçildi) |
| Rol atama | A hep koku 0 | **rol dengelemesi**: her koşulun ikinci yarısında A = koku 1; sonuçlar rol cinsinden |
| Canlı / deneme | 16 / 4 | **24 / 16** |
| Test aşamaları | her 3 bölüm | naif, A6, A12, B18, B24 (her 6 bölümde) |
| İstatistik | canlı ortalaması + bootstrap | **seçim sayısı ağırlıklı, canlı-düzeyi (küme) bootstrap ve permütasyon** (`stats.py`) |
| Geçerlilik kapısı | yok | **G**: eğitimsiz ve eğitilmiş seçim oranı ≥ 0,40; değilse A2/A3 "değerlendirilemez" = FAIL |
| Naif karşılaştırma | yalnız `plastic` | `plastic` + `frozen` havuzlanır (aynı ağ, aynı koku çifti) |
| A3 | GA 0,5'i kapsar | **eşdeğerlik**: GA ⊂ [0,30; 0,70] |
| E1 | aynı koku çifti, gerçek için seçilmiş | karıştırılmış ağ için **koku çifti yeniden kalibre edilir**; seçim oranı < 0,40 ise geçmez |
| Tohumlar | 20, 21 | **30, 31** (geliştirme: 0, 1, 2, 3) |

## 4. Geliştirme geçmişi (dürüst kayıt)

### 4.1 Tohum kullanımı
Geliştirme: 0, 1 (Evre 2 v1), 2, 3 (Evre 2b). Görülmüş doğrulayıcı tohumlar: 20, 21. **Bu belgenin doğrulayıcı tohumları 30 ve 31'e geliştirmede hiç dokunulmadı.**

### 4.2 Pilotlar (tohum 2, koku çifti 5232, 12 canlı/koşul, 8 deneme, 12 + 3 bölüm; ε = 2,0; kazanç 40/60/80)

Havuzlanmış rol-A oranı (seçim oranı), nihai değerlendirici (`evaluate2`) ile yeniden hesaplanmış:

| kazanç | naif (plastic+frozen) | A6 | A12 | B (3 bölüm sonra) | hükümler |
|---|---|---|---|---|---|
| 40 | 0,41 [0,34; 0,49] (0,67) | 0,72 (0,83) | 0,56 [0,47; 0,67] | 0,42 | A1, A2, B1 kaldı |
| 60 | 0,45 [0,37; 0,55] (0,69) | 0,76 (0,89) | 0,70 [0,60; 0,79] | 0,38 | yalnız A2 kaldı (p(frozen) = 0,0051, p(random) = 0,0474) |
| 80 | 0,56 [0,46; 0,65] (0,60) | 0,77 (0,92) | 0,70 [0,63; 0,78] | 0,39 | yalnız A2 kaldı (p(frozen) = 0,0405, p(random) = 0,0175) |

Gözlemler: (i) ε = 2,0 ile eğitimsiz seçim oranı 0,17'den 0,6–0,7'ye çıktı (G rahatça sağlanıyor). (ii) Eğitilmiş tercih v1'deki 0,90'a ulaşmıyor (0,70–0,77): doğrusal okuma
daha az "keskin" dönüş yapıyor; bu, güvenilir ölçümün bedeli. (iii) Eğitilmiş tercih A6'dan A12'ye hafifçe düştü (0,72–0,77 → 0,56–0,70); nedeni **bilinmiyor**
(sinaptik silinme/girişim ya da gürültü olabilir; 12 canlıyla ayırt edilemedi). Bu yüzden ana ölçüt A12'yi (A fazının sonu) kullanır, A6 betimseldir. (iv) 12 canlıda A2 sınırda kaldı: güç yetersiz.

### 4.3 Atılan / düzeltilen şeyler
* **`tau_smooth` (zamansal yumuşatma)**: kuramla ve ızgara aramayla işe yaramadığı gösterildi; koddan çıkarıldı.
* **A3'ün iki biçimi**: v1'in "GA 0,5'i kapsar" biçimi sıfır yanlılıkta bile ~%4–5 kendiliğinden başarısız olur ve veri arttıkça önemsiz yanlılıkta başarısızlığa yaklaşır.
  İlk düzeltmem (eşdeğerlik ±0,15) canlılar arası değişkenlikte çok dardı (güç analizinde güçlü etkide bile geçme oranı 0,91, κ = 2'de 0,71). Nihai marj ±0,20
  (= ilgilendiğimiz en küçük etki). Bu, yöntem denetimi bulgusudur; pilot verisiyle ayarlanmadı.
* **`--set` bool ayrıştırma hatası** (v1 sırasında bulundu, düzeltildi, belgelendi): `evre2_sonuclar.md`.

### 4.4 Kazanç seçim kuralı (provadan ÖNCE yazıldı)
Kazanç ∈ {60, 80} için geliştirme provası (tohum 3, koku çifti kalibrasyonla seçilir, 24 canlı, 8 deneme, 12 + 12 bölüm) koşulur.
1. Eğitimsiz `plastic`+`frozen` seçim oranı < 0,50 olan kazanç elenir (G eşiği 0,40'a yeterli pay bırakmak için).
2. Kalanlardan, `plastic`'in A6 ve A12 aşamalarındaki havuzlanmış A-oranlarının ortalaması **yüksek** olan seçilir.
3. Fark < 0,02 ise (gürültü içinde) eğitimsiz seçim oranı yüksek olan seçilir. İkisi de elenirse 60 kullanılır.
Prova yalnızca bu kararı ve hattı sınamak içindir; ölçüt değil.

### 4.5 Prova sonucu
{{PROVA}}

## 5. Yöntem denetimi (bu planın kurulduğu sırada yapıldı)

| # | Bulgu | Karar |
|---|---|---|
| 1 | A3 (v1 biçimi) kendiliğinden başarısız oluyor | eşdeğerlik ±0,20 (§4.3) |
| 2 | Naif karşılaştırma yalnız `plastic`'ti (az gözlem) | `plastic`+`frozen` havuzlanır (aynı ağ; öğrenme eğitimden önce yok) |
| 3 | Aynı canlının denemeleri bağımsız sayılmıştı | canlı = küme birimi (bootstrap ve permütasyon); testlerle tip-I hata ve kapsama sınandı (`tests/test_stats.py`) |
| 4 | A rolü hep koku 0: koku yanlılığı tercihe karışıyordu | rol dengelemesi (`--swap-roles`); koku-0 yanlılığı betimsel raporlanır |
| 5 | Çok az seçim yapan ağda A2/A3 "geçebilir" ya da kendiliğinden başarısız olabilir | G kapısı: değerlendirilemezse FAIL |
| 6 | B1 aynı canlıların önce/sonrasını eşleşmemiş karşılaştırıyor | **kasıtlı**: eşleşmemiş permütasyon daha muhafazakâr (aynı canlıların bağımlılığını yok sayar); B2 zaten mutlak ölçüt |
| 7 | Konteyner yeniden başlayabilir, koşu ölür | koşular deterministik (2 ve 4 iş parçacığı birebir aynı sonuç, aynı makine); yeniden koşulunca aynı sonuç |
| 8 | Tek sayıda canlı rol dengelemesini bozar | `--agents` çift değilse hata (`_swap_mask`) |
| 9 | E1 (v1) karıştırılmış ağları gerçek için seçilmiş koku çiftiyle sınadı | karıştırılmış ağ için koku çifti yeniden kalibre edilir (§6) |
| 10 | Karar kuralı yanlış pozitif verir mi? | güç analizi: öğrenme yokken tüm ölçütleri geçme oranı **0,00** (1000 benzetim) |

## 6. Güç analizi (`python -m sinek.experiments.power2b`, gerçek karar kodu `evaluate2` ile; 1000 benzetim)

Model: canlıya özgü tercih ~ Beta (κ = canlılar arası değişkenlik), canlı başına binom denemeler, rol dengelemesi ve koku-0 yanlılığı (0,10) dahil.
Parametreler pilot gözlemlerinden gelir, ölçülmüş "doğru" değerler değildir. Pilotlarda canlılar arası aşırı yayılım gözlenmedi (gözlenen/iki terimli varyans oranı 0,4–1,5, ortalama ≈ 0,8), bu yüzden
pilot-benzeri senaryolarda κ çok büyük alındı.

{{GUC_TABLOLARI}}

## 7. Doğrulayıcı koşular

```
python -m sinek.experiments.evre2b --seed 30 --threads 4 --out results/evre2b_s30
python -m sinek.experiments.evre2b --seed 31 --threads 4 --out results/evre2b_s31
```
Varsayılanlar kodda dondurulmuştur (`evre2.main(v2=True)`: 24 canlı, 12 + 12 bölüm, test_every 6, {{TRIALS}} deneme, rol dengelemesi; `evre2.V2_SET`: hareket okuması).
Koku çifti her tohumda **yalnızca eğitimsiz ağın iç eğilimine** göre seçilir (öğrenme/davranış sonucu kullanılmaz).

**E1 yapısal kontrolü (yalnız tohum 30 kurulumu):** MBON yaklaş/kaçın etiketleri karıştırılır (`--set cbrain.class_shuffle_seed=1`, ikinci koşuda `=2`); bağlantı ve bölme eşlemesi aynı kalır;
**koku çifti karıştırılmış ağ için yeniden kalibre edilir** (`--pattern-seed` verilmez). Değerlendirme: `python -m sinek.experiments.evre2b_e1`.
E1, ana karar kuralının parçası **değildir**; ama FAIL (ya da değerlendirilemez) ise "gerçek sınıf yapısı işe yarıyor" iddiası kurulmaz.

## 8. Başarı ölçütleri (koşu başına; hepsi iki doğrulayıcı koşuda da sağlanmalı)

Tüm istatistikler `stats.py`: birim = canlı; havuzlanmış oran = Σ A / Σ (A+B); GA = canlılar yerine koyarak %95 yüzdelik bootstrap (n = 10 000); permütasyon n = 20 000; tohum 0.
Karşılaştırmalar **A12** (A fazının son testi) ve **B24** (tersine çevirmenin son testi) aşamalarındadır.

* **G** geçerlilik: eğitimsiz (`plastic`+`frozen`) seçim oranı ≥ 0,40 **ve** A12'de `plastic` seçim oranı ≥ 0,40 (seçim oranı = seçim sayısı / (canlı × deneme)).
* **A1** A12'de `plastic` havuzlanmış A-oranı GA alt sınırı > 0,5.
* **A2** `plastic` > `frozen` ve `plastic` > `random` (A12; tek yönlü küme permütasyonu, her biri p < 0,01; oranlar da sıralı; G gerekli).
* **A3** eğitimsiz (`plastic`+`frozen`, havuzlanmış) rol-A oranı GA'sı [0,30; 0,70] içinde (G gerekli).
* **C** kaydedilip yeniden yüklenen canlı birebir aynı ağırlıklara ve aynı test sonuçlarına sahip.
* **B1** `plastic` A-tercihi A12 → B24'te düştü (tek yönlü küme permütasyonu, p < 0,01).
* **B2** B24'te `plastic` A-oranı GA üst sınırı < 0,5.

**Karar kuralı:** G, A1, A2, A3, C, B1, B2'nin **hepsi iki koşuda da** geçerse "Evre 2b ölçütü başarılı"; aksi hâlde "başarısız" (hangi ölçütlerin kaldığı raporlanır). Çoklu karşılaştırma için ek düzeltme yoktur:
ölçütlerin hepsinin geçmesi gerektiği için (kesişim) yanlış pozitif oranı tek ölçütünkinden küçüktür.
Betimsel (ölçütsüz): her aşamanın tablosu, koku-0 yanlılığı, A6/B18 aşamaları, öğrenme eğrisi grafiği.

## 9. Bilinen sınırlamalar
* Tek bağlantı haritası (tek erkek sinek, tek yarımküre); "canlılar" aynı bağlantının gürültü/yol/başlangıç tekrarlarıdır.
* Sinaps sayısı → ağırlık dönüşümü ve MBON sınıf türetimi varsayımdır (E1 yalnız sınıf türetimini sınar).
* Hareket okuması (ε, kazanç) geliştirme tohumlarında seçildi; elle yazılmıştır, öğrenilen yalnızca değer V'dir.
* Güç analizi sentetik; gerçek veride aşırı yayılım veya zamana bağlı etkiler farklı olabilir.
* A6 → A12 düşüşü açıklanmadı.
* Sanal ortam 2B ve basittir; sonuçlar gerçek sinek davranışı hakkında iddia taşımaz.
