# O5 — olasılıklı iki-kollu koku oyunu, oturum içi tersine çevirme (GELİŞTİRME TASLAĞI; ön-kayıt DEĞİL)

> Durum: pilot aşaması. Ölçüt ve eşikler henüz DONDURULMADI; doğrulayıcı koşular (tohum ≥200) bu belge "KESİNLEŞTİ" sürümüyle commit edilmeden başlamaz (R-1). Tüm rakamlar geliştirme tohumundandır (120), **kanıt değildir**.

## 1. Neden
`ogrenme_hizi` (K-040): mevcut beyin kolay protokolde tek denemede öğreniyor (tavan), yani "daha hızlı öğrenen" iddiası orada sınanamaz. Hız–gürültü ödünleşimini gösteren zor görev: **gürültülü (olasılıklı) ödül + oturum içi tersine çevirme** (iki-kollu kuşatma/bandit).

## 2. Tasarım (kod: `GAMES["O5"]`, `GameWorld.reward_p`, `play_sequence`, `bandit_schedule`, `o5_dev`)
* İki kaynak: koku A (yuva 0) ve koku B (yuva 1), rastgele konum (Gauss σ=8), arena 40×40. Her eleman bağımsız bir yaşam: **öğrenmemiş** beyin, ardışık 40 bölüm × 40 sn, ağırlıklar bölümler arasında korunur.
* İlk 20 bölümde (rol dengeli, `swap`) iyi koku p_hi=0,8, diğeri p_lo=0,2 olasılıkla ödüllü; bölüm 21'den itibaren roller TERSİNE.
* Temasta ödül = [u < p], u her bölüm başında CRN akışından önceden çekilir (kollar arasında aynı); herhangi bir kaynağın tüketimi bölümü bitirir. Ödülsüz temas → elle yazılmış δ negatif (sönüm).
* Kollar: `naive_plastic@s` (s = öğrenme oranı ölçeği), `naive@0` (öğrenmesiz; şans kontrolü).
* Ölçü: bloktaki ilk-temasların iyi kokuya oranı (temas olanlar arasında), temas-yok oranı, ödül oranı.

## 3. Önceden yazılmış tahmin (`o5_dev` docstring'i, koşudan önce)
Öğrenmesiz ≈0,5; η=1 tek denemede öğrenen "kazan-kal/kaybet-değiştir" gibi; küçük ölçek durağan fazda daha yüksek ama tersine çevirmede daha yavaş (gerçek hız–gürültü ödünleşimi).

## 4. Pilot bulgusu (geliştirme tohumu 120; 24 canlı × 2 kopya = 48 yaşam/kol; KANIT DEĞİL)
Hücre: iyi kokuyu seçme oranı (temas olanlar arasında) / temas-yok oranı.

| kol | b1 (1-5) | b2 (6-10) | b3 (11-15) | b4 (16-20) | **b5 (21-25, tersine çevirme sonrası)** | b6 (26-30) | b7 (31-35) | b8 (36-40) | ödül oranı |
|---|---|---|---|---|---|---|---|---|---|
| naive@0 (öğrenmesiz) | 0,39 / 0,52 | 0,46 / 0,52 | 0,43 / 0,59 | 0,43 / 0,57 | 0,52 / 0,57 | 0,52 / 0,57 | 0,44 / 0,63 | 0,52 / 0,50 | 0,21 |
| naive_plastic@1 | 0,46 / 0,45 | 0,67 / 0,41 | 0,65 / 0,32 | 0,63 / 0,30 | 0,43 / 0,40 | 0,60 / 0,34 | 0,67 / 0,31 | 0,68 / 0,25 | 0,36 |
| naive_plastic@0,3 | 0,50 / 0,47 | 0,61 / 0,35 | 0,61 / 0,30 | 0,68 / 0,29 | 0,27 / 0,33 | 0,51 / 0,31 | 0,53 / 0,28 | 0,62 / 0,26 | 0,36 |

Okuma (dürüst):
* **Öğrenme görünüyor:** plastik kollar ≈0,63–0,68 (şans 0,5; öğrenmesiz 0,39–0,52) ve ödül oranı 0,36 vs 0,21; temas-yok oranı 0,45 → 0,25-0,30 (kokuya yaklaşıyor).
* **Tersine çevirme bedeli ve ödünleşim görünüyor (tahmin tuttu):** η=1 tersine çevirmeden sonraki ilk blokta 0,43'e düşüp 2. blokta 0,60'a toparlanıyor; η=0,3 daha derin düşüyor (0,27: eski tercihte ısrar) ve yavaş toparlıyor (0,51, 0,53, 0,62). Durağan fazda η=0,3 biraz daha iyi (0,68 vs 0,63) — fark küçük (48 yaşam/kol; tek blok SE ≈0,05), **ayırt edilemez**.
* Mutlak başarı düşük: teorik kazan-kal/kaybet-değiştir dengesi (0,8) yerine ≈0,65; neden: yaklaşma kendisi gürültülü (temas-yok %25–45) ve değer okuma gürültüsü (K-028) burada da geçerli.
* Kol başına süre ≈50 dk (1 iş parçacığı, 48 yaşam × 40 bölüm).

## 5. Sonraki adımlar
1. Ham verinin kaydı (`o5_dev` şimdi yalnız blok özeti yazıyor) ve güç benzetimi için yaşamlar arası varyans tahmini.
2. Ölçüt taslağı: yaşam başına ödül sayısı (ikili/bölüm), geç faz-1 (11-20) ve geç faz-2 (31-40) bloklarında plastic − frozen ≥ δ; tersine çevirme bedeli betimsel. Güç benzetimi (R-6) ön-kayıttan önce.
3. Beyin değişkenlerinin karşılaştırılması için kıyas düzeneği (η ölçeği, K=8+τ=0,04, çok-zaman-ölçekli plastisite). Hipotez (SINANMADI): hızlı + yavaş plastisitenin birlikte olması ödünleşimi hafifletir.
