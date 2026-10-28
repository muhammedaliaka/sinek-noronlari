# Karar defteri, hata sicili ve değişiklik günlüğü

Bu dosya projenin **hafızasıdır**: neyi neden yaptık, neyi yanlış yaptık, bir daha yapmamak için ne ekledik. Amaç, aynı hatayı iki kez yapmamak ve bir karar
gerektiğinde geçmişteki benzer kararı hızlıca bulmaktır.

## Nasıl kullanılır

1. **Karar vermeden önce:** Bölüm 3 (değişmez kurallar) ve Bölüm 2 (hata sicili) okunur; Bölüm 1'de benzer karar aranır (ör. `grep -n "ölçüt" docs/karar_defteri.md`).
2. **Karardan sonra:** Bölüm 1'e yeni kayıt (K-nnn) eklenir: bağlam, karar, alternatifler, gerekçe, sonuç/durum, ders. Commit karma değeri yazılır.
3. **Hata bulunduğunda:** Bölüm 2'ye yeni kayıt (E-nn) eklenir; *önlem* sütunu bir test, koruma ya da kural içermelidir (yalnız "dikkat edeceğim" geçerli önlem sayılmaz).
4. **Durum etiketleri:** `doğrulandı` (sonuç beklentiyi doğruladı), `yanlış çıktı` (karar geri alındı), `bekliyor` (henüz sonuç yok), `kural` (artık değişmez kural).

---

## 1. Karar kayıtları

| Kod | Tarih | Bağlam | Karar | Alternatifler | Sonuç / durum | Ders |
|---|---|---|---|---|---|---|
| K-001 | 10-27 | Projenin ilk adımı | Önce **sentetik** (rastgele kablolu) mantar cismi ile koku/ödül öğrenme, silinmeme, bellek, tersine çevirme (Evre 1); gerçek veriye sonra geç | doğrudan tam beyin | iki bağımsız tohumda 6/6 ve 6/6 (`ba3a6e0`..`e7f77c6`) — `doğrulandı` | önce küçük, ölçülebilir çekirdek; sonra gerçek veri |
| K-002 | 10-27 | Evre 1 yeni tohumlarla doğrulanacak | **Ölçütler koşudan önce yazılır** ve koşudan sonra değişmez; başarısızlık da raporlanır | koşudan sonra ölçüt düzeltmek | tüm sonraki evrelerde uygulandı — `kural` | bkz. K-005 |
| K-003 | 10-27 | Evre 1 hata sonrası | Hatalı koşuları sonuçlara **katma**, nedenini yaz (`evre1_sonuclar.md`); hata sonrası yeni, hiç kullanılmamış tohumlar (10, 11) | hatalı koşuyu "pilot" diye tutmak | `doğrulandı` | E-01 |
| K-004 | 10-27 | Evre 2'ye geçiş | Gerçek veri olarak **MaleCNS v1.0** sağ yarımküre MB alt ağı; sürüm+md5 sabit; lisans CC BY doğrulandı (`f7ebc34`) | FlyWire / hemibrain | alt ağ: PN 123, KC 2 045, APL 1, MBON 48, DAN 161 — `doğrulandı` | veri sürümü sessizce değişmesin: uyuşmazlıkta hata |
| K-005 | 10-27 | Evre 2 (v1) sonuçları geldi: tohum 20 → 5/6, tohum 21 → 4/6 | Hüküm **"Evre 2 ölçütü başarısız"**; açıklamalar koşulardan *sonra* yapıldığı için post-hoc diye etiketlendi; ölçütler değiştirilmedi (`5310740`) | ölçütü gevşetmek | `kural` | başarısızlığı olduğu gibi yaz; açıklamayı kanıt gibi sunma |
| K-006 | 10-27 | v1 geliştirme: koku çifti seçimi "kazananın laneti"ne uğradı (ilk-geçiş skoru 0,018 → ikinci ölçüm 0,091) | iki aşamalı koku çifti seçimi; yalnız **eğitimsiz ağın iç eğilimine** göre | tek geçiş | `doğrulandı` | seçim ölçüsünü bağımsız bir ikinci ölçümle doğrula |
| K-007 | 10-27 | v1 geliştirme: tek yönlü baskılanma eğitimle eriyordu | iki yönlü sınırlı plastisite (baskılanma + geri yükleme), W ∈ [0, W0] (`420d0b3`) | yalnız baskılanma | betimsel ablasyonda (tek koşu) geliştirmedeki "erime" tam protokolde net görülmedi; geri yükleme terimi tersine çevirmeyi hızlandırıyor gibi göründü (`53caabf`) — `kısmen doğrulandı` | ablasyonu da koş |
| K-008 | 10-28 | Kullanıcı: "ölçüt gücünü artırmak için yeni ön-kayıtla başla" | **Evre 2b**: yeni ön-kayıt (`evre2b_plan.md`), yeni tohumlar 30 ve 31; v1 sonuçlarına dokunulmaz | v1'i yeniden koşmak | tohum 30 ve 31'de 7/7 ve 7/7 (`docs/evre2b_sonuclar.md`) — `doğrulandı` | v1 hükmü kalır; yeni ön-kayıt eski başarısızlığı geri almaz |
| K-009 | 10-28 | Neden düşük güç? Naif canlılar dönüp duruyor (seçim oranı 0,17–0,20; rastgele politika 0,69) | Teşhis: normalize kontrast `(Vs−Vd)/(\|Vs\|+\|Vd\|+ε)` ε=0,05 iken gürültüyü büyütüyor (sd(Vs−Vd) ≈ 0,145 ≫ ε). Çözüm: **ε=2,0** (yaklaşık doğrusal okuma) | zamansal yumuşatma | eğitimsiz seçim oranı 0,6–0,7'ye çıktı (pilot) — `doğrulandı` | önce neden ölç, sonra düzelt |
| K-010 | 10-28 | `tau_smooth` (yumuşatma) denendi | **Atıldı**: yönelim difüzyonu sıfır-frekans gürültü gücüne bağlı, yumuşatma azaltmaz (kuram + ızgara) | tutmak | `yanlış çıktı` | E-08 |
| K-011 | 10-28 | A rolü hep koku 0 → koku yanlılığı tercihe karışıyor | **Rol dengelemesi** (`--swap-roles`); **canlı-düzeyi (küme) bootstrap/permütasyon**; **geçerlilik kapısı G** (seçim oranı ≥ 0,40); naif karşılaştırma plastic+frozen havuzlanır | v1 istatistiği | testlerle tip-I hata ve kapsama sınandı (`d013ce7`) — `doğrulandı` | bağımsız olmayan denemeleri bağımsız sayma |
| K-012 | 10-28 | A3 ölçütü ("GA 0,5'i kapsar") kendiliğinden ~%4–5 başarısız | önce eşdeğerlik ±0,15, güç analizi bunu **fazla dar** buldu → **±0,20** (ilgilendiğimiz en küçük etki) (`c93b639`) | olduğu gibi bırakmak | benzetimde sıfır-etki: tüm ölçütleri geçme 0,00; güçlü etki 1,00 — `doğrulandı` | E-04 |
| K-013 | 10-28 | Kazanç (60 vs 80) nasıl seçilecek? | Seçim kuralı **prova sonuçlarından önce** commit edildi (`a2c859e`); prova (tohum 3, 24 canlı) → iki kazanç da eğitimsiz seçim oranı < 0,50 → "ikisi de elenirse 60" | gözle seçmek | kazanç **60**; her iki kazanç da provada 7/7 geçti (ölçüt sayılmaz) — `doğrulandı` | karar kuralını sonuçtan önce yaz |
| K-014 | 10-28 | Güç ızgarası: pilot-benzeri etkide 24×8 tasarımı yalnız %59 güç | **16 deneme** (24×16: %94) | 36×12, 48×8 | `evre2b_plan.md` §4.5; doğrulayıcılarda etki benzetimdeki "güçlü" senaryoya yakın çıktı, 7/7 — `doğrulandı` | tasarımı kayıttan önce benzetimle sına |
| K-015 | 10-28 | Kod incelemesi (code-review) bulguları | gerçek hatalar düzeltildi (`--quick` tek sayıda canlı, checkpoint ödülü, E1 tasarım denetimi, test dünyası set_swap); `V2_SET` dondurulmadan v2 koşusu başlamasın diye **koruma** (`3ce0808`, `994b444`) | görmezden gelmek | `doğrulandı` | kayıttan önce bağımsız kod incelemesi |
| K-016 | 10-28 | Birleştirme/büyütme stratejisi (kullanıcı: 300 bin+ nöron, iki büyük haritayı birleştir) | **Tek omurga (MaleCNS) + hedefli modül + çapraz doğrulama**; ham birleşim yalnız stres testi; iddia nöron sayısına değil ölçülebilir görevlere (`birlestirme_risk_analizi.md`) | ham birleşim | `bekliyor` | sayıyı toplamak organizma yapmaz |
| K-017 | 10-28 | Kullanıcı kararları: donanım, hedef, nöron sınırı | GPU (RTX 3070 Ti Mobile 8 GB + 32 GB RAM) **şimdilik kullanılmıyor**; kullanıcı "kullanılacak" deyince sohbet kapanır, bu yüzden bağlam depoda olmalı (devir listesi). Hedef: oyunda **en akıllı / en hızlı öğrenen** beyin; **nöron sınırı yok**; ayrıntı kararları bana bırakıldı (omurga MaleCNS; gerçek zaman şart değil). İş bitince tek paragraflık sade özet (`arkadasa_ozet.md`) | sayı hedefi (300 bin+) | `bekliyor` | sayı amaç değil sonuç (R-9) |
| K-018 | 10-28 | Evre 2b doğrulayıcı sonuçları | Hüküm: **Evre 2b ölçütü başarılı** (tohum 30 ve 31, 7/7 ve 7/7); ön-kayıtlı kural uygulandı, ölçütlere dokunulmadı. Etki orta (0,72–0,74 → 0,26–0,28), v1'in 0,90'ından düşük (farklı okuma). E1 ana karar kuralı dışında, sonuç bekleniyor | — | `doğrulandı` | başarı da etki büyüklüğüyle ve sınırlamalarıyla raporlanır |
| K-019 | 10-28 | Kullanıcı dört koku oyunu taslağı getirdi (O1 iz, O2 yalnız final, O3 yalnız temas, O4 yanıltıcı) ve eksikleri düzeltip işe koyulmamı istedi | Taslak değişmeden `docs/girdi/` altında saklandı; kodla karşılaştırılıp **24 bulgu** (Z-01…Z-24) çıkarıldı; bağlayıcı sürüm `docs/dort_koku_oyunu_plani.md`. Başlıca değişiklikler: O3 üstünlük değil **eşdeğerlik/kör temel çizgi**; süre sınırı kör başarıya göre ayarlanır (60 sn → tavan); O1 izi boylamsal gradyanlı + referans karşılaştırıcı kapısı; engel/rüzgâr/UI ertelendi | taslağı olduğu gibi uygulamak | `bekliyor` (uygulama G0'dan başlar) | plan da bir ölçümdür: kayıttan önce kodla ve hesapla karşılaştır (E-11) |
| K-020 | 10-28 | Oyun kolları nasıl eşlenecek? | **CRN (ortak rastgele sayı) eşleştirmesi:** koku açık ve koku kapalı (anosmik) kollar aynı canlı/yerleşim/gürültü ile koşar; ilk gerçek koku alımına dek yörüngeler **bit-bit aynı** olmalı (sızıntı denetimi). Gürültü ve yerleşim ayrı RNG akışları | bağımsız örneklemler + istatistiksel eşdeğerlik | `bekliyor` | sızıntıyı istatistikle değil değişmezle yakala |
| K-021 | 10-28 | Taslakta duyu katmanı (ORN/anten lobu) oyunlardan önce (§7.2/§12) ama §17 önce prototip diyor | Oyunlar **mevcut doğrudan-glomerül (L0)** girişte koşar; gerçekçi duyu katmanı ayrı, ön-kayıtlı karşılaştırma olarak sonra | önce duyu katmanı | `bekliyor` | regresyon riskini azalt: bir seferde bir değişken |
| K-022 | 10-28 | Oyun değerlendiricileri (`odor_eval.py`) yazılırken: O3 eşdeğerliği (δ_eq=0,10, 24 canlı × 16 deneme) kollar **bağımsız** olsaydı sıfır etkide bile yalnız ≈%10 geçiyor (benzetim); kollar CRN ile çoğunlukla ortak izdeyse ≈%95-100 | O3 anlamı CRN eşleşmesine bağlı; O3 pilotunda **kol ayrışma oranı** (kolların aynı denemede farklı sonuç verdiği oran) ölçülür ve güç analizi (G4) bununla koşulur; δ_eq ve canlı sayısı **ölçütü gevşetmeden** tasarımla (canlı/deneme artırarak) ayarlanır | δ_eq'i güç yetsin diye büyütmek | `bekliyor` (pilot O3) | eşdeğerlik testi güç ister: önce güç, sonra marj (R-6); testler: `tests/test_odor_eval.py` |
| K-023 | 10-28 | G3 pilotu (O1a/O1b/O2near/O2full, ön-eğitim tohumu 100, oyun tohumu 101) planın önceden yazılı seçim kurallarına karşı | Referans O1a 0,97 / O1b 0,95 ≥ 0,80 ve anosmik 0,24 / 0,23 ∈ [0,15; 0,45] → **W=4, λ=12, A=1 donduruldu**; O2 yakın referans 0,812 (n=192) ve 0,828 (n=960, tohum 105) ≥ 0,80 → **R=5 donduruldu** (R=3/8 taranmadı: kuralı sağlayan varsayılan varken sonradan R aramak serbestlik derecesi ekler); T=25 sn (kör ≈0,30). Sıfır-koku dönüş yanlılığı yok (|ort. kontrast| 0,0013, ≈0,08 rad/s). Ayrıntı `docs/odor_pilot_sonuclari.md` | R/W/λ'yı pilotta 'daha iyi' bulana ayarlamak | `bekliyor` (O1/O2 ön-kayıt) | kural önce yazıldı, sonra uygulandı; sonuç dondurulmuş varsayılanları değiştirmedi |
| K-024 | 10-28 | O2 referans kapısı (≥0,80) doğrulayıcıda nokta tahminiyle uygulanırsa: gerçek referans başarısı 0,83 iken n=384 denemede kapı rastgele ≈%10-35 kez düşer (güç benzetimi) | Çözülebilirlik **tasarım-zamanı kapısı G1** (geliştirme tohumu, n=960, ≥0,80: sağlandı) ile **doğrulayıcı tabanı** (referans ≥0,70, 'dünya bozuk mu' denetimi) ayrılır; O1'de 0,80 kalır (referans 0,95) | kapıyı olduğu gibi bırakıp %"şans kapısı" kabul etmek | `bekliyor` | kapı da bir ölçümdür: sıfır-/bilinen-etkide benzetimle sına (E-12) |
| K-025 | 10-28 | O3/O4 pilotları (G3) + çekim ölçümleri: O3 kol ayrışması 1. denemede 0, son denemelerde %19-35; O4 çekim (frozen − anosmik decoy-ilk) O4a +0,253/+0,271, O4c +0,268/+0,260, birleşik ≈+0,265 (≈1,8δ) — plandaki geçici çekim kapısı ≥2δ=0,30 bu gerçek çekimi ≈%25 olasılıkla geçerdi | **(1) O4 çekim kapısı = manipülasyon denetimi:** frozen − anosmik ≥ δ (0,15), p<0,01, %99 GA alt sınırı >0 (güç benzetimi: tam sönüm gücü 0,99; çekim yoksa kapı 0,00). **(2) O3: 4 kopya × 16 deneme (canlı başına 64)** — 2 kopyada eşdeğerlik geçme 0,90, 4 kopyada 1,00. **(3) O4 testi canlı başına 32 deneme** (O4c P2 gücü 0,82-0,89 → 0,99). Tohumlar: O3 230/231, O4a 240/241, O4c 242/243 | kapıyı 2δ bırakıp %25 şans kapısına razı olmak; oyun parametresini (genlik/σ) çekim yükselsin diye ayarlamak (bu da ön-kayıt öncesi serbestlik derecesidir) | `bekliyor` (O3/O4 ön-kayıt) | **Dürüstlük notu:** kapı eşiği pilot çekimi görüldükten sonra, ama doğrulayıcı verisinden önce ve önceden yazılı bir ilkeyle (kapı = manipülasyon denetimi; asıl ölçüt zaten ≥δ azalma ister) değiştirildi; bu değişiklik burada ve `odor_guc_analizi.md`'de açıkça kayıtlıdır |

---

## 2. Hata sicili

| Kod | Tarih | Hata | Nasıl fark edildi | Etki | Önlem (kod/test/kural) |
|---|---|---|---|---|---|
| E-01 | 10-27 | `choice_test` yeni `World` kurup koku desenlerini **test tohumundan** üretti: test kokuları eğitimdekilerle aynı değildi (`a46cd29`) | tohum 1'de eğitilmiş canlılar A'yı anlamlı biçimde **az** seçti (0,34); "gürültü" demek yerine neden arandı | ilk iki Evre 1 koşusu geçersiz, sonuca katılmadı | `World(patterns=...)`; seçim testi, yol kaydı ve checkpoint yükleme eğitim desenini kullanır; regresyon testleri |
| E-02 | 10-27 | `--set cbrain.restore=false` → `bool("false")` = True: ablasyon koşusu ana koşuyla aynıydı (`f5dcdc0`) | ablasyon sonucu ana koşuyla birebir aynı çıktı | ilk ablasyon geçersiz; yeniden koşuldu ve belgeye yazıldı | `apply_override` bool ayrıştırma; `tests/test_evre2_overrides.py` |
| E-03 | 10-27 | Koku çifti seçiminde kazananın laneti (K-006) | ilk-geçiş skoru 0,018, ikinci ölçüm 0,091 | v1 geliştirmesinde şişmiş çift | iki aşamalı seçim |
| E-04 | 10-28 | A3 "GA 0,5'i kapsar" ölçütü kusurlu (sıfır yanlılıkta ~%5 başarısız; veri arttıkça önemsiz yanlılıkta da başarısız); ilk düzeltme (±0,15) canlılar arası değişkenlikte fazla dardı | güç analizi (`power2b`) | v1'de A3 tohum 21'de kaldı | eşdeğerlik ±0,20; **yeni ölçüt = önce sıfır-etki/bilinen-etki benzetimi** (kural R-6) |
| E-05 | 10-28 | `V2_SET = []` kalmıştı: Evre 2b hareket okuması *uygulanmadan* doğrulayıcı koşu başlatılabilirdi | kod incelemesi | engellendi, koşu başlamadı | `evre2.main` korumasıyla SystemExit; `test_v2_frozen_configuration` |
| E-06 | 10-28 | `--quick` tek sayıda canlı (3) ile rol dengelemesi hata veriyordu; checkpoint `_rewards`'u saklamıyordu | kod incelemesi | duman testi çöküyordu; devam ettirilen eğitimde ödül yanlış olabilirdi | `quick` 4 canlı; checkpoint `rewards`; `_swap_mask` çift sayı denetimi |
| E-07 | 10-28 | 24×8 tasarımın pilot-benzeri etkide gücü yetersizdi (%59), plan başlangıçta 8 deneme içeriyordu | tasarım ızgarası (`power2b --design`) | doğrulayıcı koşudan önce düzeltildi: 16 deneme | güç analizi kayıttan önce zorunlu (R-6) |
| E-08 | 10-28 | `tau_smooth` önce *kodlandı*, sonra kuramla işe yaramadığı görüldü | ızgara araması + kuram | birkaç koşu boşa gitti | **önce 10 dakikalık kuram/hesap kontrolü, sonra kodlama** (R-8) |
| E-09 | 10-28 | Konteyner yeniden başlayınca uzun koşular öldü; yeniden başlatılabilir kontrol noktası yok | koşu logu durdu | birkaç saat kayıp (sonuçlar deterministik olduğundan tekrar koşuldu) | iş V-03: aşama başına kontrol noktası (**yapılmadı**, ölçek büyütmeden önce zorunlu) |
| E-10 | 10-28 | Kullanıcının getirdiği raporda BANC için 188 bin nöron / 199 milyon sinaps; aramam ~160 bin / ~10⁸ gösterdi | web araması | karar etkilenmedi | dış rakamlar [doğrulandı]/[doğrulanmadı] etiketli (R-7); iş V-01 |
| E-11 | 10-28 | Dört koku oyunu **taslağında** plan hataları: 60 sn sınırı tavan etkisi (kör gezgin %58 isabet, R=5'e %96 giriş); O3'te "tekrar harita öğrenme" beklentisi mevcut ajan için mekanik olarak imkânsız (V yalnız koku girdisinden gelir); salt yanal profilli iz sol–sağ karşılaştırıcıya yön vermez; sensör sırası çelişkisi | kodla karşılaştırma + kör gezgin hesabı (`games_blind_check.py`) | kod yazılmadan yakalandı, ölçüt/ön-kayıt etkilenmedi | R-8 uygulandı: süre kör başarıya göre seçilir, O3 eşdeğerlik, referans karşılaştırıcı çözülebilirlik kapısı; `tests/test_games_blind.py` |
| E-12 | 10-28 | Güç benzetimi (`power_odor`) ilk sürümünde canlıya özgü sapmayı referans kolda da uyguladı → O1'de 'kapılar tamam' yalnız %50 çıktı (benzetim artefaktı); ayrıca O2 referans kapısı sınırda (0,81-0,83 ≥ 0,80) olduğundan gerçekte de rastgele düşerdi | benzetimin kapı sütunu beklenmedik %50 verdi; nedenine bakıldı | kod: sapma yalnız canlı kollarına; tasarım: K-024 | `power_odor.py` düzeltildi; O2 kapısı ayrıştırıldı | araç ve kapı birlikte sınanmadan ön-kayda girmez |

---

## 3. Değişmez kurallar (kısa)

* **R-1** Doğrulayıcı koşular, ön-kayıt belgesi commit edilmeden başlamaz; ölçütler ve karar kuralı koşudan sonra değişmez.
* **R-2** Geliştirme ve doğrulayıcı tohumlar ayrıdır; doğrulayıcı tohuma geliştirmede dokunulmaz. Tohumlar tek kullanımlıktır (20, 21 yandı; 30, 31 doğrulayıcı).
* **R-3** Başarısızlık olduğu gibi raporlanır. Koşudan sonra yapılan açıklama post-hoc diye etiketlenir ve hükmü değiştirmez.
* **R-4** Sezgiye ters sonuç gürültü sayılmaz: önce yazılım hatası aranır (E-01, E-02).
* **R-5** Her hata için regresyon testi ya da koruma eklenir.
* **R-6** Yeni bir ölçüt/karar kuralı, kullanılmadan önce **sıfır-etki ve bilinen-etki benzetimiyle** sınanır (yanlış pozitif/negatif oranı).
* **R-7** Dış kaynaktan gelen her rakam [doğrulandı]/[doğrulanmadı] etiketi taşır; doğrulanmamış rakam karar dayanağı olmaz.
* **R-8** Kodlamadan önce kısa bir kuram/hesap kontrolü yapılır; "denersek görürüz" için kod yazılmaz.
* **R-9** Nöron sayısı bir başarı ölçütü değildir; "daha zeki" ancak ön-kayıtlı görev ölçütleriyle iddia edilir.
* **R-10** Gerçek sinek davranışı hakkında iddia yoktur; bilinç iddiası yoktur.
* **R-11** Elle yazılmış (öğrenilmemiş) bileşenler her raporda listelenir.

---

## 4. Değişiklik günlüğü (git geçmişinden)

| Commit | Tarih | Başlık |
|---|---|---|
| `ba3a6e0` | 2026-10-27 | Evre 1: spiking mantar cismi, 2B dünya, koku/ödül öğrenme hattı |
| `308edd4` | 2026-10-27 | Grafikler: yolları A sağda/B solda normalize et, öğrenme eğrisi lejantını düzelt |
| `a46cd29` | 2026-10-27 | Hata düzeltmesi: seçim testi eğitimdeki koku desenlerini kullanmalı |
| `e7f77c6` | 2026-10-27 | Evre 1 sonuç raporu: iki bağımsız tohumda 6/6 ölçüt, hata anlatımı, sınırlamalar |
| `f7ebc34` | 2026-10-27 | Evre 2 altyapısı: MaleCNS v1.0 mantar cismi alt ağı ve bağlantı-tabanlı beyin |
| `420d0b3` | 2026-10-27 | Evre 2: iki yönlü sınırlı plastisite, kalibrasyonlar, ön-kayıt planı |
| `81ee937` | 2026-10-27 | Evre 2: post-hoc ek analiz betiği, veri denetim raporu yenilendi |
| `5310740` | 2026-10-27 | Evre 2: sonuç raporu (5/6 ve 4/6), ek analiz, README, post-hoc testleri |
| `f5dcdc0` | 2026-10-27 | Hata düzeltmesi: --set bool değerleri doğru ayrıştırılmalı |
| `6a322e7` | 2026-10-27 | Evre 2 raporu: birebir tekrarlanabilirlik gözlemi (2 ve 4 iş parçacığı, aynı makine) |
| `53caabf` | 2026-10-27 | Evre 2 raporu: ablasyon sonucu (yalnız baskılanma) ve --set bool hatasının anlatımı |
| `d013ce7` | 2026-10-27 | Evre 2b altyapısı (ön-kayıt öncesi): rol dengelemesi, küme istatistikleri, Evre 2b değerlendirici |
| `c93b639` | 2026-10-28 | Evre 2b: A3 eşdeğerlik marjı ±0.20, güç analizi aracı (power2b), çift canlı sayısı denetimi |
| `a2c859e` | 2026-10-28 | Evre 2b: plan TASLAĞI (kazanç seçim kuralı prova öncesi sabitlendi), E1 değerlendirici, tasarım ızgarası |
| `3ce0808` | 2026-10-28 | Evre 2b: kod incelemesi düzeltmeleri (--quick çift canlı, checkpoint ödül kalıcılığı, E1 tasarım denetimi, test dünyası set_swap) |
| `994b444` | 2026-10-28 | Evre 2b: hareket okuması dondurulmadan v2 koşusu başlamasın (koruma + test) |
| `bc60d80` | 2026-10-28 | Evre 2b: güç analizi belgesi (senaryolar ve tasarım ızgarası) |
| `aed8716` | 2026-10-28 | Evre 2b: plan KESİNLEŞTİ (kazanç 60, 16 deneme, V2_SET donduruldu), prova sonuçları, dondurma testi |
| `8b3edcb` | 2026-10-28 | Birleştirme/büyütme risk analizi, karar defteri (hata sicili + değişmez kurallar + değişiklik günlüğü), CLAUDE.md |
| `7002de0` | 2026-10-28 | Kullanıcı kararları kaydedildi (donanım, hedef, nöron sınırı yok), devir kontrol listesi, arkadaş için sade özet taslağı |
| `cd51319` | 2026-10-28 | Evre 2b sonuçları: tohum 30 ve 31'de 7/7 ve 7/7; README, karar defteri ve özet güncellendi (E1 sürüyor) |
| `ff94c3e` | 2026-10-28 | Dört koku oyunu: kullanıcı taslağı kaydedildi, kodla karşılaştırılıp 24 bulgulu bağlayıcı plan (v1), kör gezgin hesabı, K-019..K-021/E-11 |
| `33eb549` | 2026-10-28 | Dört koku oyunu G0-G2: GameWorld (sonlu destekli alanlar, temas sırası, ayrı RNG akışları, CRN), referans karşılaştırıcı, eşli istatistikler, S0 regresyon testi |
| `dc7150c` | 2026-10-28 | Oyun protokolü: ön-eğitim, CRN eşli kollar, sızıntı denetimi, oturum koşucuları, pilot ve ön-eğitim komutları; akışlar (tohum, bölüm) işlevi |
