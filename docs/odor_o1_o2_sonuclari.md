# O1 ve O2 doğrulayıcı sonuçları (ön-kayıtlı, bağımsız tohumlar)

Ön-kayıtlar: `docs/odor_o1_plani.md`, `docs/odor_o2_plani.md` (commit c4f544f; ölçütler koşudan sonra değişmedi). Ham çıktı: `results/odor_val/<Oyun>_s<tohum>/{summary.md,results.json}` (git'te yok).
Canlılar: iki bağımsız ön-eğitim popülasyonu (tohum 200 ve 201; 24 canlı), öğrenmesi **kapalı**, 16 deneme/canlı (8 ayna çifti), T=25 sn, CRN eşli kollar.

## Hüküm

| oyun | popülasyon 200 | popülasyon 201 | **hüküm** |
|---|---|---|---|
| **O1a** (düz iz), tohum 210/211 | frozen−anosmik **+0,302** [%99 GA +0,198; +0,406]; frozen−random +0,234; P3 ✔ | **+0,188** [+0,091; +0,284]; +0,221; P3 ✔ | **BAŞARILI** (K1–K3, P1–P3, iki popülasyonda) |
| **O1b** (tek dönüşlü iz), tohum 212/213 | **+0,247** [+0,146; +0,352]; +0,177; P3 ✔ | **+0,255** [+0,172; +0,339]; +0,151; P3 ✔ | **BAŞARILI** |
| **O2-yakın** (R=5), tohum 220/221 | **+0,344** [+0,276; +0,419] | **+0,299** [+0,229; +0,367] | **BAŞARILI** (K1 referans 0,844/0,826 ≥0,70; K3 sızıntı 0) |
| O2-tam (betimsel, karar dışı), tohum 222/223 | +0,253 [+0,185; +0,323] | +0,214 [+0,146; +0,276] | karar vermez; fark pozitif ve ≥δ |

Başarı eşiği: eşli işaret-çevirme p<0,01 **ve** %99 küme-GA alt sınırı >0 **ve** ortalama fark ≥δ=0,15. En zayıf geçiş O1a/pop. 201: P1 +0,188 (GA alt sınır +0,091); P3 yarılarından biri +0,151 [+0,047; +0,266] — eşiğe (0) en yakın değerlerdir, hepsi geçti.

## Kol düzeyleri (p_hit)

| | O1a/200 | O1a/201 | O1b/200 | O1b/201 | O2yakın/200 | O2yakın/201 |
|---|---|---|---|---|---|---|
| frozen (koku açık) | 0,539 | 0,471 | 0,482 | 0,482 | 0,719 | 0,659 |
| anosmik (glom ≡ 0) | 0,237 | 0,284 | 0,234 | 0,227 | 0,375 | 0,359 |
| random (dönüş kazancı 0) | 0,305 | 0,250 | 0,305 | 0,331 | 0,354 | 0,370 |
| referans (elle kurulmuş üst sınır) | 0,984 | 0,971 | 0,966 | 0,971 | 0,844 | 0,826 |

* Kapılar: O1'de K1 (referans ≥0,80) ve K2 (anosmik ∈ [0,15; 0,45]) iki popülasyonda sağlandı; O1'de sızıntı denetlenecek deneme çıkmadı (iz çıkış noktasından başlar; tasarım gereği "0 deneme"). O2-yakın'da 57 ve 48 denemede ihlal 0; O2-tam'da 124 ve 142 denemede ihlal 0.
* Ayna yarıları (özgün/ayna) benzer: yön ya da duvar yanlılığı belirtisi yok (O1a/201 en büyük sapma: 0,490/0,453).

## Dürüst yorum ve sınırlar

* **Ne gösterildi:** Ön-eğitimli, öğrenmesi kapalı canlı, koku girdisi sıfırlanmış kendisinden ve yönelimsiz gezginden anlamlı ve ≥0,15 daha sık hedefe ulaşıyor (düz iz, tek dönüşlü iz, yakın alan). Anosmik ve random kollar birbirine yakın: kazanç koku girdisinden geliyor.
* **Ne gösterilmedi:** Başarı mutlak anlamda küçüktür. Frozen canlı O1'de ≈0,47–0,54'te kalıyor; aynı hareket kuralıyla gürültüsüz **referans** 0,97–0,98'e çıkıyor. Yani koku izi çözülebilir, ama bu canlı çözümün yaklaşık yarısını yakalıyor. "Zeka" iddiası yok (ön-kayıt §7): hareket kuralı ve referans elle yazılmıştır; başarı "bağlantı haritasından çıkan değer okuması bu görevde kullanılabilir" demektir.
* **Boşluğun nedeni (geliştirme ölçümü, kanıt değil):** değer sinyalinin gürültüsü büyük (8% anten farkında adım başına SNR ≈0,13–0,15); topluluk okuması K=4 bunu yarıya indirince frozen 0,510→0,552 (geniş GA). Ayrıntı: karar defteri K-027 ve `docs/evre3_dan_plani.md`.
* **O2-tam** koku alanı denemelerin yalnız %63–68'inde görüldü (kör bölge girişi aralığı ön-kayıtlı [0,3; 0,9] içinde); referans 0,72–0,73. Betimsel.
* **Kod izlenebilirliği:** raporların "kod commit" alanı rapor yazıldığı andaki HEAD'dir (7be599a, da92213, 70cd30d); koşular daha önce başlamıştı. Ön-kayıt commit'i (c4f544f) ile sonrası arasında değerlendirme yolundaki dosyalarda yalnız şu fark var: `odor_eval.py` (O4 çekim kapısı çarpanı parametresi; O1/O2 yolu aynı), `games/protocol.py` `snapshot(reps=1)` (O1/O2 `play` yolunu etkilemez), yeni dosyalar. `git diff c4f544f HEAD -- src/sinek/experiments/odor_validate.py src/sinek/games/world.py src/sinek/brain_connectome.py` boş.
* Tek ön-eğitim hattı, iki tohum; iz geometrisi ailesi dar (düz, tek dönüş); kesintili iz, rüzgâr ve çoklu kaynak kapsam dışı.
