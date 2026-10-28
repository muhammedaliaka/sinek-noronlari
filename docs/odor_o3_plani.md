# O3 — koku yalnız temasta: ÖN-KAYIT (doğrulayıcı koşulardan önce)

Bağlayıcı üst belge: `docs/dort_koku_oyunu_plani.md` (§3.3, §5, Z-01). Güç: `docs/odor_guc_analizi.md` (O3 bölümü, K-025). Ortak kurallar `docs/odor_o1_plani.md` §2 (popülasyonlar, tohum kaydı), §8 (değişiklik kuralı).
**Commit edilmeden doğrulayıcı koşu (tohum ≥200) başlamaz.**

## 1. Soru ve dürüst cümle (üstünlük değil, **eşdeğerlik**)

Bu oyunda ön-temas koku alanı yoktur: hedef konumu hiçbir duyusal ipucu vermez; koku/ödül yalnız temas anında ve tüketim süresince sunulur. Mevcut canlının (V yalnız koku girdisinden gelir; konum belleği yok)
bu dünyada **kör aramanın ötesinde bir şey yapabilmesi için bir mekanizması yoktur** (plan Z-01). Sınanan şey bir başarı değil, **gizli kanal yok** denetimidir:
*Hedefin ödüllü/kokulu/kokusuz/ödülsüz olması ve öğrenmenin açık olması, arama başarısını (ilk-temas oranı) değiştirmiyor.*
Eşdeğerlik çıkarsa yazılacak cümle: **"Koku alanı olmadan bu canlı kör arama düzeyinde kalıyor; ödül öğrenmesi konum belleği vermiyor, ve oyun dünyasında ön-temas bilgi sızıntısı yok (|Δp| < 0,10)."**
Bu bir **olumsuz kontroldür**; "zeka" iddiası taşımaz. Konum/yineleme belleği isteniyorsa bu ayrı bir devre kapısıdır (M1, kapsam dışı).

## 2. Tasarım (donduruldu)

* **Oyun:** O3 (alan yok; kaynak kimliği yalnız temas süresince her iki antene sabit seviyede, glom ≈0,98). T=25 sn, arena 40×40; hedef konumu her denemede yeni; hareket okuması `V2_SET` donmuş.
* **2×2 kol hücreleri (plastic, öğrenme açık):** **A** ödül+koku · **B** ödül, koku yok · **C** ödülsüz, koku var · **D** ikisi de yok; **kontrol: frozen:A** (öğrenme kapalı). Toplam 5 kol; CRN eşli.
* **Oturum:** canlı başına **4 kopya × 16 ardışık deneme** (ağırlıklar denemeler arasında korunur; tüketim kipi: temas → 0,4 sn tüketim → deneme biter). Ölçü: ilk temasın hedef olması (`p_hit`), canlı başına 64 denemenin toplamı.
* **Popülasyonlar ve tohumlar:** ön-eğitim 200 ve 201 (`docs/odor_o1_plani.md` §2); oyun tohumu **230** (pop. 200), **231** (pop. 201).
* **Komut:** `python3 -I -m sinek.experiments.odor_validate_s --pre results/odor_val/pre_s{200|201}.npz --game O3 --seed {230|231} --out results/odor_val/O3_s{tohum}`
  (varsayılanlar: 24 canlı, 4 kopya, 16 deneme, T=25, δ_eq=0,10, 10 000 bootstrap).

## 3. Kapı
* **G3 (yapısal, %100):** koşu boyunca hiçbir denemede koku alanı görülmedi (`field_seen_trials == 0`) — ön-temas `glom ≡ 0`. Ayrıca birim testleri (`tests/test_games_world.py`: ön-temas tam sıfır, temas→etki sırası) yeşil. Kapı düşerse karar "DEĞERLENDİRİLEMEZ" ve önce hata aranır.

## 4. Birincil ölçüt (her popülasyonda)
* **E3:** 5 kolun **10 çiftinin hepsinde**, eşli fark `Δp_hit` için canlı-kümeli %98 bootstrap GA (±2α, α=0,01) tamamen (−0,10; +0,10) içinde (TOST benzeri eşdeğerlik; bir çift bile dışarıdaysa E3 sağlanmaz).
* **Karar:** "O3 eşdeğerlik geçti" = iki popülasyonda G3 ve E3. Kör düzey (kol başına `p_hit`) her durumda raporlanır.
* **Yorum kuralı (peşin):** E3 sağlanmazsa bu bir bulgu değil **önce bir yanlılık/hata aramasıdır** (R-4): ör. öğrenme sonrası tek-yönlü dönüş yanlılığı (Z-16), duvar/ayna asimetrisi, CRN hatası. Bulunan neden karar defterine yazılır; sonuç silinmez.

## 5. Betimsel çıktılar
Kol başına `p_hit` ve ilk/ikinci yarı (öğrenme etkisi var mı), deneme sırasına göre eğilim, kol çiftleri arası ayrışma oranı (CRN sağlığı).

## 6. Güç (`odor_guc_analizi.md`)
64 deneme/canlıda sıfır sapmada tüm 10 çiftin eşdeğer çıkma olasılığı ≈1,00; marj kadar (0,10) sapmada çift başına ≈0,01 (yanlış eşdeğerlik yok); yarım marj (0,05) sapmayı çift başına ≈0,84 ayırt eder. **Yani 0,05'ten küçük farkları dışlayamaz**; "tam eşitlik" iddiası yoktur.

## 7. Sınırlar (peşin)
Yalnız *mevcut* canlıyı sınar (konum belleği/sistematik keşif yok); kör düzey T ve arenaya bağlıdır (T=25 sn'de ≈0,25-0,30). Tek ön-eğitim hattı, iki tohum. "O3'te öğrenme olmadı" sonucu canlının genel olarak öğrenemediği anlamına **gelmez**: O4 aynı canlının koku-ödül öğrendiğini ayrıca sınar.
