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

