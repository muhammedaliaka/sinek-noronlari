# O5c — DAN hedefi T=2,5 (tek öğrenici) doğrulayıcısı — ÖN-KAYIT (KESİNLEŞTİ)

> Bu belge doğrulayıcı koşulardan **önce** commit edilir (R-1). Ölçütler, eşikler, kollar, tohumlar ve karar kuralları koşudan sonra değişmez; başarısızlık olduğu gibi raporlanır (R-3). Koşudan sonra yazılan açıklamalar "post-hoc" diye etiketlenir ve hükmü değiştirmez. Dil: Türkçe, dürüst raporlama.
> Tarih: 2026-10-31. Kaynak bulgu: K-048 (`docs/dan_hedefi_dev.md` §2, §2d). **Ön-eğitim popülasyonları (tohum 206–209) bu commit'ten sonra üretilir**; oyun tohumları 274–277 hiç kullanılmadı.

## 1. İddia ve iddia OLMAYANLAR

* **C:** Öğrenmemiş beynin DAN hedefi `reward_target` T=2,5 olduğunda (tek öğrenici, hesap maliyeti 1×), olasılıklı iki-kollu koku oyununda (O5 / O5b ile aynı oyun) T=0,6 varsayılanına göre **hem seçicilik (yaklaşmadan arındırılmış net tercih) hem de ödül oranı** artar; seçicilik `frozen`a göre de korunur.
* **İddia DEĞİL:** T=2,5'in genel varsayılan olması (O1–O3 gerileme kontrolü yapılmadan olmaz, §6); öğrenme **hızı**; "genel olarak daha zeki"; nöron sayısı (R-9); mekanizma (post-hoc yorum `dan_hedefi_dev.md` §3, sınanmadı); sinek davranışı (R-10); K=4 topluluk eşdeğerliği (betimsel).

## 2. Tasarım

O5/O5b ile aynı oyun, ödül programı ve protokol (40 bölüm × 40 sn, p_hi=0,8/p_lo=0,2, tersine çevirme bölüm 21), farklar:

| öğe | değer |
|---|---|
| popülasyonlar | **4 yeni:** ön-eğitim tohumları **206, 207, 208, 209** (`odor_pretrain` varsayılan ayarları, bu commit'ten sonra üretilir) |
| oyun tohumları | **274 (pop 206), 275 (207), 276 (208), 277 (209)** — yeni, kayıtlı (K-056) |
| yaşam sayısı | **96 / popülasyon = 24 canlı × 4 kopya** (O5b'de 48; güç için, §7) |
| parçalama | 8 parça × 12 yaşam; parça c'nin dünya tohumu = oyun tohumu + 1000·c (tüm kollarda AYNI); kol × parça kontrol noktası |
| bloklar | geç faz-1 = bölüm 11–20, geç faz-2 = bölüm 31–40 |

## 3. Kollar (CRN eşli: aynı canlı, aynı dünya, aynı ödül çekimleri)

| kol | beyin | öğrenme |
|---|---|---|
| `plastic_t` | `naive_plastic`, **`reward_target` = 2,5** (yalnız bu kolda), η ölçeği 1,0, τ_valence=0,15 | AÇIK |
| `plastic` | `naive_plastic`, `reward_target` = 0,6 (yapılandırma varsayılanı) | AÇIK |
| `frozen` | `naive` | KAPALI |
| `reference` | elle kurulmuş kehanet-izleyici (çözülebilirlik kapısı) | — |

T=2,5, geliştirmede (tohum 134/135, pop 102/100; 132/133) seçilmiş tek değerdir ve burada **sabittir**; doğrulayıcı verisinde ayarlanmaz. Topluluk (K) kolu YOKTUR.

## 4. Ölçütler — her popülasyon için (`eval_o5c`)

Net tercih skoru (NP) bölüm başına: +1 iyi koku ilk temas, −1 kötü koku ilk temas, 0 temas yok. Eşli küme (yaşam) bootstrap %99 GA, eşli işaret-çevirme p, 10 000 yeniden örnekleme; hepsi için p < **α = 0,01**, GA alt sınırı > 0 ve ortalama ≥ δ.

* **Kapı G:** `reference` ödül oranı (iki geç blok birlikte) ≥ 0,60; eksikse popülasyon geçersiz ve iddia yapılamaz.
* **T1 (seçicilik kazancı):** `plastic_t − plastic` NP, iki geç blok birlikte, ≥ **δ_np = 0,06** (gözlenen +0,124'ün yarısı).
* **T2 (ödül kazancı):** `plastic_t − plastic` ödül oranı, iki geç blok birlikte, ≥ **δ_r = 0,04** (gözlenen ≈ +0,06…+0,10'un altı).
* **T3 (seçicilik korunuyor):** `plastic_t − frozen` NP ≥ **δ_abs = 0,10** (O5b N1 ile aynı).
* Betimsel (karar vermez): blok başına iyi koku seçme oranı, temas-yok, tersine çevirme bedeli.

## 5. Karar kuralı

* **C başarılı** ⇔ kapı G dört popülasyonda da tamam ∧ **T1, T2 ve T3'ün her biri en az üç popülasyonda (≥3/4)**.
* Bitmemiş koşu varsa ve kural henüz çürütülmediyse "BEKLİYOR" (`o5c_ozet.py`); sessizce atlanmaz. Tohumlar tek kullanımlıdır (R-2); başarısızlık yeni tohumla "kurtarılmaz".

## 6. Elle yazılmış bileşenler (R-11) ve sınırlar

* DAN hata kuralı `gate·(T·reward − valence)` ve **T bir elle seçilen DAN sabitidir**; motor kuralı, referans, ödül programı elle yazılmıştır ve tüm kollarda aynıdır.
* **Ölçütlerin kaynağı (dürüstlük):** T1/T2 ve δ'lar O5 geliştirme panellerinden (tohum 132/133, pop 102/100; `dan_hedefi_dev.md` §2d) türetildi — T'nin kendisi de oradaki tarama (tohum 134/135) ile seçildi. Bu verilerin hiçbiri bu belgenin popülasyon/tohumlarını içermez, ama ölçütler görülmüş veriye göre seçildi (iyimserlik riski; güç analizi bu yüzden iyimser olabilir).
* **Kapsam:** yalnız O5 oyunu. O1–O3/O4 etkisi bu doğrulayıcıda ÖLÇÜLMEZ. O4a sönüm T'den bağımsızdır (δ=−V; birebir aynı çıktı, `dan_hedefi_dev.md` §2c) ama ödüllü kazanım oyunlarında (O1–O3) T davranışı değiştirir; **T genel varsayılan yapılmadan önce O1–O3 geliştirme gerileme kontrolü ayrıca yapılır ve raporlanır** (bu doğrulayıcının hükmünden bağımsız).
* Dört popülasyon dört koku çiftini temsil eder; geniş genelleme iddiası yoktur. Hız iddiası yok.

## 7. Güç ve yanlış-pozitif analizi (R-6; `power_o5c.py`, `results/power_o5c.md`)

Gerçek ham yaşam verisinden yeniden örnekleme (E-15 dersi). Panel: yalnız **iki** popülasyon (geliştirme tohumları 132/pop 102 ve 133/pop 100, `plastic_t` kollu); planlanan 96 yaşam/popülasyon için her yeniden örneklemede 96 yaşam yerine koyarak çekilir. 300 yeniden örnekleme / senaryo / panel. Popülasyon başına geçme olasılığı (panel 132 / panel 133), 4 popülasyonlu "≥3/4" kuralına Poisson-binom ile çevrildi (iki panel tekrarlanarak; ölçütler arası bağımlılık yok sayıldı → ürün yaklaşık):

| senaryo | T1 | T2 | T3 | kural düzeyi (T1∧T2∧T3, ≥3/4) |
|---|---|---|---|---|
| sıfır etki (plastic_t↔plastic) | 0,01 / 0,00 | 0,01 / 0,00 | 1,00 (T3 sıfır-etkide ölçüt değildir) | yanlış-pozitif ≈ **0,000** |
| gözlenen etki (yeniden örnekleme) | 1,00 / 0,67 | 1,00 / 1,00 | 1,00 / 1,00 | güç ≈ **0,89** |
| yarım etki | 0,81 / 0,25 | 0,99 / 0,63 | 1,00 / 1,00 | ≈ 0,26 (etki yarıya inerse büyük olasılıkla BAŞARISIZ; bu "etki yok" demek değildir) |
| yalnız yaklaşma (plastic_t temas örüntüsü, seçim yazı-tura) | 0,00 / 0,00 | 0,24 / 0,00 | 0,00 / 0,00 | yanlış-pozitif ≈ **0,000** (T2 tek başına artefaktı geçirebilir; T1 ve T3 geçirmez) |

48 yaşamla (`results/power_o5c_n48.md`) bilinen-etki gücü ≈ 0,62'ydi; 96 yaşam bu yüzden seçildi (yalnız güç için, sonuca bakılmadan).
**Dürüst sınırlar:** (1) yalnız iki panel; popülasyon heterojenliği az temsil edilir (panel 133'te T1 gücü 0,67); (2) etki görülmüş veriden seçildi → iyimserlik; (3) ölçütler arası bağımlılık yok sayıldı; (4) yarım etkide güç düşük.

## 8. Komutlar ve işletim

```
scripts/run_o5c_validators.sh [işçi_sayısı]       # varsayılan 4; aşama 0: ön-eğitim 206-209; aşama 1: kol×parça; aşama 2: değerlendirme; yeniden başlatmaya dayanıklı
python3 -I -m sinek.experiments.o5c_ozet --dir results/o5_val --out results/o5_val/ozet_o5c.md      # ön-kayıtlı hüküm
```

Beklenen süre (1 iş parçacığı/işçi, 4 işçi): ön-eğitim ≈30 dk; kol × parça işleri 96 adet (≈10–25 dk); toplam ≈5–8 saat. Konteyner yeniden başlarsa kuyruk aynı komutla sürer.

**İşletim notu (2026-10-31, koşu başladıktan sonra; ölçütleri/tasarımı DEĞİŞTİRMEZ):** 12 yaşamlık bir `plastic`/`plastic_t` parçası 4 işçi yüklüyken ≈30–55 dk sürüyor; 96 parça + referans için toplam ≈12–20 saat. Bulgu: bulut oturumunda arka plan işleri, oturum boştayken (etkin bir tur yokken) konteyner uyutulduğu için ölüyor — ön-eğitim (35 dk) yalnızca ben etkin beklerken tamamlandı; boşta bırakılan üç kuyruk girişiminde hiçbir parça bitmedi. Bu yüzden kuyruk kalıcı, kesintisiz bir makinede (GPU makinesi / yerel) çalıştırılmalıdır; parça kontrol noktaları sayesinde kesilirse aynı komutla sürer. Bu oturumda O5c koşusu BAŞLATILMIŞ ama ilerlememiştir: hiçbir doğrulayıcı sonucu yoktur ve hüküm BEKLİYOR.
