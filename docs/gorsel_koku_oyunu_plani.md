# O6 — Görsel + koku oyun ailesi ("ısı kutusu"): sinekçil plan

**Durum: PLAN (TASLAK v1, 2026-10-30).** Hiçbir ölçüt/eşik kesinleşmedi; doğrulayıcı koşu yok. Ön-kayıt (kural R-1) pilotlar ve güç analizinden sonra ayrı belgelerde (`docs/odor_o6a_plani.md` …) yazılıp commit edilir.
Kaynak: kullanıcının "koku tuzağı ve görsel karar" önerisi (4 aşama; üç kontrol kolu; ölüm yerine ceza). Bu belge o fikri **sinek biyolojisine ve deneysel düzene** göre yeniden yapılandırır. Kararlar: `karar_defteri.md` K-049.
Etiketler: **[doğrulandı]** bu oturumda kaynakla/veriyle kontrol edildi (kaynak özeti düzeyinde ise belirtilir); **[doğrulanmadı]** anımsama; karar dayanağı yapılmaz (R-7).

## 0. Önerinin değerlendirmesi (neyi aldım, neyi değiştirdim, neden)

| Öneri | Karar | Gerekçe |
|---|---|---|
| Koku tuzağa çekerken görüntü güvenli olanı göstersin (çatışma) | **Aldım** (O6c) | Bilimsel olarak en bilgilendirici: koku-yalnız kolu tuzağa gitmeli, görüntü kullanan kol gitmemeli → görsel katkı doğrudan ölçülür. |
| Dört aşama (koku → görüntü → çatışma → kural değişimi) | **Aldım, sırayı sıkılaştırdım** (O6a–d) | Her aşama bir sonrakinin "kontrol deneyi": başarısızlık görüntü algısına / kokuya aşırı bağlanmaya / yeni kural öğrenmeye atfedilebilsin. |
| Üç kontrol kolu (koku+görüntü, yalnız koku, görsel kapalı) | **Aldım, genişlettim** | Dört deneysel kol + dondurulmuş, kör (rastgele) ve elle yazılmış referans (bkz. §4). "Yalnız koku" ve "görsel kapalı" aynı kol değildir; ikisini ayırdım. |
| Ölüm yerine ceza | **Aldım** | Gerçek düzenekler de ölümcül değil: ısı cezası (aşağıda). Tuzak = **ısıtılmış bölge**: temas aversif sinyal + bölüm sonu. Ölüm yok. |
| "Mıknatıs gibi çeken makine" | **Çıkardım** | Biyolojik karşılığı yok. Yerine: **tuzak kaynağı daha güçlü (genlik ×k) ve ödüllü kokuyu yayar** — "koku çekimi" aynı devrede, ölçülebilir ve kademeli. |
| Sahte ödül yolu (ödüllü gibi kokar, bazen tuzağa çıkar) | **Ertelendi** (O6e) | O4'te sahte hedef zaten doğrulandı (decoy). İlk sürümde değişken sayısını artırmamak için çıkarıldı. |
| Birçok iz + görsel işaret (karışık ortam) | **Ertelendi** (O6e) | Mevcut oyun dünyası 2 yuvalı; çoklu kaynak ayrı altyapı işi. Önce 2 yuvada ölçüt sağlam olmalı. |
| Görüntü = resim | **Değiştirdim** | Sinekte yüksek çözünürlüklü resim yok; renk/parlaklık/desen **özellik kanalları**, iki göz, açısal pencere, uzaklığa bağlı görünürlük (bkz. §3). |
| Genelleme (yeni konum/yoğunluk) | **Aldım** | Konum zaten her bölümde rastgele; yoğunluk (genlik) testte kaydırılır. |
| Yeni "neden ölçüt" listesi (hayatta kalma, güvenli oran, kokuya direnme, görsel katkı, hız, uyum, aktarım) | **Aldım, tanımlarını sıkılaştırdım** (§5) | E-15 dersi: ham "güvenli ödül oranı" yaklaşmayla karışır → **net tercih** (yaklaşmadan arındırılmış) ana ölçüt. |

## 1. Dürüst başlangıç: bugün ne var, ne yok

* **Beynin görsel girdisi YOK.** `Creature.step` beyne yalnız `glom` (koku), `taste`, `touch` verir; görsel nöron/kanal yok. Bu oyun ailesi bir **yeni duyu kanalı** işidir (V0 altyapı), yalnız yeni oyun değil.
* **Bağlantı verisinde görsel girdi VAR** (bu oturumda hesaplandı, **[doğrulandı]**: `docs/gorsel_girdi_denetimi.md`, `python3 -I -m sinek.connectome.visual_audit`): sağ yarımküredeki 2 045 KC'den **KCg-d (107 KC) girdi ağırlığının %7,3'ü, KCab-p (65 KC) %2,4'ü görsel projeksiyon nöronlarından** (126 / 24 benzersiz nöron;
  en ağırlıklı tipler: KCg-d ← aMe12, MeVP41, LoVP42, MeVP36, aMe20; KCab-p ← aMe26, MeVP45); tek KCg-s1 hücresinde %18,7. Diğer alt tiplerde (KCg-m, KCab-s/m/c, KCa'b') görsel girdi ≈0. Mevcut işlenmiş alt ağda görsel PN yok → yeni çıkarma gerekir (V0). Şu an modelde KCg-d'nin 90/107'si **hiç girdi almıyor** (susuyor).
* **Literatür (arama özeti düzeyinde okundu; birincil tam metin okunmadı):**
  * **[doğrulandı, özet]** Vogt ve ark. 2016, eLife 5:e14009 — sinekte görsel ve koku ilişkisel belleği **aynı mantar cismi devrelerini** paylaşır; **γd KC'leri** görsel yanıtlı alt kümedir (yetişkinde ≈75 hücre), bloke edilince renk ayırt etme öğrenmesi bozulur; görsel girdiyi görsel projeksiyon nöronları (VPN) getirir. <https://elifesciences.org/articles/14009>
  * **[doğrulandı, özet] Sınır:** Ofstad, Zuker, Reiser 2011, Nature 474:204 — görsel **yer** öğrenmesi (ısıtılmış zeminde serin nokta) **elipsoid cisimde** yapılır, **mantar cisimlerinde değil**. Bizim model yalnız mantar cismi: **yer öğrenmesi iddiası yok**; oyun *desen/renk* öğrenmesi (aşağıda) olarak kurulur. <https://www.nature.com/articles/nature10131>
  * **[doğrulandı, özet]** Brembs & Heisenberg 2001, J Exp Biol 204:2849 — uçuş simülatöründe desen+renk bileşik uyaranları: **sağlam bloklama yok**, belirgin **duyusal ön-koşullama**, küçük ikinci derece koşullama. Sonuç: bloklama ölçüt YAPILMAZ; duyusal ön-koşullama ileri aşama adayıdır (O6f, kapsam dışı). <https://bjoern.brembs.net/download/conditioning-with-compound-stimuli-in-drosophila-melanogaster-in-the-flight-simulator/>
  * Isıtmalı düzenekler (ısı kutusu, ısı labirenti) sinekte yaygın ceza düzenekleridir **[doğrulanmadı: bu oturumda ayrıca doğrulanmadı]**; aversif öğretici sinyalin PPL1 DAN'larıyla taşındığı bilgisi de **[doğrulanmadı]** — bizde bu yol hazır (δ<0 → PPL1).

## 2. Sinekçil tasarım ilkeleri
1. **Aynı MB, aynı öğrenme kuralı, aynı motor kural.** Yeni elle yazılmış kural eklenmez; yalnız **duyu ön ucu** (görsel PN'ler) eklenir. Böylece görsel sonuç "yeni kural"a değil "aynı devre yeni girdiyle" atfedilir.
2. **Görsel kod keyfî ve sabittir, koku gibi.** Oyun için iki görsel desen X ve Y: sabit rastgele özellik vektörleri (renk-benzeri/parlaklık-benzeri/desen-benzeri kanallar). Beyin hangisinin güvenli olduğunu **öğrenir**; cevap verilmez (öneriyle uyumlu).
3. **Ceza = ısı:** tuzak temasında aversif tat-benzeri kanal (acı sınıfı GRN → δ<0 → PPL1 bölmeleri), yeme süresi boyunca; bölüm biter. Ölüm, enerji kaybı yok.
4. **Görsel menzil kokudan uzun, çözünürlük düşük:** sinek uzaktan görür, yakından koklar → görsel bilgi **erken**, koku **geç** gelir; çatışmada koku çekimi ancak yakın mesafede başlar. (Parametreler pilotta; §3.)
5. **Öğrenme ve test ayrı:** edinim (öğrenme açık) → dondurulmuş test (O4 `snapshot` deseni) → kural değişimi (öğrenme açık). Ölçüt testte, öğrenme gürültüsü karıştırıcı olmasın.
6. **Her aşama bir önceki için kontrol:** görsel yol önce **tek başına** (O6b) çalışmadan çatışma (O6c) koşulmaz.

## 3. Dünya ve beyin ekleri (V0 altyapı; vis kapalıyken bit-bit aynı)
* **Dünya:** `GameWorld.sense_vis()` → (B, 2 göz, F) özellik etkinliği. Kaynak s için göz e: `görünürlük = pencere(açı_e) × 1/(1+d/d₀)`; desen `p_s ∈ [0,1]^F`. `F`, `d₀`, pencere genişliği pilotta ayarlanır (kuram kontrolü önce, R-8). Slot başına `visual: "X"|"Y"|"none"` ve `reward ∈ {+1, 0, −1}` (−1 = ısı). Mevcut oyunlarda `visual="none"` → davranış bit-bit aynı (test).
* **Beyin:** `ConnectomeBrain.step(glom, taste, touch, learn, vis=None)`. `vis=None` → mevcut yol, **bit-bit aynı** (altın koşu + `test_s0_regression` kapısı). `vis` verilince: ham veriden çıkarılan ≈150 görsel PN (VPN → KCg-d/KCab-p, gerçek sinaps ağırlıkları, min. 20 sinaps) Poisson ateşler; oranı `taban + maks × (sabit-rastgele-ayar · özellik)`; VPN→KC ağırlıkları PN→KC ile aynı kalibrasyonla. **VPN ayarı (tuning) elle yazılmış bileşendir (R-11).**
* **Veri:** `connectome/visual_audit.py` (yazıldı), `connectome` çıkarma adımına `vpn_kc.feather` (küçük; depoya girer, ham veri girmez).
* **Kapı G-V0 (kodlamadan önce kuram/hesap, R-8):** VPN etkinliği → KC (özellikle KCg-d) yanıtı için X ile Y'nin **ayrılabilirliği** (öğrenmeden): KC yanıt vektörlerinin kosinüs/Fisher ayrımı yeterli mi? Yetmiyorsa oyun koşmaz; "bu bağlantı verisiyle görsel desen ayrımı yetersiz" bir **sonuçtur** (ayar sürüsü yapılmaz, E-08).

## 4. Oyun ailesi (aşamalar, kollar)

Ortak: 2 yuva; bölüm başına ≤40 sn; güvenli yuva ödül +1 (olasılık p_hi, O5b'deki gibi sürüm O6e), tuzak yuvası ısı −1 + bölüm biter; konum her bölümde rastgele, ayna çiftleri ve CRN.

| Aşama | Soru | Koku | Görsel | Ana ölçüt | Karşılaştırılan kollar |
|---|---|---|---|---|---|
| **O6a** koku tabanı | Mevcut beyin koku ile güvenli/ısı ayırt eder mi? (tuzaklı O5-benzeri) | güvenli=A, tuzak=B | **yok** | net tercih NP (güvenli +1, tuzak −1, temas yok 0) | plastic, frozen, reference |
| **O6b** yalnız görsel | Görsel yol çalışıyor mu? | iki yuvada **aynı** koku | güvenli=X, tuzak=Y | NP | plastic(vis), plastic(**görsel kapalı**; NP≈0 beklenir), frozen, reference |
| **O6c** çatışma | Görüntü, kokunun çekimine rağmen güvenli yuvayı seçtirir mi? | tuzak: ödüllü koku, genlik ×k (k=1,2,4); güvenli: aynı koku ×1 | güvenli=X, tuzak=Y (O6b'de öğrenilmiş) | NP(k) ve eğim; *kokuya direnme* = NP(k=4)−NP_görsel-kapalı(k=4) | plastic(vis), olfaction-only (görsel kapalı), vis-only (anosmik), frozen, reference |
| **O6d** kural değişimi | Görsel anlam tersine dönünce yeniden öğrenir mi, koku sabitken? | sabit, bilgi taşımaz | güvenli: X→Y, tuzak: Y→X | tersine çevirme sonrası NP ve "N bölümde NP>0'a dönüş" | plastic(vis), olfaction-only, frozen |

Notlar: O6b, O6c'nin ön koşuludur (§2.6). O6d'de koku bilgi taşımadığı için "kokuya aşırı bağlanma" (sürekli aynı yuva) ayrı görünür. Test O6c/O6d'de dondurulmuş anlık görüntü ile de alınır.

**Kollar ve eşleşme:** hepsi aynı tohum, aynı dünya (CRN). *Görsel kapalı* = aynı beyin, `vis` sıfırlanır (VPN lezyonu eşdeğeri; **sızıntı denetimi:** görsel sinyal olmayan denemelerde sonuç bit-bit aynı). *Yalnız koku* ≡ görsel kapalı (aynı kol; çift adlandırma karışıklığını kaldırdım). *Yalnız görsel* = anosmik kol. *Rastgele/kör* = dönüş kazancı 0 (yönelimsiz). *Referans* = elle yazılmış kehanet izleyici (ölçekleme için; tavan; kapı ≥ eşik).

## 5. Ölçütler (kesinleşme öncesi; E-15 dersiyle)
1. **Ana: net tercih** `NP = P(güvenli ilk temas) − P(tuzak ilk temas)` (temas yoksa 0) — yaklaşma oranından bağımsız; sıfır-etki düzeyi ≈0 (O5b'de sınanmış mantık).
2. **Ceza oranı** (tuzağa girme/bölüm) — hayatta kalma karşılığı.
3. **Görsel katkı** = NP(plastic) − NP(görsel kapalı), eşli (aynı dünya); O6b'de ≈ tüm etki, O6c'de kokuya direnme.
4. **Kokuya direnme** = NP(k=4) − NP_görsel-kapalı(k=4); k büyüdükçe görsel-kapalı kolun NP'si düşmeli (bilinen-etki, R-6 benzetimi).
5. **Öğrenme hızı** = NP>0'a ilk geçiş bölümü (bölüm bloklarıyla, kümeli bootstrap).
6. **Kural değişimi uyumu** = tersine çevirme sonrası ilk iki blok NP ve toparlanma eğrisi.
7. **Aktarım:** test genliği/konumu eğitimdekinden farklı (k ve başlangıç ızgarası), yeniden eğitim yok.
İstatistik: mevcut `paired_cluster_ci`, `paired_signflip_p`, `_superior` kuralı; eşikler (δ) **pilot sonrası**; güç analizi gerçek ham veriyi yeniden örnekleyerek (power_o5b yöntemi); sıfır-etki ve bilinen-etki benzetimi ön-kayıttan önce (R-6); ≥4 bağımsız popülasyon (O5b dersi); tohum/ön-eğitim ayrımı (R-2).

## 6. Karar ağacı (başarısızlık nereye atfedilir?)
* O6a geçmez → ısı/ceza yolu (negatif tat) sorunlu, görsel konusu değil.
* O6a geçer, O6b geçmez → **görsel yol** (VPN→KC ayrılabilirlik, kazanç, kalibrasyon). Önce G-V0 sayıları, sonra VPN kazancı; ayar sürüsü yok.
* O6b geçer, O6c geçmez → görsel bilgi var ama **koku baskın**: k kademeleri ve motor kuralın normalize kontrastı (`contrast_eps`) incelenir; koku/görüntü ağırlıklandırması MB'de nasıl çözülüyor (hangi KC alt tipleri) ayrı analiz.
* O6c geçer, O6d geçmez → **yeniden öğrenme** (DAN sönüm yolu, K-048 T ve η bulguları ile ilişkili) — görsel algı sorunu değil.

## 7. Elle yazılmış bileşenler (R-11) ve sınırlar
Elle yazılmış: VPN ayarı ve oranları, görünürlük kuralı (pencere × uzaklık), ısı = acı-GRN kanalı, DAN hata kuralı (`δ = kapı·(T·ödül − V)`), normalize motor kural, referans karşılaştırıcı, ödül programı.
Sınırlar: **yer öğrenmesi/merkezi kompleks yok** (elipsoid cisim modelde yok, §1 [doğrulandı]); gerçek sinek davranışı iddiası yok (R-10); gerçek renk/ışık fiziği yok; tek göz çifti ve iki yuva; bloklama ölçüt değil; mantar cismi görsel girdisi yalnız ≈%5 KC (γd, α/β-p) — yeterliliği G-V0'ın cevabıdır, varsayım değil.

## 8. İş sırası
1. **V0 altyapı:** `vpn_kc.feather` çıkarma → `ConnectomeBrain.step(..., vis=None)` → `GameWorld.sense_vis` → `SlotSpec.visual/reward=-1` → testler (vis kapalı bit-bit aynı; sızıntı; ısı = negatif tat; bölüm sonu) → altın koşu ve tüm test paketi yeşil.
2. **G-V0 kuram/hesap kontrolü** (öğrenmesiz X/Y ayrılabilirliği) ve sonucun yazılması.
3. **Pilotlar** (geliştirme tohumları <200): O6a → O6b → O6c → O6d; her biri TAHMİN (R-8) → koşu → dürüst kayıt.
4. **Güç analizi + ön-kayıt** (aşama başına belge, R-1/R-6) → yeni tohum/popülasyon → doğrulayıcı.
5. GPU: aynı kodla ölçek (K, η, T) ızgaraları; `docs/gpu_devri.md`.
