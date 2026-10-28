# Evre 2b güç analizi

Üretici: `python -m sinek.experiments.power2b --sims 1000` (senaryo tablosu) ve `python -m sinek.experiments.power2b --design --sims 1000` (tasarım ızgarası).
Benzetim, gerçek karar kodunu (`evre2b.evaluate2`) sentetik seçim sayılarıyla çalıştırır; tüm sayılar **ölçüt başına geçme olasılığıdır** (1000 benzetim, tohum 0).
Model: canlıya özgü rol tercihi ~ Beta(μκ, (1−μ)κ) (κ küçük = canlılar arası değişkenlik büyük), canlı başına binom denemeler, rol dengelemesi ve eğitimsiz
koku-0 yanlılığı 0,10 (dengeleme ile sönümlenir). Parametreler geliştirme gözlemlerinden gelir; ölçülmüş "doğru" değerler değildir.
**Sınırlama:** benzetimde eğitimsiz `plastic` ve `frozen` bağımsız çekilir (gerçekte aynı ağ); `frozen`/`random` gruplarının aşamalar arası bağımlılığı modellenmemiştir.
Bu yüzden değerler tam bir güç tahmini değil, karar kuralının duyarlılığı ve yanlış-pozitif davranışı için bir göstergedir.

## 1. Senaryolar (24 canlı × 8 deneme, κ = 6 aksi belirtilmedikçe)

| senaryo | G | A1 | A2 | A3 | B1 | B2 | **hepsi** |
|---|---:|---:|---:|---:|---:|---:|---:|
| sıfır (öğrenme yok) | 1.00 | 0.02 | 0.00 | 1.00 | 0.01 | 0.03 | **0.00** |
| güçlü (v1 benzeri: 0,90 → 0,15) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** |
| orta (0,80 → 0,30) | 1.00 | 1.00 | 0.90 | 1.00 | 1.00 | 0.94 | **0.85** |
| zayıf (0,70 → 0,40) | 1.00 | 0.97 | 0.41 | 1.00 | 0.94 | 0.47 | **0.19** |
| güçlü, canlılar arası değişkenlik yüksek (κ=2) | 1.00 | 1.00 | 0.98 | 0.96 | 1.00 | 1.00 | **0.95** |
| güçlü, eğitimsiz seçim oranı düşük (0,30; G kapısı) | 0.00 | 1.00 | 0.00 | 0.00 | 1.00 | 1.00 | **0.00** |
| Evre 2 v1 tasarımı benzeri (16 canlı, 4 deneme, rol dengelemesi yok, eğitimsiz seçim 0,15), güçlü | 0.00 | 1.00 | 0.00 | 0.00 | 1.00 | 0.96 | **0.00** |

Okuma: öğrenme **yokken** tüm ölçütleri geçme olasılığı 0,00 (karar kuralı yanlış-pozitif üretmiyor). Güçlü etkide 1,00, orta etkide 0,85, zayıf etkide (0,70 → 0,40) yalnız 0,19.
Evre 2 v1'in tasarımı (16 canlı × 4 deneme, rol dengelemesi yok, eğitimsiz seçim oranı 0,15) G kapısında zaten elenir: v1 tasarımı bu ölçütlerle de geçemezdi.

## 2. Tasarım ızgarası (geliştirme pilotlarına benzeyen etkiler)

Pilotlarda canlılar arası aşırı yayılım gözlenmedi (gözlenen/iki terimli varyans oranı 0,4–1,5, ortalama ≈ 0,8), bu yüzden κ çok büyük (10⁶) alındı;
seçim oranları pilotlardan: eğitimsiz 0,55, A12 0,88, B 0,80, random 0,65.

| eğitilmiş → tersine | tasarım (canlı × deneme) | G | A1 | A2 | A3 | B1 | B2 | **hepsi** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0.76 → 0.36 | 24 × 8 | 1.00 | 1.00 | 0.98 | 1.00 | 1.00 | 0.92 | **0.89** |
| 0.76 → 0.36 | 36 × 8 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.98 | **0.98** |
| 0.76 → 0.36 | 48 × 8 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** |
| 0.76 → 0.36 | 24 × 16 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** |
| 0.76 → 0.36 | 36 × 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** |
| 0.72 → 0.40 | 24 × 8 | 1.00 | 1.00 | 0.87 | 1.00 | 1.00 | 0.69 | **0.59** |
| 0.72 → 0.40 | 36 × 8 | 1.00 | 1.00 | 0.97 | 1.00 | 1.00 | 0.85 | **0.83** |
| 0.72 → 0.40 | 48 × 8 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.94 | **0.94** |
| 0.72 → 0.40 | 24 × 16 | 1.00 | 1.00 | 0.99 | 1.00 | 1.00 | 0.94 | **0.94** |
| 0.72 → 0.40 | 36 × 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.96 | **0.96** |
| 0.68 → 0.42 | 24 × 8 | 1.00 | 1.00 | 0.62 | 1.00 | 0.98 | 0.54 | **0.34** |
| 0.68 → 0.42 | 36 × 8 | 1.00 | 1.00 | 0.85 | 1.00 | 1.00 | 0.66 | **0.56** |
| 0.68 → 0.42 | 48 × 8 | 1.00 | 1.00 | 0.95 | 1.00 | 1.00 | 0.80 | **0.76** |
| 0.68 → 0.42 | 24 × 16 | 1.00 | 1.00 | 0.95 | 1.00 | 1.00 | 0.82 | **0.77** |
| 0.68 → 0.42 | 36 × 12 | 1.00 | 1.00 | 0.97 | 1.00 | 1.00 | 0.85 | **0.82** |

Okuma: pilot-benzeri etkide (0,72 → 0,40) **24 × 8 tasarımı yalnız %59** güce sahiptir (zayıf halka B2: tersine çevirmede GA üst sınırı < 0,5 ve A2). **24 × 16 tasarımı %94**
(36 × 12 %96, 48 × 8 %94). Hesap bakımından en ucuz olan 24 × 16 seçilmiştir (eğitim maliyeti canlı sayısıyla, test maliyeti canlı × deneme ile artar).
Daha zayıf etkide (0,68 → 0,42) bile 24 × 16 ≈ %77. Etki büyüklüğü bilinmediğinden bu analiz **garanti değil**; başarısızlık da raporlanacaktır.
