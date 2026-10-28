# SİNEK NÖRONLARI — DÖRT KOKU OYUNU İÇİN BİLİMSEL TASARIM, GELİŞTİRME VE DOĞRULAMA PLANI

**Belge türü:** Uygulanabilir araştırma/tasarım planı; kod veya gerçekleşmiş deney sonucu değildir.  
**Tarih:** 28 Ekim 2026  
**Kaynak depo:** [muhammedaliaka/sinek-noronlari](https://github.com/muhammedaliaka/sinek-noronlari)  
**İncelenen dal:** `ccr-2e9cee22-nxwnkt`; **sabitlenen commit:** [`cd51319b3c78e22e527f7c8581f28f5e10398589`](https://github.com/muhammedaliaka/sinek-noronlari/commit/cd51319b3c78e22e527f7c8581f28f5e10398589)  
**Ana amaç:** Dört oyunu tamamlatmak değil; dijital canlının kokuyu algılama, kokuyla yön bulma, ipucu olmadan keşfetme, ödülden öğrenme ve yanıltıcı bilgiden davranış güncelleme yeteneklerini birbirinden ayırarak ölçmek.

> **Güvenilirlik uyarısı:** Buradaki oyun parametreleri, örnek sayıları ve eşikler **önerilen tasarım başlangıçlarıdır**, biologik sabitler veya ölçülmüş proje başarıları değildir. Pilotlardan sonra, doğrulayıcı deney başlamadan önce sabitlenir. Proje deposunda kod değişikliği yapılmadı, oyunlar çalıştırılmadı. Depodaki Evre 2b sonuçları geliştirme için referanstır; bu dört oyunun başarı kanıtı değildir.

---

## 0. Ön karar — dört oyun yapılmalı mı?

**Evet; kontrollü bir araştırma hattı olarak yapılmalı.** Fakat bunlar yalnızca sırayla zorlaşan dört seviye değildir. İlk oyun **koku kaynağına yönelim**, ikinci oyun **kokusuz alanda keşif + yakın alan kokusu**, üçüncü oyun **hedefin yerini bildirmeyen temas-ödül sinyali**, dördüncü oyun **yanıltıcı kokuyu deneyimle etkisizleştirme** testidir. Üçüncü ve dördüncü oyunda hedefi yalnız koku kullanarak uzaktan bulmak bilgi kuramsal olarak mümkün olmayabilir. Başarı koşulunu buna göre yazmamak, gerçek kapasiteyi cezalandırır.

**Önerilen sıra:** Evre 2b mevcut davranışı değişmeden yeniden üretme → mevcut duyusal girdi sözleşmesini doğrulama → yeni koku reseptörü/ORN/anten lobu katmanını ayrı test etme → Oyun 1 → Oyun 2 → Oyun 3 → Oyun 4 → çapraz geçiş/ablasyon/tekrarlanabilirlik. Oyun 3 ve 4'te başarısızlık, daha önce ispatlanmamış mekânsal bellek/keşif sisteminin eksikliğinden de kaynaklanabilir.

### Dört oyunun özeti

| Oyun | Sinek hedeften önce ne koklar? | Konum bilgisi nereden gelebilir? | Ölçülen şey | Tek başına neyi ispatlamaz? |
|---|---|---|---|---|
| **O1 — Kokunun tam yolu** | Hedefe uzanan kesintisiz, kontrollü koku koridoru | Yerel yoğunluk, zaman içindeki değişim, varsa rüzgâr | Koku takibi ve kaynak bulma | Genel zekâ, yeni koku öğrenme |
| **O2 — Sadece final çevresi** | Finalin yakınındaki küçük bölgede koku; dışında **sıfır** | Önce keşif; yakınlaşınca yerel koku | Keşif → kokuyu fark etme → yakın mesafede tamamlama | Uzaktan koku izleyerek hedef bulma |
| **O3 — Sadece finale temas anı** | Hedefe değmeden önce **hiçbir yerde koku yok** | Rastgele/sistematik keşif; varsa önceki deneyim veya başka meşru duyu | İpucusuz keşif, temas ödülünden öğrenme | O denemede önceden koku ile yön bulma |
| **O4 — Yanlış yola götüren koku** | Koku gerçek hedefe **değil**, yanıltıcı bölgeye yönlendirir | Koku yanılgısından geri dönüş + keşif, geri bildirim | Eski koku beklentisini güncelleme, tuzaktan uzaklaşma | Kokunun gerçeğe aykırı olduğunu ilk görüşte bilme |

---

## 1. Projeden doğrulanmış başlangıç durumu

### 1.1 Mevcut yetenekler

1. `README.md`: 2B arenada iki koku, yemek/ödül, hareket ve belleğin kayıt/yükleme akışı var. Evre 2b'de iki bağımsız doğrulayıcı tohumda **7/7, 7/7** ön-kayıtlı ölçüt geçilmiş; A ödülü öğrenilip B'ye taşındığında tercih değişiyor.
2. `src/sinek/world.py`: `sense()` sol/sağ anten pozisyonları ile kaynak uzaklıklarından koku yoğunluğu çıkarır, sonucu **doğrudan glomerül aktivasyonuna** çevirir. Var olan ifade kabaca `exp(-d²/(2σ²))` tabanlıdır. Bu, matematiksel olarak sıfırdan büyük sonsuz kuyruk üretir; oyundaki **tam sıfır koku** koşulu için yeterli değildir.
3. `src/sinek/brain_connectome.py`: yaklaşık **4.780 temsil edilen nöron/canlı**; MaleCNS sağ yarımküre mantar cismi verisi sol/sağ kanal için iki kez kullanılır. İlgili alt ağ: yarımküre başına **123 PN, 2.045 KC, 1 APL, 48 MBON, 161 DAN**. Gerçek bağlantı sayıları yalnızca seçili yollarda kullanılır; geri kalan bazı işlevler varsayımsaldır.
4. `src/sinek/agent.py`: sabit ileri hız, öğrenilmiş sol/sağ `V` farkından dönüş, rastgele gezinme. **Planlama, geçmiş konum haritası veya çok adımlı sistematik keşif modülü burada yok.** Bu yüzden O3/O4 üstünlüğünü peşinen beklememek gerekir.
5. `src/sinek/experiments/protocol.py`: seçim testinde öğrenme kapatılabilir; canlı başına birden fazla deneme vardır. Önceki istatistik dersi: tekrarları birbirinden bağımsız canlı saymamak, canlı-düzeyinde kümelendirmek.
6. `docs/karar_defteri.md`: **R-1–R-11** araştırma kuralları var: deney ölçütünü önceden yaz, tohumları ayır, başarısızlığı gizleme, hatayı araştır, sıfır-etki benzetimi yap, nöron sayısını başarı sayma, elle yazılan bileşenleri açıkla. **E-01**: test kokularının eğitimden farklı örüntüyle üretilmesi geçmişte ciddi hata oluşturmuş; yeni oyunlarda bu özellikle korunmalı.
7. `docs/birlestirme_risk_analizi.md`: R-F1 duyusal arayüz, R-F2 motor arayüz, R-E3 elle yazılı ödül-hata devresi, R-F5 açlık/durum, R-H1 hesaplama ölçeği, R-J4 belge-kod kayması gibi riskler bu oyunları doğrudan etkiler.

**Sonuç:** Bugünkü sistem **yapay koku örüntüsü → PN → mantar cismi → V → elle yazılı dönüş** düzeninde çalışır. **Gerçekçi OR/IR reseptör cevabı, ORN→anten lobu bağlantıları ve anten lobunun tüm işlemesi modellenmiş sayılmaz.** Bu oyunlar önce mevcut modeli sınayabilir, sonra yeni duyusal arayüzün gerçekten bir kazanım getirip getirmediğini ölçebilir.

### 1.2 Bilimsel sınır ve yanlış beklenti

- Bir koku kanalını görmek, kaynağın nerede olduğunu otomatik bilmek değildir. Sineklerin gerçek koku navigasyonunda **rüzgâr yönü**, **kokuya giriş/çıkış zamanlaması**, **sınır izleme** ve **kısa süreli yön belleği** rol oynar. Bir gradienti takip eden yalın `V_sol - V_sağ` politikası her tür kokuda doğal davranış üretmez.
- Gerçek kokular hava akımıyla değişken bir **plume** oluşturabilir. Ekranda çizilmiş kusursuz çizgi, biyolojik gerçekçilikten çok **kontrollü öğretici test** olmalıdır.
- O2/O3'te uzaktan hiç koku olmadığında nöronlara hedef doğrultusu bilgisi iletilmez. **Kokudan doğru hedef yönünü çıkaramamak bir hata değildir.**
- O4'te yalnızca yanlış yerden koku geliyorsa doğru çıkışa ilişkin doğrudan kimyasal bilgi yoktur. Birden fazla denemede ödül geri bildirimiyle yanlış kokuyu göz ardı etmek mümkün olabilir, ama bunun için uygun keşif, bellek ve değer güncelleme devresi gerekir.

---

## 2. Ortak bilimsel tasarım: oyun nasıl adil olur?

### 2.1 Bilgi sınırları (en önemli kural)

Sinek ajanına **yalnızca gerçek sensör arayüzünden gelen** bilgiler verilir: sol/sağ koku reseptörü çıktısı, izinli temas/tat sinyali, kendi hareketinden türetilen özduyum (eklendiği ve açıkça etiketlendiği takdirde), varsa ayrı bir deneyde rüzgâr. **Gizli değişkenler verilmez:** hedefin X/Y koordinatı, en kısa yol, oyun adı, kalan doğru mesafe, yanlış kokunun “yanlış” etiketi, gelecekteki ödül, tüm koku ısı haritası, seviye sonu bilgisi. Seyirci arayüzü bunları gösterebilir; ajana girdi olmamalı.

**O1'de “kokunun tam yolu gözükür” ifadesinin uygulama yorumu:** koku yolu **insan gözlemciye** ısı haritası olarak gösterilir. Sinek koku yolunu ekrandan görmez, kendi iki anteniyle yerel duyusal bilgi alır. Eğer sineğin de çizgiyi görebilmesi istenirse bu **ayrı bir görsel duyu kontrolü** olmalı; koku başarısı sayılmamalıdır.

### 2.2 Koku alanının doğru temsil edilmesi

- Ortamda birden çok koku türü ayrı konsantrasyon kanallarıyla taşınsın: `C_k(x,y,t) ≥ 0`.
- Duyusal girdi `r_i(t)=f_i(C_1,...,C_K, adaptasyon, gürültü)` ile reseptör tipi `i` için hesaplansın; `f_i` açıkça model varsayımı olarak tanımlansın. Girdiler **moleküler reseptör**, **ORN** ve **PN** olarak ayrı doğrulansın; her reseptör protein molekülünü tek tek simüle etmek şart değildir.
- Gerçekçi mod: kaynak, hava akımı, taşınma, difüzyon, kesintiler (plume) ve anten pozisyonu. Temel test modu: sabit ve tam bilinen analitik koku alanı. **Birincisi biyolojik yakınlık, ikincisi neden-sonuç denetimi sağlar; birbirine karıştırılmaz.**
- O2 için **sonlu destekli koku maskesi**: hedef bölgesi dışı kesin `C=0`, sayısal tolerans içinde sıfır; maske dışında uzaktan gradient veya algoritmik önbilgi yok.
- O3 için **temas kapısı**: ilk gerçek hedef temasına kadar tüm bölgelerde `C=0` (kokunun zamansal geçmişi de sıfır). Temasta koku verilir; bu koku o anki kararı geçmişe dönük etkileyemez. Adım sırası açıkça tanımlanmalı: önce pre-contact sensör okuması → hareket → temas tespiti → yeni koku/ödül etkisi **bir sonraki adımda**.
- O4 için kokunun fiziksel kaynağı sahte hedefte; gerçek hedefte test koşuluna göre koku `0`. Sahte kokuyu “hedefin kokusu” olarak gizlice etiketlememek; anlamını deneyim belirlesin.
- **`C=0` ile tüm nöronların susması aynı şey değil:** mevcut modelin PN temel Poisson ateşleme hızı sıfır konsantrasyonda bile bulunabilir. “Koku yok” koşulunu `C=0` ve **kokuya bağlı artış = 0** olarak raporla; temel spontan ateşleme ayrıca izlenir.

### 2.3 Dünya ve hareket

**Başlangıç prototipi (öneri, henüz onaylı sonuç değil):** 40×40 sanal birimlik 2B arena; `dt=0,02 s`, sabit hareket hızı mevcut kodda `8 birim/s`, hedef temas yarıçapı `1,5 birim`. Karşılaştırmalarda bu değerler **değişmeden** tutulsun. Pilotla doğrulanmazsa yeniden kalibre et ve **yeni ön-kayıt** oluştur. Önce açık arena, sonra engelli arena; duvarlar fiziksel olarak geçilemesin, köşeye takılma ve uzun süre sabit dönme ölçülsün.

Her oyun için test haritası şu şartları sağlamalı:

1. Hedef ve başlangıç aynı navigasyon bağlı bileşeninde; yol gerçekten var (**A*/grid flood fill oracle** yalnız test doğrulamada, ajana değil).
2. Başlangıç konumu, yön, koku/decoy yönü ve engel yerleşimi **sol/sağ ayna simetrisi** ile dengelenmiş olsun; sabit yön veya hareket kazanmasın.
3. Engelli ve engelsiz sürümler ayrı raporlansın; zorluk artışı bilgide mi geometride mi anlaşılabilsin.
4. Haritanın kenarı ve duvar zıplaması hedefi otomatik bulmaya yarayan gizli işaret olmasın.
5. Eğitim haritaları ve doğrulama haritaları ayrışsın. Aynı haritada aşırı öğrenmenin yeni haritaya aktarılmasıyla karıştırılmasın.
6. Görselleştirme açık/kapalı ajanın durumunu, rastgele sayıları veya girdi tensörünü değiştirmesin.

### 2.4 Durma ve “bulana kadar devam etme”

Kullanıcının istediği gibi bir canlı hedefe varmadığında **anında başarısız ilan edilmesin**. Ama sonsuz döngü de çalıştırılmasın.

- **Tek deneme sınırı:** ana karşılaştırma için önerilen `60 sanal saniye`; uzun keşif için ayrıca `120 sanal saniye` analizi. Bunlar seçilmiş tasarım değerleridir; pilotta ulaşılabilirlik denetlenir.
- **Hedefe temas:** o deneme tamamlandı/kazanıldı; doğru kokunun yakınında gezmek kazanmak değildir.
- **Süre dolduysa:** `timeout / henüz ulaşmadı` olarak kaydet, başarısız öğrenme olarak etiketleme. Yeni deneme/araştırma bölümüyle ilerle; öğrenilmiş ağırlıklar gerektiğinde korunabilir.
- **Uzun eğitim:** otomatik checkpoint; takılma varsa alt nedeni raporla. Rastgele tohum, harita, beden ve koku durumu kaydedilerek yeniden üretilebilsin.
- **Ölüm/enerji:** başlangıçta enerji sistemini sabit tut veya tüm koşullara eşit uygula; metabolizma kaynaklı erken durmayı koku başarısızlığı sayma. Enerji, ayrı sonraki araştırma sorusudur.

### 2.5 Eğitim ve sınama ayrı

1. **Sensör testleri:** beyin/öğrenme kapalıyken giriş-çıkış doğruluğu.
2. **Önceden ödüllü koku öğrenmiş canlı:** Evre 2b kayıtlarından uyumlu checkpoint kullan; ilk oyunda ölçtüğümüz şeyin **koku takibi** olduğundan emin ol.
3. **Sıfırdan eğitim:** aynı koku ilk kez görüldüğünde, ödül ancak fiziksel temasla gelsin. Başarının kaç deneyimde geliştiği ayrı ölçülsün.
4. **Doğrulama:** öğrenme kapalı, bilinmeyen haritalar ve daha önce kullanılmamış tohumlarla; belleğin gerçekten işe yarayıp yaramadığına bak.
5. **Çevrim içi uyum testi:** öğrenme açık, geribildirim gelir; burada zaman içinde davranış değişimi ölçülür. Bu test doğrulama testiyle karıştırılmaz.

---

## 3. OYUN 1 — KESİNTİSİZ KOKU YOLU

**Kısa hikâye:** Bir uçta sinek, uzakta koku ve yiyecek kaynağı var. Hedefe uzanan **kesintisiz, izlenebilir** koku bandı bulunuyor. Gözlemci bütün koku yolunu şeffaf renkli gösterimde görüyor. Sinek yalnızca bulunduğu noktadaki iki antenin koku değerlerini alıyor. Hedefe temas edince kazanıyor; aksi halde gezinmeye devam ediyor.

### 3.1 Asıl soru

**“Koku örüntüsü, doğru bağlantıdan geçerek hareketi yönlendirebiliyor mu ve kokudan gelen bilgi hareketi rastgele keşfe göre iyileştiriyor mu?”** İlk denemede amacımız bütün sinek zekâsını değil, **sensör → beyin → motor kapalı döngüsünü** doğrulamak.

### 3.2 Dünya üretimi

- O1a: engelsiz düz koridor, kaynak son noktada. Bilinen kokunun yoğunluğu yola paralel kontrollü biçimde artsın. Kolay ve sentetik.
- O1b: eğri koku koridoru (tek dönüş), koku yoğunluğu yalnız doğru yol boyunca erişilebilir; sahte bağlantı olmadığından emin ol.
- O1c: kesintili şerit/plume, koku kısa aralıklarla kaybolur; yön belleği varsa sınanır. **Bu alt seviye ana O1 geçtikten sonra**.
- O1d: hafif rüzgâr; rüzgâr duyu kanalı gerçekten eklenmişse açık. Rüzgâr olmayan bir ajandan “rüzgâra karşı uçmasını” isteme.
- Yoğunluk/kontrast dengesi: hareket kuralını doyuran aşırı güçlü kokudan kaçın. Sol/sağ anten cevap farkı sıfırlanıyorsa motor yön tayin edemez; bu veri olarak kaydedilsin.
- Hedef kokuyu tam yol boyunca sunmak doğal kaynak-plume simülasyonu değildir; **kontrollü eğitim geometrisi** olarak etiketlensin.

### 3.3 Başarı ve kayıp mekanizması

- Kazanma: hedef bölgesine gerçek fiziksel temas.
- Süre dolması: tamamlanmadı; kayıt ve yeniden deneme.
- Puan verilecekse yalnız araştırmacıya: ulaşma oranı, ulaşma süresi, gidilen yol, çarpışma, koku temas süresi, koku kaybından dönüş. Sinir ağına gizli puan gönderilmez.

### 3.4 Beklenen davranış (kesin beklenti değil)

Ödüllü kokuyu öğrenmiş bir model, bilinen kokuyla karşılaşınca daha sık onun yönüne yönelebilir; kokudan uzaklaşınca arama/dönüş davranışı gösterebilir. Mevcut motor kuralı yalnız `V_sol−V_sağ` kullandığı için iki antenin benzer koku alması durumunda **düzgün ilerleme garantisi yoktur**. Önceden koku-ödül eşlemesi olmayan bireyin hemen başarılı olması beklenmez.

### 3.5 Kontroller

- `plastic` öğrenme açık, `frozen` öğrenme kapalı; ayrıca **öğrenilmiş checkpoint + doğrulamada öğrenme kapalı**.
- Koku sıfır: sadece rastgele hareketle varış düzeyi.
- ORN devre dışı: koku bilgisi geldiğinde motor çıktısı kokuya göre değişmemeli.
- Eski **doğrudan glomerül** girişi ile yeni **ORN→AL→PN** girişi **aynı koku görevinde** kıyasla; yeni katman daha karmaşık diye otomatik iyi sayılmasın.
- Kokunun A/B veya kimlik 0/1 rolü değiştirilsin, harita aynalansın.
- Motor “oracle” hedef koordinatını biliyorsa yalnız **ulaşılabilirlik üst sınırı**dır, biyolojik kontrol değildir.

### 3.6 Önerilen geçiş ölçütleri (doğrulama öncesi kesinleşecek)

- Sensör-motor hattının tüm yapısal testleri PASS.
- Aynı haritalarda koku açık modelin ulaşma oranı, koku kapalı rastgele modele göre **en az +0,15 mutlak oran** yüksek olsun; **%99 güven aralığının fark alt ucu 0'ın üzerinde** olsun. Bu bir öneridir, pilot/güç analiziyle nihai hale getirilecek.
- Ulaşabilenler arasında yol verimi, kör modele göre daha iyi olsun; karşılaştırma sansürlü süreleri de hesaba katsın.
- Ayna testi ve yeni tohumlarda yön yanlılığı olmasın; yeni reseptör modülü eski basit modele göre aynı ya da daha kötü kalırsa sonuca dürüstçe yaz.

**Özellikle kaçınılacak aldatıcı başarı:** Görsel ısı haritasını sineğe girdi yapmak; hedef koordinatını ödül fonksiyonundan sızdırmak; çizgiye kilitlenmiş hazır dönüş kuralına “öğrenme” demek.

---

## 4. OYUN 2 — KOKU YALNIZCA FİNAL BÖLGESİNDE

**Kısa hikâye:** Oyun alanının neredeyse tamamında koku **sıfır**. Yalnızca hedef çevresinde küçük bir bölgeye girilince koku algılanabiliyor. Sinek uzaktan hedefi koklayamaz; bölgeye keşifle rastlarsa son birkaç adımı kokuyla tamamlayabilir.

### 4.1 O1'den temel fark

O1'de açık yoldan sürekli rehberlik vardır. O2'de koku, **hedefe ulaşmak için ilk büyük mesafeyi katetmede bilgi sağlamaz**. Bu nedenle “hedefi hızlı buldu” ile “kokuyla buldu” ayrı ölçülecek.

### 4.2 Fiziksel/matematiksel kural

- Örnek final koku yarıçapı `R=5 birim`, kazanma temas yarıçapı `r=1,5 birim` (tasarım önerisi). `d ≥ R` olduğunda `C=0`; `d < R` olduğunda yumuşak ve sınırlı artan bir yoğunluk. Maskenin kenarında ani türev nedeniyle fiziksel artefakt oluşursa buna “sanal koku kapısı” denir.
- **Yarıçap 5 birim** biyolojik sabit değil. R daraltma/genişletme ablas­yonu: `R=3/5/8` gibi geliştirme varyantları; doğrulama için tek değer sabitlenecek.
- Başlangıç noktası tüm denemelerde `d > R + anten uzunluğu + güvenlik payı`; aksi halde ilk anda koku koklama hilesi olur.
- Final yakınında kokunun **gerçekten** bulunması için her koku kanalı ve iki anten birim testi yapılmalı.
- Hedef alanı ile koku çemberi her haritada birlikte taşınsın, fakat sineğe koku dairesinin merkezi doğrudan iletilmesin.

### 4.3 İki ayrı alt ölçüm

**A. Bulma/arama:** İlk kez `R` koku bölgesine girme olasılığı ve süresi. O2'nin koku sistemi bunun dışındaki aşamada katkı vermemelidir. Yeni haritalarda, önceden mekânsal bilgi yoksa bu performansın kör keşfe benzemesi beklenir.

**B. Son yaklaşma:** Koku bölgesine girdikten sonra gerçek hedefe ulaşma olasılığı ve kalan süre. Koku arayüzü etkiliyse burada koku açık/kapalı farkı çıkabilir.

**Geriye dönük seçilim hatası:** Yalnızca koku bölgesine giren canlıları karşılaştırmak farklı koşullarda farklı bireyleri seçebilir. Çözüm: aynı içeri giriş konumu/yönüyle **eşleşmiş son-yaklaşma testleri** kur; bütün denemelerde de toplam başarı oranını ayrıca tut.

### 4.4 Kontroller ve geçiş

- `R=0` / koku tamamen kapalı kontrolü.
- Final bölgesine aynı konumdan giren koku açık/kapalı eşli test.
- R ve hedefin yeri gizli; başka duyuların yanlışlıkla işaret vermediği kontrol.
- Beklenen doğru rapor: **“Uzaktan koku rehberliği yok; bölgeye giriş keşifle, son yönelim kokuyla olabilir.”**
- Önerilen başarım: eşleştirilmiş son-yaklaşma kazanma oranı farkı >0 ve istatistiksel olarak güvenilir; tüm-oyun başarı oranı ayrıca raporlanır. Eğer bölgeye rastlama oranı çok düşükse bu koku öğrenmesinin değil **arama politikasının** sınırıdır.

**Önemli:** O2 deneyini “tamamen kokusuz oyunda koku ile yol buldu” diye adlandırma.

---

## 5. OYUN 3 — KOKU SADECE FİNALE GERÇEKTEN ULAŞINCA

**Kısa hikâye:** Sinek başlangıçta, koridorda, final yakınında, hatta finalin bir adım gerisinde bile koku almaz. Sadece **hedefe fiziksel olarak dokunduğunda** hedefle ilişkili koku ve ayrı tanımlanmış ödül/temas sinyali oluşur. Kullanıcı kuralına göre temas öncesinde kokunun hiçbir izi yoktur.

### 5.1 Bilgi kuramsal gerçeklik

Aynı başlangıç, aynı duyusal geçmiş ve kokusuz iki farklı hedef konumu düşün. **Yalnız kokuya bakan ajan** bu iki dünyayı hedefe temas etmeden önce ayırt edemez. Bu durumda bir hedefe uzaktan özel olarak yönelmesi beklenemez. Hedefi buluyorsa olası nedenler: şans, arama alışkanlığı, öğrenilmiş dünya düzeni, özduyum, başka gerçek duyu veya bilgi sızıntısı.

O3'ü **“koku algılayıcısını sınamak” diye değil**, **“ipucusuz keşif + tesadüfi temastan sonra öğrenme/bellek”** diye yorumla. Bu test tek başına biyolojik sineğin böyle bir görevde üstün olması gerektiği anlamına gelmez.

### 5.2 Temas olay sırası — tartışmasız sözleşme

1. Adım başında tüm ortam `C=0`; her iki anten için kokuya bağlı aktivasyon sıfır.
2. Beyin yalnız geçmişteki ve o anda izin verilen bilgileri değerlendirir.
3. Motor hareketi uygulamaya konur; temas **hareketten sonra** saptanır.
4. Temas yoksa `C=0` kalır; **finale yakın** olmak ödül/duyu üretmez.
5. Temas varsa “kazandı” olayı işlenir; sonrasında koku/ödül sinyali bir sonraki uygun adımda sunulur. İlk temas kararını geriye dönük değiştiremez.
6. Oyun biterken olay kaydı saklanır; varsa sinaptik öğrenme **sonraki denemelerde** incelenir.

### 5.3 O3'ün gerçekten cevaplayabileceği sorular

- İlk kez hedefi bulma olasılığı ne? Kör rastgele kontrolle kıyaslandığında arama davranışı daha mı verimli?
- Aynı harita farklı başlangıçlarda tekrarlandığında önceki ziyaretin anısı sonraki denemede fayda sağlıyor mu?
- **Harita değişince** fayda kayboluyor mu? Eğer kayboluyorsa yer/rota ezberi ile genel keşif stratejisini ayır.
- Temasta gelen **koku etiketi**, temasta gelen **ödül** ve salt **temas**, sinaptik öğrenmeyi farklı etkiliyor mu?
- Koku bir sonraki denemede yine yalnızca temasta geliyorsa ilk adımda kokuyu kullanarak hedef araması mümkün değildir. Koku daha sonra önceden sunulursa bu **yeni, ayrı transfer deneyi** olur.

### 5.4 Zorunlu faktöriyel denetimler

| Koşul | Hedefte temas ödülü | Hedef temasında koku | Amaç |
|---|---|---|---|
| O3-A | Var | Var | Kullanıcının asıl oyunu |
| O3-B | Var | Yok | Koku gerekli mi? |
| O3-C | Yok, yalnız nötr temas | Var | Koku tek başına ödül mü sanılıyor? |
| O3-D | Yok | Yok | Tam kör temel çizgi |

Tüm koşullarda hedefe **temasın fiziksel tespiti** aynı çalışmalı. Temas sinyali beynin üzerinde önceden tanımlı “burası final” etiketi taşımamalı.

### 5.5 Başarı nasıl yorumlanmalı?

- **Etkili keşif** varsa ve farklı yeni haritalarda kör arama temel çizgisini geçiyorsa mekânsal arama için kanıt olabilir.
- **Eşit sonuç** çıkarsa ve hiçbir önbilgi yoksa bilimsel olarak makul olabilir; otomatik FAIL değildir.
- Öğrenilmiş bir rota aynı haritada tekrar kullanılıyorsa bu hafıza lehine bulgudur, fakat motor sistemin veya başlama yönünün hilesiyle ayırt edilmelidir.
- O3 tamamlanmadan önce “uzaktan koku aldığı” görülürse bilimsel başarı değil **kritik bilgi sızıntısı**dır.

### 5.6 Hazır olmayan sistem için dürüst kapı

Mevcut `agent.py` karmaşık yer belleği/harita modülü sağlamıyor. O3'te kör hareketle yetinen canlı uzun süre dolaşabilir. Önce **mevcut modelin kör temel çizgisi** kaydedilsin; daha sonra merkezî kompleks/çalışma belleği/ziyaret edilen bölgeyi kısa süreli tutma modülü eklenirse aynı deney, tüm kontrol koşulları korunarak tekrarlansın. “Özduyum ve bellek” eklendiği açıkça yazılsın.

---

## 6. OYUN 4 — TAMAMEN YANLIŞ YOLA ÇEKEN KOKU

**Kısa hikâye:** Gerçek hedef başka bir yerde. Güçlü/fark edilir bir koku sineği **yanlış çıkmaza** veya ödülsüz kaynağa çekiyor. İlk denemelerde kokuyu izleyip yanılabilir. Ama bu yolu izlediğinde hedefe ulaşamaması ve/veya ödülsüz temas yaşaması sayesinde sonraki denemelerde davranışını yeniden ayarlaması araştırılır.

### 6.1 Önce çözülmesi gereken mantık

Yanlış kokuya rağmen doğru finale ulaşmak **iki ayrı beceri** içerir:

1. **Aldatıcı kokuyu öğrenip takip etmemek.** Olası olarak mevcut KC→MBON değer güncellemesiyle kısmen öğrenilebilir, ancak dekoy kokuyla ödülsüz temasın öğrenme devresine gerçekten iletilmesi gerekir.
2. **Doğru hedefi bulmak.** Yanlış koku dışındaki bölgelerde hiç ipucu yoksa O3'teki keşif problemi aynen devam eder. Yanlış kokuya güvenmeyi bırakmak, doğru hedef koordinatını bilmek değildir.

Bu ikisini tek “oyunu kazandı/kaybetti” sayısına sıkıştırma.

### 6.2 Oyun alanı

- Başlangıçtan çıkan **iki makul yol**: biri yanlış kokulu çıkmaza, diğeri gerçek hedefe. Her iki yola erişim açık; engel ve yol uzunluğu mümkün olduğunca dengeli.
- İlk ana protokolde **yalnız yanlış yol kokulu**, gerçek final kokusuz. Alternatif deneyde hem yanlış hem doğru koku varsa bu **O4b** adında ayrı koşuldur.
- Sahte kaynağa gidiş mümkün; temas halinde **ödül = 0**, nötr temas. İlk deneyde keyfî acı/ceza eklemeyelim; ceza içeren sürüm ayrı şarttır.
- Şu an modelde `last_delta = temas × (hedef_ödül − V)` benzeri **elle tanımlanmış** hata sinyali bulunuyor. Sahte temasta beklenti varsa ödül yokluğuyla değer değişimi olabilir; bu, otomatik “yanlış bilgi tespit eden zekâ” değil modellenmiş öğrenme kuralıdır.
- Sahte koku kimliğini bazen önce ödüllü koku (öğrenilmiş çekicilik), bazen daha önce görülmemiş koku yap. **Bu iki koşulu birleştirip tek başarı diye raporlama.** Yeni kokunun ilk denemede çekici olmak zorunda olmadığı açık.

### 6.3 Üç zorunlu alt oyun

**O4a — Beklenti çatışması:** Önce O1'de kokunun ödüllü olduğu öğrenilmiş. Aynı kokunun kaynağı yanlış yola konur; sahte temas ödülsüzdür. Ölç: sahte kaynağa ilk gidiş, kaç bölümde bu çekim azalıyor? Bu en doğrudan **değer yeniden öğrenme** testidir.

**O4b — Aynı anda doğru ve yanlış koku:** Doğru hedef daha zayıf ama gerçek ödüllü koku taşır, sahte hedef güçlü veya tanıdık koku taşır. Burada koku bilgisiyle **seçim/çelişki çözme** ölçülebilir. Kullanıcının asıl O4 şartını değiştirdiği için ayrı etiketlenir.

**O4c — Doğru hedef tamamen kokusuz:** Sinek yanlış kokuyu terk eder ve genel keşifle gerçek hedefi arar. O4'ün en zor sürümüdür. **Kokudan doğru hedef çıkarımı beklenmez.** Bu koşul O3'le aynı kör arama problemine bağlıdır.

### 6.4 Eğitim ve beklenen öğrenme eğrisi

- Önce ön-kayıtlı sayıda **yalnızca doğru ödüllü koku** deneyimi: başlangıçta pozitif koku tercihi gerçekten var mı doğrula.
- Sonra **aldatıcı faz**: her deneme aynı davranış protokolü, ama harita ve sahte yol konumu dengeli. Her bölümde sahte yola ilk dönüş, sahte temas, gerçek hedefe temas, karar süresi, kapana saplanma, yeniden keşif ve öğrenilmiş koku değeri kaydedilsin.
- Sonra **transfer testi**: yanlış kol sağdan sola, sahte koku kimliği başka kimliğe, gerçek hedef yeni haritaya taşınsın. Yalnız konum ezberlemişse genelleme iddiası kurulmaz.
- Sonra **ödül geri geldi testi** (ayrı): eskiden sahte olan koku yeniden ödüllendirilince öğrenme geri dönebiliyor mu? Bu, katı “kokuyu her zaman kötüdür” ezberinden farklıdır.
- **Başlangıçta şaşırması normal olabilir.** Asıl öğrenme ölçütü, deneyimle ve yeni tohumlarda sahte kokuyu izleme eğiliminin anlamlı biçimde azalmasıdır.

### 6.5 Zorunlu kontroller

- `frozen`: aynı sahte ödülsüz temasları yaşar, ama sinapslar değişmez.
- `random`: kokuya göre dönmez, aynı hareket/gürültü bütçesiyle dolaşır.
- `sham decoy`: sahte yer aynı geometride var, koku yok; koku cezası ile çıkmaz geometrisini ayırır.
- Yer değişimi ve ayna; sahte kokunun yönü hiçbir zaman sabit kalmaz.
- Sahte kokunun miktarı/kapsadığı alan hedef kokusuna göre aşırı genişse sürece **kokunun baskınlığı** hükmedebilir; dikkatlice kaydet.
- Ödül sinyali sahte temasta gerçekten `0` mı? Koku, ödülsüz bilgi güncellemesine bağlanıyor mu? Birim test.
- **İki ölçüt ayrı:** “aldatıcıya gitme oranı azaldı” ve “gerçek hedefe ulaşma oranı yükseldi”. İlki gerçekleşip ikincisi gerçekleşmeyebilir; bu anlamlı bir bulgudur.

### 6.6 Geçiş ölçütü önerisi

- Sahte yol/ödülsüz temas oranı ardışık önceden sabit eğitim pencerelerinde, `frozen` kontrolüne kıyasla **en az 0,15 mutlak oran** azalsın; fark için %99 kümeli güven aralığı 0'ı dışlasın (güç analizinden sonra sabitlenir).
- Yeni harita/ayna kombinasyonlarında etki kısmen korunsun; doğrulamada tekrar görülmezse “ezber olabilir” diye raporla.
- Gerçek finale varma başarısı **ayrıca** kör arama temeliyle kıyaslanmalı; doğru hedef kokusuzsa O3 düzeyinde kalabilir. Başarı kriteri iki ayrı özelliği karıştırmamalı.
- Öğrenme yok kontrolünde koku takip oranı kendiliğinden düşüyorsa **habituasyon, tükenme, test düzeni veya motor gürültüsü** gibi nedenleri araştır.

---

## 7. Reseptörleri ve koku nöronlarını ekleme stratejisi

### 7.1 Şimdi milyonlarca reseptör molekülü simüle etmeyin

Gerçek sinekte **reseptör proteini çeşidi**, **reseptör protein kopyası**, **ORN hücresi**, **glomerül** ve **PN nöronu** farklı ölçeklerdir. Bunları aynı “nöron sayısı”na toplamak yanlıştır. Başlangıç için az sayıda reseptör **tipinin matematiksel tepkisi** yeterli olabilir. Biyolojik kayıtlardan kaynaklı molekül-tepki tablosu doğrulanmadan “gerçek sinek reseptörü tamamlandı” denmez.

### 7.2 Geliştirme basamakları

| Basamak | İş | Giriş/çıkış şartı |
|---|---|---|
| **S0** | Mevcut doğrudan glomerül hattına dokunmadan dondurulmuş Evre 2b regresyonu | Aynı tohum/konfigde eski sonuç ve checkpoint bozulmuyor |
| **S1** | `C_k` kimyasal koku konsantrasyonu ve antene örnekleme | Testte istenen maske dışında sıfır, hedefe göre konumla değişiyor |
| **S2** | Tip-bazlı OR/IR yanıtı (konsantrasyon tepkisi, doyma, adaptasyon) | Birim test: sıfır/az/çok, çapraz tepki ve saturasyon |
| **S3** | ORN aktivitelerini glomerül popülasyonlarına grupla | Aynı sınıf ORN'leri uygun glomerül kanalına yönleniyor |
| **S4** | Anten lobu yerel işleme; ilk adımda basit, sonra kaynak-temelli | Bilinen yapay koku örüntüsüne beklenen PN cevabı; koku yokta yalnız bazal aktivite |
| **S5** | PN → mevcut KC devresine adapte et | Eski kontrol deneyleri yeni sensörle çalışıyor; farklar açıklanabiliyor |
| **S6** | O1–O4 oyunları | Eski ve yeni sensör aynı harita, motor, ödül ve zaman bütçesinde kıyaslanıyor |

### 7.3 Önerilen teknik modüller (sadece tasarım; oluşturulmadı)

- `sensory/odor_field`: moleküler koku haritası ve sonlu maske; rüzgâr ayrı.
- `sensory/receptors`: tip bazlı koku-cevap/tuning, adaptasyon.
- `sensory/orn`: isteğe göre tip-popülasyon veya hücre-düzeyi ateşleme.
- `sensory/antennal_lobe`: ORN→glomerül→PN dönüşümü.
- `experiments/odor_games`: dört oyunun ortak sözleşmesi ve koşum denetimi.
- `experiments/controls`: koku yok, ORN kesme, öğrenme kapama, ayna, eşleşmiş başlangıç, oracle doğrulaması.
- `experiments/reporting`: olay kayıtları, belirsizlik ve görseller.

**Eski `brain.step(glom, taste, touch, learn)` API'sini başlangıçta korumak** regresyon riskini azaltır: yeni katman `glom` çıktısını üretir. Daha sonra daha biyolojik PN ateşleme arayüzüne geçilecekse eski koda uyum katmanı ve yeni ön-kayıt kullanılmalı.

### 7.4 Gerçekçilik katmanları

- **L0 — Sentetik sensör:** kontrollü Gauss/plume konsantrasyonundan doğrudan glomerül; mevcut sistemle kıyas için.
- **L1 — Tip-bazlı reseptör:** birden çok kokuya farklı, doğrulanan reseptör tepkisi ve adaptasyon.
- **L2 — ORN hücre/popülasyon seviyesi:** olası binlerce hücre ama sınırlı tip; sayıyı artırmak tek başına hedef değil.
- **L3 — Anten lobu + gerçeğe dayalı bağlantılar:** tip eşleme, glomerül işlemesi, nöromodülasyon ve bağlantı/parametre belirsizliği.

Her katmanda **ablasyon**: katkı var mı? Yoksa model büyümesi başarı sayılmaz. Gerçek connectome duyu periferisini eksiksiz içeriyormuş gibi davranma; veri uygunluğu kontrol edilsin.

---

## 8. Evrensel deney protokolü

### 8.1 Sıfırdan doğrulamaya sekiz kapı

**K0 — Depo sabitleme:** branch/commit, bağımlılık sürümleri, veri lisansı/hash, temel testler ve eski Evre 2b sonuç referansı kayda geçir. Eski doğrulayıcı `seed=30,31` yeni sonuç doğrulaması için tekrar kullanılsa bile **yeni oyunun doğrulayıcı tohumları olarak yeniden seçilmesin**.

**K1 — Oyun fizik doğrulaması:** harita gerçekten geçilebilir mi; koku hangi koordinatlarda sıfır; temas sırası doğru mu; başlangıçtan beklenmedik hedef görünürlüğü var mı? Birim test.

**K2 — Sensör izolasyonu:** kaynaktan uzaklık, konsantrasyon, her reseptör tipi, ORN, anten lobu, PN ve V çıktısını ayrı ayrı kaydet; “koku yok” ve “koku var” arası fark izlenebilir olsun.

**K3 — Hareket testi:** koku değeri `V_sol > V_sağ` iken sola/sağa beklenen dönüş; eşitken gürültü rejimi, duvarda takılmama, süre ve enerji tutarlılığı.

**K4 — Rastgele ve frozen temel çizgiler:** her harita için önce aynı şartlarda kör ve öğrenme kapalı politikalar; doğal kazanma zorluğu ölçülmeden “öğrendi” demeyin.

**K5 — Pilot:** geliştirme tohumları ve az örnekle yalnız hata ayıklama, arayüz parametresi seçimi, güç hesabı. Pilot sonuçları **kanıt sayılmaz**.

**K6 — Ön-kayıt:** oyun, harita üretme kodu, örnek sayısı, ölçütler, hata kapıları, analiz kodu ve durma kuralı **doğrulayıcı koşulardan önce** versiyonlanır. Sıfır-etki ve bilinen-etki benzetimiyle yanlış pozitif/güç kontrolü.

**K7 — Kör doğrulama:** daha önce kullanılmamış tohum, harita ve koku çiftleri. Hata olursa sebep araştırılır; koşu atılmaz. Gerçek yazılım hatası varsa ön-kayıt uyarınca geçersiz sayılır ve hatanın izleri korunur.

**K8 — Sonuç ve bağımsız tekrar:** aynı kod/konfig ile ham olay sonuçları, hata analizi, grafikleri, hash'leri. İmkân varsa farklı seed/cihaz ve farklı koku kimliğiyle çoğaltma.

### 8.2 Asgari kontrol matrisi

| Kodu | Kontrol | Yanıtladığı soru |
|---|---|---|
| C0 | Öğrenme açık, tam duyusal hat | Hedef model ne yapıyor? |
| C1 | `frozen` | Deneyimle değişme gerçekten var mı? |
| C2 | Motor koku kazancı sıfır (`random`) | Kör keşifle aynı şey mi? |
| C3 | ORN/koku katmanı tamamen kesik | Fark koku girişinden mi geliyor? |
| C4 | Eski doğrudan glomerül modu | Yeni reseptör katmanının katkısı var mı? |
| C5 | Harita/koku/hedef aynalanmış ve yer değiştirmiş | Sabit yön/konum hilesi var mı? |
| C6 | Koku kimlikleri değişmiş ama ödül rolleri dengeli | Yalnız koku 0'a yanlılık mı? |
| C7 | Sensör verileri zaman içinde permüte/geciktirilmiş | Anlık doğru koku bilgisinin önemi ne? |
| C8 | Hedef yalnız oracle ile doğrulanmış | Harita gerçekten çözülebilir mi? |
| C9 | Kaydet/yükle sonrası aynı giriş | Bellek ve yeniden üretim korunuyor mu? |
| C10 | Seyirci ısı haritası açık/kapalı | Arayüz fizik veya ajanı etkiliyor mu? |

**Kontrol kapsamı oyuna göre değişebilir**, ama başlıca neden-sonuç iddiası desteklenmeden hiçbir oyun “kanıtlanmış” ilan edilmemeli.

---

## 9. Ölçüm sistemi: tek “kazandı/kaybetti” yeterli değil

### 9.1 Tanımlar

- `N`: geçerli deneme sayısı; `n_hit`: zaman sınırından önce gerçek hedef temas sayısı.
- **Hedefe varma oranı:** `p_hit = n_hit / N`.
- **İlk kokuyu alma zamanı:** sensörün bazal ateşlemesinden anlamlı derecede ayrıldığı ilk zaman (önceden belirlenen eşik; kör eşik üzerinden değil).
- **Final çevresine ilk giriş zamanı:** O2'de hem koku bölgesine giriş hem gerçek bitiş ayrı.
- **Aldatıcıya ilk yönelme/ilk temas:** O4'te gerçek hedeften bağımsız davranış ölçüsü.
- **Toplam yol `L_travel`**; başarılı denemelerde **yol verimi** `E = L_shortest / L_travel`, `0 < E ≤ 1`. Yalnız başarılıları seçerek yorumlamamak için `p_hit` ve tüm denemeler için sansürlü süre analizi de raporlanır.
- **Varış süresi:** ulaşılanlarda süre; ulaşılmayanlar **sağdan sansürlü** olarak raporlanır. “Yalnız kazananların ortalaması” başarı karşılaştırmasını çarpıtır.
- **Davranış eğrisi:** eğitim bölümü → hedefe varış oranı, decoy temas oranı, belleğe kalan etki.
- **Bilgi kullanımı:** koku alındı/alınmadı, anten farkı, `V_sol/V_sağ`, dönüş, temas ve ödül olayları zaman çizelgesi.
- **Nedensel katkı:** aynı deneyde reseptör açık/kesik, motor açık/sabit ve koku doğru/karıştırılmış farkları.

### 9.2 Ön-kayıtlı ana metrikler

| Oyun | Ana metrik | İkincil metrik | Beklenen dürüst yorum |
|---|---|---|---|
| O1 | Koku açık−koku kapalı `p_hit` farkı | Yol verimi, süre, anten farklılaşması | Koku ile navigasyon katkısı |
| O2 | Eşleşmiş final-bölgesi girişlerinden sonra `p_hit` farkı | Bölgeye ilk giriş süresi, tüm oyun başarısı | **Yakın** koku algısı; uzak arama farklı beceri |
| O3 | `p_hit` ve haritalar arası keşif verimi (kör baseline göre) | Aynı harita tekrarında öğrenme, koku/ödül etkisi | Kokusuz arama; önceden koku yönlendirmesi yok |
| O4 | Eğitimle decoy takip oranındaki azalma (`plastic`−`frozen`) | Hedef başarısı, yeniden öğrenme, transfer | Değer güncelleme; gerçek hedefi bulma ayrı |

### 9.3 İstatistik ve örnekleme planı

**Ön örnek planı (kesin güç analizi değildir):** 2 bağımsız doğrulayıcı rastgelelik tohumu × **24 sanal canlı** × **canlı başına 16 harita/deneme** × 4 oyun = **3.072 temel deneme / model koşulu**. Her oyun için 768 deneme/koşul; bunun 16 tekrarı **bağımsız 16 yeni canlı değildir**. Ayrı harita tohumu ve aynı beyin kökeni yüzünden hem **canlı** hem **harita** bağımlılığı ele alınmalıdır.

- Mümkünse **eşleştirilmiş deney**: aynı canlı, aynı başlangıç ve harita, fakat duyu açık/kapalı; random stream ayrımı ve kopya durumu önceden sabitlenir.
- Güven aralığı: canlı ve harita düzeylerini koruyan hiyerarşik bootstrap veya uygun karma-etki model. Basit deneme başına binom testi tek başına kullanılmaz.
- **İstatistiksel alfa önerisi:** ana doğrulayıcı karşılaştırma için `0,01`; birden çok keşifsel ikili test yapılacaksa düzeltme veya açık keşif etiketi.
- **Etkili fark eşiği önerisi:** `+0,15` mutlak `p_hit` / `−0,15` decoy oranı gibi asgari pratik büyüklük. Bu **keyfî başlangıçtır**, sentetik sıfır/bilinen etki simülasyonları ve bütçe üzerinden **önceden** kalibre edilir.
- Pilotlar: ör. **8 canlı × 4 deneme** / oyun ve kör kontroller; hata ayıklama/güç hesabı için, başarı iddiası için değil.
- Nihai örnek büyüklüğü, etkili birimleri ve gereken güç **pilot varyansı üzerinden yeniden hesaplanıp doğrulamadan önce dondurulmalı**. Etki küçükse 24×16 yetersiz çıkabilir.
- Bir oyunun “başarısı” tüm ölçütlere bağlıysa, aynı Evre 2b gibi **ön-kayıtlı birleşim kuralı** kullanılmalı. Ama **O3 için ‘koku açık > kör’ koşulu konamaz**, çünkü kokunun yön bildirmediği koşulda böyle bir üstünlük mantıksal olarak gerekmez.

### 9.4 Çalışma yükü kaba hesabı — ölçülmüş performans değil

- Temel deneme sayısı: `2 × 24 × 16 × 4 = 3072`.
- Hepsi **60 sanal saniye** sınırına kadar sürerse: deneme başına `60 / 0,02 = 3000` dünya adımı; toplam `3072 × 3000 = 9.216.000 ajan·dünya-adımı` (**tek model koşulu için üst kaba hesap**).
- Modelin dünya adımı başına `10` nöral alt adımı kullanıldığı varsayımıyla `92.160.000 ajan·nöral-alt-adımı`. Bu, **hesap süresi değil operasyon sayacı**; her adımda işlem sayısı bağlantı ve uygulamaya göre değişir.
- Örneğin 5 ana karşılaştırma koşulu eşit şekilde çalıştırılırsa teorik üst sayı `5 × 3072 = 15.360 deneme` ve `46.080.000 ajan·dünya-adımı` olur; ek eğitim, harita üretimi, örnekleme ve kontroller dahil değildir.
- Bu bütçe bugün CPU'da kullanışlı olmayabilir. **Önce küçük pilotta sanal saniye / gerçek saniye, RAM/VRAM tepe kullanımı, adım/s ölçülür.** 3070 Ti Mobile 8 GB / 32 GB RAM kapasitesi hakkında test yapmadan süre veya garanti verilmez.
- `batch` ile eşzamanlı çok canlı çalıştırma **16 denemenin maliyetini otomatik yok etmez**; modelin `KC→MBON` ağırlık tensörü yoğun saklanıyorsa VRAM baskısı olabilir. Çok sayıda ORN eklenirse seyrek/vektörize tasarıma öncelik verilir.

---

## 10. Risk sicili — bütün kritik ve yüksek riskler

**Skala:** Olasılık `O`: Düşük/Orta/Yüksek, Etki `E`: Orta/Yüksek/Kritik. Bunlar ölçülmüş olasılık değil, tasarım önceliklendirmesidir. Her “kritik” risk kabul kapısından önce testle kapatılmalı. **Tam kapsam garantisi vermek mümkün değildir**, ancak bu liste bilimsel/geometrik/yazılımsal/istatistiksel ana hata sınıflarını kapsar.

| ID | Risk | O / E | Belirti | Zorunlu önlem / kanıt |
|---|---|---|---|---|
| R01 | Gauss kuyruğundan O2/O3'e uzak koku sızması | Y/K | Uzakta küçük >0 `C` | Sert destek maskesi; tüm ızgarada ve rasgele alt-piksel noktalarda zero-test |
| R02 | PN bazal ateşlemesini gerçek koku sanmak | Y/Y | `C=0` iken spike var | Kokuya bağlı ek ateşlemeyi bazaldan ayır |
| R03 | Seyirci koku ısı haritasının sineğe girmesi | O/K | Arayüz kapatınca başarı değişiyor | İki ayrı veri akışı; arayüz açık/kapalı eşitlik testi |
| R04 | Hedef koordinatı, bitiş mesafesi veya yol oracledan sızıyor | O/K | Kokusuzken kusursuz hedef dönüşleri | Beyin API girdi denetimi, oyuncu logu, adversarial haritalar |
| R05 | O3'te temastan önce koku tetiklenmesi | Y/K | Finale yakınken sensör aktif | Zaman sıralama/invariant testi; adım önce/sonra log |
| R06 | O2 koku bölgesine başlangıçta yanlışlıkla girilmesi | O/Y | İlk adımda koku | Başlangıç uzaklığı/anten güvenlik payı doğrulama |
| R07 | Hedefle temas fiziksel olarak imkânsız | O/K | Oracle bile kazanmıyor | Bağlılık ve yol-uzunluk testi |
| R08 | Yalnız doğuya/sağa giderek kazanma | O/Y | Ayna testinde çöküş | Harita ve hedef rol dengelemesi |
| R09 | Sonsuz döngü, köşede takılma | Y/Y | Süre dolana dek sabit dönme | Timeout, stuck sayacı, checkpoint, ayrı hareket hatası |
| R10 | “Süre doldu” durumunu öğrenme başarısızlığına eşitlemek | Y/Y | O3 gereksiz FAIL | Sansürlü başarı/süre raporu |
| R11 | O3'ü koku yönlendirme başarısı diye yorumlamak | Y/K | Kokusuzken “koku buldu” iddiası | Bilgi sınırı notu, faktöriyel kontroller |
| R12 | O4'te decoydan kaçınmayı hedef bulma ile karıştırmak | Y/K | Decoy azalıyor, hedef bulunmuyor | İki ayrı ana çıktı |
| R13 | O4 sahte kokuya hiç başlangıç ilgisi olmaması | O/Y | Yanıltılamıyor | Önce ödüllü koku checkpoint'i doğrula; novel odor ayrı |
| R14 | Sahte temas negatif öğrenme üretmiyor | Y/Y | Koku değeri hiç değişmiyor | `delta`, gate, sinaps güncelleme izleri; birim test |
| R15 | Ödül/temas ile koku aynı olayda yanlış sırada işleniyor | Y/K | Önceden haber verilmiş gibi davranıyor | Çift zaman damgası; nedensel adım sözleşmesi |
| R16 | Yeni ORN duyarlılığı aşırı güçlü/zayıf | Y/Y | Doyma veya sessizlik | Konsantrasyon-yanıt eğrileri, kalibrasyon |
| R17 | Re­septör–glomerül eşlemesi keyfî ve yanlış | O/Y | Yeni koku kimliği tutarsız | Kaynak tablosu/etiket denetimi; model varsayımı olarak açıklama |
| R18 | ORN katmanı eski Evre 2b öğrenmesini bozuyor | Y/Y | Regresyon başarısız | Eski API ve S0 dondurma, kapalı açılır modül |
| R19 | Sağ yarımküre verisini ikiye kopyalamayı gerçek iki yarımküre sanmak | O/Y | Anatomik iddia | Model açıklaması, veri kaynağı ve ikileme notu |
| R20 | Rüzgâr yokken rüzgâra karşı yönelim beklemek | Y/Y | O1c sahte başarısız | Rüzgâr sensörü eklenmediyse bu davranışı ölçüt yapma |
| R21 | Koku yolunun biyolojik olarak gerçek dışı “parlak çizgi” olması | Y/O | Oyunda mükemmel iz | Öğretici kontrollü test etiketi; ayrı plume modu |
| R22 | Ödülün gerçekten son hedef dışında verilmesi | O/K | Sahte hedefte başarı öğrenimi | Ödül/temas olay sözleşmesi ve invariant test |
| R23 | Koku deseni eğitim/testte değişiyor (eski E-01) | O/K | Eğitimde başarılı, testte tutarsız | Desen/hashes checkpoint'e bağlı, regresyon testi |
| R24 | `frozen`/`random` kontrolü yanlış uygulanıyor | O/K | Kontrol öğreniyor veya motor dönüyor | Ağırlık değişmezlik ve dönüş kazancı testleri |
| R25 | Tek canlıdaki 16 denemeyi 16 bağımsız canlı saymak | Y/K | Sahte dar CI | Canlı/harita kümeli analiz |
| R26 | Hedefi gördükten sonra eşik değiştirmek | Y/K | Sürekli “PASS” | Ön-kayıt + doğrulama tohumu karartma |
| R27 | Koku kimliği/kaynağı pilotta aşırı seçilmiş | O/Y | Başka kokuya geçince çöküş | Bağımsız koku ve harita çiftleri, raporlanmış seçim kuralı |
| R28 | Harita ezberinin genellemeymiş gibi görünmesi | Y/Y | Yeni geometriden başarısız | Eğitim/test haritası ayrımı |
| R29 | Ödül kalkınca davranış azalmasının sadece duyusal adaptasyon olması | O/Y | Öğrenme kapalıda da azalma | `frozen`, koku adaptasyonu sıfırlama ve süre eşleştirme |
| R30 | Hareket gürültüsünün/seed'in koşullarda farklı ilerlemesi | O/Y | Paired kontrol tam eşleşmiyor | Ayrı RNG akışları ve loglanan tohum/akış |
| R31 | Enerji azalması/ölümden kaynaklı yanlış sonuç | O/Y | Koku yokken erken durma | Enerji sabitle; sonra ayrı faktör olarak ekle |
| R32 | GPU/CPU sayısal farkı sonuç değiştiriyor | O/Y | Tohum aynı, yörünge farklı | Referans CPU; tolerans ve duyarlılık raporu |
| R33 | Uzun deney çöküyor, checkpoint yetersiz | Y/Y | Ara sonuç kayboluyor | Aşama bazlı atomik checkpoint ve doğrulanan resume |
| R34 | Yeni nöron arttıkça RAM/VRAM doluyor | O/Y | OOM, yavaşlama | Pilot profil, mini-batch, seyrek/tip düzeyi ORN |
| R35 | Ödül beklenti hatası elle tasarlanmış ama “sinek kendi keşfetti” denmesi | Y/K | Abartılı zekâ açıklaması | Learned vs hard-coded bileşenler tabloyla ayrılır |
| R36 | E1 MBON sınıf-karıştırma kontrolü bitmeden gerçek yapı iddiası | O/Y | “Gerçek beyin kanıtlandı” | E1 durumu ayrı, başarı iddiası sınırlı |
| R37 | Aynı veri kökenli 24 sanal canlıyı biyolojik bağımsız beyin saymak | Y/Y | N=24 gerçek organizma iddiası | Tek connectome kökeni açıkça belirtilir |
| R38 | Yeni koku var diye oyun bir anda çözülebilir sanmak | Y/Y | Ön-öğrenme yokken O1 başarısız | Önceden eğitim ve sıfırdan öğrenme ayrı koşular |
| R39 | O2 son bölgeye giren canlılarda seçilim yanlılığı | O/Y | Son yaklaşma farkı çarpık | Eşleşmiş giriş konumu/yönü deneyleri |
| R40 | O3/O4 doğru hedef kokusuzken gereksiz üstün başarı şartı | Y/K | Mantıken imkânsız gate | Bilgi kuramsal üst sınır ve kör kontrol |
| R41 | Görsel kanalda ya da motor kuralında gizli öğrenme | O/Y | Sadece kokuya atfedilen etki | Modül bazlı ablasyon, bileşen katkı raporu |
| R42 | Sinaps ağırlıkları kaydediliyor, ama ödül/duyu/harita geçmişi restore edilmiyor | O/Y | Kaldığı yerden farklı davranış | Tam checkpoint durumu + aynı-çıktı testi |
| R43 | Sahte kokunun yanlış yönünü belirleyen sabit geometri | O/Y | Kol yer değişince başarısız | Sol/sağ rol ve yol uzunluğu dengesi |
| R44 | Bir oyunda başarısız örneklerin rapordan ayıklanması | O/K | Sadece güzel yollar | Tüm denemeler; önceden tanımlanmış geçersiz koşul |
| R45 | Bir oyunun başarısı diğer oyunun yeteneği sayılması | Y/Y | O1 → O3 için haksız genelleme | Bağımsız ana ölçüt, çapraz test |

### 10.1 Risk sahipliği ve durdurma

- **Deney geçersiz / dur:** R01, R03–R05, R07, R15, R22–R26, R40, R44 gibi bilgi sızıntısı/ölçüm hataları gerçekleşirse **önce hatayı gider, mevcut doğrulayıcı seriyi açıkça geçersiz say**; sayıları uygun sonuç gibi yeniden kullanma.
- **Model sınırı / bilimsel sonuç:** O2/O3'te kokusuz uzak arama başarısızsa yeni sensory input eklemek çözüm olmayabilir. Buna “FAIL — koku reseptörü bozuk” demek yerine arama/yer belleği eksikliği hipotezini kontrol et.
- **Maliyet ve sistem:** R32–R34 olduğunda koşu yeniden başlatılabilir olmalı. Sadece çıkış kodu 0 değil, `N_valid`, olay logu, hash, PASS/FAIL ve eksik deneme sayısı doğrulanmalı.

---

## 11. Görsel oyun arayüzü — gelişimi gerçek zamanlı izlemek

### 11.1 Seyirci modu ve sineğin duyuları ayrı

Ekranda kullanıcı için iki panel önerilir:

**Sol panel — Oyun:** arena, sinek noktası/bedeni, yürüdüğü rota, gerçek hedef/decoy, oyun durumu ve **isteğe bağlı** renkli koku ısı haritası. Hedefi seyirciden saklama modu da olsun. **Ekranda görünen hiçbir yardımcı çizgi beyin girdisine otomatik dönüşmesin.**

**Sağ panel — Bilimsel telemetri:** iki antenin anlık koku derişimi, aktif reseptör tipleri, ORN/PN etkinlik özeti, KC seyrekliği, MBON yaklaş/kaçın sinyalleri, `V_sol−V_sağ`, ödül-hata sinyali, dönme hızı, son temas, o anki sensör modülü, öğrenme açık/kapalı. Koku yokken “bazal nöral aktivite” ayrı işaretlensin.

Alt kısımda zaman çizelgesi: **koku algılandı / koku kayboldu / tuzağa girdi / ödül verildi / ilk koku bölgesine girdi / gerçek hedefe temas**. Geliştirmede yavaşlat/tek adım/yeniden oynatma; doğrulamada bu kontroller algoritmanın zamanını etkilememeli.

### 11.2 Dört oyun için gösterim

- **O1:** tam koku koridoru mor/yeşil ısı haritası; sineğin rotası ayrı; video gözlemcide koku var, sinir ajanında yalnız iki anten verisi.
- **O2:** seyirci isterse hedefin küçücük koku adasını görür. Telemetri uzaktayken ısrarla `0` göstermeli.
- **O3:** hedefe kadar koku ısı haritası ve ORN artışı **tamamen boş**; temas karesinden sonra olay ışığı. Finale yakın bile önceden koku yok.
- **O4:** yanlış koku koridoru ile gerçek hedef farklı işaretlenir (seyirci için). Zaman çizelgesi canlı önce aldanıyor mu, sonra vazgeçiyor mu göstermeli.

### 11.3 Uygulamada aldatıcı animasyondan kaçın

Kokuyu yıldız gibi sineğe doğru akıtan animasyon, ajan gerçek veri akışını kullanmıyorsa sadece dekor olur. Çizimde **gerçek kayıtlı konsantrasyon tensorü** kullan; kaynağı, zaman damgasını ve renk normalizasyonunu göster. Otomatik renk ölçeği küçük sızıntıları görünmez kılabileceği için **sıfır değer kontrolü renkli UI ile değil sayısal testle** yapılmalı.

---

## 12. Hangi oyunu hangi evrede açmalı?

| Ön koşul | Ardından açılan oyun | Neden |
|---|---|---|
| Evre 2b regresyon ve sensory zero-test geçildi | **O1a/O1b** | Önce kapalı döngü koku takibi |
| O1 testte rastgele/frozen kontrolünü geçti | **O2** | Kokuya ancak yakınken ulaşmanın farkını test et |
| O2'nin uzak arama ile yakın koku etkisi ayrıştırıldı | **O3** | Kokusuz aramanın sınırını ölç, bellek ihtiyacını tanı |
| O4 için ödülsüz decoy teması öğrenme sinyalini gerçekten güncelliyor ve O1'de ödüllü koku öğrenilmiş | **O4a** | Önce değer tersine öğrenmesi |
| O4a tutarlı, O3'ün kör temel çizgisi biliniyor | **O4c** | Yanlış kokuyu terk edip kokusuz finali bulma |
| Önceki ana testler tamam | **O1c/O4b/çeşitli rüzgâr** | Karmaşık genelleme ve rakip ipuçları |

**Bu sıralama koşulludur.** O3'te düşük başarı O4a'yı engellemek zorunda değil: decoy değerini güncellemek, kokusuz doğru çıkışı bulmaktan farklıdır. Ancak O4c'nin yorumlanması için O3 kör keşif temel çizgisi gereklidir.

---

## 13. Geliştirici/başka yapay zekâ için somut görev dökümü

### Paket A — Kod yazmadan önce

- [ ] Bu belgeyi `README`, `karar_defteri` ve Evre 2b planı ile karşılaştır; çelişki ve eksik varsayımları kaydet.
- [ ] Koku var/yok bilgi sınırı; dokunma sırası; sensör ile seyirci ayrımını sözleşme olarak yaz.
- [ ] O2/O3 koku önbilgisi yokluğu için kısa matematiksel doğrulama hazırla.
- [ ] O4'te “yanlış kokuyu öğrenmek” ile “doğru yeri bulmak” için iki ayrı ölçüt belirle.
- [ ] Mevcut `V` motor politikasının O3/O4 için neyi yapamayacağını denetle; saklı “zihin haritası” varsayma.

### Paket B — En küçük güvenli değişiklik

- [ ] Mevcut `world.sense()` davranışını koruyan eski mod kalsın.
- [ ] `odor_field` ve maskeli `C` üzerinde sıfır sızıntı testi yaz.
- [ ] Ödül/temas olayları ile koku tetiklenmesi kesin sıralama testinden geçsin.
- [ ] O1a/O2/O3/O4a için harita oracle ve ayna testleri bulunsun.
- [ ] Görselleştirmeyi kapattığında olay ve sensör çıktısı aynı olsun.
- [ ] O2/O3'te antenler başlangıçta `C=0` okuyunca temel PN ateşleme ile koku artışı birbirine karışmasın.

### Paket C — Sensor mimarisi

- [ ] OR/IR tip tablolarının kaynağı/lisansı listelensin; doğrulanmamış kurallar açık varsayım olsun.
- [ ] ORN popülasyonlarını sağ/sol doğru ölçekte kur, iki yarımküreyi yanlış iki kat nöron diye sayma.
- [ ] Glomerül indekslerinin mevcut `MBData.pn_glom` ile uyumu doğrulansın.
- [ ] Yeni sensörü kapatınca Evre 2b eski davranışı korunmuş olsun.
- [ ] Regresyon testleri ve reseptör açık/kapalı testleri olmadan “tamamlandı” denmesin.

### Paket D — Pilot ve araştırma

- [ ] Her oyunda **kör/random/frozen** temel çizgiyi çıkar.
- [ ] 8×4 pilot (öneri) ile ulaşılabilirlik, duyu dinamiği, zaman sınırı, güçlü/çok zayıf görevler teşhis edilsin.
- [ ] İstatistiksel güç, yanlış-pozitif, harita varyansı, canlı kümeleri benzetimle hesaplanıp kesin örnek sayısı seçilsin.
- [ ] İlk testlerde başarısız olan her kuralın kök nedeni raporlanıp test yazılsın.
- [ ] Pilot değerlerini doğrulayıcı sonuç yerine kullanma.

### Paket E — Ön-kayıt ve sonuç

- [ ] Dört oyunun her biri için versiyonlanmış ayrı plan ve doğrulayıcı tohum listesi.
- [ ] Koku maskesi, örüntü hash, hedef/decoy konumu, başlangıç konumu, rastgelelik, model yapılandırması ve eğitim checkpoint hash'ini rapora yaz.
- [ ] Önceden belirlenmiş çift koşular, bağımsız doğrulayıcı tohumlar.
- [ ] Test sonunda yalnız PASS değil: **etki, belirsizlik, başarısızlık, deney geçerliliği, riskler, örnek yollar** da göster.
- [ ] Gerçek sinek, özgür irade, bilinç veya biyolojik tamlık iddiası kurma.

---

## 14. Beklenen sonuçların doğru yorumlanması — karar ağacı

1. **O1 başarısız, kokulu/kokusuz sensör çıkışı farklı değil:** koku fiziği, reseptör, ORN→PN hattını incele. Öğrenmeyi değiştirmeden önce duyuyu doğrula.
2. **O1 sensör çalışıyor ama dönme yok:** `V`, motor kazancı, doyma/sol-sağ simetri, gürültü. Motor hatasını biyolojik öğrenme hatası sayma.
3. **O1 `plastic` başarılı, frozen da aynı başarılı:** daha önce öğrenilmiş checkpoint, doğuştan yanlılık, motor veya koku kimliği etkisi. Yeni öğrenme iddiası için faz ayrımını denetle.
4. **O2 çok az canlı koku bölgesine giriyor:** kokunun menzil sınırı ve arama temel çizgisi. Final-bölgesi girişine koşullu testle koku katkısını ölç.
5. **O2 giriş var, yakın varış yok:** yakın derişim dönüş sinyali, eşik ve koku saturasyonunu kontrol et.
6. **O3 kör kontrolle aynı:** önbilgi yoksa makul. Aynı haritada tekrarlarla ve izinli bellekle kıyasla. Kokuyu genişleterek oyunun şartını gizlice değiştirme.
7. **O3 koku finalden önce algılandı:** STOP; deney geçersiz, bilgi sızıntısı. Bu başarı değil hatadır.
8. **O4 sahte kokuya hiç çekilmiyor:** önce ödüllü koku beklentisi ve decoy tanımlamasını doğrula; yeni koku ile öğrenilmiş koku ayrımı.
9. **O4 sahte kokuya çekiliyor, sonra kaçınmayı öğreniyor ama gerçek hedefi bulamıyor:** değer güncellemesi var, genel keşif yeterli olmayabilir. O3 ile kıyasla.
10. **O4 yalnız aynı haritada iyi:** muhtemel ezber/konum yanlılığı; yeni layout/koku kimliği transferi şart.
11. **Dört oyunun hepsi iyi ama ablation etkisiz:** başarı reseptör katmanından gelmeyebilir; varsayılan motor/hardcoded heuristikleri analiz et.

---

## 15. Son rapor dosyalarının örnek çıktıları (gelecekte oluşacak, şu an yok)

```text
results/odor_games/<run_id>/
  manifest.json                  # commit, veri-hash, koşul, tohumlar, zaman
  preregistration.md             # ölçütler koşudan ÖNCE
  world_maps.json                # eğitim/test ayrımı, harita geometrisi
  odor_field_checks.json         # sıfır-sızıntı/temas sırası kanıtları
  events.csv                     # zaman, koku, motor, temas, ödül
  agents.csv                     # birey / deneme / başarı / timeout
  checkpoints/                  # atomik, restore-doğrulanmış
  figures/                       # 4 oyun rota+sensör+öğrenme grafikleri
  summary.md                     # sonuç+CI+kontroller+negatif bulgular
  known_limitations.md            # elle yazılan parçalar, açık riskler
```

**Not:** Bu dizinler öneri tasarımıdır; dosyaların var olduğunu iddia etmez.

---

## 16. Bilimsel kaynaklar ve neden önemli oldukları

1. [Sinek Nöronları — incelenen GitHub commit](https://github.com/muhammedaliaka/sinek-noronlari/commit/cd51319b3c78e22e527f7c8581f28f5e10398589). Bu dosyadaki **mevcut proje durumu** için birincil kaynak; laboratuvar biyolojisinin bağımsız kanıtı değildir.
2. [README — Evre 1, 2, 2b](https://github.com/muhammedaliaka/sinek-noronlari/blob/cd51319b3c78e22e527f7c8581f28f5e10398589/README.md) ve [karar defteri](https://github.com/muhammedaliaka/sinek-noronlari/blob/cd51319b3c78e22e527f7c8581f28f5e10398589/docs/karar_defteri.md). Önceki hatalar ve ön-kayıt disiplini.
3. [Smelling on the fly: sensory cues and strategies for olfactory navigation in Drosophila (2012)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3323672/). ORN→glomerül→PN biyolojik bilgi yolu, koku navigasyonu.
4. [A vector-based strategy for olfactory navigation in Drosophila (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11844514/). Gerçek sineklerin koku sınırı takibi, rüzgâr yönü ve iç yön belleği; yalnız yoğunluk takibinin sınırları.
5. [Wind Gates Olfaction Driven Search States in Free Flight (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11461137/). Rüzgâr olan ve olmayan ortamlarda farklı koku arama stratejileri.
6. [Neural dynamics for working memory and evidence integration during olfactory navigation in Drosophila (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12632460/). Koku kaybolduktan sonra yön bilgisinin kısa süreli tutulmasının biyolojik temeli.
7. [Odour motion sensing enhances navigation of complex plumes (Nature, 2022)](https://www.nature.com/articles/s41586-022-05423-4). Kokunun zaman ve hareket özelliklerinin önemini gösterir.
8. [Wind history shapes olfactory search response in free-flying Drosophila melanogaster (2026)](https://pubmed.ncbi.nlm.nih.gov/42483766/). Koku ve rüzgâr geçmişini ayırmanın gerekliliğine ilişkin güncel sonuç.
9. [Fundamental principles of the olfactory code (2018)](https://www.sciencedirect.com/science/article/pii/S0303264717303143). Koku uzayının ve duyu→beyin kodlamasının karmaşıklığı.

Bu çalışmalar, **yeni kuracağımız sanal oyunun birebir gerçek sinek davranışı** olduğunu göstermez; tasarımda hangi fizyolojik etkenlerin göz ardı edilmemesi gerektiğini gerekçelendirir.

---

## 17. Nihai tavsiye ve uygulanabilir karar

**Önerim:** Bu dört oyun kesinlikle iyi bir araştırma omurgası olur; en büyük getirisi, “koku algılama”, “koku ile yön bulma”, “kokusuz arama”, “ödül belleği” ve “yanıltıcı kokuya tepki”yi birbirinden ayırmasıdır. Önce eski sistemi sabit tutup **O1a + O2 sıfır-sızıntı + O3 temas sırası + O4a ödülsüz koku** için çok küçük bir prototip yapılmalı. Ardından gerçekçi ORN/anten lobu katmanı **geriye uyumlu ve devre dışı bırakılabilir** eklenmeli. Geçiş kararlarını başarı animasyonuna göre değil **kontroller + güven aralığı + yeni harita + yeni tohum + kayıtlı negatif sonuçlara** göre ver.

**Önemli son söz:** O3 ve O4'te gerçek hedefin kokusu hiç yoksa, mevcut koku devresinin tek başına o hedefin yerini bilmesi beklenemez. Bu sınır doğru korunursa oyunlar *çok daha değerli* olur: ileride ekleyeceğin keşif, kısa süreli yön belleği ve karar verme devrelerinin gerçekten yeni bir şey kazandırıp kazandırmadığını ayırabilirsin.
