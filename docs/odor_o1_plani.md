# O1 — kesintisiz koku izi: ÖN-KAYIT (doğrulayıcı koşulardan önce)

Bağlayıcı üst belge: `docs/dort_koku_oyunu_plani.md` (§2 sözleşmeler, §3.1, §5). Güç: `docs/odor_guc_analizi.md`. Pilot: `docs/odor_pilot_sonuclari.md` (K-023).
Bu belge **commit edilmeden doğrulayıcı koşu (tohum ≥200) başlamaz**; ölçütler koşudan sonra değişmez; başarısızlık raporlanır.

## 1. Soru ve dürüst cümle

*Ön-eğitimli, öğrenmesi kapalı bir canlı, kokuyla işaretli sürekli bir izi hedefe kadar, aynı canlının koku girdisi sıfırlanmış hâlinden ve yönelimsiz rastgele
gezginden daha sık bulur mu?* Evet ise yazılacak cümle: **"Bu canlı, hedefe uzanan sürekli bir koku izini izleyebiliyor (iz boyunca sol–sağ karşılaştırma yeterli);"**
hayır ise: **"Bu canlı, bu iz üzerinde kokudan fayda sağlamadı."** Zeka/planlama iddiası yoktur.

## 2. Tasarım (donduruldu)

* **Oyunlar:** O1a (düz iz) ve O1b (tek dönüşlü iz, dönüm sapması h=8, işaret ayna çiftiyle). İz tüpü `C = A·(1−(n/W)²)³₊·exp(−s_kalan/λ)`, **W=4, λ=12, A=1** (pilotta kuralı sağladı, K-023).
  Süre sınırı **T=25 sn** (kör ≈0,30). Arena 40×40, temas 1,5, hız 8, hareket okuması `V2_SET` donmuş (ε=2,0, kazanç 60). O1b'nin O1a'dan ayrı bir iddiası vardır; ikisi ayrı karar verir.
* **Canlılar:** iki bağımsız popülasyon: ön-eğitim tohumları **200** ve **201**, her biri 24 canlı (`python3 -I -m sinek.experiments.odor_pretrain --seed S --agents 24 --episodes 12 --episode-seconds 60 --calib-candidates 40 --out results/odor_val/pre_sS.npz`; koku çifti yalnız eğitimsiz ağdan seçilir). Aynı iki dosya O2, O3 ve O4 doğrulayıcılarında da kullanılır (ön-eğitim oyun sonucunu görmez).
* **Oyun tohumları (yerleşim/gürültü):** O1a: **210** (pop. 200), **211** (pop. 201); O1b: **212** (pop. 200), **213** (pop. 201). 30, 31 ve 100–149 kullanılmaz.
* **Deneme:** canlı başına **16 deneme** (8 ayna çifti), test kipi (ilk temas sonlandırır), öğrenme **kapalı**. Kollar CRN eşli: `frozen` (koku açık), `anosmic` (glom ≡ 0), `random` (dönüş kazancı 0), `reference` (elle kurulmuş üst sınır; V=0,15·Σ ödüllü koku glom).
* **Komut:** `python3 -I -m sinek.experiments.odor_validate --pre results/odor_val/pre_s{200|201}.npz --game {O1a|O1b} --seed {tohum} --out results/odor_val/{oyun}_s{tohum}`
  (varsayılanlar bu belgedekilerdir: 24 canlı, 16 deneme, T=25, δ=0,15, referans ≥0,80, 10 000 bootstrap/permütasyon).

## 3. Kapılar (geçerlilik — başarısız olursa karar "DEĞERLENDİRİLEMEZ", beyin başarısızlığı sayılmaz)

* K1 referans `p_hit ≥ 0,80`. K2 anosmik `p_hit ∈ [0,15; 0,45]` (kör düzey tavana/tabana yapışmadı). K3 sızıntı denetimi: koku alınmayan denemelerde frozen ve anosmik sonuçları bit-bit aynı (ihlal=0; O1'de denetlenecek deneme çıkmayabilir — bu, tasarım gereği, boş geçer ve raporda "0 deneme" olarak yazılır).
* Kapı düşerse: parametre doğrulayıcı tohumda **ayarlanmaz**; neden raporlanır, düzeltme yeni tohumlarla yeni ön-kayıt gerektirir.

## 4. Birincil ölçütler (her popülasyonda her biri sağlanmalı)

* **P1** frozen − anosmik: eşli işaret-çevirme p<0,01 **ve** eşli %99 küme-GA alt sınırı >0 **ve** ortalama fark ≥0,15.
* **P2** frozen − random: aynı kural.
* **P3** ayna yarılarının (çift/tek denemeler) **her ikisinde** frozen − anosmik ortalama farkı >0 (duvar/yön yanlılığı kontrolü).
* **Karar:** "O1a başarılı" = iki popülasyonda da K1–K3 ve P1–P3 sağlandı; "O1b başarılı" aynı kuralla ayrı. Aksi: "başarısız" ya da (kapı düştüyse) "değerlendirilemez".

## 5. Betimsel (karar dışı) çıktılar
Kol başına `p_hit` ve küme-GA, hedefe ortalama süre/yol (isabetler), ayna yarıları, koku-alma oranı, canlı başına dağılım. İkincil uç nokta (öğrenme hızı, sıfırdan rejim) bu belgede **yok**; ayrı ön-kayıt.

## 6. Güç ve beklenti (belge `odor_guc_analizi.md`)
Pilotta gözlenen frozen−anosmik farkı O1a +0,27, O1b +0,25 (≈1,7–1,8δ). Benzetim: 1,5δ gerçek etkide tohum başına güç 0,94, sıfır etkide 0/500 geçiş. İki tohumun ikisinde geçme olasılığı gözlenen etkide yüksektir ama **garanti değildir**.

## 7. Sınırlar (peşin)
Ön-eğitimli, **öğrenmesi kapalı** canlı; hareket kuralı (sol–sağ kontrast, ε=2,0) elle yazılmıştır, referans karşılaştırıcı da öyle — başarı "bağlantı haritasından çıkan değer okuması bu görevde kullanılabilir" demektir, "beyin planlama yapıyor" demek değildir. Tek iz geometrisi ailesi (düz, tek dönüş); kesintili iz ve rüzgâr kapsam dışı. Tek ön-eğitim hattı (iki tohum).

## 8. Değişiklik kuralı
Koşudan sonra eşik/ölçüt/kapı/tohum değiştirilmez. Hata bulunursa karar defterine (E-numaralı) yazılır; düzeltilmiş analiz ayrıca ve etiketli raporlanır, özgün sonuç silinmez.
