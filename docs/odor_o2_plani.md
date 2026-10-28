# O2 — koku yalnız hedef çevresinde: ÖN-KAYIT (doğrulayıcı koşulardan önce)

Bağlayıcı üst belge: `docs/dort_koku_oyunu_plani.md` (§3.2, §5, K-024). Ortak tasarım ve kurallar için `docs/odor_o1_plani.md` §2, §4, §8 aynen geçerlidir; yalnızca farklar yazılmıştır.
**Commit edilmeden doğrulayıcı koşu (tohum ≥200) başlamaz.**

## 1. Soru ve dürüst cümle
*Kokuyu yalnızca hedefin hemen çevresinde (R=5) alabilen canlı, bölgenin yakınından başladığında hedefi, koku girdisi sıfırlanmış kendisinden daha sık bulur mu?*
Evet ise: **"Uzaktan koku rehberliği yok; bölgeye giriş keşifle, son yönelim kokuyla."** Hayır ise: **"Bu canlı yakın alan kokusundan fayda sağlamadı."**

## 2. Tasarım (donduruldu)
* **Alan:** `C(d)=A(1−(d/R)²)³` (d<R), aksi **tam 0,0**; **R=5, A=1** (K-023). T=25 sn.
* **Birincil oyun O2-yakın:** başlangıç, hedefi çevreleyen R+2=7 yarıçaplı halkada, yön düzgün rastgele; kollar CRN eşli. Koku alanı görülmeyen denemelerde (≈%13) frozen ve anosmik yörüngeleri bit-bit aynı olmalı.
* **O2-tam (betimsel, karar dışı):** başlangıç düzgün rastgele (d≥14); bölgeye ilk giriş ve toplam `p_hit` raporlanır. Kör bölge girişi (anosmik) pilotta 0,65 ∈ [0,3; 0,9] (tasarım-zamanı kapısı sağlandı).
* **Popülasyonlar:** ön-eğitim tohumları 200 ve 201 (24 canlı, `docs/odor_o1_plani.md` §2 ile aynı ve **aynı dosyalar**). **Oyun tohumları:** O2-yakın **220** (pop. 200), **221** (pop. 201); O2-tam **222**, **223**.
* **Deneme:** canlı başına 16 deneme (8 ayna çifti), test kipi, öğrenme kapalı. Kollar: frozen, anosmic, random, reference.
* **Komut:** `python3 -I -m sinek.experiments.odor_validate --pre results/odor_val/pre_s{200|201}.npz --game {O2near|O2full} --seed {tohum} --ref-min 0.70 --out results/odor_val/{oyun}_s{tohum}`

## 3. Kapılar
* **Tasarım-zamanı G1 (tamam, K-023/K-024):** referans O2-yakın `p_hit` 0,812 (n=192, tohum 101) ve **0,828 (n=960, tohum 105)** ≥0,80.
* **Doğrulayıcı tabanı K1:** referans `p_hit ≥ 0,70` (dünya bozuk mu denetimi; nokta tahmini 0,83 civarında beklenir, ≥0,80 şartı doğrulayıcıda şans kapısı olurdu — K-024). K3: sızıntı ihlali = 0.
* Kapı düşerse karar "DEĞERLENDİRİLEMEZ".

## 4. Birincil ölçüt (her popülasyonda)
* **P1** O2-yakın: frozen − anosmik: eşli işaret-çevirme p<0,01 **ve** eşli %99 küme-GA alt sınırı >0 **ve** ortalama fark ≥0,15.
* **Karar:** "O2 başarılı" = iki popülasyonda K1, K3 ve P1. O2-tam sayıları karar vermez.

## 5. Güç (`odor_guc_analizi.md`)
Pilot O2-yakın farkı +0,32 (≈2,1δ); 1,5δ'da güç 0,97, sıfır etkide 0/500.

## 6. Sınırlar (peşin)
Anosmik kör düzey yüksektir (≈0,42: halka başlangıcı hedefe yakın), bu yüzden fark kör düzeyden ölçülür, tavan sınırlı değil ama sonuç yalnız **yakın alan** için geçerlidir. R yalnız 5'tir (R=3/8 taranmadı). Yakın alan yönelimi elle yazılmış sol–sağ kontrast kuralıyla yapılır; referans karşılaştırıcı 0,83'te kalır, yani alan kusursuz çözülebilir değildir.
