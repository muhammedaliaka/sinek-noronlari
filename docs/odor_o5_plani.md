# O5 — olasılıklı iki-kollu koku oyunu, oturum içi tersine çevirme — ÖN-KAYIT (KESİNLEŞTİ)

> Bu belge doğrulayıcı koşulardan **önce** commit edilir (R-1). Aşağıdaki ölçütler, eşikler, kollar, tohumlar ve karar kuralı koşudan sonra değişmez; başarısızlık olduğu gibi raporlanır (R-3). Koşudan sonra yazılan her açıklama "post-hoc" diye etiketlenir ve hükmü değiştirmez. Dil: Türkçe, dürüst raporlama.
> Tarih: 2026-10-29. Geliştirme tohumu 120 pilotu (§9) ve güç benzetimi (§7) bu belgeden önce yapıldı; doğrulayıcı tohumlara (260, 261) hiç dokunulmadı.

## 1. Soru ve neden

`ogrenme_hizi` (K-040): mevcut beyin kolay protokolde tek denemede öğreniyor (tavan etkisi); "daha hızlı öğrenen" iddiası orada sınanamaz. O5 daha zor bir görev kurar: **gürültülü (olasılıklı) ödül + oturum içi tersine çevirme** (iki-kollu kuşatma / bandit).

**Bu ön-kaydın sorusu (dar):** öğrenmemiş MaleCNS mantar-cismi beyni, ödül olasılığı %80/%20 olan iki kokulu kaynak arasında, (a) tersine çevirmeden önce ve (b) tersine çevirmeden sonra, öğrenmesi kapalı aynı beynden **belirgin biçimde daha çok ödül topluyor mu**, ve bu üstünlük *iyi kokuyu kötüden ayırmaktan* mı geliyor (yoksa yalnız "her kokuya yaklaşmaktan" mı)?

Bu ön-kayıt bir **hız** iddiası içermez ve beyin varyantlarını (η ölçeği, K, τ, çok-zaman-ölçekli plastisite) karşılaştırmaz; o karşılaştırmalar geliştirme aracı olarak kalır (`o5_dev`). Bu koşu, O5'i ileride varyant karşılaştırmasında kullanılabilecek **doğrulanmış bir zemin** yapmak içindir.

## 2. Tasarım (kod: `GAMES["O5"]`, `GameWorld.reward_p`, `play_sequence`, `bandit_schedule`, `odor_validate_o5`)

| öğe | değer |
|---|---|
| dünya | 40×40 arena; iki Gauss kaynak (σ=8): koku A (yuva 0), koku B (yuva 1); rastgele konum, birbirinden ve başlangıçtan ≥14 |
| ödül | temasta ödül = [u < p(yuva)], u her bölüm başında CRN akışından çekilir (kollar arasında AYNI); herhangi bir kaynağın tüketimi bölümü bitirir; ilk temas sayılır |
| olasılıklar | iyi koku p_hi = **0,8**, kötü koku p_lo = **0,2** |
| tersine çevirme | bölüm 1–20 (faz 1) iyi koku X; bölüm 21–40 (faz 2) iyi koku diğeri; hangi kokunun ilk iyi olduğu canlılar arasında dengeli (`world.swap`) |
| yaşam | bir canlı × 40 bölüm × 40 sn, **öğrenmemiş** beyin, ağırlıklar bölümler arasında korunur (plastic kolunda) |
| birim | **yaşam** (canlı × kopya); 24 canlı × 2 kopya = **48 yaşam / tohum** |
| parçalama | 4 parça × 12 yaşam; parça c'nin dünya tohumu = oyun tohumu + 1000·c (tüm kollarda AYNI); kol × parça kontrol noktası (K-037 deseni) |
| popülasyon | ön-eğitim dosyaları `results/odor_val/pre_s200.npz` (tohum 260), `pre_s201.npz` (tohum 261); yalnız rol dengelemesi/yapılandırma için, naive kollar öğrenmemiştir |
| doğrulayıcı tohumları | **260** (pop 200), **261** (pop 201) — yeni, kayıtlı (karar_defteri K-042) |

## 3. Kollar (CRN eşli: aynı canlı, aynı dünya, aynı ödül çekimleri)

| kol | beyin | öğrenme |
|---|---|---|
| `plastic` | `naive_plastic` (öğrenmemiş MaleCNS beyni, DAN kuralı elle yazılmış), öğrenme oranı ölçeği 1,0 | AÇIK |
| `frozen` | `naive` (aynı öğrenmemiş beyin) | KAPALI (şans kontrolü) |
| `reference` | elle kurulmuş, öğrenmesiz izleyici; her bölümde hangi kokunun iyi olduğunu **bilir** (tersine çevirmede takip ettiği kokuyu da değiştirir: `world.swap` ters çevrilir) | — |

`reference` bir rakip değil, **çözülebilirlik kapısıdır** (üst sınır ≈0,8 × temas oranı). Sızıntı: ödül olasılığı `reward_p` kodda yalnız dünyadaki ödül çekiminde kullanılır (`games/world.py`); `plastic` ve `frozen` beyinlerinin girdisi yalnız koku ve temasta gelen ödüldür (kod taraması, 2026-10-29).

## 4. Ölçütler (karar veren) — her doğrulayıcı tohum için

Bloklar (0-tabanlı yarı açık): **geç faz-1 = bölüm 11–20**, **geç faz-2 = bölüm 31–40** (öğrenmenin oturması ve tersine çevirmeden sonra yeniden öğrenmenin tamamlanması için ilk yarıları dışarıda bırakır). Yaşam başına blok ödülü = bloktaki ödüllü bölüm sayısı (bölüm başına 0/1).

* **Kapı G (referans):** `reference` ödül oranı (iki geç blok birlikte) ≥ **0,60**. Başarısızsa tohum geçersiz (kapı eksik), ölçütler yine de raporlanır.
* **P1 (geç faz-1 üstünlüğü):** `plastic − frozen` ödül oranı farkı ≥ **δ = 0,10** ödül/bölüm **ve** eşli küme (yaşam) bootstrap %99 GA alt sınırı > 0 **ve** eşli işaret-çevirme p < **α = 0,01**.
* **P2 (geç faz-2 üstünlüğü):** aynı kural, geç faz-2 bloğu.
* **P3 (özgüllük):** bölüm başına net tercih skoru (+1 iyi koku ilk temas, −1 kötü koku ilk temas, 0 temas yok), iki geç blok birlikte; `plastic − frozen` yaşam başına toplam farkı için eşli işaret-çevirme p < α **ve** %99 GA alt sınırı > 0 (asgari etki büyüklüğü istenmez). Amaç: üstünlüğün koku-ödül ayrımından geldiğini göstermek; yalnız "her kokuya yaklaş" ödül oranını artırabilir ama net tercihi artıramaz.

Bootstrap/permütasyon: 10 000 yeniden örnekleme; tohumlar P1=7, P2=8, P3=9 (`eval_o5`).

## 5. Karar kuralı

* **Tohum başarılıdır** ⇔ G, P1, P2, P3 hepsi sağlanır.
* **O5 doğrulayıcısı başarılıdır** ⇔ **iki tohum (260 ve 261) da** başarılıdır. Biri geçip diğeri geçmezse sonuç "kısmi / başarısız" diye aynen raporlanır ve iddia yapılmaz.
* Tohumlar tek kullanımlıktır (R-2): başarısızlık, yeni tohumla "kurtarılmaz"; yeni bir deneme yeni ön-kayıt + yeni tohum ister.
* Betimsel (karar vermez; raporlanır): blok (5 bölüm) başına iyi-kokuyu-seçme oranı (temas olanlar arasında), temas-yok oranı, ödül oranı, **tersine çevirme bedeli** (bölüm 16–20 ile 21–25 arasındaki düşüş), kol başına toplam ödül oranı.

## 6. Elle yazılmış bileşenler (R-11) ve sınırlar

* DAN (dopamin) hata kuralı `last_delta = gate·(reward_target·reward − valence)` elle yazılmıştır; ödül-olasılığını *kendi başına* tahmin etmez, yalnız o anki ödül/değer farkına tepki verir. "Öğrenme" bu kuralın plastik W üzerindeki etkisidir.
* Motor kuralı (turn_gain 60, contrast_eps 2,0, wander_σ 1) elle yazılmıştır, tüm kollarda aynıdır.
* `reference` elle kurulmuş bir kehanet-izleyicidir; bir beyin değildir.
* Ödül programı (0,8/0,2, tek tersine çevirme, bölüm 21) elle seçilmiştir; pilot tek tohumdan.
* Öğrenmemiş beyin ve çok kısa yaşam (40 bölüm): bu, "hızlı öğrenen" kanıtı değil, "ödüle göre davranışını değiştiren" kanıtı olacaktır (başarılı olursa).

## 7. Güç ve yanlış-pozitif benzetimi (R-6)

Gerçek değerlendirici (`eval_o5`) ile, 48 yaşam / tohum, 300 benzetim / senaryo (`results/power_o5.md`; `power_odor.py` senaryoları). Girdiler tek geliştirme pilotundan (tohum 120; §9): `plastic` blok başına (temas, iyi seçme) = (0,55;0,55) (0,70;0,65) (0,60;0,40) (0,72;0,67); `frozen` (0,47;0,48); `reference` (0,97;0,97); yaşam arası beceri sapması sd = 0,08 (**varsayım**, pilotta ham veri yoktu).

| senaryo | hepsi geçti | P1 / P2 / P3 geçme |
|---|---|---|
| sıfır etki (plastic = frozen) | **0,00** | 0,00 / 0,00 / 0,02 |
| pilot etkisinin yarısı | **0,16** | 0,34 / 0,46 / 0,57 |
| pilot etkisi (beklenen) | **0,99** | 1,00 / 1,00 / 1,00 |
| yalnız faz-1 öğreniyor (P2 başarısız olmalı) | 0,00 | 0,99 / 0,00 / 0,69 |
| yalnız yaklaşma, iyi/kötü ayrımı yok (P3 başarısız olmalı) | 0,00 | 0,63 / 0,75 / 0,00 |
| referans düşük (kapı başarısız olmalı) | 0,00 (kapılar 0,00) | 0,99 / 1,00 / 1,00 |

Ek (kod incelemesinde, ölçütten bağımsız, `tests/test_odor_validate_o5.py`): yalnız-yaklaşma senaryosu 400 ek benzetimde 3 kez geçti (≈%0,75); üçü de P3'ün kendi yanlış-pozitifiydi (nominal α = 0,01 ile uyumlu) — ölçüt "sıfır yanlış-pozitif" vaat etmez.

**Dürüst sınırlar:**
1. Güç benzetimi girdileri O5'i geliştirirken **etki görülen** tek pilottan geldi; etki büyüklüğü iyimser olabilir ("kazananın laneti"). **Pilot etkisinin yarısında güç yalnız 0,16'dır:** gerçek etki küçükse bu doğrulayıcı büyük olasılıkla BAŞARISIZ olur ve başarısızlık "etki yok" demek **değildir**.
2. Yaşam arası varyans varsayımdır; gerçek varyans büyükse güç düşer.
3. Sıfır etki ve artefakt senaryoları ölçütün yanlış kabul oranını düşük gösteriyor; ama benzetim, CRN eşleşmesinin ve dünya yapısının yarattığı yapısal ilişkileri modellemez (kollar bağımsız varsayıldı → muhafazakâr).

## 8. Komutlar ve işletim

```
scripts/run_o5_validators.sh [işçi_sayısı]        # varsayılan 4; yeniden başlatmaya dayanıklı; çıktı results/o5_val/s260, s261
# elle: python3 -I -m sinek.experiments.odor_validate_o5 --pre results/odor_val/pre_s200.npz --seed 260 --threads 1 --out results/o5_val/s260
```

Kuyruk önce kol × tohum işçilerini (`--only-arms`, yalnız kontrol noktası yazar), sonra tohum başına değerlendirmeyi çalıştırır. Beklenen süre: plastic/frozen için kol × tohum başına ≈1–1,5 saat (1 iş parçacığı), reference birkaç dakika. `--pilot` geliştirme tohumlarıyla (<200) sınırlıdır; doğrulayıcı tohumlarda yasaktır (kod koruması).

## 9. Geliştirme geçmişi (kanıt değildir; tohum 120; 48 yaşam / kol)

`o5_dev` pilotu, bölüm başına blok (5 bölüm) iyi-kokuyu-seçme oranı / temas-yok oranı:

| kol | b1 | b2 | b3 | b4 | **b5 (21-25, tersine çevirme sonrası)** | b6 | b7 | b8 | ödül oranı |
|---|---|---|---|---|---|---|---|---|---|
| naive@0 (öğrenmesiz) | 0,39 / 0,52 | 0,46 / 0,52 | 0,43 / 0,59 | 0,43 / 0,57 | 0,52 / 0,57 | 0,52 / 0,57 | 0,44 / 0,63 | 0,52 / 0,50 | 0,21 |
| naive_plastic@1 | 0,46 / 0,45 | 0,67 / 0,41 | 0,65 / 0,32 | 0,63 / 0,30 | 0,43 / 0,40 | 0,60 / 0,34 | 0,67 / 0,31 | 0,68 / 0,25 | 0,36 |
| naive_plastic@0,3 | 0,50 / 0,47 | 0,61 / 0,35 | 0,61 / 0,30 | 0,68 / 0,29 | 0,27 / 0,33 | 0,51 / 0,31 | 0,53 / 0,28 | 0,62 / 0,26 | 0,36 |

Okuma: plastik kollar ≈0,63–0,68 (öğrenmesiz 0,39–0,52), ödül oranı 0,36 vs 0,21; tersine çevirme sonrası η=1 hemen düşüp 2. blokta toparlıyor, η=0,3 daha derin düşüp daha yavaş toparlıyor (hız–gürültü ödünleşimi, K-041). Mutlak başarı düşük (≈0,65; teorik "kazan-kal/kaybet-değiştir" ≈0,8): temas-yok %25–45, değer okuma gürültüsü (K-028).

Duman koşusu (`results/o5_val/smoke_s130`, geliştirme tohumu 130, 16 yaşam × 8 bölüm): yalnız hattın uçtan uca çalıştığını gösterir (kontrol noktası → birleştirme → değerlendirici → rapor); referans ödül oranı 0,73–0,75 (kapı 0,60 ✔); ölçüt sonuçları 16 yaşamla anlamsızdır, **kanıt değildir**.
