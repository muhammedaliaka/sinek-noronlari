# DAN hedefi (`reward_target`) ve öğrenme hızı (η) geliştirme taramaları — O5 (KANIT DEĞİLDİR; geliştirme tohumları <200)

Amaç: O5b sonrası (K-047) seçicilik (iyi kokuyu seçme ≈0,65; soyut öğrenici ≈0,9, referans ≈0,93) ve yaklaşma boşluğunu kapatacak bir **ucuz** kaldıraç bulmak. Araç: `python3 -I -m sinek.experiments.o5_dev` (kol belirtimi `<kol>@<η ölçeği>[/k<K>][/t<τ>][/r<reward_target>]`).
Her satır: 48 yaşam (24 canlı × 2 kopya), 40 bölüm × 40 sn, tersine çevirme bölüm 20; p 0,8/0,2; kollar aynı tohumda **eşli dünyalar** (CRN). Geç blok = bölüm 11–20 ve 31–40 (b3,b4,b7,b8 ortalaması). Hepsi tek koşu, güven aralığı YOK (o5_dev yalnız blok ortalaması yazar); betimsel.
Tahminler koşudan önce `o5_dev.py` docstring'inde commit edilmiştir (TAHMİN-3 `edd69f9`, TAHMİN-4 `5f66f60`, TAHMİN-5 sonraki commit).

## 1. η (öğrenme hızı) ölçeği taraması — tohum 134, popülasyon 102

| kol | geç seçicilik | geç temas-yok | b5 (tersine çevirme sonrası) | b6 | ödül/bölüm |
|---|---|---|---|---|---|
| η×1 (varsayılan) | 0,655 | 0,295 | 0,36 | 0,56 | 0,39 |
| η×2 | 0,660 | 0,372 | 0,52 | 0,62 | 0,37 |
| η×4 | 0,623 | 0,417 | 0,45 | 0,62 | 0,33 |
(tohum 120, pop. 100'de de η×0,3 ve η×1 geç seçiciliği ayırt edilemezdi.) **TAHMİN-3 tuttu**: η kaldıraç değil; η büyüdükçe temas AZALIYOR (yaklaşma kaybı), tersine çevirme sonrası ilk blok biraz toparlanıyor.

## 2. DAN hedefi T (`reward_target`, varsayılan 0,6) taraması — tohum 134, popülasyon 102

| kol | geç seçicilik | geç temas-yok | b5 | b6 | ödül/bölüm |
|---|---|---|---|---|---|
| T=0,4 | 0,627 | 0,367 | 0,41 | 0,50 | 0,34 |
| T=0,6 (varsayılan) | 0,655 | 0,295 | 0,36 | 0,56 | 0,39 |
| T=1,5 | 0,700 | 0,207 | 0,45 | 0,59 | 0,46 |
| T=2,5 | 0,715 | 0,165 | 0,44 | 0,67 | 0,48 |

Tek yönlü monoton doz–yanıt: T büyüdükçe seçicilik artıyor, temas-yok azalıyor, ödül artıyor (T=2,5: +0,09 — O5b'deki K=4 topluluğunun ortalama kazancı kadar, ama **1× hesap**). **TAHMİN-4 değerlendirmesi:** yön tuttu (T↓ bozar, T↑ iyileştirir); T=1,5 seçicilik kazancı +0,045 (eşik +0,05'in hemen altı); T=0,4 −0,028 (eşik −0,03'e yakın); **T=2,5 için "doygunluk/bozulma" tahmini YANLIŞ**: eğri düzleşiyor (+0,045 → +0,015) ama bozulmuyor.

### 2b. Yineleme — tohum 135, FARKLI popülasyon (100), aynı protokol (TAHMİN-5)

| kol | geç seçicilik | geç temas-yok | b5 | b6 | ödül/bölüm |
|---|---|---|---|---|---|
| T=0,6 (varsayılan) | 0,677 | 0,285 | 0,44 | 0,62 | 0,37 |
| T=2,5 | 0,713 | 0,182 | 0,41 | 0,65 | 0,44 |
| T=4 | 0,722 | 0,180 | 0,44 | 0,59 | 0,44 |

**TAHMİN-5 değerlendirmesi:** (a) T=2,5 − T=0,6: ödül +0,07 (eşik ≥ +0,05 ✔), seçicilik +0,036 (eşik ≥ +0,03 ✔), temas-yok −0,10 ✔ → **bulgu farklı popülasyonda yinelendi**. (b) T=4 ≈ T=2,5 (ödül farkı 0,00 ≤ 0,03 ✔; seçicilik +0,009; "hafif bozulma" seçeneği gerçekleşmedi) → **plato** T≈2,5. "Temas artmaya devam eder" tahminim kısmen yanlış: temas-yok 0,182 → 0,180 (düz). Betimsel, iki popülasyon, her biri 48 yaşam; güven aralığı yok.

## 3. Post-hoc yorum (hükmü etkilemez; mekanizma VARSAYIMI, sınanmadı)
`δ = kapı·(T·ödül − V)`: ödüllü temasta itme `T − V` (büyük), ödülsüz temasta `−V` (T'den bağımsız). T büyütmek ödülün ağırlığını sönüm itmesine göre artırır; η büyütmek ikisini birden. O5'te iyi kokuda bile temasların %20'si ödülsüz olduğundan sönüm itmesi çoğunlukla **gürültüdür** → η büyürse yaklaşma kaybolur, T büyürse yaklaşma ve seçicilik artar. Bu açıklama tutarlı ama doğrudan sınanmadı (örn. kapalı-form kuram + δ'nın ödüllü/ödülsüz ayrımı ölçümü gerekir).

## 4. Yapılacak / bekleyen (sıra önemli)
1. **Yineleme (TAHMİN-5, tohum 135, FARKLI popülasyon 100)**: `@1`, `@1/r2,5`, `@1/r4` — koşuyor. Tutmazsa T bulgusu popülasyona özgü sayılır.
2. **Gerileme kontrolü (TAHMİN-6, koşudan önce)**: sönüm (O4a) T'den etkilenmemeli; ödülsüz decoy temasında `δ = −V`, T'den bağımsız. Tahmin: `plastic` (T=2,5) − `plastic` (T=0,6) decoy-ilk oranı farkı |Δ| ≤ 0,05 ve frozen'a göre azalma korunur (≈0,30). Bozulursa T global varsayılan OLAMAZ, yalnız oyuna özgü ayar kalır.
3. T hem O5'te hem sönümde sağlamsa: yeni **O5c** ön-kayıt (yeni tohum/popülasyon, ≥4 popülasyon) — T yükseltilmiş `plastic` vs varsayılan `plastic` (+ isteğe K=4); kural/güç R-6 ile.

## 5. Elle yazılmış bileşenler (R-11)
`reward_target` bir DAN-hedef sabitidir (elle seçilmiş); DAN hata kuralı `δ = kapı·(T·ödül − V)`, motor kuralı (normalize kontrast), ödül programı ve referans karşılaştırıcı elle yazılmıştır. "T yükseltmek" öğrenilmiş bir şey değil, elle ayarlanan bir sabittir; ayarın 4 popülasyonda doğrulanması gerekir.
