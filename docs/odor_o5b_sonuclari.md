# O5b doğrulayıcısı — sonuçlar (ön-kayıt: `docs/odor_o5b_plani.md`, commit `288fc43`; koşular 2026-10-29/30)

**Ön-kayıtlı hükümler (`o5b_ozet`):**
* **A — seçicilik / öğrenme: BAŞARILI.** Kapı G dört popülasyonda tamam; N1 4/4, N2 4/4 (kural: N1 4/4 ∧ N2 ≥3/4).
* **B — topluluk (K=4, τ=0,04): BAŞARILI.** Kapı G tamam; E1 **3/4** (tohum 272'de geçmedi; kural: ≥3/4).

Ölçütler, eşikler, tohumlar ve kurallar koşudan önce dondurulmuştu ve değişmedi. Kod commit `288fc43` (ön-kayıt commit'i), ham veri `results/o5_val/b_s270…b_s273/` (git'te yok), özet `results/o5_val/ozet_o5b.md`. Dört yeni popülasyon: ön-eğitim 202–205, oyun tohumu 270–273; 48 yaşam/popülasyon, 8 parça.

## 1. Ön-kayıtlı sonuç tablosu (geç bloklar: bölüm 11–20 ve 31–40; %99 GA, eşli, yaşam birimli)

| tohum (pop.) | ödül: plastic_ens / plastic / frozen / referans | N1 net tercih `plastic − frozen` (≥0,10) | N2 faz-2 (>0) | E1 ödül `plastic_ens − plastic` (≥0,08) | E2 (betimsel) |
|---|---|---|---|---|---|
| 270 (202) | 0,482 / 0,380 / 0,304 / 0,765 | **+0,327** [+0,243; +0,409] ✔ | +0,317 [+0,179; +0,446] ✔ | +0,080 [+0,013; +0,150] p=0,0018 ✔ | +0,073 [−0,043; +0,186] ✘ |
| 271 (203) | 0,457 / 0,372 / 0,259 / 0,757 | +0,198 [+0,086; +0,310] ✔ | +0,171 [+0,025; +0,312] ✔ | +0,104 [+0,027; +0,185] ✔ | +0,138 [−0,001; +0,276] ✘ |
| 272 (204) | 0,431 / 0,375 / 0,197 / 0,744 | +0,201 [+0,103; +0,300] ✔ | +0,250 [+0,098; +0,398] ✔ | **+0,065 [+0,008; +0,123] ✘** (ortalama <δ_r) | +0,057 [−0,060; +0,176] ✘ |
| 273 (205) | 0,474 / 0,386 / 0,247 / 0,757 | +0,191 [+0,104; +0,274] ✔ | +0,133 [+0,008; +0,256] ✔ | +0,106 [+0,053; +0,160] ✔ | +0,100 [−0,015; +0,203] ✘ |

## 2. Dürüst okuma

**A (güçlü):** öğrenen beyin, iyi kokuyu kötüden **yaklaşma oranından bağımsız** ayırt ediyor ve tersine çevirmeden sonra yeniden öğreniyor — dört yeni popülasyonda. Net tercih farkı +0,19…+0,33 (eşik 0,10; güç analizinin öngördüğü gözlenen etki +0,20…+0,23). `frozen`ın temas oranı yine çok değişti (0,38–0,57); N ölçütleri bundan etkilenmedi (E-15 düzeltmesi işe yaradı).

**B (daha zayıf, dikkatle oku):**
* Ödül kazancı küçüldü: E1 = +0,080 / +0,104 / +0,065 / +0,106 (ortalama ≈ **+0,089**), geliştirme panellerinde +0,159 ve +0,111 görülmüştü ("kazananın laneti": ön-kayıt §7 sınır 1'de uyarılmıştı). Eşik δ_r = 0,08'e yakın; tohum 272 eşiğin altında kaldı, kural ≥3/4 olduğu için hüküm BAŞARILI. Dört popülasyonun hepsinde GA alt sınırı >0 (≥ +0,007).
* **Kazanç yaklaşmadan geliyor, seçicilikten değil** (post-hoc, `o5_posthoc`): `plastic_ens − plastic` temas farkı **+0,144 / +0,127 / +0,093 / +0,131**; temasta iyi koku seçme farkı yalnız **+0,007 / +0,058 / +0,020 / +0,039**; net tercih farkı (E2, betimsel) hiçbir popülasyonda ön-kayıtlı kuralı geçmedi (0/4). Yani topluluk kopyaları esas olarak okuma gürültüsünü azaltıp yaklaşmayı iyileştiriyor.
* Maliyet ≈4× hesap (K=4). Bu bir "daha zeki öğrenme kuralı" değil; aynı kural, daha az gürültülü okuma ve kopya ortalaması (R-9).

**Tersine çevirme bedeli (betimsel):** tersine çevirmeden sonraki ilk 5 bölümde iyi koku seçme oranı (b5) plastic: 0,46 / 0,32 / 0,55 / 0,39, plastic_ens: 0,39 / 0,32 / 0,41 / 0,45 (öğrenmesiz ≈0,5); 2.–3. blokta toparlanıyor (0,56–0,70). Topluluk tersine çevirme bedelini küçültmüyor.

**Hâlâ büyük boşluk:** referans ödül 0,74–0,77; plastic_ens 0,43–0,48; seçicilik 0,65–0,73 (referans 0,91–0,95), temas 0,81–0,86 (referans ≈1,0).

## 3. Sınırlar
* Dört popülasyon dört koku çiftidir; geniş genelleme iddiası yok. K yalnız 4, τ=0,04 (K-045'ten sabit); K'nın etkisi ve ağırlık paylaşımı ayrı iş.
* Ölçütler görülmüş veriden seçildi (O5 doğrulayıcı verisi 260/261 post-hoc ve geliştirme panelleri) — iyimserlik riski ön-kayıtta yazılıydı; E1'deki küçülme bunun izi olabilir.
* Elle yazılmış bileşenler (R-11): DAN hata kuralı, motor kuralı, referans kehanet-izleyici, ödül programı. "Öğrenme" bu elle yazılmış δ kuralının plastik W üzerindeki etkisidir.
* **Hız iddiası yok.** Hız–gürültü ödünleşimi (η ölçeği) bu doğrulayıcıda sınanmadı.
* Tohumlar 270–273 ve ön-eğitim 202–205 yandı (R-2).

## 4. Sonraki adım (öneri; ön-kayıtlı değil)
Boşluğun iki bileşeni belli: (1) *seçicilik* — topluluk onu artırmıyor; öğrenme kuralı/değer okuması tarafı (DAN hata terimi, plastisite ölçeği) çalışılmalı; (2) *tersine çevirme bedeli*. Zaman ölçeği mühendisliği kuramda ≤0,02 kazanç verdi (K-043). Adaylar: η ölçeği × K ızgarası (GPU), DAN sönüm yolu (PPL1), tersine çevirmeyi hızlandıran mekanizma için önce R-8 kuram kontrolü.
