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
