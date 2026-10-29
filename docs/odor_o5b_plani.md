# O5b — seçicilik (yaklaşmadan arındırılmış) ve plastik topluluk doğrulayıcısı — ÖN-KAYIT (KESİNLEŞTİ)

> Bu belge doğrulayıcı koşulardan **önce** commit edilir (R-1). Ölçütler, eşikler, kollar, tohumlar ve karar kuralları koşudan sonra değişmez; başarısızlık olduğu gibi raporlanır (R-3). Koşudan sonra yazılan açıklamalar "post-hoc" diye etiketlenir ve hükmü değiştirmez. Dil: Türkçe, dürüst raporlama.
> Tarih: 2026-10-29. Önceki O5 ön-kaydı (K-042) KISMİ sonuçlandı (K-044, E-15); bu belge o dersin uygulamasıdır. **Ön-eğitim popülasyonları (tohum 202–205) bu commit'ten sonra üretilir**; oyun tohumları 270–273 hiç kullanılmadı.

## 1. İddialar (iki ayrı hüküm) ve iddia OLMAYANLAR

* **A — Seçicilik / öğrenme:** öğrenmemiş beyin, olasılıklı (%80/%20) iki-kollu koku oyununda, öğrenmesi kapalı aynı beyne göre iyi kokuyu kötüden **yaklaşma oranından bağımsız** ayırt etmeyi öğrenir ve tersine çevirmeden sonra yeniden öğrenir.
* **B — Topluluk:** plastik topluluk (`PlasticEnsembleBrain`, K=4 bağımsız öğrenen kopya, τ_valence=0,04; karar için valence ortalaması) tek kopyalı plastik beyne göre belirgin biçimde daha çok ödül toplar.
* **İddia DEĞİL:** öğrenme **hızı**; "genel olarak daha zeki"; nöron sayısı (R-9); B'nin nedeni (kopya ortalaması okuma gürültüsünü ve öğrenme gürültüsünü azaltır, yeni bir öğrenme kuralı değildir); sinek davranışı hakkında bir şey (R-10).

## 2. Tasarım

O5 ile aynı oyun, ödül programı ve protokol (`docs/odor_o5_plani.md` §2: 40 bölüm × 40 sn, p_hi=0,8/p_lo=0,2, tersine çevirme bölüm 21, 24 canlı × 2 kopya = **48 yaşam / popülasyon**), farklar:

| öğe | değer |
|---|---|
| popülasyonlar | **4 yeni:** ön-eğitim tohumları **202, 203, 204, 205** (`odor_pretrain` varsayılan ayarları, bu commit'ten sonra üretilir; naive kollar ön-eğitimli ağırlık kullanmaz, popülasyon = koku çifti + rol dengelemesi + beyin tohumu) |
| oyun tohumları | **270 (pop 202), 271 (203), 272 (204), 273 (205)** — yeni, kayıtlı (karar_defteri K-046) |
| parçalama | **8 parça × 6 yaşam** (O5'te 4); parça c'nin dünya tohumu = oyun tohumu + 1000·c (tüm kollarda AYNI); kol × parça kontrol noktası |
| bloklar | geç faz-1 = bölüm 11–20, geç faz-2 = bölüm 31–40 (O5 ile aynı) |

## 3. Kollar (CRN eşli: aynı canlı, aynı dünya, aynı ödül çekimleri)

| kol | beyin | öğrenme |
|---|---|---|
| `plastic` | `naive_plastic` (öğrenmemiş MaleCNS beyni, elle yazılmış DAN kuralı), η ölçeği 1,0, τ_valence=0,15 | AÇIK |
| `plastic_ens` | `plastic` + `PlasticEnsembleBrain(K=4, τ_valence=0,04)`: K kopya bağımsız öğrenir, kararda valence ortalaması | AÇIK |
| `frozen` | `naive` | KAPALI |
| `reference` | elle kurulmuş kehanet-izleyici (çözülebilirlik kapısı) | — |

K=4 ve τ=0,04 geliştirmede (K-045) bir kez sınanan değerlerdir ve burada **sabittir**; doğrulayıcı verisinde ayarlanmaz.

## 4. Ölçütler — her popülasyon (oyun tohumu) için (`eval_o5b`)

Net tercih skoru (NP) bölüm başına: +1 iyi koku ilk temas, −1 kötü koku ilk temas, 0 temas yok. Boş-model düzeyi her temas oranında ≈0'dır; bu yüzden `frozen`ın temas oranı (popülasyonlar arasında 0,41–0,64) ölçütü kaydırmaz (E-15: ödül oranı kaydırıyordu).

* **Kapı G:** `reference` ödül oranı (iki geç blok birlikte) ≥ 0,60. Eksikse popülasyon geçersiz ve iki iddia da yapılamaz.
* **N1 (seçicilik):** `plastic − frozen` NP farkı, iki geç blok birlikte, ≥ **δ_np = 0,10**, eşli küme (yaşam) bootstrap %99 GA alt sınırı > 0 ve eşli işaret-çevirme p < **α = 0,01**.
* **N2 (tersine çevirme sonrası yeniden öğrenme):** `plastic − frozen` NP farkı yalnız geç faz-2 bloğunda (31–40) > 0: p < 0,01 ve %99 GA alt sınırı > 0; **asgari etki büyüklüğü yok** (10 bölümlük blokta 48 yaşam δ=0,10 için yetmiyor; güç analizi §7).
* **E1 (topluluk):** `plastic_ens − plastic` ödül oranı farkı, iki geç blok birlikte, ≥ **δ_r = 0,08**, %99 GA alt sınırı > 0, p < 0,01.
* **E2 (betimsel, karar vermez):** `plastic_ens − plastic` NP farkı (aynı kural, δ=0,10 ile gösterilir); geliştirmede iki popülasyonda tutarsızdı (+0,224 ve +0,128 [−0,009; +0,259]).
* Betimsel (karar vermez): blok başına iyi koku seçme oranı, temas-yok, ödül oranları, tersine çevirme bedeli.

Bootstrap/permütasyon 10 000 yeniden örnekleme; sabit tohumlar (`eval_o5b`: N1=7, N2=8, E1=9, E2=10).

## 5. Karar kuralları

* **A başarılı** ⇔ kapı G dört popülasyonda da tamam ∧ **N1 dört popülasyonda (4/4)** ∧ **N2 en az üç popülasyonda (≥3/4)**.
* **B başarılı** ⇔ kapı G dört popülasyonda da tamam ∧ **E1 en az üç popülasyonda (≥3/4)**.
* Hükümler birbirinden bağımsızdır. Bitmemiş koşu varsa ve kural henüz çürütülmediyse "BEKLİYOR"; sessizce atlanmaz (`o5b_ozet.py`).
* Tohumlar tek kullanımlıdır (R-2); başarısızlık yeni tohumla "kurtarılmaz".

## 6. Elle yazılmış bileşenler (R-11) ve sınırlar

* DAN hata kuralı `last_delta = gate·(reward_target·reward − valence)`, motor kuralı (turn_gain 60, ε 2,0, wander_σ 1), referans kehanet-izleyici, ödül programı: elle yazılmış, tüm kollarda aynı.
* **Ölçütlerin kaynağı (dürüstlük):** N1/N2/E1 ve δ'lar (δ_np ≈ gözlenen NP farkının (0,20–0,23) yarısı; δ_r ≈ gözlenen +0,111/+0,159'un altı) **O5 doğrulayıcı verisinden (tohum 260/261, post-hoc, K-044) ve iki geliştirme panelinden (pop 100/102, tohum 132/133) türetildi**. Bu verilerin hiçbiri bu belgenin popülasyon/tohumlarını içermez; ama ölçütler görülmüş veriye göre seçildi (E-15'in tersi yönde bir serbestlik derecesi) — güç analizi bu yüzden iyimser olabilir.
* B yalnız K=4/τ=0,04'ü sınar; K'nın ya da kopyaların ağırlık paylaşımının etkisi ayrı iştir. Maliyet ≈4× hesap.
* Dört popülasyon dört koku çiftini temsil eder; geniş genelleme iddiası yoktur.
* Hız iddiası yok; ölçek eksenindeki test-zamanı topluluk (K-038) başka bir iddiadır.

## 7. Güç ve yanlış-pozitif analizi (R-6; `power_o5b.py`, `results/power_o5b.md`)

Parametrik benzetim yerine **gerçek ham yaşam verisinden** yeniden örnekleme (E-15 dersi: popülasyon heterojenliği): paneller O5 doğrulayıcı popülasyonları 260/261 (yalnız plastic/frozen/reference) ve geliştirme panelleri 132/133 (ayrıca plastic_ens). 1000 yeniden örnekleme / senaryo / panel; Poisson-binom ile 4 popülasyonluk karar kurallarına çevrildi (B için yalnız iki panel olduğundan 2 popülasyonluk tahmin).

| senaryo | popülasyon başına geçme | karar kuralı düzeyi |
|---|---|---|
| sıfır etki N (plastic↔frozen) | N1 0,00–0,01; N2 0,00–0,01 | A yanlış-pozitif ≈ **0,000** |
| gözlenen etki (yeniden örnekleme) | N1 0,99–1,00; N2 0,74–0,96 | P(N1 4/4) = **0,976**; N2 4/4 yalnız 0,558 ama **≥3/4 = 0,921** → A gücü ≈ 0,90 |
| gözlenen etki, topluluk | E1 1,00 ve 0,90 (E2 0,98 ve 0,46) | E1 için iki popülasyonda 0,90; dört popülasyonda ≥3/4 ≳ 0,95 (tahmin) |
| yarım etki N / E | N1 0,50–0,75; N2 0,30–0,71 / E1 0,49 ve 0,06 | A (N1 4/4) **0,128**; B zayıf → etki yarıya inerse bu doğrulayıcı büyük olasılıkla BAŞARISIZ olur ve bu "etki yok" demek değildir |
| yalnız yaklaşma (plastic ve ens) | tüm ölçütler 0,00 | yanlış-pozitif 0,000 (N ve E ölçütleri yalnız "yaklaş" artefaktını geçirmez) |
| sıfır etki E (ens↔plastic) | E1 0,00; E2 0,00–0,01 | B yanlış-pozitif ≈ **0,000** |

**Dürüst sınırlar:** (1) yeniden örnekleme gözlenen etkiyi sabit alır ve etkinin görülmüş veriden seçildiği iyimserliği taşır; (2) E için yalnız iki panel var; (3) popülasyonlar arası heterojenlik yalnız bu dört panelle temsil edilir; (4) yarım etkide güç düşüktür.

## 8. Komutlar ve işletim

```
scripts/run_o5b_validators.sh [işçi_sayısı]       # varsayılan 4; aşama 0: ön-eğitim 202-205; aşama 1: kol×parça; aşama 2: değerlendirme; yeniden başlatmaya dayanıklı
python3 -I -m sinek.experiments.o5b_ozet --dir results/o5_val --out results/o5_val/ozet_o5b.md      # ön-kayıtlı hüküm
```

Beklenen süre (1 iş parçacığı/işçi, 4 işçi): ön-eğitim ≈30 dk; `plastic_ens` parçası ≈30 dk × 32; plastic/frozen parçaları ≈8 dk × 64; toplam ≈6–7 saat. Konteyner yeniden başlarsa kuyruk aynı komutla sürer (parça kontrol noktaları diskte).
