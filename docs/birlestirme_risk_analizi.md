# Birleştirme ve büyütme aşaması: uzman-panel analizi, riskler, hazır yedek planlar

**Durum:** PLAN / ANALİZ BELGESİ. Bu belgede anlatılan Evre 3–5 işlerinin **hiçbiri henüz yapılmadı**. Depoda bugün çalışan tek şey Evre 1 (sentetik mantar cismi) ve
Evre 2/2b'dir (MaleCNS v1.0 sağ-yarımküre mantar cismi alt ağı, 4 780 nöron). Bu belge, büyütmeye girmeden önce *neyin ters gidebileceğini*, *bunu nasıl
önceden anlayacağımızı* ve *ters giderse hangi hazır yedek planı kullanacağımızı* yazar. Kararlar ve hatalar `karar_defteri.md` içinde izlenir; yeni bir karar vermeden önce
orası okunur.

Tarih: 2026-10-28. Etiketler: **[doğrulandı]** kaynakla kontrol edildi, **[doğrulanmadı]** başka bir yerden alındı ya da anımsamadır ve kullanmadan önce kontrol edilmelidir.

---

## 0. Kısa hüküm (sorularınıza yanıt)

1. **"Önce kendi 20 bin nöronumuzu yapıp sonra bağlayacağız, değil mi?"** Yol haritasındaki sıra şudur: tek omurga üzerinde çalışan ve doğrulanmış bir çekirdek → 10–20 bin
   tasarlanmış nöronun ayrı modüller olarak eklenmesi (her biri ablasyonla ölçülür) → ölçek testleri. Yani *evet*, 20 bin nöron ayrı geliştirilir; ama eklenmeden önce
   omurganın kendisi kararlı çalışmalıdır. Aksi hâlde yeni modülün etkisi, taşıyıcı ağdaki sorunlardan ayrılamaz.
2. **"En büyük iki sistemi birleştirip üstüne 20 bin ekleyince 300 bin+ nöron."** Bu sayı aritmetik olarak çıkar, ama **biyolojik olarak yanlış bir toplamdır**: MaleCNS, FlyWire ve BANC
   *aynı türün aynı sinir sisteminin* farklı bireylerden alınmış haritalarıdır (Bölüm 1). İkisini toplamak her hücre tipinden iki kopya (ör. iki mantar cismi, iki merkezi kompleks)
   üretir; bunlar birbirine karşı çalışır ("çift devre sorunu"). 300 bin+ nöron daha **zeki** bir yaratık vermez; zekâ sayıdan değil devre yapısı, öğrenme kuralı ve
   görevden gelir. 300 bin+ ancak (a) bir **ölçek/mühendislik stres testi** olarak (bilimsel iddiasız) ya da (b) iki omurgayı **birleştirmeden, çapraz doğrulama için ayrı ayrı** koşturarak anlamlıdır.
   Önerim: omurga **tek** (MaleCNS), diğer veri setleri **doğrulama ve belirli tamamlayıcı modüller** için kullanılır (Bölüm 4).
   *Güncelleme (kullanıcı kararı):* nöron sayısı için sınır yok; hedef "oyunda en hızlı öğrenen ve en akıllı beyin"; sayı gerekirse bir sonuç olur, hedef olmaz (Bölüm 8).
3. **"Daha zeki, hatalarını daha hızlı anlayan yaratık."** Bunu ölçülebilir hâle getirdim (Bölüm 6): öğrenme hızı, genelleme, tersine çevirme hızı, unutma, ve özellikle
   **hata tespiti gecikmesi** (beklenen ödül gelmediğinde davranışın ne kadar sürede değiştiği). Hata tespiti devresi gerçek MB'de MBON→DAN geri beslemesidir; Evre 2'de bu geri beslemeyi
   **elle yazdık** (`delta = temas·(0.6·ödül − V)`). Bunu veriden gelen bağlantıyla değiştirmek ayrı, sınanabilir bir kilometre taşıdır (R-E3).
4. **"Her şeyi düşündün mü?"** Hayır, hiçbir plan her şeyi öngöremez; bu belge 11 uzmanlık merceğinden 50'den fazla riski, *erken uyarı işaretini* ve *hazır yedek planı*
   yazar. Ne öngörülemezse, kararlar defteri ve "dur kuralları" (Bölüm 7) yanlış yöndeki işi erken durdurmak içindir.

---

## 1. Veri durumu ve rakamlar (kaynaklı)

| Veri seti | Kapsam | Nöron | Sinaps | Lisans | Durum |
|---|---|---:|---|---|---|
| **MaleCNS** (Janelia/Google, erkek, **merkezi sinir sistemi: beyin + optik loblar + VNC**) | tüm CNS | ~166 700 [doğrulandı: [Sci.News](https://www.sci.news/biology/complete-fruit-fly-connectome-15053.html), [Janelia sürüm notları](https://male-cns.janelia.org/release/)] | milyonlarca; kesin toplam bu aramada bulunamadı [doğrulanmadı] | CC BY (Evre 2'de sürüm+md5 ile doğrulandı, `data/README.md`) | **kullanımda** (v1.0, 8 Haz 2026; v0.9 Eki 2025) |
| **FlyWire** (dişi, **yalnız beyin**) | beyin, VNC yok | 139 255 [proje raporu; doğrulanmadı] | ~50–54,5 milyon [proje raporu; doğrulanmadı] | kontrol edilmedi | kullanılmadı |
| **BANC** (dişi, **beyin + sinir kordonu**; Nature'da yayımlandı) | beyin + VNC | **~160 bin** (bir kaynak 158 262) [kısmen doğrulandı: [Tuthill lab pdf](https://faculty.washington.edu/tuthill/docs/banc2026.pdf), [FlyWire blog](https://blog.flywire.ai/?p=1823)] | büyüklük mertebesi ~10⁸ [doğrulanmadı] | kontrol edilmedi | kullanılmadı |

**Dikkat — mesajınızdaki rapordaki rakamlar** ("BANC ~188 000 nöron, ~199 milyon sinaps"): benim aramamda **doğrulanamadı**; kaynaklar BANC için ~160 bin nöron ve ~10⁸ sinaps mertebesi veriyor.
Rapordaki sayı farklı bir sayım ölçütünden (ör. parçalar/fragmanlar dahil) gelmiş olabilir. Karar vermeden önce makaleden (Nature) kontrol edilecek (iş: V-01). Rakam sıralaması
(hangisi "daha büyük") bizim kararımızı değiştirmez; çünkü karar *nöron sayısına* değil *kapsam, kalite, lisans ve elimizdeki boru hattına* dayanır.

**Neden toplanmaz:** aynı tür; aynı hücre tipleri üç haritada da bulunur (farklı bireyler, MaleCNS erkek, diğerleri dişi). MaleCNS makalesi 262 cinsiyete özgü ve 114 cinsel dimorfik hücre tipi bildiriyor
[doğrulandı: aynı Sci.News/MRC LMB özeti]; yani erkek ve dişi parçalarını karıştırmak, doğada bulunmayan bir **kimera** üretir.

---

## 2. Mimari seçenekleri ve öneri

| Seçenek | Ne yapar | Artı | Eksi | Karar |
|---|---|---|---|---|
| **A. Tek omurga + hedefli modül** | MaleCNS omurga; başka veri setlerinden yalnız gerekçeli, tip-düzeyi modül; + 10–20 bin tasarlanmış nöron | tek tutarlı organizma; çift devre yok; ablasyon temiz | omurga dışı veri sınırlı kullanılır | **ÖNERİLEN** |
| **B. İki omurga, çapraz doğrulama** | aynı protokol MaleCNS ve BANC/FlyWire omurgalarında ayrı ayrı koşar | bulguların veri setine bağlı olup olmadığını gösterir; erkek/dişi farkı da ölçülür | iki kat hesap | **ÖNERİLEN (A'ya ek, Evre 3 sonunda)** |
| **C. Ham birleşim (300 bin+)** | iki haritayı tek ağda birleştirir | büyük sayı | çift devre, kimlik/ölçek/işaret uyumsuzluğu, kimera; bilimsel anlamı yok | **YALNIZ stres testi** olarak (Evre 5), iddiasız |
| **D. Konsensüs konnektom** | iki/üç bireyin tip-düzeyi *ortalama* bağlantısı tek ağ | birey gürültüsünü azaltır; ~150 bin nöron kalır | araştırma problemi, tip eşleme gerekir | **İSTEĞE BAĞLI (Evre 5)** |

---

## 3. Uzman-panel riskleri

Her satır: **kod · risk · erken uyarı (nasıl anlarız) · hazır yedek plan.** Önem: ● yüksek, ◐ orta, ○ düşük.

### 3.1 Konnektom verisi mühendisi

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-A1 ● | **Kimlik çakışması ve sürüm kayması:** `bodyId` (MaleCNS), `root_id` (FlyWire; proofreading ile değişir), BANC kimlikleri farklı uzaylardadır | aynı kimlik iki veri setinde farklı hücre; sürüm değişince eşleşme bozulur | değişmez `neuron_uid = hash(kaynak, sürüm, kimlik)`; kaynak+sürüm+md5 tablosu; veri sürümü sessizce değişirse hata (MaleCNS için zaten var, `sources.py`) |
| R-A2 ● | **Kapsam farkı:** FlyWire'da VNC yok; kesik aksonlar (boyun) → inen/çıkan nöronlar eksik girdi/çıktı alır | sınır nöronlarında ortalamadan çok düşük giriş derecesi; sessiz kalan nöronlar | sınır nöronları işaretlenir; tonik sürüş ile hedef ateşleme hızına kalibre (homeostatik); sonuçlar "sınır etkisi" duyarlılığıyla raporlanır |
| R-A3 ◐ | **Sinaps tespit eşiği:** her veri setinin sinaps güven eşiği farklı; sayı = güç değildir | eşiği değiştirince sonuç değişiyor | eşik taraması (3 değer) her ana sonuçta duyarlılık tablosu |
| R-A4 ● | **Sinaps sayısı → ağırlık:** Evre 2'de ortalamaya bölme varsayımı kullandık; veri setleri arası ölçek bağımsız | iki harita aynı tip için ölçekçe farklı giriş derecesi | veri seti başına ölçek, ortak çapa tiplerinin (ör. KC, PN) girişine göre kalibre; yoksa birleştirme yapma |
| R-A5 ◐ | **Lisans/atıf:** MaleCNS CC BY [doğrulandı]; FlyWire/BANC/Eon/FlyGym için kontrol edilmedi; Eon GPL (kopyaleft) [proje raporu; doğrulanmadı] | türev iş GPL'e bağlanıyor | kullanmadan önce lisans tablosu (V-02); GPL kodu *kopyalama*, yalnız yöntem/çıktı karşılaştırması |
| R-A6 ○ | **Boyut/indirme:** ham dosyalar ~GB; proxy/zaman aşımı | indirme yarıda kesilir | boyut+md5 doğrulama (zaten var); devam ettirilebilir indirme |

### 3.2 Hücre tipi ve homoloji uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-B1 ● | **Erkek/dişi kimera:** dimorfik tipler (ör. kur yapma devreleri) karışır | dimorfik tip listesindeki nöron nakledilmiş modülde | nakil için **yalnız cinsiyetten bağımsız tipler**; dimorfik tip kara listesi (MaleCNS makalesinden) |
| R-B2 ● | **Bireyler arası değişkenlik:** KC sayısı, glomerül başına PN sayısı bireyde değişir; bir bireyden alınan modül başka omurgaya arayüz uyuşmazlığı yaratır | nakil modülünün girişleri omurgada karşılıksız | nöron-düzeyi değil **tip-düzeyi** bağlantı; modül tüm nöropil ile (giriş+çıkış) birlikte nakledilir ya da hiç |
| R-B3 ● | **Çift devre:** omurgada MB varken nakledilen MB onunla yarışır | iki MB da MBON çıkışı verir | aynı işi yapan ikinci modülü **eklemeyiz**; yalnız omurgada *eksik* ya da *düşük kaliteli* bölge nakli |
| R-B4 ◐ | **Tip eşleme hatası:** farklı veri setlerinde aynı ad farklı hücre olabilir | eşleşen tiplerin giriş/çıkış profilleri uyuşmuyor | eşleme "bağlantı profili benzerliği" ile doğrulanır; eşik altı eşleşme reddedilir |

### 3.3 Nörokimya / nörotransmitter uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-C1 ● | **İşaret hatası:** nörotransmitter değerleri sınıflandırıcı tahminidir (ör. DPM için "dopamin" yanlış çıktı, `data/README.md`) — yanlış işaret kaçak uyarılma ya da sessizlik üretir | tahmin güveni düşük nöron oranı; ağ tümüyle ya sessiz ya nöbetli | tip-düzeyi oy birliği (birden çok veri seti/literatür); altın standart tipler (KC=ACh, DAN=DA); **işaret duyarlılığı testi:** düşük güvenli %5'in işaretini çevir → sonuç sağlam mı? |
| R-C2 ◐ | **Glutamat çift işaretli** (reseptöre bağlı) | Glu nöronlarının davranışı literatürle uyuşmuyor | varsayılan baskılayıcı + literatürdeki istisna listesi; işaretli test devreleri |
| R-C3 ● | **Nöromodülasyon ağda yok:** dopamin, serotonin, oktopamin, peptidler yaygın/ekstrasinaptik etki; açlık, uyarılma, uyku bağlantıdan çıkmaz | açlık/doymuşluk testinde davranış değişmiyor | **açık durum değişkenleri** (açlık vb.) ayrı katman olarak eklenir ve model varsayımı diye etiketlenir |
| R-C4 ◐ | **Elektriksel sinapslar (gap junction)** EM sinaps tespitinde yok | bilinen elektriksel eşleşmeli devre (ör. dev lif) çalışmıyor | göz ardı + açık sınırlama; yalnız bilinen vakalar elle eklenir |

### 3.4 Biyofizik / hücre modeli uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-D1 ● | **Tek tip LIF:** optik lobda dereceli (spike atmayan) nöronlar var; hepsini sivri LIF yapmak yanlış | optik lob çıkışları doygun/sessiz | sınıfa özgü model: sivri LIF vs dereceli sızdıran integratör; parametreler literatürden, her sınıf için belgelenir (yayımlanmış tek-tip LIF tam-beyin modelleri bazı devreleri yeniden üretmiştir [doğrulanmadı]; bu üst sınır değil referans) |
| R-D2 ● | **Dinamik kararlılık:** büyük tekrarlayan ağ ya nöbet (kaçak) ya sessizlik; ateşleme hızı dağılımı gerçekçi değil | ortalama hız sınıf başına makul aralığın dışında; hız zamanla yükseliyor | hedef hıza **otomatik küresel ölçek kalibrasyonu**; kaçak durumunda küresel baskılama; kabul ölçütü: sınıf başına hız aralığı + 60 sn'de kaçak yok |
| R-D3 ◐ | **Gecikmeler ve adım boyutu:** sinaptik gecikme bilinmiyor; adımı değiştirince sonuç değişir | adımı yarıya indirince sonuç farklı | adım boyutu duyarlılık testi (yarıya indir → sonuçlar tolerans içinde); gecikme taraması |
| R-D4 ◐ | **Parametre belirsizliği** | küçük parametre değişimi sonucu ters çeviriyor | parametre topluluğu (çoklu çekim) üzerinde koşturup yalnız dayanıklı sonuçlar rapor edilir |

### 3.5 Sinaptik plastisite ve öğrenme uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-E1 ● | **Her yeri plastik yapmak ağı bozar** | öğrenme sürerken ağın kendi hızı kayıyor (sürüklenme) | plastisite **bölge bölge** açılır (önce yalnız KC→MBON); her yeni plastik yer ayrı ablasyonla sınanır |
| R-E2 ● | **Girişim / felaketle unutma:** Evre 2 pilotunda A6→A12 düşüşü gözlendi ve açıklanamadı | sıralı görevlerde eski görevin başarısı düşüyor | **tutma matrisi** (görev i sonrası görev j başarısı); yavaş/hızlı ağırlık ayrımı (konsolidasyon); sınırlı iki yönlü kural zaten var |
| R-E3 ● | **Hata sinyali elle yazılı:** `delta = temas·(0.6·ödül − V)` gerçek devre değil; "hataları daha hızlı anlayan" iddiası bu haliyle kurulamaz | DAN yanıtı ödül beklentisine bağlı değil | MBON→DAN ve DAN geri besleme kenarlarını **veriden** aç (işaretleri R-C1 ile); test: beklenen ödülde DAN yanıtı azalıyor mu, beklenmedik ödülde artıyor mu (öngörü hatası imzası) |
| R-E4 ● | **Öğrenme hızı ölçekle değişir:** 4 780 nöron için ayarlanan η, 160 bin nöronda taşmaz | aynı görevde öğrenme çok yavaş/çok hızlı | η, giriş derecesi normalizasyonuyla ölçeklenir; bölme başına küçük kalibrasyon koşusu |
| R-E5 ◐ | **Sınırlar (W ∈ [0, W0]) yeni modüllerde tanımsız** | ağırlıklar sınıra yapışıyor | her plastik yer için W0 açıkça tanımlanır, sınıra yapışma oranı izlenir |

### 3.6 Devre ve davranış sinirbilimi uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-F1 ● | **Duyusal arayüz:** koku dışındaki duyular (tat, mekanik, görme, ısı) için girdi kodlaması bağlantıdan gelmez | duyusal nöronlar sessiz ya da doygun | her duyu için tanımlı duyusal nöron sınıfı + literatürden bilinen yanıt (ör. belirli ORN → beklenen PN deseni) ile **doğrulama birim testi** |
| R-F2 ● | **Motor arayüz:** şimdiki dönüş kuralı elle yazılı; tam beyinde inen nöronlar (DN) → hareket eşlemesi gerekir | bilinen DN'yi uyarınca beklenen dönüş/yürüme olmuyor | literatürde işlevi bilinen DN'lerle ("uyar → beklenen hareket") kapalı döngü birim testleri; olmayan eşleşmede elle yazılmış kontrol *açıkça işaretlenir* |
| R-F3 ● | **Gömme sorunu:** MB tek başına öğreniyor, ama tüm beyine gömüldüğünde öğrenme bozulabilir (ek girdiler, geri beslemeler) | gömülü MB, yalıtılmış MB'den farklı sonuç veriyor | **gömme testi:** aynı Evre 2b protokolü tüm-CNS içinde koşar; fark → hangi ek bağlantının neden olduğu ablasyonla bulunur |
| R-F4 ◐ | **Elle yazılı davranışın payı** şeffaf değil | "bağımsız davranıyor" iddiası | her sonuç raporuna "elle yazılı bileşenler" listesi; mümkünse ölçülen pay |
| R-F5 ◐ | **Durumlar:** açlık, uyarılma, uyku olmadan "ihtiyaca göre karar" yapılamaz | görev açlık durumunda değişmiyor | R-C3 durum değişkenleri + testler |
| R-F6 ○ | **VNC:** yürüme için gerekir; FlyWire'da yok | bedene bağlanınca yürüyemiyor | önce 2B dünyada kal; 3B bedende alt düzey kontrol (CPG) betimlenmiş olarak, sonra VNC ile değiştir |

### 3.7 Beden / fizik (FlyGym) uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-G1 ● | **Zaman ölçeği uyuşmazlığı:** fizik adımı ile sinir adımı farklı | gecikme, kararsızlık, kayıp adımlar | senkron adım şeması; iletişim periyodu duyarlılık testi |
| R-G2 ◐ | **Sensör/duyu üretimi** (koku alanı, görüntü) pahalı | simülasyonun çoğu zamanı render | önce 2B dünya, beyin doğrulanana kadar 3B yok |
| R-G3 ○ | **Sürüm kayması** (MuJoCo vb.) | aynı tohum farklı sonuç | sürüm sabitleme; altın koşu testi |

### 3.8 Hesaplama / mühendislik uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-H1 ● | **Ölçek:** bugünkü ortam 4 çekirdek CPU, ~16 GB RAM, GPU yok; Evre 2b'nin 72 canlı × 4 780 nöronluk (~344 bin nöron-örneği) bir koşusu ~3 saat sürüyor. 160 bin nöronlu *tek* canlı bile CPU'da bu ortamda uygun değil | adım/sn ölçümü hedefin çok altında | **ölçek eğrisi** ölçümü (5 bin, 20 bin, 50 bin, 100 bin, 160 bin nöron: adım/sn, RAM, VRAM); seyrek (CSR) GPU yolu; hedef donanım **RTX 3070 Ti Mobile 8 GB + 32 GB RAM** (Bölüm 8); 8 GB VRAM'e sığmazsa alt ağ stratejisi / yarım duyarlık / canlı başına yalnız plastik ağırlıklar |
| R-H2 ● | **İstatistiksel güç / bütçe:** Evre 2b'de canlı başına aşırı yayılım yok (varyans oranı ~0,8) → güç, canlı sayısından çok deneme sayısıyla artıyor | tasarım ızgarası (`evre2b_guc_analizi.md`) | büyük ağda az canlı × çok deneme; ama küme-düzeyi analiz korunur; güç analizi her yeni tasarımdan **önce** |
| R-H3 ◐ | **Sayısal tekrarlanabilirlik:** CPU↔GPU, iş parçacığı sayısı → kayan nokta farkları | aynı tohum farklı sonuç | tolerans temelli tekrarlanabilirlik; CPU referans koşusu (2/4 iş parçacığı birebir aynı, bu makinede doğrulandı) |
| R-H4 ● | **Uzun koşuların kırılganlığı:** konteyner yeniden başlayınca koşu ölür (Evre 2b geliştirmesinde yaşandı) | koşu logu aniden durur | **aşama başına yeniden başlatılabilir kontrol noktası** (ölçek büyütmeden önce yapılacak iş: V-03) |
| R-H5 ◐ | **Checkpoint boyutu:** canlı başına tüm ağırlıkları saklamak | disk dolar | yalnız plastik ağırlıklar canlı başına; statik ağırlıklar paylaşılan |

### 3.9 Biyoistatistik / değerlendirme uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-I1 ● | **Araştırmacı serbestliği ve kazananın laneti** (Evre 2 v1'de yaşandı: koku çifti seçimi) | geliştirme ve doğrulama sonuçları arasında büyük fark | geliştirme/doğrulama tohumları ayrı; ölçütler koşudan önce commit; ölçütler benzetimle sınanır (`power2b`) |
| R-I2 ● | **Ölçütün kendisi hatalı olabilir** (A3'ün iki biçimi kusurluydu; kendiliğinden başarısız oluyordu) | boş durumda (öğrenme yok) ölçütün geçme/kalma oranı | her yeni ölçüt için **sıfır-etki ve bilinen-etki benzetimi** (yanlış pozitif/negatif oranı) zorunlu |
| R-I3 ● | **"Zeki"nin tanımı yok:** sayı arttı diye zeki denemez | görev başarısı yerine sayı raporlanıyor | Bölüm 6'daki görev takımı + temel çizgiler: yalnız omurga; omurga + 20 bin rastgele; omurga + 20 bin tasarlanmış; derece-korumalı rastgele bağlantı |
| R-I4 ◐ | **Çoklu karşılaştırma** | çok ölçüt, kesişim kuralı yoksa | "hepsi geçmeli" kesişim kuralı; görev başına ön-kayıt |
| R-I5 ◐ | **Negatif kontroller eksik** | davranış öğrenme olmadan da var | `frozen`, `random`, sınıf-karıştırma (E1) gibi kontroller her ana iddiada |
| R-I6 ○ | **Ölçüt gücü yetersizse sonuç "başarısız" görünür** (Evre 2 v1'de olduğu gibi) | eğitimsiz seçim oranı düşük | geçerlilik kapısı (G): kapı geçilmezse sonuç "değerlendirilemez" olarak raporlanır, geçmiş sayılmaz |

### 3.10 Yazılım kalitesi / süreç uzmanı

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-J1 ● | **Sessiz hatalar** (Evre 1'de test kokuları yanlış desenle üretildi; `bool("false")` doğru ayrıştırılmadı) | sonuçlar sezgiye ters (ör. eğitilmiş canlı B'yi seçiyor) | **sezgiye ters sonucu gürültü sayma, nedenini ara**; her hata için regresyon testi; altın koşu (küçük, deterministik, özeti sabit) |
| R-J2 ● | **Modül arayüzleri belirsiz:** eklenen nöron grubu duyu/motor/durum/plastisite ile nasıl bağlanır | modül eklenince başka bir testin bozulması | tipli arayüz (duyu girişi, motor çıkışı, modülatör, plastisite maskesi) ve modül başına birim testleri; modül kapatma = ablasyon |
| R-J3 ◐ | **Ayar dağınıklığı** | hangi ayarla koşulduğu belli değil | tek sürümlü yapılandırma; sonuç dosyasına yapılandırma + git sürümü yazılır (Evre 2'de var) |
| R-J4 ◐ | **Belge kayması** | belgelerle kod uyuşmuyor | kararlar defteri; dondurma testleri (`test_v2_frozen_configuration`) |
| R-J5 ○ | **Sessiz yedek veri** | veri sürümü kendiliğinden değişir | md5 sabitleme; uyuşmazlıkta hata (var) |

### 3.11 Dürüstlük / etik / lisans

| Kod | Risk | Erken uyarı | Hazır yedek plan |
|---|---|---|---|
| R-K1 ● | **Aşırı iddia:** "bilinç", "gerçek sinek gibi", "daha zeki" | rapor dilinde kanıtsız genel cümle | her rapor "ne ölçüldü / ne ölçülmedi" bölümü; bilinç iddiası yok |
| R-K2 ◐ | **Kaynak rakamlarının doğrulanmaması** (bu belgede BANC rakamı örneği) | iki kaynak çelişiyor | her dış rakam [doğrulandı]/[doğrulanmadı] etiketi taşır |
| R-K3 ◐ | **Atıf ve lisans yükümlülükleri** | veri kullanımı atıfsız | `data/README.md` atıf bölümü her yeni veri için genişletilir |

---

## 4. Birleştirme (nakil) protokolü — yapılırsa nasıl

Bir modül başka veri setinden nakledilecekse **şu sırayla ve ancak hepsi geçerse**:
1. **Gereklilik kanıtı:** omurgada o işlev eksik/bozuk mu? (omurga testinde ölçülmüş başarısızlık). Yoksa nakil yok.
2. **Tip eşleme:** nakledilecek tipler omurgayla bağlantı profili benzerliğiyle eşleştirilir (R-B4); dimorfik tipler çıkarılır (R-B1).
3. **Bütünlük:** modül giriş **ve** çıkış bağlantılarıyla birlikte alınır (R-B2); omurgadaki yinelenen işlev kapatılır (R-B3).
4. **Ölçek ve işaret:** ağırlık ölçeği çapa tiplerle (R-A4), işaretler oy birliğiyle (R-C1).
5. **Kararlılık:** R-D2 kabul ölçütü.
6. **Etki ölçümü:** ablasyon (modül açık/kapalı) + derece-korumalı rastgele bağlantılı kontrol (R-I3). Önceden yazılmış ölçüt, benzetimle sınanmış (R-I2).
7. **Geri alma:** nakil tek bir yapılandırma anahtarıyla kapatılabilmelidir; kapalıyken sonuçlar nakilden önceki sürümle birebir aynı.

---

## 5. Yürütme planı ve kapılar

| Adım | İş | Giriş koşulu | Çıkış ölçütü (önceden yazılacak) | Yedek / dur kuralı |
|---|---|---|---|---|
| **V** | Doğrulamalar: BANC/FlyWire rakam+lisans (V-01, V-02), yeniden başlatılabilir koşular (V-03) | — | tablo + test | — |
| **2b** | Evre 2b doğrulayıcı koşular (sürüyor) | ön-kayıt kesin | `evre2b_plan.md` §8 | başarısız = rapor; ölçüt değişmez |
| **3.0** | Ölçek eğrisi ve donanım kararı | 2b raporlandı | adım/sn, RAM/VRAM tablosu; hedef: tam-CNS adımı için GPU gerekir mi | GPU yoksa yalnız alt ağlarda ilerle (MB + merkezi kompleks gibi) |
| **3.1** | Tam-CNS sessiz/serbest dinamik kararlılığı | 3.0 | R-D2 kabulü, işaret ve adım duyarlılığı (R-C1, R-D3) | kararsızsa küresel ölçek kalibrasyonu; olmazsa alt ağ stratejisine dön |
| **3.2** | **Gömme testi:** MB'nin tam-CNS içinde öğrenmesi | 3.1 | Evre 2b ölçütleriyle aynı protokol, ön-kayıtlı karşılaştırma | bozulursa hangi ek bağlantı → ablasyon; çözülmezse MB yalıtımlı kalır |
| **3.3** | Hata sinyalinin veriden gelmesi (MBON→DAN) | 3.2 | öngörü hatası imzası + Bölüm 6 T10 | çalışmazsa elle yazılı delta *açıkça* etiketli kalır; "hata tespiti" iddiası yok |
| **3.4** | Duyusal/motor arayüz birim testleri | 3.1 | R-F1, R-F2 birim testleri | eşleşmeyen yerde elle yazılı kontrol işaretli |
| **3.5** | Çapraz doğrulama (BANC/FlyWire omurgası) | 3.2 | aynı sonuçlar mı? fark = bulgu | veri uyumsuzsa yalnız alt ağ düzeyinde karşılaştır |
| **4.x** | 10–20 bin tasarlanmış nöron: modül modül (ör. öğrenme, bellek, karar, duyusal) | 3.3 | her modül için ablasyon + rastgele bağlantılı kontrol; ölçütler önceden yazılmış ve benzetimle sınanmış | fayda yoksa modül **atılır**, rapor edilir |
| **5** | Ölçek stres testi (300 bin+), konsensüs konnektom | 4.x | yalnız performans/bellek ölçümü; bilimsel iddia yok | donanım yetmezse durur |

Her adımın başında `karar_defteri.md` okunur; sonunda yeni kayıt yazılır.

---

## 6. "Daha akıllı" ne demek — ölçülebilir görev takımı

Hiçbiri henüz uygulanmadı (T1–T2 Evre 1/2'de var). Her görev için temel çizgiler: `frozen` (öğrenme kapalı), `random`, yalnız omurga, omurga + rastgele 20 bin, omurga + tasarlanmış 20 bin.

| Kod | Görev ("oyun") | Ne ölçer |
|---|---|---|
| T1 | koku–ödül öğrenme | öğrenme (yapıldı) |
| T2 | ödül tersine çevirme | esneklik (yapıldı) |
| T3 | sönme ve kendiliğinden geri dönüş | bellek dinamiği |
| T4 | ikinci derece koşullanma | zincirleme öğrenme |
| T5 | ayırt etme ve genelleme (karışık koku, derişim) | genelleme |
| T6 | bağlama bağlı seçim (iki ortamda zıt ödül) | bağlam kullanımı |
| T7 | açlık/doygunluk durumuna göre seçim | iç durumla karar |
| T8 | ceza/kaçınma ve risk | değerlendirme asimetrisi |
| T9 | yeni ortama aktarım | transfer |
| T10 | **hata tespiti:** beklenen ödül gelmedi → davranışı değiştirme gecikmesi | "hatalarını daha hızlı anlama" |

Metrikler: ölçütlere ulaşma bölümü (öğrenme hızı), asimptotik başarı, genelleme farkı, tersine çevirme hızı, tutma matrisi, T10 gecikmesi. Hepsi ön-kayıtlı, benzetimle sınanmış, küme-düzeyi istatistikle.

---

## 7. Genel dur kuralları

* Bir adımın ölçütü ön-kayıttan sonra **değişmez**; başarısızlık raporlanır.
* Geliştirme sonucu doğrulayıcı sonuca ters düşerse (kazananın laneti işareti) doğrulayıcı sonuç esastır.
* Bir modül ablasyonda fayda göstermezse atılır; "ama sayı arttı" gerekçe değildir.
* Sezgiye ters sonuç (ör. eğitilmiş canlı yanlış seçer) **önce yazılımda hata olarak** aranır (R-J1).
* Bir hata ikinci kez yapılırsa, ilgili sicil kaydına işaret eden bir test ya da koruma eklenir.
* Hiçbir sonuç "gerçek sinek böyle davranır" diye sunulmaz.

---

## 8. Verilen kararlar (kullanıcı, 2026-10-28) ve açık kalanlar

| Konu | Karar |
|---|---|
| **Donanım** | Şimdilik bu bulut ortamı (CPU, GPU yok). Kullanıcı "GPU kullanılacak" dediği anda bu sohbet kapatılacak ve **RTX 3070 Ti Mobile (8 GB VRAM) + 32 GB RAM** kullanılacak. Bu yüzden her şey depoda kendi kendine yeterli olmalı (Bölüm 9). |
| **Hedef** | Oyun içinde **en hızlı öğrenen ve en akıllı** beyin. İlk sınama alanı oyun; sonra başka testler. |
| **Nöron sınırı** | **Yok.** Ne kadar gerekirse o kadar; gerekmiyorsa eklenmez. 300 bin+ bir hedef değil, gerekirse bir sonuçtur: 200 bin nöronluk iyi eğitilmiş bir ağ 300 binlik kötü eğitilmişi geçebilir (R-I3, R-9). |
| **Ayrıntı kararları** | Kullanıcı bana bıraktı: omurga **MaleCNS**; gerçek zamanlılık **şart değil** (deney verimliliği ve tekrarlanabilirlik öncelikli); nöron eklemek ancak ablasyonla fayda gösterirse. |
| **Rapor** | İş bittiğinde, hangi aşamada olduğumuzu ve hedefi anlatan **tek paragraflık sade metin** (`docs/arkadasa_ozet.md`). |

Açık kalan tek konu: 300 bin+ ham birleşim **bilimsel** nesne olarak istenirse konsensüs konnektom (seçenek D) gerekir; şimdilik gerekmiyor.

---

## 9. Devir (GPU'ya geçiş) kontrol listesi

GPU'ya geçildiğinde bu sohbet kapanacağı için bağlam **yalnız depoda** yaşar. Geçişten önce yapılacaklar (durum 2026-10-28):

1. **Kurulum betiği ve README** — `bekliyor`: Windows/PowerShell'de sıfırdan kurulum (Python sürümü, `pip install -e .`, CUDA'lı PyTorch), veri indirme, `pytest`, duman testi; her komut çalıştırılarak denenmiş olmalı (bu ortam Linux/CPU: Windows adımları denenemez, "denenmedi" diye işaretlenecek).
2. **CUDA yolu duman testi** — `hazır, GPU'da denenmedi`: `python3 -I -m sinek.experiments.altin_kosu --device cuda --check docs/altin_kosu_referans.json`. CPU↔GPU nokta nokta eşleşme **beklenmez** (Poisson akışı cihaza özgü); denetim istatistikseldir: CPU'da 8 beyin tohumunun ortalaması ±4·SD (en az mutlak tolerans), tolerans koşudan önce yazıldı. Aynı cihazda tekrar bit-bit aynı olmak zorunda.
3. **Verim eğrisi betiği** — `kısmen hazır`: `python3 -I -m sinek.experiments.olcek_egrisi --device cuda --batches 64,256,1024,4096` (adım/sn, bellek; sabit ağ, değişen canlı sayısı, topluluk K için canlı·K). **Tam-CNS 5 bin → 160 bin nöron seyrek yolu bu depoda yok**; yalnız mantar cismi alt ağı ölçülür. 8 GB VRAM sınırı ölçüm sonucudur, henüz yok.
4. **Yeniden başlatılabilir koşular** (V-03; E-09) — `yapıldı`: `scripts/run_validators.sh` kuyruğu + O3/O4 doğrulayıcısında kol-kol kontrol noktası (K-029); Evre 2b (E-09) önceden vardı.
5. **Devir notu** — `bekliyor`: `CLAUDE.md` + `karar_defteri.md` + bu belge güncel; sonuçların nerede olduğu (`results/` git'te yok → önemli sonuçların özeti `docs/` içinde: `odor_o1_o2_sonuclari.md`, O3/O4 sonuç belgesi yazılacak).
6. **Altın koşu** — `yapıldı (CPU)`: `python3 -I -m sinek.experiments.altin_kosu --device cpu --check docs/altin_kosu_referans.json` (~25 sn, 16 canlı); referans CPU, torch 2.14.1+cpu üzerinde üretildi, farklı torch sürümünde yeniden üretilmeli.
