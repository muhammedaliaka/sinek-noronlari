# Ölçek ekseni doğrulayıcısı — sonuçlar (ön-kayıt: `docs/olcek_plani.md`, K-036/K-037)

Dört doğrulayıcı koşu (O1a 250/251, O1b 252/253; ön-eğitim popülasyonları 200/201; 24 canlı × 16 deneme × 25 sn; K=8, τ_valence=0,04; öğrenme kapalı) **ön-kayıtlı kuralla** değerlendirildi. Ölçüt, eşik, K, τ ve tohumlar koşudan sonra değişmedi. Özet tabloyu `python3 -I -m sinek.experiments.olcek_ozet` üretir.

## Sonuç: ölçek iddiası BAŞARILI (O1a ve O1b, iki popülasyonda)

| oyun | tohum | referans | anosmik | frozen (taban) | anosmic_ens | **ens** | P1 ens−frozen [%99 GA] | P2 ens−anosmic_ens [%99 GA] | P3 (betimsel) | karar |
|---|---|---|---|---|---|---|---|---|---|---|
| O1a | 250 | 0,990 | 0,247 | 0,497 | 0,307 | **0,820** | +0,323 [+0,247; +0,396] ✔ | +0,513 [+0,438; +0,578] ✔ | +0,060 [−0,003; +0,130] ±δ_eq dışında | BAŞARILI |
| O1a | 251 | 0,990 | 0,240 | 0,518 | 0,299 | **0,781** | +0,263 [+0,174; +0,339] ✔ | +0,482 [+0,359; +0,594] ✔ | +0,060 [−0,008; +0,130] dışında | BAŞARILI |
| O1b | 252 | 0,953 | 0,219 | 0,453 | 0,289 | **0,703** | +0,250 [+0,177; +0,326] ✔ | +0,414 [+0,302; +0,510] ✔ | +0,070 [−0,010; +0,151] dışında | BAŞARILI |
| O1b | 253 | 0,971 | 0,286 | 0,479 | 0,266 | **0,745** | +0,266 [+0,195; +0,339] ✔ | +0,479 [+0,354; +0,594] ✔ | −0,021 [−0,089; +0,047] ±δ_eq içinde | BAŞARILI |

* Kapılar (referans ≥0,80, anosmik pencere 0,15–0,45, sızıntı ihlali 0) dört koşuda tamam. Tüm P1/P2 için p = 0,0001 (10 000 işaret-çevirme; ulaşılabilir en küçük p), %99 GA alt sınırı > 0, ortalama fark ≥ δ = 0,15.
* Güç benzetiminin öngördüğü etki 1,5–2δ idi (güç 0,93–0,99); gözlenen P1 etkisi 1,7–2,2δ (+0,25 … +0,32).
* **Sızıntı kapısı bu oyunda içi boştur:** koku ilk adımdan itibaren alındığı için "koku hiç alınmayan deneme" yok (denetlenen 0); önceki O1 doğrulayıcılarında da aynıydı. Kapı yanlış geçmez ama bir şey de ölçmez.
* **İlk çalışmada yürütme düzeni değişti** (K-037): canlılar 4 parçaya bölündü; ölçüt ve tasarım aynı. İlk (parçasız) denemede görülen referans/anosmik değerleri karara girmedi.

## Ne söylenebilir, ne söylenemez

Söylenebilir:
1. O1 (iz sürme) oyunlarında ölçülen başarı, **test anı okuma gürültüsüyle sınırlıydı**: ağırlıklar değişmeden (öğrenme kapalı) K=8 gürültü örneği ortalaması + kısa entegrasyon süresi frozen p_hit'i 0,45–0,52'den 0,70–0,82'ye çıkardı; geliştirme tohumlarındaki bulgu ön-kayıtlı doğrulayıcıda iki ayrı popülasyonda yinelendi (K ve τ yalnız popülasyon 100'de seçilmişti).
2. Kazanç **kokudan geliyor**, yalnız kör düzeyin kaymasından değil: eşleşmiş kör kola göre koku avantajı taban beyinde +0,19 … +0,28 (frozen−anosmik) iken topluluk beyninde +0,41 … +0,51 (P2).

Söylenemez / dikkat:
1. **Referansa ulaşılmadı:** ens 0,70–0,82, referans 0,95–0,99 (boşluk 0,17–0,29). O1b'de geliştirmedeki 0,79 doğrulayıcıda 0,70/0,75 çıktı (geliştirme tek örneklemdi; doğrulayıcı daha düşük).
2. **Betimsel P3: kör düzey topluluk altında hafifçe yükseldi** (üç koşuda +0,06…+0,07; GA'lar sıfırı kapsıyor ama ±0,10 eşdeğerliği kanıtlanmadı). P1'in tamamı koku kazancı sayılamaz; ancak (post-hoc, hükmü değiştirmez) P1'den bu kayma çıkarılsa bile fark dört koşuda da ≥0,18 kalır (0,26; 0,20; 0,18; 0,29) ve ölçüt P2 zaten kayma-bağışıktır.
3. Bu bir **"daha zeki beyin" kanıtı değildir** (R-9): ağırlıklar aynı, değişen yalnızca okumanın gürültüsü; maliyet adım başına ≈K=8 kat (ens kolu ≈6× süre: tek kolda ≈55 dk, frozen ≈9 dk, 1 iş parçacığı). "Öğrenme hızı" burada ölçülmedi (öğrenme kapalı).
4. Yalnız O1 (iz sürme) oyunlarına özgü; O2-yakın tavan etkisi nedeniyle kapsam dışı bırakıldı (K-036), O2-tam/O3/O4 ölçek eksenini sınamaz.
5. Elle yazılmış bileşenler değişmedi (DAN hata terimi, referans karşılaştırıcı); eğitim–test uyumsuzluğu (K=1 ile eğitilip K=8 ile okuma) çalışıyor ama topluluğu eğitimde kullanmanın ek kazanç verip vermediği sınanmadı.

## Sonraki adımlar (kuram: `evre3_dan_plani.md` §6.3)
Kalan boşluk okuma gürültüsü değil (ens ≈ gürültüsüz tablo 0,82). Sıra: (H1) ön-eğitim bölüm sayısı/η ile gürültüsüz tablonun değişimi = ilk gerçek **öğrenme hızı** ölçümü; (H2) motor kuralı (ε, turn_gain); (H3) sensör sınırı. Bunlar geliştirme tohumlarında (100–149) yapılır; doğrulayıcıya girecek her ayar yeni ön-kayıt ve güç benzetimi ister. GPU aşamasında: paylaşılan-ağırlık plastik topluluk (tek W, K gürültü örneği) ve K ∈ {32, 64}.
