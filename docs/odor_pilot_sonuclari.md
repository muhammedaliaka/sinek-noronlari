# Dört koku oyunu: pilot (geliştirme) sonuçları

**Pilottur, kanıt değildir** (R-2): geliştirme ön-eğitimi tohum 100, oyun tohumları 101–103. Amaç, planın (`docs/dort_koku_oyunu_plani.md`) önceden
yazılmış seçim kurallarını uygulayıp parametreleri dondurmak ve araçları gerçek ağırlıklarla sınamaktır. Ham çıktılar `results/odor_pilot/`
(git'te yok); aşağıdaki sayılar oradan alınmıştır. Bu sayılar doğrulayıcı sonuç olarak **anılamaz**; doğrulayıcılar 200'lü tohumlarda,
oyun başına ön-kayıttan sonra koşulur.

Ortak ayar: 24 canlı × 8 deneme (4 ayna çifti), süre sınırı T=25 sn, kollar CRN eşli.

## 1. O1 (iz) — düz (O1a) ve tek dönüşlü (O1b), oyun tohumu 101

| kol | O1a p_hit | O1b p_hit |
|---|---|---|
| frozen (koku açık) | 0,510 [0,417; 0,604] | 0,484 [0,411; 0,557] |
| anosmik (glom ≡ 0) | 0,240 [0,182; 0,302] | 0,234 [0,177; 0,297] |
| random (dönüş kazancı 0) | 0,297 [0,219; 0,370] | 0,297 [0,219; 0,370] |
| referans (elle kurulmuş üst sınır) | 0,969 [0,948; 0,990] | 0,948 [0,911; 0,979] |

* frozen − anosmik: O1a **+0,271** [%99 GA +0,141; +0,396], O1b **+0,250** [+0,146; +0,365] (eşli, canlı-kümeli).
* random − anosmik: +0,057 [−0,068; +0,182] ve +0,062 [−0,057; +0,182] → anosmik canlı, yönelimsiz rastgele gezgin gibi davranıyor (beklenen).
* **Seçim kuralı (plan §3.1): referans `p_hit ≥ 0,80` ve anosmik ∈ [0,15; 0,45].** İkisi de sağlandı (0,97/0,95; 0,24/0,23) → **W=4, λ=12, A=1 varsayılanları donduruldu**, ayar gerekmedi.
* T=25 sn: kör gezgin hesabı (G2) ≈0,30; anosmik 0,24 ve random 0,30 ile uyumlu → süre sınırı tavan/taban etkisi yaratmıyor (frozen 0,51; referans 0,97; boşluk var).
* Ayna yarıları (özgün/ayna), frozen: O1a 0,510/0,510; O1b 0,521/0,448. Yön yanlılığı belirtisi yok; O1b'de fark gürültü düzeyinde (n küçük).
* **Sızıntı denetimi O1'de boştur:** iz çıkış noktasından başlar, her denemede alan ilk adımdan beri görülür (alan görülen deneme oranı 1,00) → "ilk koku alımına dek bit-bit aynı" denetlenecek deneme yok. O1 için denetim, kollar arası farkın yalnız koku girdisinden gelmesine dayanır (anosmik kolda glom ≡ 0, testli); bu bir sızıntı *kanıtı* değil, tasarım gereğidir.

## 2. O2-yakın (R=5, halka başlangıcı R+2), oyun tohumu 101

| kol | p_hit |
|---|---|
| frozen | 0,734 [0,667; 0,802] |
| anosmik | 0,417 [0,354; 0,484] |
| random | 0,354 [0,286; 0,422] |
| referans | 0,812 [0,750; 0,865] |

* frozen − anosmik: **+0,318** [+0,219; +0,417].
* Koku alanı görülen deneme oranı 0,87: %13 denemede canlı bölgeye hiç girmedi; bu denemelerde (25 deneme) frozen ve anosmik sonuçları **bit-bit aynı**, ihlal 0 (sızıntı denetimi geçti).
* **Kapı G1 (referans O2-yakın ≥ 0,80):** 0,812 → geçti, ama sınıra yakın (GA alt sınırı 0,75). Doğrulayıcıda kapı nokta tahminiyle uygulanır; bu yakınlık R=5'in çözülebilirliğin alt ucunda olduğunu gösterir. R=5 varsayılanı korunuyor (planın aday değeri, önceden yazılı); R∈{3, 8} taranmadı — kuralı sağlayan varsayılan zaten var, sonradan "daha iyi" R aramak ön-kayıt öncesi serbestlik derecesi eklerdi.
* Anosmik O2-yakın düzeyi (0,42) yüksek: halka başlangıcı hedefe yakın (7 birim) olduğu için kör gezgin de sık buluyor. Sonuç: etki, **tavandan değil kör düzeyden** ölçülür (frozen 0,73).

## 3. Sıfır-koku dönüş yanlılığı (Z-16, G3 tanısı), ön-eğitim tohumu 100

Anosmik kol, öğrenme kapalı, 24 canlı × 8 deneme, O1a yerleşimleri:
* canlı başına zaman-ortalamalı kontrast: havuz ortalaması −0,0002; |ortalama| 0,0013 (≈ 0,08 rad/s); |z| > 2,58 olan canlı oranı 0,04 (sıfır yanlılıkta ≈ 0,01; 24 canlıda 1 canlı).
* **Sonuç:** ön-eğitimli ağda pratik bir tek-yönlü dönüş yanlılığı yok. Bu ölçüm **öğrenme açıkken, oturum boyunca** tekrarlanmalı (hemisfere-özgü öğrenme sonrası yanlılık riski, plan Z-16) — O3 oturum koşusu bunu `plastic` kollarında ayrıca raporlar.

## 4. O2-tam (koku kaynağın tamamında; kör bölge girişi), oyun tohumu 101

| kol | p_hit |
|---|---|
| frozen | 0,510 |
| anosmik | 0,240 |
| random | 0,297 |
| referans | 0,724 |

* frozen − anosmik **+0,271** [%99 GA +0,198; +0,354]. Koku alanı görülen deneme oranı 0,65 (frozen) / 0,77 (referans): denemelerin ≈%35'inde canlı koku bölgesine hiç girmedi. Sızıntı denetimi: 68 deneme, ihlal 0.
* Referans 0,724 (<0,80): O2-tam **betimsel** oyundur; çözülebilirlik kapısı yalnız O2-yakın için uygulanır (plan §8, K-024). Bu bir bulgu olarak doğrulayıcıda da raporlanır.

## 5. O3 (koku yalnız temasta), oyun tohumu 102 — oturum pilotu (2 kopya × 16 deneme)

| kol | p_hit | ilk yarı | ikinci yarı |
|---|---|---|---|
| plastic:A (ödül+koku) | 0,272 | 0,263 | 0,281 |
| plastic:B (ödül, koku yok) | 0,247 | 0,240 | 0,255 |
| plastic:C (ödülsüz, koku var) | 0,273 | 0,258 | 0,289 |
| plastic:D (ikisi de yok) | 0,247 | 0,250 | 0,245 |
| frozen:A | 0,250 | 0,242 | 0,258 |

* Kör düzey ≈0,25 (T=25 sn); plastic − frozen farkları −0,003…+0,023, hepsinde %99 GA 0'ı kapsıyor → **kör düzeyde, öğrenme etkisi yok** (beklenen: bu canlıda konum belleği mekanizması yok).
* Kol ayrışması (CRN sağlığı; güç girdisi): 1. denemede 0, sonraki denemelerde %19-35 (K-025) → doğrulayıcı tasarımı 4 kopya (canlı başına 64 deneme).

## 6. O4a / O4c (sönüm; decoy), oyun tohumları 103-109 — oturum ve çekim pilotları

* **Çekim odası (frozen − anosmik decoy-ilk):** O4a +0,253 (tohum 104) ve +0,271 (108); O4c +0,268 (107) ve +0,260 (109). Birleşik ≈ +0,265 (≈1,8δ). Bu ölçüm plandaki geçici ≥2δ kapısını yanlış kılar → K-025 (kapı = manipülasyon denetimi, ≥δ).
* **O4a oturum pilotu (tohum 103; 12 bölüm × 2 kopya):** öğrenme kapalı anlık testte decoy-ilk oranı plastic 0,562 (bölüm 0) → 0,188 (3) → 0,271 (6) → 0,167 (12); frozen 0,562 → 0,542 → 0,562 → 0,500; anosmik 0,21-0,29. Plastic'in düşüşü gözlendi (sönüm benzeri); bu bir pilottur.
* **O4c oturum pilotu (tohum 106):** plastic decoy-ilk 0,500 → 0,188 → 0,167 → 0,208, gerçek-ilk 0,042 → 0,188 → 0,167 → 0,208 (anosmik gerçek-ilk 0,15-0,31: kör düzey). **Gözlem (hata aranacak):** plastic için bölüm 3, 6 ve 12'de decoy-ilk ve gerçek-ilk **sayıları birebir aynı** (9/9, 8/8, 10/10 / 48). Olay kümeleri ayrık (ortak eleman yok), yani kodda doğrudan özdeşlik yok; üç ardışık eşitliğin rastlantı olasılığı küçük (kabaca ≈10⁻³). Doğrulayıcı O4c (tohum 242/243) çıktılarında aynı örüntü yineleniyorsa slot atama / temas sırası kodu denetlenir (R-4); yinelenmiyorsa rastlantı sayılır ve burada kayıtlı kalır.
