# Ölçek ekseni doğrulayıcısı — ön-kayıt (K-036)

> Bu belge doğrulayıcı koşulardan **önce** commit edilir (R-1). Aşağıdaki ölçütler, eşikler, kollar ve tohumlar koşudan sonra değişmez; başarısızlık olduğu gibi raporlanır (R-3). Dil: Türkçe, dürüst raporlama.

## 1. Soru

Geliştirme bulgusu (K-028, `evre3_dan_plani.md` §6.1–6.2): oyun başarısını şu an sınırlayan şey DAN devresi değil, **öğrenilmiş değer okumasının Poisson gürültüsü**. Aynı ağırlıklarla, test anında (a) anten başına K=8 gürültülü kopya ortalaması ve (b) kısa okuma entegrasyonu (τ_valence = 0,04 sn; varsayılan 0,15) kullanılınca O1a frozen p_hit geliştirme tohumlarında 0,51–0,55 → 0,77–0,82 çıktı.

**Soru:** bu kazanç, ön-eğitimli popülasyonlarda, ön-kayıtlı doğrulayıcı tohumlarında yinelenir mi — ve kazanç *kokudan* mı geliyor (yoksa kör davranışın düzeyinin değişmesinden mi)?

Bu bir "beyin daha zeki oldu" iddiası **değildir**: ağırlıklar aynı, değişen yalnızca test anı okuma gürültüsünün azaltılmasıdır (R-9). İddia edilebilecek en fazla şey: "ölçülen oyun başarısı okuma gürültüsüyle sınırlıydı".

## 2. Sabitlenen ayarlar (doğrulayıcı verisinde AYARLANMAZ)

| ayar | değer | kaynak |
|---|---|---|
| topluluk büyüklüğü K | **8** | dev: O1a tohum 110 (K=8: 0,807), tohum 111 (K=8: 0,771); K=16 ek kazanç vermedi (§6.1) |
| okuma entegrasyon süresi τ_valence | **0,04 sn** | dev: tohum 110/111 K=1 taraması (0,02–0,04 en iyi), K=8 ile birlikte |
| taban (`frozen`) beyin | ön-kayıtlı doğrulayıcı beyni: K=1, τ=0,15 | `odor_validate` / O1–O2 ön-kayıtları |
| öğrenme | **kapalı** (test anı) | tüm kollar |
| topluluk | `EnsembleBrain(brain, k=8, tau_valence=0.04)`; kopyalar ağırlık paylaşımlı, yalnız Poisson gürültüsü bağımsız | `src/sinek/ensemble.py` |
| canlı × deneme | 24 canlı × 16 deneme, 25 sn / deneme | O1 ön-kaydıyla aynı |
| popülasyon | ön-eğitim 200 ve 201 (`results/odor_val/pre_s200.npz`, `pre_s201.npz`), önceki doğrulayıcılarla aynı dosyalar | R-2: popülasyon önceki O1–O4 doğrulayıcılarında kullanıldı; **oyun tohumları yenidir** |
| oyun tohumları | **O1a 250 / 251, O1b 252 / 253** | yeni, daha önce kullanılmamış (karar_defteri tohum kaydı) |
| δ / δ_eq / α | 0,15 / 0,10 / 0,01 | O1 ön-kaydıyla aynı |
| referans kapısı | referans p_hit ≥ 0,80 (O1) | O1 ön-kaydıyla aynı |

`--pilot` geliştirme tohumları (<200) içindir; doğrulayıcı tohumlarda yasaktır (kod korumasıyla).

## 3. Kollar (CRN eşli; aynı canlı, aynı deneme düzeni, aynı dünya tohumu)

| kol | beyin | koku |
|---|---|---|
| `frozen` | taban (K=1, τ=0,15) | açık |
| `ens` | aynı ağırlıklar + `EnsembleBrain(K=8, τ=0,04)` | açık |
| `anosmic` | taban | kapalı (kör) |
| `anosmic_ens` | topluluk beyni | kapalı (kör) |
| `reference` | elle kurulmuş (öğrenmesiz) karşılaştırıcı | açık |

## 4. Karar kuralı

**Kapılar** (hepsi sağlanmalı, yoksa koşu "kapılar eksik" olur ve başarı sayılmaz):
* referans p_hit ≥ 0,80;
* sızıntı denetimi (taban `frozen` ↔ `anosmic`): ihlal = 0;
* anosmik (taban) p_hit ∈ [0,15; 0,45] (O1 kör düzey penceresi).

**Karar veren ölçütler** (geçti kuralı: eşli işaret-çevirme p < 0,01 **ve** %99 kümeli GA alt sınırı > 0 **ve** ortalama fark ≥ δ = 0,15; birim = canlı, kümeleme = deneme):
* **P1 — ölçek kazancı:** `ens − frozen` ≥ δ.
* **P2 — kazanç kokudan:** `ens − anosmic_ens` ≥ δ (eşleşmiş kör kolun düzeyi topluluktan da yükselse bile, topluluğun *koku* kazancı aranır).

**Betimsel (karar vermez, her raporda yer alır):**
* P3: `anosmic_ens ~ anosmic` eşdeğerliği (±δ_eq). *Neden karar dışı:* güç benzetimi (R-6), eşdeğerlik testinin tek başına gerçek eşitlikte bile yalnız ≈%75–85 geçtiğini gösterdi (24×16 örnekleme, δ_eq = 0,10); karar kuralına koymak toplam gücü yarıya indirir. Artefakt koruması P2 ile sağlanır (benzetim, "koku etkisi yok" senaryosunda P2'nin geçmediğini gösterir: aşağıda). P3 sonucu ne olursa olsun hükmü değiştirmez; yalnız yorumlanır.

**Oyun hükmü (O1a ve O1b için ayrı):** BAŞARILI ⇔ **iki popülasyonun ikisinde de** (tohum 250 ve 251, ya da 252 ve 253) kapılar tamam ve P1 ile P2 geçti.
**Ölçek ekseni iddiası:** "ölçek ekseni okuma gürültüsünü azaltıyor" ancak O1a **ve** O1b BAŞARILI ise kurulur. Biri başarısızsa kısmi sonuç olarak aynen raporlanır; iddia kurulmaz.

## 5. Güç ve yanlış-pozitif benzetimi (R-6; ön-kayıttan önce yapıldı)

`python3 -I -m sinek.experiments.power_odor --games SC` (gerçek `eval_scale` işlevi, 300 benzetim/senaryo, 24 canlı × 16 deneme; parametreler O1 pilotuna uygun: kör düzey 0,27, referans 0,97, canlı sd 0,08, kol ayrışma 0,5, etki yayılımı 0,6). Sonuçlar `results/power_sc_O1.md` (git'te yok; aşağıya aynen geçirildi):

| senaryo | hepsi geçti | P1 | P2 | P3 (betimsel) |
|---|---|---|---|---|
| sıfır etki (ens = frozen) | **0,00** | 0,00 | 0,98 | 0,84 |
| etki = δ = 0,15 | 0,42 | 0,42 | 1,00 | 0,87 |
| etki = 1,5δ = 0,225 | 0,93 | 0,93 | 1,00 | 0,84 |
| etki = 2δ = 0,30 | **0,99** | 0,99 | 1,00 | 0,83 |
| kör düzey kayması +δ_eq ve ens kazancı 2δ | 0,98 | 0,98 | 1,00 | 0,00 |
| koku etkisi yok: ens yalnız kör düzeyi yükseltiyor | **0,00** | 0,42 | **0,00** | 0,00 |

Yorum:
* Yanlış pozitif: sıfır etkide ve "koku etkisi yok" artefaktında hepsini-geçme 0,00 (P2 artefaktı yakalıyor; P1 tek başına bu senaryoda 0,42 geçerdi).
* Güç: geliştirmede gözlenen kazanç ≈ +0,22 … +0,27 (≈1,5–1,8δ) → beklenen güç ≈ 0,93–0,99. **Tam δ kadar kazançta güç yalnız 0,42** (eşik δ'nın kendisine eşit olan bir etkiyi görmek zaten yarı yarıya şanstır; bu bilinerek kabul edildi).
* Betimsel P3, kör düzey gerçekten değişmişken (+δ_eq) sıfıra düşüyor, yani betimsel olarak artefaktı işaretliyor.

Bu benzetim yer tutucu parametrelere dayanır (pilottan); gerçek varyans farklıysa güç farklı olabilir. Hüküm gerçek veriyle verilir, benzetimle değil.

## 6. Kapsam dışı (ve nedeni)

* **O2-yakın:** dev ölçümü (tohum 115): referans 0,812, taban frozen (K=1, τ=0,04) 0,698; en iyi durumda bile referans ile taban arasındaki fark ≈ 0,11–0,15 ≈ δ. Güç benzetimi (`results/power_sc_O2.md`, p0 = 0,37, taban 0,66, referans 0,83): etki = δ'da hepsini-geçme **0,07**, 2δ'da 0,77 → P1 ≥ δ ölçütü **tavan etkisi** nedeniyle bu oyunda adil sınanamaz. δ'yı oyuna göre sonradan düşürmek yeni bir serbestlik derecesi olurdu; bu yüzden O2-yakın bu ön-kayda alınmadı. (Geliştirme sonucu betimsel olarak `evre3_dan_plani.md` §6.2'ye yazılır.)
* **O2-tam, O3, O4a, O4c:** ölçek eksenini sınamaz (O3 negatif kontrol; O4 sönüm elle yazılmış δ terimine dayanır; O2-tam betimseldi).
* Öğrenen (plastik) topluluk, paylaşılan-ağırlık topluluğu, GPU ölçeği: ayrı tasarım ve ön-kayıt (Evre 3 / GPU aşaması).

## 7. Komutlar (dondurulmuştur)

```
python3 -I -m sinek.experiments.odor_validate_scale --pre results/odor_val/pre_s200.npz --game O1a --seed 250 --threads 1 --out results/scale_val/O1a_s250
python3 -I -m sinek.experiments.odor_validate_scale --pre results/odor_val/pre_s201.npz --game O1a --seed 251 --threads 1 --out results/scale_val/O1a_s251
python3 -I -m sinek.experiments.odor_validate_scale --pre results/odor_val/pre_s200.npz --game O1b --seed 252 --threads 1 --out results/scale_val/O1b_s252
python3 -I -m sinek.experiments.odor_validate_scale --pre results/odor_val/pre_s201.npz --game O1b --seed 253 --threads 1 --out results/scale_val/O1b_s253
```

Varsayılanlar (`--agents 24 --trials 16 --seconds 25 --k 8 --tau 0.04 --delta 0.15 --delta-eq 0.10 --boot 10000`) bu belgedeki ayarlarla aynıdır. Kol-kol kontrol noktası (V-03) ve `scripts/run_scale_validators.sh` kuyruğu yalnızca kesilen koşuyu **aynı hesapla** sürdürür; ölçüt ya da eşik keşfetmez.

## 8. Elle yazılmış / öğrenilmemiş bileşenler (R-11)

* DAN hata terimi (`last_delta = gate·(ödül_hedefi·ödül − valans)`) elle yazılmıştır (Evre 3.3 kapısı karşılanmadı).
* `reference` karşılaştırıcısı elle kurulmuştur (öğrenmez).
* Topluluk kopya sayısı K ve τ_valence geliştirmede seçildi (iki dev oyun tohumu, tek dev ön-eğitimi: 100); doğrulayıcı popülasyonları (200/201) farklı ön-eğitimlerdir, dolayısıyla ayarın genellenmesi ilk kez burada sınanır.
* Topluluk yalnızca test anındadır; ağırlıklar K=1 ile eğitilmiştir (eğitim–test uyumsuzluğu olası bir kayıp kaynağıdır).

## 9. Dürüstlük notu / sınırlar

* Başarı olsa bile, referansa uzaklık (≈0,98 − ≈0,8) kapanmış olmaz; yalnızca "kazancın bir kısmı okuma gürültüsünden" denir.
* Topluluk, K kat işlem maliyetidir (K=8 → ≈8× adım başına maliyet); bu "daha zeki" değil, "daha pahalı ve daha az gürültülü" bir okumadır. GPU aşamasında asıl soru, aynı gürültü azaltmasının paylaşılan-ağırlık tek-W topluluğuyla ucuza elde edilmesidir.
* Sonuç O1 (iz sürme) oyunlarına özgüdür; O2/O3/O4'e genellenmez.
