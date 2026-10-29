# O5 doğrulayıcısı — sonuçlar (ön-kayıt: `docs/odor_o5_plani.md`, commit `35d2db4`; koşular 2026-10-29)

**Ön-kayıtlı hüküm: KISMİ — iddia YOK (başarısız sayılır).** Tohum 260 BAŞARILI, tohum 261 BAŞARISIZ; ön-kayıt iki tohumun da geçmesini şart koşuyordu (§5). Ölçütler, eşikler ve tohumlar koşudan önce dondurulmuştu ve değişmedi. Kod commit `e8903ec`; ham veri `results/o5_val/` (git'te yok), özet `results/o5_val/ozet.md`.

## 1. Ön-kayıtlı sonuç (tohum başına 48 yaşam; kol başına 40 bölüm; geç bloklar: bölüm 11–20 ve 31–40)

| tohum (pop.) | ödül oranı: plastic / frozen / reference | P1 geç faz-1 (`plastic − frozen`) | P2 geç faz-2 | P3 özgüllük (net tercih) | kapı G | karar |
|---|---|---|---|---|---|---|
| 260 (200) | 0,380 / 0,218 / 0,756 | **+0,204** [+0,115; +0,292] p=0,0001 ✔ | **+0,227** [+0,156; +0,296] p=0,0001 ✔ | **+0,203** [+0,105; +0,296] p=0,0001 ✔ | tamam | **BAŞARILI** |
| 261 (201) | 0,374 / 0,316 / 0,756 | +0,029 [−0,037; +0,098] p=0,1541 ✘ | +0,087 [−0,002; +0,175] p=0,0095 ✘ (GA alt sınırı <0 ve ortalama <δ) | **+0,199** [+0,093; +0,299] p=0,0001 ✔ | tamam | **BAŞARISIZ** |

Kapı G: referans ödül oranı 0,756 / 0,756 (≥0,60 ✔; üst sınır ≈0,8). Betimsel tersine çevirme bedeli (iyi koku seçme, 5 bölümlük bloklar; tersine çevirme bölüm 21'de): tohum 260 plastic b4 0,66 → b5 0,47 → b6 0,52 → b7 0,63; tohum 261 plastic b4 0,70 → b5 0,55 → b6 0,66 (öğrenmesiz frozen ≈0,5 boyunca). Yani iki popülasyonda da tersine çevirme sonrası düşüş ve toparlanma görülüyor.

## 2. Neden başarısız: POST-HOC çözümleme (hükmü DEĞİŞTİRMEZ; `o5_posthoc.py`, `results/o5_val/posthoc.md`)

Geç bloklar, yaşam ortalaması:

| tohum | kol | temas oranı | temasta iyi koku seçme | ödül oranı |
|---|---|---|---|---|
| 260 | plastic | 0,711 | 0,638 | 0,425 |
| 260 | frozen | 0,412 | 0,492 | 0,209 |
| 261 | plastic | 0,650 | 0,681 | 0,385 |
| 261 | frozen | **0,636** | 0,529 | 0,327 |

`plastic − frozen` ayrışması: seçicilik farkı (temaslı bölümlerde iyi koku seçme) **+0,146 ve +0,152** (iki popülasyonda aynı); net tercih farkı (P3) **+0,203 ve +0,199** (aynı); ama **temas farkı +0,299 [+0,227; +0,368] ve +0,014 [−0,049; +0,080]** (çok farklı). Ödül farkı (+0,216 / +0,058) bu iki bileşenin ürünü.

Okuma (post-hoc, etiketli):
1. Öğrenme etkisi — kokuları iyi/kötü diye ayırt etmek ve tersine çevirmeden sonra yeniden öğrenmek — iki popülasyonda **aynı büyüklükte** göründü (seçicilik +0,15, P3 +0,20 ve her ikisinde ön-kayıtlı P3 geçti).
2. Ödül oranı ölçütü (P1/P2) iki şeyi karıştırıyor: *yaklaşma* (temas oranı) ve *seçicilik*. Tohum 261'in popülasyonunda eğitimsiz `frozen` beyin zaten %64 temas ediyor (260'ta %41; geliştirme pilotunda 0,53); plastic'in temas oranı hep ≈%65–71'de kaldı. Temas zaten yüksekken kazanç yalnız seçicilikten gelebilir: ödül farkı ≈ temas × (p_hi − p_lo) × seçicilik farkı = 0,65 × 0,6 × 0,15 ≈ **+0,06 < δ = 0,10**. Hatta tam temasta bile 1 × 0,6 × 0,15 = 0,09 < 0,10: **ölçülen seçicilik kazancı ödül-oranı ölçütünün δ'sını tek başına hiçbir temas düzeyinde geçemezdi**; P1/P2 ancak yaklaşma kazancı (frozen'ın zayıf yaklaştığı popülasyonda) ya da seçiciliğin ≥0,17–0,26'ya çıkması ile geçilebilirdi.
3. Frozen'ın temas oranı popülasyondan popülasyona çok değişiyor (0,41 / 0,64 / 0,53): eğitimsiz beynin doğuştan koku eğilimi (W0 ve koku desenine bağlı) popülasyon özelliği. Bu, ön-kayıttaki güç benzetiminin modellemediği bir değişkenlik kaynağı.

## 3. Hata ve sınırlar (karar defteri E-15, K-044)
* **Tasarım hatası (E-15):** P1/P2 ödül-oranı ölçütü yaklaşma ile seçiciliği karıştırıyor ve δ=0,10 seçicilik kazancıyla ulaşılamaz bir düzeydi; güç benzetimi (R-6) girdilerini tek geliştirme popülasyonundan aldığı için bunu görmedi. Güç benzetimindeki "pilot etkisi 0,99" değeri tek popülasyonun temas farkına (+0,3) dayanıyordu; ön-kayıt §7 sınır 1–2'de "iyimser olabilir / varyans varsayım" diye uyarılmıştı, ama **popülasyon heterojenliği** ayrıca öngörülmemişti.
* **Çıkarım birimi:** yaşam; ama iki tohum yalnızca iki popülasyonu (koku çifti) temsil ediyor. Bu doğrulayıcının "genelleme" gücü iki popülasyonla sınırlı; popülasyon düzeyi değişkenlik (frozen temas oranı) baskın çıktı.
* **Denetim notu (kod incelemesi, 2026-10-29):** bağlantı verisinden gelen `naive` beyin aynı başlangıç ağırlığı W0'la başlar (rastgele sapma yok); yaşamlar arasındaki fark dünya yerleşimi ve Poisson gürültüsünden gelir. Dört parçada aynı eleman indeksi aynı gürültü tohumunu paylaşır ama dünyalar (dolayısıyla koku girdileri ve eylemler) farklıdır → parçalar arası beyin-başlangıcı sahte-tekrarı YOK; gürültü akışı ortaklığı yörüngeler ayrıştığı için önemsiz sayılır (doğrulanmadı: ölçülmedi).
* **Elle yazılmış bileşenler (R-11):** DAN hata kuralı, motor kuralı, referans kehanet-izleyici, ödül programı (§6 ön-kayıt) — değişmedi.
* Hız iddiası yok; yalnız "ödüle göre davranış değiştirir" sınandı ve bütünüyle (iki tohumda) kanıtlanamadı.

## 4. Sonraki adım (ön-kayıtlı değil; öneri)
Tohumlar 260/261 yandı (R-2). Yeni bir O5 doğrulayıcısı (O5b) için **yeni ön-kayıt + yeni tohumlar** gerekir ve şunlar gözetilmelidir: (a) karar veren ölçü olarak seçicilik (temaslı bölümlerde iyi koku seçme ya da net tercih) — yaklaşmayı ayrı betimsel/kapı yap; (b) δ'yı bu koşunun popülasyonlarına bakarak seçme riskini ("kazanan lanet") ve güç benzetimini **popülasyon heterojenliğiyle** (frozen temas 0,4–0,65) yap (R-6); (c) ≥4 popülasyon (koku çifti) — naive kollar ön-eğitim gerektirmez, yalnız koku desenleri; (d) yeni tohumlar. Bu koşunun verisi O5b'nin ölçütünü seçmek için kullanılırsa belgede açıkça "bu veriden türetildi" yazılmalı. Bu, bir iddia değil; bir plan önerisidir.

## 5. Geliştirme kolları (KANIT DEĞİL; geliştirme popülasyonu 102, oyun tohumu 132; 48 yaşam; aynı dünyalar, eşli)

**5.1 Düz O5'in geliştirme tekrarı** (ön-kayıt kuralıyla, betimsel): P1 +0,171 [+0,085; +0,256], P2 +0,146 [+0,044; +0,246], P3 +0,220 [+0,114; +0,329]; `frozen` temas 0,493, plastic 0,654; temasta iyi koku seçme farkı +0,173. Yani seçicilik kazancı üç popülasyonda kararlı (+0,146 / +0,152 / +0,173) ve `frozen` temas oranı 0,41–0,64 arasında değişiyor; P1/P2 ödül ölçütü bu yüzden popülasyona duyarlı (E-15).

**5.2 Plastik topluluk (`PlasticEnsembleBrain`, K=4, τ_valence=0,04; TAHMİN-2 koşudan önce `o5_dev.py` başlığına yazılmıştı: "geç bloklarda ödül oranı ≥ +0,05")**

| ölçü (geç bloklar 11-20, 31-40) | plastic (K=1) | plastic_ens (K=4) | fark `ens − plastic` [%99 GA, eşli, yaşam birimli] |
|---|---|---|---|
| ödül oranı | 0,391 | 0,550 | **+0,159 [+0,098; +0,225]** |
| temas oranı | 0,654 | 0,839 | +0,184 [+0,132; +0,239] |
| net tercih (P3 ölçüsü) | — | — | +0,224 [+0,103; +0,343] |

Referans 0,77; `frozen` 0,232. İyi koku seçme (5 bölümlük bloklar) K=4: 0,65 0,74 0,75 0,77 | tersine çevirme 0,46 | 0,64 0,75 0,73 (K=1: 0,66 0,72 0,71 0,60 | 0,43 | 0,52 0,67 0,62). Ayrıca ön-kayıtlı kuralla `plastic_ens − frozen`: P1 +0,304, P2 +0,331, P3 +0,444 (betimsel). Önceki, kontrol noktasız ve ham veri tutmayan `o5_dev` koşusu (popülasyon 100, tohum 121, 24 yaşam): ödül 0,39 → 0,45, temas-yok geç bloklarda 0,25–0,32 → 0,12–0,22 — yön tutarlı.

**TAHMİN-2: TUTTU** (tek geliştirme popülasyonunda; geliştirme tohumu). Yorum (sınırlı): kazanç hem yaklaşmadan (+0,18) hem seçicilikten geliyor; tersine çevirme sonrası ilk blokta düşüş (b5 0,46) K=1'deki (0,43) gibi kalıyor, yani hız–gürültü ödünleşiminin tersine çevirme bedeli ayrıca duruyor.

**Sınırlar:** tek popülasyon ve tek geliştirme tohumu; maliyet ≈K× (K=4 → yaklaşık 4×); "daha zeki" değil, daha az gürültülü okuma + kopya ortalamasıyla öğrenme gürültüsü azaltımı (R-9); kopyalar bağımsız öğrenir, ağırlık paylaşımı yok (paylaşılan ağırlıklı tasarım ayrı iş, GPU devri 3b). Doğrulayıcı için yeni ön-kayıt + yeni tohum + ≥4 popülasyon gerekir (§4).
