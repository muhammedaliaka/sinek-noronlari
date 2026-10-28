# Dört koku oyunu — incelenmiş ve bağlayıcı plan (v1)

**Belge türü:** plan (kod ve sonuç değil). **Henüz ön-kayıt değildir:** doğrulayıcı koşular için her oyuna ayrı `docs/odor_<oyun>_plan.md` ön-kayıt belgesi gerekir (R-1).
**Tarih:** 2026-10-28 · **Karar kayıtları:** K-019…K-021, E-11 (`docs/karar_defteri.md`)
**Kaynak taslak:** `docs/girdi/dort_koku_oyunu_taslak_v0.md` — kullanıcıdan geldi, **değiştirilmeden** saklandı. Bu belge ile taslak çelişirse **bu belge geçerlidir**.
Taslağın risk sicili (R01–R45), kaynakçası (§16) ve gözlem/UI fikirleri (§11) aynen geçerli kalır; aşağıda yalnız değişenler ve bağlayıcı kararlar vardır.

---

## 0. Özet

* Dört oyun (O1 kesintisiz iz, O2 yalnız final bölgesinde koku, O3 koku yalnız temasta, O4 yanıltıcı koku) iyi bir araştırma omurgasıdır: **koku algısı, kokuyla yön bulma, kokusuz arama, ödülden öğrenme ve yanlış beklentiyi sönümleme** birbirinden ayrılır.
* Taslağı kodla (`world.py`, `agent.py`, `brain_connectome.py`, `protocol.py`) ve küçük bir hesapla karşılaştırdım; **24 bulgu** çıktı (§1). En önemli beşi:
  1. **O3, mevcut ajan için kuramsal olarak kör aramadır.** Hareket kuralı yalnız `V_sol−V_sağ` kullanır, `V` yalnız koku girdisinden gelir; `C=0` iken dünyanın hiçbir durumu beyne ulaşmaz. O3 bu yüzden bir *üstünlük* testi değil, **boş-sonuç (eşdeğerlik) kontrolü ve kör temel çizgi ölçümüdür**; "aynı haritada tekrar öğrenme" mevcut modelde mekanik olarak imkânsızdır (yer temsili yok) → yeni modül kapısına (M1) taşındı.
  2. **Taslağın 60 sn sınırı tavan etkisi yaratır:** kör gezgin 60 sn'de hedefin %58'ini bulur, R=5 koku bölgesine %96 girer (hesap §1, Z-02). Süre sınırı **kör başarı ≈ 0,20–0,40** olacak şekilde seçilecek (aday: 25 sn).
  3. **Sol–sağ karşılaştırıcı için salt yanal profilli koridor yön vermez**; izin hedefe doğru artan boylamsal gradyanı olmalı ve çözülebilirlik elle kurulmuş bir **referans karşılaştırıcıyla** doğrulanmalı.
  4. **Ortak rastgele sayılarla (CRN) eşleştirme + bit düzeyinde sıfır-sızıntı testi:** koku açık ve koku kapalı kollar aynı canlı, aynı yerleşim, aynı gürültüyle koşar; ilk gerçek koku alınana dek yörüngeler **birebir aynı** olmak zorundadır. Bu, istatistiksel eşdeğerlikten çok daha keskin bir sızıntı denetimidir.
  5. **Duyu katmanları (ORN/anten lobu) oyunlardan önce değil sonra gelir** (taslağın kendi §17'si böyle diyor, §7.2/§12 çelişiyordu). Oyunlar mevcut doğrudan-glomerül girişte (L0) koşar; gerçekçi duyu katmanı ayrı, ön-kayıtlı bir karşılaştırma olarak sonra gelir.
* **Dürüst beklenti (ön-kayıt öncesi tahmin, sonuç değil):** O1 ve O2-yakın yaklaşma → olumlu etki beklenir; O3 → boş sonuç (kör düzey) beklenir; O4a → sönüm beklenir (çekim yoksa değerlendirilemez); O4c → decoy'dan kaçınma olabilir ama gerçek hedefi bulma **kör düzeyi aşmaz**. Bunlar başarısızlık değildir; hangi yeni devrenin (bellek, sistematik keşif) gerekeceğini gösterir.

---

## 1. İnceleme bulguları (taslak v0 → v1)

Kanıt türleri: **K** = kod okuması (dosya), **H** = hesap/benzetim (`docs/girdi` dışında, `src/sinek/experiments/games_blind_check.py` + `tests/test_games_blind.py`), **T** = taslak içi tutarsızlık.

| Kod | Taslakta | Sorun / kanıt | Düzeltme (bağlayıcı) |
|---|---|---|---|
| Z-01 | O3'te "aynı haritada tekrar öğrenme", plastic>frozen beklentisi ima edilir (§5.3) | **K:** `brain_connectome.py` — `valence` yalnız `pn_p`'ye (koku) bağlıdır; `taste/touch` yalnız `delta`'yı (öğrenme) sürer. `C=0` iken PN girdisi sabit Poisson (3 Hz): dönüş süreci **durağan ve konumdan bağımsız**. Yer/rota belleği yok. | O3 = eşdeğerlik + kör temel çizgi (§3.3). "Tekrar harita" sorusu kapı M1'e ertelendi (§8). |
| Z-02 | Tek deneme sınırı 60 sn (§2.4); R=5 (§4.2) | **H:** kör gezgin (World fiziği, 20 000 deneme, başlangıç–hedef ≥14): p_hit = 0,237 (20 sn), 0,343 (30 sn), **0,576 (60 sn)**; R=5 bölgesine giriş 0,654 / 0,800 / **0,958**. 60 sn'de O2'nin "arama" ölçümü tavana yapışır, O3 etki odası daralır. | Süre ızgarası {15,20,25,30,40} sn; kural: kör p_hit'in 0,20–0,40 kaldığı en küçük T (aday 25). Hesap bütçesi de 2–3 kat düşer. |
| Z-03 | O1a "yoğunluk yola paralel artsın" (§3.2) | **K:** hareket kuralı yalnız iki anten farkına bakar. Salt yanal Gauss profilli bir şerit, yolun *üzerindeyken* sol–sağ farkı vermez; yön bilgisi boylamsal gradyandan ve eğik gidişten gelir. Referans doğrulaması yok. | İz alanı = yanal sınırlı tüp × hedefe doğru artan boylamsal terim; **referans karşılaştırıcı** (elle kurulmuş, aynı motor kuralı) çözülebilirlik kapısıdır (§3.1, G1). Çapa oyunu O1-R (tek Gauss kaynak) eklendi. |
| Z-04 | "Duvar zıplaması gizli işaret olmasın" (§2.3-4) diye *kural*, mekanizma yok | **K:** `_walls` yönü yansıtıp konumu kıstırır; hedef hep uç duvarın karşısındaysa yansıma yardım eder. | Başlangıç, hedef ve yön rastgele; ayna çiftleri; hedef kenar payı ≥6; test: kör başarı ayna yarılarında eşit (§2.6, T-5). |
| Z-05 | §0/§7.2/§12 duyu katmanı → oyun sırası; §17 önce prototip | **T:** çelişki. | Oyunlar L0'da; duyu katmanları (S2–S5) sonraki, ön-kayıtlı karşılaştırma (K-021). |
| Z-06 | +0,15 etki eşiği "keyfî başlangıç", örnek sayısı sabit (24×16×2 tohum) | R-6: kural, kullanılmadan önce sıfır-etki/bilinen-etki benzetimi ister. | Oyun-başına güç benzetimi (`power_odor.py`, gerçek değerlendirici) ön-kayıttan önce zorunlu; null'da hepsini-geçme ≈ 0, bilinen etkide ≥0,90 (§5, G5). |
| Z-07 | "Canlı ve harita hiyerarşik bootstrap" (§9.3) | `stats.py` canlı-kümelidir; harita rastgele etken olarak modellenmemiş. | **Birim = canlı**, kollar **canlı içi eşli**, haritalar sabit blok (ayna çiftleri); ikincil: harita-bazlı döküm ve ayrık eğitim/test haritası. Eşli küme bootstrap/işaret-çevirme permütasyonu eklenir (§5.2). |
| Z-08 | K0'da tohum cümlesi çelişkili | **T:** "30/31 tekrar kullanılsa bile yeniden seçilmesin" anlaşılmıyor. | Tohum kaydı (§2.7): 30/31 Evre 2b'de yandı; oyun tohumları ayrı aralıklardan, ön-eğitim ve test tohumları ayrı. |
| Z-09 | RNG akışları ayrımı (R30) belirtilmiş, mekanizma yok | **K:** `Creature.motor` gürültüyü `world.gen`'den çeker; aynı üreteç yerleşim ve (forage'da) yeniden doğuşu da sürer. | `noise_gen`/`layout_gen` ayrı; `Creature.motor` `getattr(world,"noise_gen",world.gen)` — eski `World` için **bit-bit aynı** (S0 regresyon testi). |
| Z-10 | Decoy/gerçek hedef ödülü | **K:** `reward_by_odor` koku-türü başınadır; "kokusuz ama ödüllü hedef" (O4c) ve aynı kokulu ödülsüz kaynak ifade edilemez. | Kaynak-başı dizi: `src_odor` (−1 = kokusuz), `src_reward`, `src_role`, `src_profile`. |
| Z-11 | Decoy teması denemeyi bitirir mi? (§6.2 belirsiz) | Sönme (extinction) için temas-ödülsüz **tüketim** gerekir; test için ilk-temas seçimi. | Eğitim: decoy tüketilir (dokunma sinyali, ödül yok), deneme gerçek hedefe/zaman aşımına dek sürer; test: öğrenme kapalı, ilk temas. Yeniden-tetikleme koruması (`rearm`) eklendi. |
| Z-12 | O3: "temasta koku bir sonraki adımda" (§5.2) | **K:** mevcut sıra zaten böyle (algı → beyin → hareket → temas; tat/dokunma sonraki adımda). | Sözleşme olarak yazıldı ve **testle** sabitlendi (T-3). |
| Z-13 | Ödül/öğrenme penceresi | **K:** öğrenme yalnız tüketim süresinde (`feed_time`=0,4 sn) olur; kazanılan denemede tüketim fazı olmazsa öğrenme olmaz. | Her temas sonrası tüketim fazı; öğrenme kapalı testlerde de süre bütçesine sayılır (§2.5). |
| Z-14 | Kontrol matrisi C0–C10 × 4 oyun × 5 rejim — öncelik yok | Kombinatoryal patlama; çoğu kontrol istatistiksel kol değil **test**. | Doğrulayıcı kol sayısı oyun başına 4–5 (§4); C7, C9, C10 birim/entegrasyon testi. |
| Z-15 | "ORN kesik" (C3) ile `random` (C2) | İkisi farklı sorular: kör gürültüyle yönelim (anosmik) ve yönelimsiz (random). | İkisi de ayrı kol: **anosmik** (glom ≡ 0, motor/beyin açık) ve **random** (dönüş kazancı 0). |
| Z-16 | Sıfır-koku bölgesinde plastik canlının davranışı | **K:** W yarımküre başına ayrı öğrenilir → öğrenme sonrası sıfır-koku bölgesinde sabit bir dönüş yanlılığı doğabilir; "plastic ≠ random" farkı arama becerisi değil yanlılık olabilir. | Tanı: sıfır-koku bölgesinde canlı başına imzalı ortalama dönüş (raporlanır); O3/O4c kör temel çizgisi hem `random` hem `frozen` ile verilir. |
| Z-17 | Süre/sansür, yol verimi (§9.1) | Tanımlar var, test yok. | Birincil: `p_hit`; ikincil: kısıtlı ortalama süre (RMST, T'ye dek), yol verimi `E=L_düz/L_yol` (açık arenada `L_düz`=|başlangıç−hedef|−temas yarıçapı). |
| Z-18 | O3 "eşit sonuç makul" ama eşdeğerlik ölçütü yok | Ölçütsüz "makul" sonradan yorumdur. | Eşdeğerlik marjı δ_eq (aday 0,10) ön-kayıtta, güç benzetimiyle (§5.3). |
| Z-19 | Hedef duvara yakınsa R diski arena dışına taşar | Asimetri. | Hedef kenar payı = max(3, R+1) = 6. |
| Z-20 | O2 "yumuşak, sınırlı" profil (§4.2) tanımsız | Kenar türevi artefakt yaratır. | `C(d) = A·(1−(d/R)²)³` (d<R), aksi **tam 0.0**; C² süreklidir (§3.2). |
| Z-21 | O2 koşullu "bölgeye girenler" karşılaştırması seçilim yanlılığı | Taslak "eşleşmiş giriş" diyor ama nasıl yapılacağı yok. | **O2-yakın** deneme türü: başlangıç bölgenin dışında R+2 halkasında, yön rastgele, kollar CRN eşli (§3.2). |
| Z-22 | Ön-eğitim her oyunda ayrı mı? | Gereksiz hesap. | Tohum başına **bir** ön-eğitim (A fazı, 12 bölüm, Evre 2b ile aynı), oyunlar `select` ile kopyalar (ön-eğitim ≈ 10 dk). |
| Z-23 | Kaynak/bağlantılar | Taslak `muhammedaliaka/sinek-noronlari` adresine bağlanıyor; bu oturumda erişilen depo `…/sinek-n-ronlar-`. `git push` çıktısı "This repository moved … sinek-noronlari" dedi: **depo yeniden adlandırılmış**, adres uyuşmazlığı bu. İçeriğe (commit `cd51319`) bu oturumdan doğrudan bakılmadı. | Depo adresi **[doğrulandı: yönlendirme]**, commit bağlantısı **[doğrulanmadı]**; kaynakça durumu §10. |
| Z-24 | İş yükü: "3 072 deneme × 3 000 adım" varsayımı | 60 sn ve ölçülmemiş hız. | Ölçülen alt sınır ≈1,4 bin canlı-adım/sn (Evre 2b s30); T=25 sn ile oyun-tohum başına ≈ 25 dk (§7). Gerçek hız pilotta yeniden ölçülür. |

---

## 2. Bağlayıcı sözleşmeler

### 2.1 Bilgi sınırı
Beyin yalnız `brain.step(glom, taste, touch, learn)` alır (API değişmez). `glom` = iki antendeki glomerül aktivasyonu (alandan hesaplanır), `taste` = işaretli tat, `touch` = 0/1. **Beyne asla** hedef/decoy koordinatı, en kısa yol, oyun adı, "yanlış" etiketi, gelecekteki ödül, koku ısı haritası, deneme zamanı veya konum verilmez. Birim test: `brain.step`'e giden argümanlar casusla izlenir (T-4).

### 2.2 Dünya adımı (nedensel sıra)
1. `sense()` — mevcut konum/yönelimden anten okuması (alan + varsa temasa-bağlı koku). 2. Beyin adımı → `V`. 3. Motor → hareket (+ duvar). 4. Temas saptanır. 5. **Temas etkisi (tat, dokunma, temasa-bağlı koku) en erken bir sonraki adımın 1. aşamasında görülür.** Bir temas, kendi karar adımını geriye dönük değiştiremez.

### 2.3 "Koku yok" tanımı
Dünya düzeyinde: alan değeri `C` ve `glom` **tam 0.0** (bit düzeyi). Beyin düzeyinde: PN bazal 3 Hz Poisson ateşlemesi vardır ve "koku yok" demek **kokuya bağlı artış yok** demektir; bazal etkinlik raporlarda ayrı etiketlenir. (R02)

### 2.4 RNG akışları
`layout_gen` (yerleşim; yalnız sıfırlamada), `noise_gen` (motor gürültüsü; adım başına `B` sayı), beyin üreteci (adım başına sabit sayıda çekim). Hiçbir akış durumdan bağımlı sayıda sayı tüketmez → **CRN eşleştirmesi mümkün**: aynı tohum, aynı canlı sırası, aynı yerleşim → kollar yalnız karşılaştırılan etkende ayrışır.

### 2.5 Deneme yapısı
`arama → (temas) → tüketim → bitti`. Tüketim: `feed_time` boyunca hareketsiz, tat/dokunma/temasa-bağlı koku sunulur, öğrenme (açıksa) çalışır. **Test** denemeleri ilk temasta biter (Evre 2b seçim testi gibi), **eğitim** denemeleri hedef temasında tüketimle biter; decoy tüketilir ve `rearm` yarıçapı (temas+1,0) dışına çıkılınca yeniden etkinleşir. Zaman aşımı = *sansürlü gözlem*, öğrenme başarısızlığı değil. Enerji sabit.

### 2.6 Yerleşim kuralları
Arena 40×40, hız 8, temas 1,5, anten (0,6; 1,2), `dt=0,02`, hareket okuması `V2_SET` (ε=2,0, kazanç 60) **donmuş**. Başlangıç payı 3, hedef/decoy payı 6, başlangıç–hedef ≥14, hedef–decoy ≥14. Yön düzgün rastgele. Yerleşimler **ayna çiftleri** halinde üretilir (2k özgün, 2k+1 x→L−x aynası). Koku kimliği dengelemesi Evre 2b gibi (`swap`): canlının ödüllü kokusu 0 veya 1. Başlangıç, ilk adımda her iki anten için `C=0` olacak biçimde bölgeden ≥ R+1,34+1,0 uzakta. Eğitim ve doğrulama yerleşim kümeleri ayrı tohumlardan.

### 2.7 Tohum kaydı
* 30, 31: Evre 2b'de yandı (yalnız ön-eğitim *altyapısı* olarak değil, hiçbir yeni doğrulama için kullanılmaz).
* Geliştirme/pilot: 100–149. Doğrulayıcı: oyun başına iki tohum (200-serisi; ön-kayıtta yazılır). Ön-eğitim tohumu ≠ test tohumu.
* Koku çifti seçimi Evre 2b gibi **yalnız eğitimsiz ağ üzerinden** (`calibrate_odors`).

---

## 3. Oyunlar

### 3.1 O1 — kesintisiz koku izi
* **O1-R (çapa, doğrulayıcı değil):** tek Gauss kaynak (σ=8), Evre 1/2'deki duyu: döngünün çalıştığını gösteren temel.
* **O1a düz iz, O1b tek dönüşlü iz:** tüp `C = A·(1−(n/W)²)³₊ · exp(−s_kalan/λ)`; `n` = izin çokgenine yanal uzaklık, `s_kalan` = izdeki kalan yay uzunluğu. Başlangıç değerleri W=4, λ=12, A=1, O1b dönüm sapması h=8 (işaret ayna çiftiyle). **W, λ, A pilotta** şu kuralla seçilir ve dondurulur: referans karşılaştırıcının `p_hit ≥ 0,80` ve anosmik kolun `p_hit` ∈ [0,15; 0,45].
* **O1c (kesintili iz) ve O1d (rüzgâr):** *ertelendi* (R20; yönlü bellek ve rüzgâr duyusu yok; gerçek sinekte bu iş merkezî kompleks gerektirir — kaynakça §10).
* **Referans karşılaştırıcı:** `V_taraf = 0,15·Σ_{g∈hedef kokusu} glom_taraf,g` veren, öğrenmeyen, aynı motor kuralını kullanan beyin kuklası. Bu **elle yazılmış üst sınırdır**, biyolojik kontrol değil (R-11 listesine girer).

### 3.2 O2 — koku yalnız final bölgesinde
`C(d) = A·(1−(d/R)²)³` (d<R), aksi **tam 0.0**; aday R=5, A=1 (R∈{3,5,8} yalnız geliştirmede; doğrulamada tek değer). İki deneme türü:
* **O2-tam:** başlangıç düzgün rastgele (d≥14). Ölçer: bölgeye ilk giriş ve toplam `p_hit`.
* **O2-yakın:** başlangıç bölge dışında R+2 halkasında, yön düzgün rastgele; kollar CRN eşli. **Birincil ölçüm bu**dur: yakın alanda koku katkısı, seçilim yanlılığı olmadan.
* Beklenen dürüst cümle: *"Uzaktan koku rehberliği yok; bölgeye giriş keşifle, son yönelim kokuyla olabilir."*
* **Risk (Z-20 devamı):** R=5'te anten farkı küçüktür; yakın alan yönelimi ε=2,0 doğrusal okumayla zayıf kalabilir. Pilot, referans karşılaştırıcıyla "alan ısrarla çözülebilir mi"yi önce sınar (G1).

### 3.3 O3 — koku yalnız temasta
Alan yoktur; kaynağın kimliği (`src_odor`) temas anında **tüketim süresince** her iki antene sabit seviyede (glom ≈ 0,98) sunulur. 2×2: A (ödül+koku), B (ödül, koku yok), C (ödülsüz+koku), D (ikisi de yok). Her canlı ardışık 16 denemelik bir **oturum** koşar; her denemede hedef konumu yeni; plastic kolda ağırlıklar oturum boyunca korunur. **Bağlayıcı yorum:** (i) ön-temas `glom` tüm denemelerde ≡ 0.0 (G3), (ii) kollar arası `p_hit` farkı eşdeğerlik marjında (E3), (iii) kör temel çizgi `p_hit(T)` olarak raporlanır. **Üstünlük ölçütü yoktur.** Kollar arasında anlamlı fark çıkarsa (ör. Z-16 yanlılığı) bu önce bir yanlılık/hata aramasının konusudur (R-4).

### 3.4 O4 — yanıltıcı koku
* **O4a — sönüm (extinction), gerçek hedef yok:** decoy = canlının *ödüllü* kokusu, ön-eğitimdeki gibi Gauss (σ=8), ödülü 0. Aşamalar: **P0** çekim testi (öğrenme kapalı, decoy'a `p_hit` vs anosmik kör düzey) → **P1** aldatıcı eğitim (decoy tüketilir, öğrenme plastic'te açık, frozen'da kapalı; n bölüm) → **P2** testler (3., 6., 12. bölüm). Birincil ölçü: decoy'a `p_hit` (ve eğitim bölümlerinde decoy temas sayısı).
* **O4c — decoy + kokusuz gerçek hedef:** gerçek hedef `src_odor=−1`, ödül 1. Test: öğrenme kapalı, ilk-temas seçimi (decoy / gerçek / yok). Birincil ölçüler: decoy-ilk oranı (plastic < frozen) ve gerçek-ilk oranının kör düzeyden **aşağı düşmemesi** (eşdeğerlik değil, aşağı-tarafsızlık).
* **O4b (ikisi de kokulu), kimlik değişimi, ayna/transfer, ödül-geri-geldi:** ikinci aşama (kapı: O4a/O4c tamam).
* **Çekim odası kapısı (G4):** frozen decoy `p_hit` − anosmik `p_hit` ≥ 2δ olmalı; değilse O4 *değerlendirilemez* (tavan: tek azalma yönü).

---

## 4. Kollar ve kontroller

| Kol | Tanım | Gerekli olduğu oyunlar |
|---|---|---|
| `plastic` | ön-eğitimli, öğrenme açık | O3, O4 |
| `frozen` | ön-eğitimli, öğrenme kapalı (eta=0) | hepsi |
| `random` | dönüş kazancı 0 (yönelimsiz) | hepsi |
| `anosmik` | `glom ≡ 0` (alan hiç okunmaz), beyin/motor açık | O1, O2, O4 |
| `referans` | elle kurulmuş karşılaştırıcı | O1, O2 (çözülebilirlik kapısı) |

Taslak C7 (zaman permütasyonu), C9 (kaydet/yükle), C10 (görselleştirme) **test**tir, kol değil. Kollar CRN ile eşlidir (§2.4).

**Rejimler:** ön-eğitimli (birincil) ve sıfırdan (`öğrenme hızı`, ikincil). *Öğrenme hızı* (kullanıcının "en hızlı öğrenen" hedefi): sıfırdan öğrenen canlının bölüm başına `p_hit` eğrisinin altında kalan alan ve ölçüte ulaşma bölümü; ön-kayıtlı ikincil uç noktadır.

---

## 5. Ölçütler, istatistik, güç

### 5.1 Oyun başına karar kuralı (şablon; eşikler ön-kayıtta dondurulur)
Her oyun için: **G** (geçerlilik kapıları) ve **P** (birincil ölçütler), "iki doğrulayıcı tohumda da hepsi geçmeli" (Evre 2b ile aynı).

| Oyun | Geçerlilik kapıları | Birincil ölçütler |
|---|---|---|
| O1 | G1 referans `p_hit≥0,80` ve anosmik ∈[0,15; 0,45]; G0 S0 regresyon | P1 frozen(koku açık) − anosmik: eşli %99 GA alt sınırı >0 ve ≥δ₁; P2 aynısı vs `random`; P3 ayna yarılarının *her ikisinde* fark >0 |
| O2 | G1 tasarım-zamanı (referans, O2-yakın `p_hit≥0,80`, geliştirme tohumunda n≥900) + doğrulayıcı tabanı referans ≥0,70 (K-024); G2 **CRN: ilk koku alımına dek yörüngeler bit-bit aynı (%100)**; kör bölgeye giriş ∈[0,3; 0,9] (O2-tam, tasarım-zamanı) | P1 O2-yakın: koku açık − anosmik `p_hit` farkı (eşli, α=0,01, ≥δ₂) |
| O3 | G3 ön-temas `glom≡0` (%100), temas→etki sırası testi | E3 tüm kol çiftlerinde `|Δp_hit|` GA ⊂ [−δ_eq, δ_eq]; kör düzey raporu |
| O4a | G4 çekim odası | P1 plastic − frozen decoy `p_hit` (eşli, ≤ −δ₄); ikincil: bölüm eğilimi |
| O4c | G3-benzeri, G4 | P1 decoy-ilk oranı plastic<frozen−δ₄; P2 gerçek-ilk oranı kör düzeyin δ_eq altına düşmemeli |

δ₁=δ₂=δ₄ aday 0,15; δ_eq aday 0,10. Bunlar **keyfî başlangıçtır**; §5.3 benzetimi güç ≥0,90 ve null'da hepsini-geçme ≈0 vermezse tasarım (canlı sayısı, deneme sayısı, T) değişir, ölçüt gevşetilmez.

### 5.2 İstatistik
Birim canlıdır; her canlı için kol başına isabet sayısı. Eşli fark `d_i=(h_i^A−h_i^B)/n_deneme`; **canlı-kümeli bootstrap GA** ve **işaret-çevirme permütasyonu** (tek yönlü). `stats.py`'a `paired_cluster_ci` ve `paired_signflip_p` eklenir; ikisi de null ve bilinen-etki testiyle sınanır. Harita etkisi: ayna yarısı ve harita-başına döküm (raporlama). α=0,01, çoklu keşifsel testte etiket.

### 5.3 Güç ve yanlış-pozitif (R-6)
`power_odor.py`: gerçek değerlendirici fonksiyonla; senaryolar: tümü sıfır etki, O1/O2/O4 bilinen etki (δ civarı ve 2δ), O3 sıfır + δ_eq'e eşit sapma. Sonuç `docs/odor_guc_analizi.md`'ye yazılır; **ön-kayıttan önce**.

**Ön bulgu (K-022, `tests/test_odor_eval.py`):** O3 eşdeğerliği kolların CRN ile ortak izde olmasına dayanır; bağımsız kollarda δ_eq=0,10 ve 24×16 tasarımında sıfır etkide geçme ≈%10'dur. Bu yüzden O3 pilotunda kol ayrışma oranı ölçülür ve benzetim o gürültü düzeyiyle koşulur; marj değil tasarım (canlı/deneme sayısı) ayarlanır. Değerlendiriciler: `src/sinek/experiments/odor_eval.py` (`eval_o1/o2/o3/o4a/o4c`).

---

## 6. Elle yazılmış parçalar (R-11)
Sabit ileri hız; "yüksek değerli antene dön" kontrast kuralı (ε=2,0, kazanç 60); rastgele gezinme; dopamin hatası `delta=gate·(0,6·ödül−V)`; temas/tat; oyun alanı fonksiyonları; referans karşılaştırıcı. Kuramsal sınır: bunlar yönelim ve değer güncellemesi içindir; **keşif/bellek/planlama modülü yoktur**.

---

## 7. Hesap bütçesi (ölçülmüş / hesaplanmış, etiketli)
* **Ölçülen alt sınır [doğrulandı]:** Evre 2b s30: 12 310 sn (≤16,7 M canlı-adım) → ≥ ≈1,4 bin canlı-adım/sn, 4 çekirdek CPU, iki koşu aynı anda.
* **Hesap:** T=25 sn → 1 250 adım; oyun-tohum başına 4 kol × 24 canlı × 16 deneme × 1 250 ≈ **1,9 M adım ≈ 25 dk**; O3 oturumları ve O4 eğitimi dahil dört oyun ≈ 2–3 saat/tohum, ön-eğitim ≈ 10 dk/tohum. GPU gerekmez; iş yükünü pilotta yeniden ölçeriz.

---

## 8. Aşamalar ve kapılar

| Kapı | İçerik | Durum |
|---|---|---|
| G0 / S0 | Eski `World` + `Creature` davranışının **bit-bit** korunması (regresyon) | **tamam**: `agent.py` değişikliğinden önce/sonra aynı özet (sentetik `008a03d53b45c166`, bağlantı-tabanlı `a5eb9525e58a5bfa`, bu makinede); kalıcı test `tests/test_s0_regression.py` (takma ad yolu bit-bit eşit) |
| G1 | Oyun fiziği birim testleri: sıfır-sızıntı, temas sırası, yerleşim değişmezleri, RNG ayrımı, bilgi sınırı casusu, CRN | **tamam**: `src/sinek/games/` + `tests/test_games_world.py` (tam test paketi geçti) |
| G2 | Kör temel çizgi (World fiziğiyle uyumlu) + referans karşılaştırıcı çözülebilirliği | **tamam (ilk bakış, T=25 sn, dev tohumu 101, 400 deneme)**: kör ≈0,30; referans O1R 0,82 · O1a 0,96 · O1b 0,94 · O2tam 0,70 · O2yakın 0,83; anosmik = kör (CRN). Kör gezgin iki bağımsız uygulamada uyuşuyor (testle) |
| G3 | Pilot (dev tohumları): T, W, λ, R seçimi; sıfır-koku dönüş yanlılığı tanısı | **araçlar hazır** (`odor_pretrain`, `odor_pilot`, `odor_session`, `odor_bias`); dev ön-eğitimi (tohum 100) sürüyor, pilot koşuları sonra |
| G4 | `power_odor.py` + `docs/odor_guc_analizi.md` | **araç hazır** (`odor_eval.py` değerlendiriciler + `power_odor.py` benzetim, testli); parametreler pilottan gelince koşulur |
| G5 | Oyun-başına ön-kayıt commit | bekliyor |
| G6 | Doğrulayıcı koşular (O1→O2→O3→O4) | bekliyor |
| M1 | Yeni devre kapısı: kısa süreli yön belleği / sistematik keşif — O3/O4c boş sonuçta veya O1c için | **kapsam dışı (şimdilik)** |
| S2–S5 | ORN/anten lobu katmanları (taslak §7) | oyunlardan sonra; ön-kayıtlı L0'a karşı karşılaştırma |

**Ertelenenler ve nedenleri:** engelli arena/çıkmaz (hareket kuralı engel planlamaz; ek karıştırıcı), rüzgâr/kesintili iz (duyu ve bellek yok), görsel arayüz (olay kaydı tutulur, arayüz sonra; arayüz hiçbir zaman ajana girdi olmaz), O4b ve transfer.

---

## 9. Taslağın bölümleri → durum
§0–1 korundu (Z-23/Z-01 notlarıyla) · §2.1–2.3 korundu, §2.4 **değişti** (Z-02), §2.5 korundu (ön-eğitim ayrı, Z-22) · §3 O1: **değişti** (Z-03) · §4 O2: **değişti** (Z-20/21) · §5 O3: **yeniden çerçevelendi** (Z-01) · §6 O4: **değişti** (Z-10/11) · §7 duyu katmanları: **ertelendi** (Z-05) · §8 kapılar/kontroller: **sadeleşti** (Z-14/15) · §9 ölçüm: **somutlaştı** (Z-06/07/17/18) · §10 risk sicili: **aynen geçerli** · §11 arayüz: ertelendi, değişmezleri geçerli · §12 sıra: **değişti** (Z-05) · §13 paketler: kapılara (G0–G6) eşlendi · §14 karar ağacı: geçerli · §15 çıktı yapısı: geçerli (kullanıldıkça oluşur) · §16 kaynakça: **[doğrulanmadı] etiketli** (§10).

---

## 10. Kaynakça durumu (bu oturumda arama ile)
* Odor motion sensing (Kadakia ve ark., *Nature* 611, 2022) — **[doğrulandı]**.
* Vector-based strategy for olfactory navigation (Siliciano ve ark.) — bioRxiv 2025 **[doğrulandı]**; taslaktaki PMC kimliği ve dergi sürümü **[doğrulanmadı]**.
* Working memory / evidence integration (Kathman, Lanz, Freed, Nagel) — bioRxiv **[doğrulandı]**; taslaktaki PMC kimliği **[doğrulanmadı]**.
* Wind history … free-flying Drosophila — veri kaydı (Dryad) bulundu, makale sürümü **[doğrulanmadı]**; Wind gates (bioRxiv) **[doğrulandı]**.
* Bu çalışmalar yalnız tasarımda hangi etkenlerin göz ardı edilmemesi gerektiğini gerekçelendirir; oyunun gerçek sinek davranışı olduğunu göstermez (R-10).
