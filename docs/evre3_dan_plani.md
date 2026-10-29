# Evre 3.3 — DAN devresi geliştirmesi: PLAN TASLAĞI (geliştirme aşaması; ölçütler henüz DONDURULMADI)

Bağlayıcı üst belgeler: `docs/birlestirme_risk_analizi.md` (§5 kapı 3.3, T10), `docs/karar_defteri.md` K-026, veri kontrolü `docs/dan_girdi_analizi.md`.
**Durum:** TASLAK. Bu belge geliştirme tohumlarında (100-149) yapılacak keşfi tanımlar; doğrulayıcı koşulardan önce **ayrı bir "KESİNLEŞTİ" sürümü** commit edilecek (ölçütler ve doğrulayıcı tohumları orada dondurulur, CLAUDE.md kural 2).

## 1. Neden bu adım
Beyin modelinde dopamin (DAN) etkinliği bugün elle yazılmıştır: `delta = kapı·(hedef·ödül − valence)`, PAM = max(δ,0), PPL1 = max(−δ,0).
Veri (`dan_girdi_analizi.md`): DAN girdisinin %58'i doğrudan KC'den, %32'si mantar cismi dışı aracılardan, MBON'dan yalnız <%3'tür; MBON↔DAN karşılıklılığı gerçek ama işareti belirsiz (glutamat). Literatür (özet düzeyinde): KC→DAN uyarıcı geri besleme öğrenmeyi güçlendirir (Cervantes-Sandoval 2017); MBON→DAN uyarıcı geri besleme + MBON yanal baskılama ödül tahmini, sönüm ve tek denemelik öğrenme üretir (Springer & Nawrot 2021) [doğrulandı: özet düzeyi; tam metin okunmadı].
**Hedef:** hata/öğretmen sinyalinin bir kısmını elle yazılmış kurala değil, bağlantı verisinden gelen devreye bırakmak; bunun öğrenme hızını, sönümü ve kararlılığı **bozmadığını, tercihen iyileştirdiğini** ölçmek. "Hata sinyali veriden türetildi" iddiası yalnız V3 koşulunda ve yalnız ölçütler sağlanırsa kurulabilir.

## 2. Varyantlar (kademeli; her biri bir öncekine tek bileşen ekler)
| varyant | DAN sürüşü | amaç |
|---|---|---|
| V0 | elle δ (mevcut) | referans |
| V1 | V0 + KC→DAN uyarıcı geri besleme (bağlantı ağırlıklı, kazanç g_kc) | öğrenme hızı / kararlılık |
| V2 | V1 + MBON→DAN (işaretli, glutamat iki varsayım) + MBON→MBON yanal baskılama | ödül tahmini, sönüm |
| V3 | V2, elle δ yok; yalnız dışsal ödül/ceza (tat) girdisi | "elle yazılmış hata terimi gerekli mi?" |

Her varyantta **kontroller**: (a) tüm yeni bağlantılar sıfır (ablasyon = V0 ile birebir aynı olmalı, regresyon testi); (b) derece-koruyan rastgele (yeni bağlantı hedefleri karıştırılır); (c) glutamat işareti −1/+1.

## 3. Aşamalar ve kapılar
* **Aşama A — indirgenmiş devre prototipi** (`sinek.experiments.dan_proto`, CPU-hafif, tam beyin yok): gerçek bağlantı ağırlıklarıyla, KC desenleri sentetik. Sorular: (A1) kararlılık (özdeğer / sınırlı etkinlik); (A2) edinim hızı; (A3) tekrarlı ödülde PAM yanıtının azalması (tahmin); (A4) ödülsüz sunumda sönüm. Sıfır-etki (bağlantılar kapalı, V0) ve bilinen-etki (elle kurulmuş çıkarıcı geri besleme) benzetimleriyle **ölçüt kuralları sınanır** (CLAUDE.md kural 3).
* **Aşama B — tam beyin, geliştirme tohumları:** `brain_connectome` içinde isteğe bağlı `dan_mode` (varsayılan = V0, mevcut sonuçları değiştirmez). Edinim hızı, Evre 2b benzeri seçim, O4a sönümü; kararlılık. **Başlangıç koşulu:** çalışan doğrulayıcı kuyruğu (`scripts/run_validators.sh`) bitmiş olmalı.
* **Aşama C — dondurma:** geliştirmede seçilen kazançlar, ölçütler ve güç benzetimi bu belgenin KESİNLEŞTİ sürümüne yazılır; sonra yeni tohumlarla doğrulayıcı.

## 4. Peşin kabul edilen sınırlar
* Aracı nöron sinyalleri (%32) modelde dışsal girdi olarak kalır; yeni devre onları temsil etmez. Nörotransmitter işaretleri sınıflandırıcı tahminidir [doğrulanmadı].
* Aşama A sentetik KC desenleri kullanır; sonuçlar tam beyin için kanıt değil, **tasarım ipucudur**.
* Nöron sayısı başarı ölçütü değildir; bu adım yeni nöron eklemez, mevcut nöronların bağlantı kümesini genişletir.

## 5. Geliştirme bulguları (2026-10-28; geliştirme tohumları 100–149; KANIT DEĞİL, tasarım ipucu)
**Örneklem küçüktür (18 canlı-koku çifti, güven aralığı yok); yalnız yön ve büyüklük sırası okunur.** Harness: `sinek.experiments.dan_dev` (tam spiking beyin; 6 canlı × 3 koku çifti; 12 edinim + 8 sönüm; `results/dan_dev/grid1.md`, `grid2.log`, git'te yok). `sel` = V_A − V_B (öğrenmesi kapalı test).

| varyant | edinim-1 sel | edinim-12 sel | sönüm-8 sel | kararlılık / not |
|---|---|---|---|---|
| V0 (elle δ) | +0,33 | +0,41 | +0,01 | 1 denemede öğrenir, 2 denemede söner; DAN tepe 1,0 |
| V1 (KC→DAN, g_kc 1…30) | +0,34…+0,40 | +0,40…+0,41 | ≈0 | V0'dan ayırt edilemez: ek terim öğrenmeyi etkilemiyor |
| V2/− (MBON→DAN, glutamat −, g=0,02–0,05) | +0,28…+0,31 | **+0,58…+0,65** | **+0,17…+0,27** | plato V0'dan yüksek, ama sönüm bozuk; DAN tepe 1,3–3,2 |
| V2/− (g ≥ 0,5) | +0,16…+0,19 | +0,68 → +0,25 (g=8) | +0,43 → +0,20 | kararsız: sahte öğretmen (ödülsüz sunumda DAN etkinliği) 0,56…5,7; DAN tepe 32…515 |
| V2/+ (glutamat +, g=0,02) | +0,42 | +0,78 (edinim 8: +0,81) | +0,45 | en hızlı ve en yüksek plato, sönüm bozuk |
| V2/+ (g ≥ 0,5) | +0,28 → +0,05 | +0,18 → +0,01 | +0,08 → 0,00 | sahte öğretmen 1,4…13,9: öğrenmeyi yok eder |
| V3 (elle δ yok) | +0,10…+0,13 | +0,45 / +0,05 | +0,34 / +0,02 | glutamat − için işe yarar, + için çöker; sönüm bozuk |
| derece-koruyan kontrol (g=2; tek karıştırma tohumu) | +0,19 | +0,24 / +0,05 (−/+) | −0,04 / +0,00 | gerçek bağlantı kontrolden ayrışıyor (glutamat −: 0,44 vs 0,24), ama kararsız bölgede |

**Okuma (dürüst):**
1. Elle yazılmış δ (V0) zaten hızlı ve kararlıdır; V1 hiçbir şey eklemez. "Hata sinyali veriden türetildi" iddiası için adayların hepsi ya kararsızdır (g ≥ 0,5) ya sönümü bozar (düşük g). **Kapı 3.3 şu an karşılanmadı**; plan ölçütleri bu yüzden KESİNLEŞTİRİLMEDİ.
2. Düşük kazançta (g=0,02–0,05) MBON→DAN geri beslemesi platoyu yükseltiyor (0,41 → 0,58–0,81) fakat sönümü bozuyor (0,01 → 0,17–0,45). Olası açıklama (SINANMADI, hipotez): "tahmin hatasının iki yönü"nden yalnız pozitif yarısı (PAM) çalışıyor; PPL1 (ceza/sönüm) yolu bağlantı verisinden henüz gelmiyor. Sonraki geliştirme sorusu: sönüm için PPL1'e giden MBON→DAN işaretinin (glutamat varsayımı) ve ek bir iç-nöron aracılığının (R-8 bölüm D: %32 aracı girdi) eklenmesi.
3. Kararlılık kapısı (yeni, K-028 ile birlikte): her varyant için "ödülsüz sunumda sahte öğretmen < 0,05 ve DAN tepe < 3×V0" koşulu **sönümden önce** sınanır; kararsız bölgedeki sonuçlar (g ≥ 0,5) değerlendirmeye alınmaz.

## 6. Ölçek ekseninin önceliği (K-028)
Gürültüsüz öğrenilmiş değer okuması (K→∞ tablo) O1a'da frozen kolu 0,510 → **0,818**'e çıkarıyor (referans 0,984); K=4 topluluk yalnız 0,552. Yani oyun başarısını şu an sınırlayan şey DAN devresi değil, **değer okumasının Poisson gürültüsü**. Sonuç:
* Öncelik sırası: (1) ölçek/gürültü ekseni (K=8,16, τ_valence, paylaşılan-ağırlık topluluk okuması; GPU aşamasının ana işi), (2) DAN devresi (sönüm yolu) ikinci sırada.
* GPU aşaması için not: `EnsembleBrain` kopyaları ağırlık paylaşımlı kuruluyor ve öğrenme kapalı. Öğrenen (plastik) topluluk için kopyalar arasında ağırlık paylaşımı gerekir (tek W, K gürültü örneği): ayrı bir tasarım ve test (sıfır-etki: K=1 birebir aynı) gerekir.
* `scale_dev` sonuçları geliştirme tohumundadır (110); doğrulayıcı tohumlarıyla (≥200) çalıştırılamaz (R-2).

### 6.1 Ölçek eğrisi ve okuma süresi taraması (geliştirme, O1a, ön-eğitim 100, 24 canlı × 8 deneme, KANIT DEĞİL)
Her nokta tek örneklemdir (192 deneme; kümeli standart hata ≈0,04–0,05): ±0,05 altındaki farklar gürültüden ayırt edilemez.

| K (anten başına gürültülü kopya, τ=0,15) | 1 | 2 | 4 | 8 | 16 | ∞ (gürültüsüz tablo) | referans |
|---|---|---|---|---|---|---|---|
| frozen p_hit (oyun tohumu 110) | 0,510 | 0,510 | 0,552 | 0,625 | 0,646 | 0,818 | 0,984 |
| frozen − anosmik [%99 GA] | +0,224 | +0,224 | +0,266 | +0,339 | +0,359 | +0,531 | |

* K ile tek yönlü ama **yavaş** yükselme: K=16'da 0,646; K→∞ tablosuna (0,818) hâlâ 0,17 var. Basit "√K ile gürültü azalır" beklentisi karşılanmıyor. Olası nedenler (SINANMADI): kopyalar aynı dünya girdisini paylaşıyor (yalnız Poisson kıvılcım gürültüsü bağımsız); okuma doğrusal olmayan; K→∞ tablosu kayan zaman gecikmesini yok sayar. Bu yüzden GPU aşamasında K'yı artırmak tek başına yeterli sayılmaz.
* **τ_valence (okuma entegrasyon süresi)**, K=1, frozen p_hit (tohum 110 / tohum 111):

| τ (sn) | 0,02 | 0,04 | 0,08 | 0,15 (varsayılan) | 0,3 | 0,6 | 1,2 |
|---|---|---|---|---|---|---|---|
| tohum 110 | (koşuyor) | 0,583 | 0,495 | 0,510 | 0,448 | 0,448 | 0,375 |
| tohum 111 | (koşuyor) | 0,615 | — | 0,552 | — | — | — |

  Uzun entegrasyon (≥0,3 sn) açıkça kötü (hareket eden canlı için gradyan bulanıyor, gecikme); kısa τ=0,04 iki tohumda da varsayılandan ≈+0,06–0,07 iyi ama τ=0,08 bu sırayı bozuyor (tek örneklem gürültüsü). Varsayılan τ **değiştirilmedi**: ön-kayıtlı doğrulayıcılar bu beyin tanımıyla koştu; τ değişirse yeni ön-kayıt gerekir (kural 2).

### 6.2 Kısa τ + topluluk birlikte (geliştirme; KANIT DEĞİL)
Topluluk (gürültü azaltma) ile kısa okuma süresi (gecikme azaltma) birbirini tamamlıyor: gürültü azalınca kısa τ'nun yarattığı ek gürültü artık sorun olmuyor.

| ayar (O1a, frozen p_hit) | tohum 110 | tohum 111 |
|---|---|---|
| K=1, τ=0,15 (ön-kayıtlı doğrulayıcı beyin tanımı) | 0,510 | 0,552 |
| K=1, τ=0,04 | 0,583 | 0,615 |
| K=1, τ=0,02 | 0,578 | 0,589 |
| K=8, τ=0,15 | 0,625 | — |
| **K=8, τ=0,04** | **0,807** | **0,771** |
| **K=8, τ=0,02** | **0,823** | — |
| K=∞ tablo (τ=0,15) | 0,818 | — |
| referans (elle kurulmuş) | 0,984 | 0,984 |

Yorum: K=8 + kısa τ, gürültüsüz tablo düzeyine (≈0,8) ulaşıyor; yani frozen kolun tavanı artık referansa (0,98) uzaklığın çoğunu oluşturan başka bir şey (okumanın kendisi/hareket kuralı). Tek ön-eğitim hattı (dev tohumu 100), iki oyun tohumu; **doğrulayıcı koşulmadı**. Bu ayarın "beyin tanımı" olması için yeni ön-kayıt + bağımsız tohumlar gerekir (kural 2/3): sıradaki iş.

**Genelleme (geliştirme, ön-eğitim 100; oyun tohumları 112 / 115; KANIT DEĞİL):** aynı ayar (K=8, τ=0,04) diğer oyunlarda:

| oyun (tohum) | anosmik | K=1, τ=0,04 | **K=8, τ=0,04** | referans | K=8 − anosmik [%99 GA] |
|---|---|---|---|---|---|
| O1b (112) | 0,208 | 0,615 | **0,792** | 0,958 | +0,583 [+0,453; +0,708] |
| O2-yakın (115) | 0,333 | 0,698 | **0,729** | 0,812 | +0,396 [+0,292; +0,484] |

O1b'de O1a'daki kazanç yinelendi (+0,18, K=1 aynı τ'ya göre). **O2-yakın'da kazanç küçük (+0,03) ve referans tavanı 0,81'e yakın**: taban ile referans arasında zaten ≈0,11–0,15 boşluk var, yani "ölçek kazancı ≥ δ=0,15" ölçütü bu oyunda tavan etkisiyle sınanamaz (güç benzetimi: δ'da 0,07). Bu yüzden ön-kayıtlı ölçek doğrulayıcısı (`docs/olcek_plani.md`, K-036) O2-yakın'ı kapsam dışı bıraktı.

### 6.3 Kalan boşluk: sonraki geliştirme adımı için ÖNCEDEN yazılmış kuram (R-8; henüz sınanmadı)
K=8 + τ=0,04 ile frozen kolu gürültüsüz tablo düzeyine (≈0,8) çıkıyor; referans 0,96–0,98. Yani artık boşluğun (≈0,17–0,19) kaynağı **okuma gürültüsü değil**. Aday açıklamalar (hepsi SINANMADI, sıralama tahmin):
* **H1 — öğrenilmiş değer fonksiyonunun kalitesi.** Ön-eğitim 12 bölüm; değer eğrisinin koku yoğunluğuna göre eğimi zayıf/düz olabilir. Sınama: gürültüsüz tablonun (oracle) başarısı ön-eğitim bölüm sayısı ve plastisite öğrenme oranı η ile nasıl değişiyor (tablo, 5 nokta). "En hızlı öğrenen" hedefi doğrudan buna bağlıdır: p_hit'i bölüm sayısına karşı çizmek, öğrenme hızının ilk gerçek ölçümüdür.
* **H2 — motor kuralı.** `contrast = (v_L − v_R)/(|v_L|+|v_R|+ε)` normalleştirir; değerler ε=0,05'e yakınsa dönüş zayıflar, büyükse işaret gürültüsü (±1) doğrudan dönüş hızına geçer. `turn_gain=10`, `wander_σ=1` elle seçilmiştir. Sınama: gürültüsüz tablo ile ε ∈ {0,01; 0,05; 0,2} × `turn_gain` ∈ {5; 10; 20} (geliştirme tohumunda; sonra hangi parametrenin doğrulayıcıda sabitleneceği yeni ön-kayıtta).
* **H3 — sensör SNR'si.** Anten arası mesafe × gradyan; referans ayrıca gradyanı kusursuz kullanıyor. Sınama: referans kolunu aynı anten gürültüsüyle koşmak ("sensör sınırı") — referans zaten sensörsüz (dünyayı doğrudan okur) ise bu sınır ölçülemez; bu durumda H3 ayrıştırılamaz ve bu bir sınırlılık olarak yazılır.
* Doğrulayıcı kuralı: bu sınamalar geliştirme tohumlarındadır (100-149); ayarlardan biri doğrulayıcıya girecekse yeni ön-kayıt + güç benzetimi gerekir (R-1, R-6).

### 6.4 Kalan boşluğun ayrıştırması: motor kuralı baskın (geliştirme, O1a tohum 110, gürültüsüz tablo; KANIT DEĞİL)
Araç: `python3 -I -m sinek.experiments.gap_dev` (K→∞ gürültüsüz tablo, öğrenme kapalı, CRN). **Not:** oyun kontrol noktalarındaki gerçek motor ayarı `turn_gain=60, contrast_eps=2,0, wander_σ=1` (`Config` varsayılanları 10/0,05 değil; ilk tarama yanlış rejimdeydi ve düzeltildi).

| değer kaynağı (motor ε=2, kazanç 60) | p_hit |
|---|---|
| referans (elle) | 0,984 |
| öğrenilmiş tablo | 0,818 |
| tablo, iki yarımküre ortalaması (sol–sağ asimetri YOK) | 0,812 |
| tablo, canlı başına doğrusal V=a·s | 0,875 |

→ **H4 (sol–sağ kazanç asimetrisi) ve H1 (eğri biçimi) boşluğu açıklamıyor** (simetrikleştirme 0,818→0,812; doğrusallaştırma +0,06).

Motor kuralı taraması (aynı gürültüsüz tablo; satır ε, sütun turn_gain):

| ε \ turn_gain | 10 | 20 | 40 | **60** | 120 |
|---|---|---|---|---|---|
| 0,02 | 0,917 | 0,958 | 0,958 | 0,958 | 0,948 |
| 0,1 | 0,870 | 0,906 | 0,958 | 0,958 | 0,958 |
| 0,5 | 0,635 | 0,771 | 0,901 | 0,927 | 0,958 |
| **2 (mevcut)** | 0,484 | 0,547 | 0,719 | **0,818** | 0,891 |
| 8 | 0,307 | 0,396 | 0,406 | 0,521 | 0,714 |

(Aynı taramada referans: ε=2/60 → 0,984; ε=0,1/60 → 1,000.)

**Bulgu:** öğrenilmiş değerlerin ölçeği (≈0–0,5) ε=2'ye göre küçüktür; kontrast paydası ε tarafından yutulduğundan dönüş hızı ≈ (gain/ε)·Δv (neredeyse doğrusal, normalleşmemiş) ve değer ne kadar zayıfsa o kadar az dönülür. ε'yi değer ölçeğine göre küçültmek (0,1–0,5) gürültüsüz tabloyu 0,82 → 0,93–0,96'ya, yani **referansa 0,03–0,05 yakına** çıkarıyor. Yani kalan boşluğun büyük kısmı **öğrenilmiş devrede değil, elle yazılmış motor normalleştirmesindedir (R-11)**.
**Çekince (sınanıyor):** küçük ε, gürültülü okumada işareti büyütür (kontrast ±1'e doymaya yaklaşır); K=1 ve K=8 ile gürültülü etkisi `scale_dev --eps --turn-gain` ile ölçülüyor (tohum 110). Bu bir motor ayar değişikliğidir, "daha zeki beyin" değil; doğrulayıcıya girerse yeni ön-kayıt + güç benzetimi gerekir (R-1, R-6), ve ε'nın kullanıcı-seçimli ayar olduğu açıkça yazılır.

### 6.5 Motor kuralı gürültülü okumada (geliştirme, O1a tohum 110, K=8, τ=0,04; tek örneklem; KANIT DEĞİL)
`scale_dev --eps --turn-gain` (aynı motor TÜM kollara uygulanır). Mevcut motor (ε=2, kazanç 60) için K=8 sonucu daha önce 0,807 (anosmik 0,286).

| ε | turn_gain | K=∞ tablo | K=1 | **K=8** | anosmik | referans |
|---|---|---|---|---|---|---|
| 2 (mevcut) | 60 | 0,818 | 0,583* | 0,807 | 0,286 | 0,984 |
| 0,5 | 60 | 0,938 | 0,401 | **0,859** | 0,115 | 1,000 |
| 0,1 | 60 | 0,953 | 0,328 | **0,891** | 0,005 | 1,000 |
| 0,1 | 30 | 0,953 | 0,495 | 0,849 | 0,073 | 1,000 |
| 0,5 | 120 | 0,938 | 0,203 | 0,807 | 0,021 | 1,000 |

(*τ=0,04, K=1.) Okuma:
* K=8'de küçük ε, p_hit'i en çok +0,05…+0,08 artırıyor (0,807 → 0,86–0,89); tek örneklemde kümeli SE ≈0,04–0,05, yani ≈1–1,5 SE: **ayırt edilebilir bir kazanç sayılmaz.** Gürültüsüz tablonun vaadi (0,95) gerçekleşmiyor: K=8 hâlâ gürültülü.
* K=1'de küçük ε **zarar veriyor** (0,58 → 0,20–0,50): işaret gürültüsü doğrudan dönüş hızına geçiyor.
* **Kör karşılaştırıcı çöküyor:** anosmik p_hit 0,286 → 0,005–0,12 (koku yokken bile değer gürültüsü kontrastı ±1'e taşıyor; yaratık yerinde dönüyor). Bu "koku kazancı"nı (frozen − anosmik) yapay olarak şişirir (+0,75…+0,89) ve O1 anosmik-pencere kapısını (0,15–0,45) bozar; yani ölçütler bu motorla yeniden tasarlanmak zorunda kalırdı.
* **Karar (K-039):** motor ε/kazanç ayarı doğrulayıcıya **alınmadı**; kazanç küçük, tek örneklem ve kör karşılaştırıcıyı bozuyor. ε, gürültü tabanına (≈ okuma SD'si) göre seçilmiş bir ölü-bölge gibi çalıştığı için mevcut ε=2 savunulabilir bir ayar. GPU aşamasında (K ≥ 16, daha az gürültü) ε–K birlikte taranmalıdır; o zaman kör karşılaştırıcı için ayrı bir tanım (ör. eşleşmiş-gürültü kör kol) gerekir.

## 7. Öğrenme HIZI ölçümü (geliştirme, tohum 101; 6 canlı × 3 koku çifti; KANIT DEĞİL)
Araç: `python3 -I -m sinek.experiments.ogrenme_hizi` (`dan_dev` protokolü; her denemeden sonra öğrenmesi kapalı test; ölçüte ilk ulaşılan deneme: edinim sel=V_A−V_B ≥ 0,20; sönüm sel ≤ yarısı; tersine çevirme V_B−V_A ≥ 0,20; hücre: ortanca (ortalama; sansürlü oranı), en çok 12 deneme). Öğrenme ölçeği = öğrenme oranı η çarpanı (1 = doğrulayıcı beyni). **Tahmin koddan önce yazıldı** (araç docstring'i).

| varyant | ölçek | edinim | sönüm | tersine çevirme | plato sel | sahte öğretmen |
|---|---|---|---|---|---|---|
| V0 (elle δ) | 0,01 | 13 (sansür %56) | 1 | 13 (%78) | +0,04 | 0 |
| V0 | 0,03 | 11 (%44) | 3 | 13 (%78) | +0,13 | 0 |
| V0 | 0,1 | 4 | 3 | 6 | +0,29 | 0 |
| V0 | 0,3 | 2 | 2 | 2 | +0,39 | 0 |
| V0 | **1 (mevcut)** | **1** | **1** | **1** | +0,39 | 0 |
| V0 | 3 | 1 | 1 | 1 | +0,37 | 0 |
| V2/− g_mbon=0,03 | 0,03 | 12 (%50) | 2 | 13 (%72) | +0,09 | 0,053 |
| V2/− | 0,1 | 4 | 6 | 9 | +0,27 | 0,049 |
| V2/− | 0,3 | 2 | 4 | 3 | +0,44 | 0,046 |
| V2/− | 1 | 1 | 2 | 1 | +0,58 | 0,041 |
| V2/− | 3 | 1 (ortalama 1,0) | 1 (ortalama 2,8; %6 sansür) | 1 | +0,72 | 0,038 |

Okuma (dürüst):
* **Tahmin büyük ölçüde doğru:** küçük ölçeklerde süre ≈ 1/ölçek (0,1→4, 0,3→2, 1→1), plato ölçekten bağımsız. Tersine çevirme küçük ölçeklerde edinimden yavaş (0,1: 6 vs 4; 0,03: sansürlü 13), ölçek ≥0,3'te eşit — bu kısım **kısmen yanlış çıktı**: tavan etkisi tersine çevirmenin ek maliyetini gizliyor.
* **Mevcut beyin bu protokolde zaten tek denemede öğreniyor, söndürüyor ve tersine çeviriyor (tavan).** Yani bu protokolde öğrenme oranını artırmak hız kazandırmaz; "daha hızlı öğrenen" iddiası bu kadar kolay bir görevle sınanamaz. Hız farkı ancak **zor** görevlerde ortaya çıkar: seyrek/olasılıklı ödül, gecikmiş ödül, çok koku (karışma), bir oturumda tersine çevirme.
* V2/− (MBON→DAN geri besleme) hızı değiştirmeden **plato yükseltiyor** (0,39 → 0,58 → 0,72) ama sönümü yavaşlatıyor ve küçük bir sahte öğretmen (≈0,04–0,05) getiriyor — §5 bulgusuyla tutarlı.
* Ölçek ≥3'te aşırı genelleme/kararsızlık görülmedi (V0 sahte öğretmen 0); sınır daha büyük ölçeklerde aranabilir.
* **Sonraki adım (tasarım):** hız farkını görünür kılan görev = **olasılıklı ödül + oturum içi tersine çevirme** (iki-kollu kuşatma/bandit: A %80, B %20 ödül; 20 denemede tersine çevirme). Metrikler: kümülatif pişmanlık, tersine çevirme sonrası adaptasyon denemesi. Bu yeni bir oyun (O5) olur: ön-kayıt + güç benzetimi gerektirir; plastik kollar oyun içinde öğrenir.

## 8. İki zaman ölçekli plastisite: soyut kuram kontrolü (R-8; 2026-10-29; KANIT DEĞİL, beyin değil)

Hipotez (§7 sonu, O5 pilotundan): "hızlı + yavaş plastisite birlikte olursa hız–gürültü ödünleşimi hafifler." Beyne kod yazmadan önce soyut bir ödül öğrenicide sınandı (`kuram_iki_zaman.py`, `results/kuram_iki_zaman.md`; O5 programı, 40 000 yaşam/öğrenici, Q ← Q + α(r − Q), softmax T=0,15). Tahmin koşudan önce dosya başlığına yazıldı.

| öğrenici (üçü ortalama = geç faz-1, geçiş, geç faz-2) | ödül/bölüm |
|---|---|
| tek EMA α = 0,05 / 0,1 / 0,2 / 0,3 / **0,5** / 0,8 / 1,0 | 0,519 / 0,570 / 0,635 / 0,664 / **0,682** / 0,678 / 0,655 |
| en iyi sabit karışım (hızlı 0,8, yavaş 0,15, w_hızlı 0,7) | 0,669 (−0,013) |
| en iyi sürprizle kapılı α (0,15 → 0,8) | 0,675 (−0,008) |

Tahminler: (1) tek EMA'da orta α'da tepe — **tuttu** (α = 0,5). (2) karışım en iyi tek α'dan farksız (|fark| < 0,01) — **yönü tuttu, büyüklüğü hafif aştı**: karışım en iyi tek α'nın 0,013 **altında** (iki üstel çekirdek tek üstelden iyi değil, orta ağırlıkta daha kötü). (3) kapılı α için +0,01…+0,03 kazanç — **YANLIŞ çıktı**: basit sürpriz kapısı kazanç vermedi (−0,008). Bu "hiçbir kapı olmaz" demek değil; yalnız denenen basit kapı kazandırmadı (Bernoulli 0,8/0,2 geri bildirimi değişimi bölüm başına zayıf işaretlediği için tespit gecikmesi baskın).

**Sonuç (yön, kanıt değil):** (a) tek EMA eğrisi α = 0,3–0,8 arasında neredeyse düz (0,664–0,682): zaman ölçeği mühendisliğinden beklenen üst kazanç **≈0,02 ödül/bölüm** — O5 ön-kaydının δ = 0,10'unun çok altında ve O5'teki asıl boşluğun (öğrenmiş beyin ≈0,36 vs soyut tavan ≈0,6–0,75) küçük bir parçası. (b) İki zaman ölçekli plastisite bu yüzden **düşük öncelik**; "ödünleşimi hafifletir" hipotezi soyut modelde desteklenmedi. (c) Asıl kaldıraç tahmini: yaklaşma (temas-yok %25–45) ve değer okuma gürültüsü (K-028); ölçek ekseni (K=8, τ=0,04) O5'te plastik kol için sınanmalıdır — ama `EnsembleBrain` kopyaları öğrenme kapalı okuma içindir; plastik kolda topluluk okuması için yeni tasarım gerekir (§GPU devri 3b).
Sınır: soyut modelde okuma gürültüsü ve yaklaşma yok; gerçek beyinde ödünleşim eğrisi farklı olabilir.
