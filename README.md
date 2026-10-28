# Sinek Nöronları — koku/ödül öğrenen dijital canlı

Sinek beyninden esinlenen, **algılayan, hareket eden, deneyimle öğrenen ve öğrendiğini koruyan** sanal bir canlı.
Bu depo uzun vadeli bir projenin **Evre 1, Evre 2 ve Evre 2b** çıktısıdır. Proje bağlamı ve hedefler: [`docs/proje_raporu.md`](docs/proje_raporu.md).

> **Dürüstlük notu:** Evre 1'de ağ, sineğin mantar cismi (*mushroom body*) mimarisinden esinlenen **sentetik** bir devredir.
> Evre 2'de aynı deney, **MaleCNS v1.0 bağlantı haritasından** çıkarılan gerçek mantar cismi alt ağıyla tekrarlandı
> (aşağıda). Hiçbiri gerçek sinek davranışı hakkında iddia taşımaz: ortam sanal, hareket kuralı elle yazılmış,
> öğrenme kuralı ve birçok parametre model varsayımıdır. **Evre 2'nin önceden yazılmış ölçütleri tam karşılanmadı** (tohum 20: 5/6, tohum 21: 4/6); ölçüm gücü artırılmış yeni ön-kayıtlı **Evre 2b**'de (tohum 30 ve 31) 7/7 ve 7/7 geçti.

## Ne yapıyor?

Sanal bir 2B arenada iki koku (A, B) vardır. Canlı başta hiçbirine yönelmez. Yiyeceğe rastlayıp tatlı bir tat
aldığında, o sırada duyduğu kokuyu ödülle ilişkilendirir. Sonra o kokuya **kendi ağının çıktısıyla** yönelir.
Ödül başka kokuya taşınırsa tercihini değiştirir. Öğrendikleri diske yazılıp yeniden yüklenince korunur.

```
 2B dünya (koku bulutları, yiyecek, enerji)
        │ koku (sol/sağ anten)            ▲ hareket
        ▼                                  │
 ORN/PN (Poisson) → KC (seyrek LIF, APL) → MBON yaklaş / MBON kaçın ──► değer V (sol, sağ)
                          ▲ plastik KC→MBON                                     │
 tat + temas nöronları → DAN: δ = temas × (ödül − V) ◄───────────────────────────┘
```

* **Beyin** (`src/sinek/brain.py`): canlı başına ~2 232 nöron; Kenyon hücreleri seyrek kodlar, MBON'lar değer üretir.
* **Öğrenme:** üç etkenli kural. KC etkinlik izi × dopamin × MBON türü. Dopamin, ödül ile ağın kendi değer tahmini
  arasındaki farktır, bu yüzden ödül kalkınca tahmin söner (silinme) ve ödül tersine çevrilince tercih döner.
* **Hareket** (`src/sinek/agent.py`): hazır parçalar sabit ileri hız, "daha değerli antene dön" eşlemesi ve rastgele
  gezinmedir. **Hangi kokunun çekici/itici olduğu** yalnızca ağın öğrendiği değerden gelir.
* **Dünya** (`src/sinek/world.py`): toplu (batch) hesaplanır; yüzlerce bağımsız canlı/deneme tek tensörde koşar.

### Bilinçli basitleştirmeler (Evre 1)

* MBON'lar tür başına ortak bir KC→MBON ağırlık vektörünü paylaşır (nöronlar bağımsız gürültüyle ayrışır).
* DAN ve APL spike atmaz (hız/gradyan birimi). Gerçekte APL zaten spike atmaz.
* Sol ve sağ yarımküre aynı KC kablolamasını kullanır, ağırlıklarını ayrı öğrenir.
* Öğrenme spike zamanlamasına (STDP) değil, KC etkinlik izine dayanır.
* Tüm parametreler model varsayımıdır, ölçülmüş biyolojik değer değildir (`src/sinek/config.py`).

## Kurulum (Windows)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

PyTorch'un CUDA sürümü için <https://pytorch.org/get-started/locally/> adresindeki komutu kullan.
`--device cuda` seçeneği kodda mevcut ama **bu sürümde CUDA üzerinde test edilmedi**; Evre 1 CPU'da koşturuldu
(2 232 nöron için GPU gerekmez).

Linux / WSL2 için aynı komutlar (`source .venv/bin/activate`).

## Deneyleri çalıştırma

```powershell
# ~2 dk, yalnızca boru hattı çalışıyor mu diye bakar (istatistik vermez)
python -m sinek.experiments.evre1 --quick --out results\quick

# tam deney: A (öğrenme) → C (bellek) → B (tersine çevirme)
python -m sinek.experiments.evre1 --out results\evre1
```

Çıktılar `results/` altına yazılır: `summary.md`, `results.json`, `ogrenme_egrisi.png`, `temaslar.png`,
`yollar.png` ve `after_A.npz` (öğrenilmiş belleğin checkpoint'i).

## Deney tasarımı ve başarı ölçütleri

Üç koşul **aynı batch içinde** koşar (aynı kablolama, aynı dünya dağılımı):

| Koşul | Ne farkı var |
|---|---|
| `plastic` | Öğrenme açık |
| `frozen` | Aynı deneyimi yaşar, sinapslar sabit (η = 0) |
| `random` | Dönüş kazancı 0, yalnızca rastgele gezinme |

* **Eğitim:** gezinme arenasında 3 A + 3 B kaynak; A tatlı (ödül), B ödülsüz. Yiyecek tüketilince yeniden doğar.
* **Seçim testi:** öğrenme kapalı, canlı merkezde, A ve B karşılıklı 12 birim uzakta (taraf rastgele). İlk temas = seçim.
  Ölçü: **A tercih oranı = A/(A+B)**, canlı başına ortalama, canlılar arası bootstrap %95 GA.
* **Ödül tersine çevirme (B):** A ödülsüz, B ödüllü; yeniden eğitim ve test.
* **Bellek (C):** checkpoint diske yazılır, sıfırdan yeni canlı kurulup yüklenir, aynı rastgele düzenlerle test edilir.

Başarı ölçütleri **sonuçlar görülmeden önce** sabitlendi; betik bunları otomatik hesaplayıp PASS/FAIL yazar:

| Kod | Ölçüt |
|---|---|
| A1 | Eğitilmiş `plastic` A-tercihi > 0.5 (GA alt sınırı) |
| A2 | `plastic` > `frozen` ve `plastic` > `random` (permütasyon testi p < 0.01) |
| A3 | Naif canlının tercihi yok (GA 0.5'i kapsar) |
| C | Yeniden yüklenen canlının ağırlıkları ve test sonuçları birebir aynı |
| B1 | Tersine çevirmeden sonra A-tercihi anlamlı düşer (p < 0.01) |
| B2 | Tersine çevirmeden sonra B tercih edilir (A-tercihi GA üst sınırı < 0.5) |

### Sonuçlar (iki bağımsız tohum, koşul başına 20 canlı)

| | Tohum 10 | Tohum 11 |
|---|---|---|
| A tercihi, eğitimsiz (`plastic`) | 0,53 | 0,51 |
| A tercihi, A eğitiminden sonra (`plastic`) | **0,74** [0,64; 0,84] | **0,88** [0,80; 0,95] |
| A tercihi, `frozen` / `random` kontrol | 0,50 / 0,46 | 0,53 / 0,51 |
| A tercihi, ödül B'ye taşındıktan sonra | **0,10** [0,03; 0,17] | **0,16** [0,07; 0,27] |
| Yeniden yüklenen canlı birebir aynı | evet | evet |
| Ölçütler | 6 / 6 PASS | 6 / 6 PASS |

Ayrıntılar, grafikler, sınırlamalar ve **ilk iki geçersiz koşuya yol açan bir hatanın hikâyesi**:
[`docs/evre1_sonuclar.md`](docs/evre1_sonuclar.md). Bu sayılar sentetik devre ve sanal dünya içindir.

## Evre 2: gerçek bağlantı haritasıyla mantar cismi

Aynı dünya, hareket kuralı ve deney hattı; beyin ise **MaleCNS v1.0** (erkek *Drosophila* beyni, sağ yarımküre mantar cismi) bağlantı
haritasından çıkarıldı: PN 123, KC 2 045, APL 1, MBON 48, DAN 161 — canlı başına **4 780 nöron**. PN→KC, KC→APL→KC ve KC→MBON sinaps
sayıları ve MBON'un hangi DAN bölmesinden dopamin aldığı **veriden** gelir. Sinaps sayısı → ağırlık dönüşümü, MBON "yaklaş/kaçın" sınıfının DAN bölme payından türetilmesi,
tat → dopamin kuralı ve hareket **varsayım/modeldir** ([`docs/evre2_plan.md`](docs/evre2_plan.md) §2: neyin veri, neyin varsayım olduğu tablosu).

Plan ve ölçütler koşulardan **önce** yazılıp commit edildi. Doğrulayıcı koşular iki yeni tohumla (geliştirmede kullanılmayan 20 ve 21), koşul başına 16 canlıyla yapıldı:

| | Tohum 20 | Tohum 21 |
|---|---|---|
| A tercihi, eğitimsiz (`plastic`) | 0,56 [0,31; 0,81] | 1,00 [1,00; 1,00] (**4 seçim**) |
| A tercihi, A eğitiminden sonra (`plastic`) | **0,92** [0,85; 0,98] | **0,90** [0,80; 0,98] |
| A tercihi, `frozen` / `random` kontrol | 0,67 / 0,47 | 0,61 / 0,54 |
| A tercihi, ödül B'ye taşındıktan sonra | **0,27** [0,10; 0,47] | **0,14** [0,07; 0,23] |
| Yeniden yüklenen canlı birebir aynı | evet | evet |
| Ölçütler | **5 / 6** (A2 FAIL) | **4 / 6** (A2, A3 FAIL) |

* **Öğrenme ve tersine çevirme büyük ve tutarlı**, bellek birebir korundu.
* **A2** (`plastic` > `frozen`, p < 0,01) iki koşuda da kaldı (p = 0,063 / 0,068). **A3** (naif tercih yok) tohum 21'de kaldı: naif ağ nadiren kaynağa ulaştığından
  (64 denemede 4–11 seçim) bu iki ölçüt çok az gözleme dayanıyor. Bu açıklama koşulardan **sonra** yapıldı; ölçüt hükmü değiştirilmedi.
* Sınıf etiketlerini karıştırma kontrolü (E1) ön-kayıtlı ölçütü formel olarak geçti, ama karıştırılmış ağlar neredeyse hiç seçim yapmadığı için kanıt zayıf.

Tam sonuçlar, grafikler, post-hoc analizler ve sınırlamalar: [`docs/evre2_sonuclar.md`](docs/evre2_sonuclar.md) ·
ek analiz: [`docs/evre2_ek_analiz.md`](docs/evre2_ek_analiz.md) · veri denetimi: [`docs/evre2_veri_denetimi.md`](docs/evre2_veri_denetimi.md).

```powershell
# veri (bir kez; ~1 GB indirme, boyut + md5 doğrulanır). Çıkarılan alt ağ depoda hazır: data/processed/malecns_v1.0_R
python -m sinek.connectome.fetch
python -m sinek.connectome.malecns
# doğrulayıcı koşu (~80 dk, CPU)
python -m sinek.experiments.evre2 --agents 16 --episodes 12 --reversal-episodes 12 --test-every 3 --trials 4 --seed 20 --threads 2 --out results\evre2_s20
# duman testi (~5 dk; yalnızca boru hattı çalışıyor mu diye bakar, istatistik vermez)
python -m sinek.experiments.evre2 --quick --out results\evre2_quick
```

**Veri atfı:** MaleCNS connectome (FlyEM / HHMI Janelia, Cambridge Zoology, MRC LMB, Google Research), CC BY 4.0; ayrıntı [`data/README.md`](data/README.md).
Nörotransmitter değerleri sınıflandırıcı tahminidir, ölçüm değildir.

## Evre 2b: aynı soru, artırılmış ölçüm gücü (yeni ön-kayıt)

Evre 2'nin iki ölçütü ölçüm gücü yüzünden kalmıştı (eğitimsiz ağ kaynağa nadiren ulaşıyor, çok az gözlem). Evre 2b, **v1'in hükmüne dokunmadan** yeni bir ön-kayıt yazdı
([`docs/evre2b_plan.md`](docs/evre2b_plan.md)): hareket okuması yaklaşık doğrusal yapıldı (ε = 2,0; eğitimsiz canlılar artık dönüp durmuyor, seçim oranı 0,17 → ~0,55), koku kimliği yanlılığı rol
dengelemesiyle giderildi, istatistik canlı-düzeyi (küme) bootstrap/permütasyona geçti, geçerlilik kapısı (G) eklendi, ölçütler benzetimle sınandı (A3'ün kusuru bu sırada bulunup düzeltildi),
deneme sayısı 16'ya çıkarıldı. Doğrulayıcı tohumlar 30 ve 31 (geliştirmede hiç kullanılmadı), koşul başına 24 canlı:

| | Tohum 30 | Tohum 31 |
|---|---|---|
| A tercihi, eğitimsiz | 0,50 [0,45; 0,54] | 0,47 [0,42; 0,52] |
| A tercihi, A eğitiminden sonra (`plastic`) | **0,72** [0,67; 0,76] | **0,74** [0,68; 0,80] |
| `frozen` / `random` kontrol | 0,51 / 0,49 | 0,46 / 0,47 |
| A tercihi, ödül B'ye taşındıktan sonra | **0,28** [0,22; 0,35] | **0,26** [0,21; 0,32] |
| Ölçütler | **7 / 7** | **7 / 7** |

* Ön-kayıtlı karar kuralına göre **Evre 2b ölçütü başarılı**. Etki orta büyüklükte (v1'de 0,90–0,92'ydi; farklı hareket okuması nedeniyle doğrudan karşılaştırılamaz).
* Hata sinyali (dopamin) hâlâ elle yazılı; "hataları daha hızlı anlama" bu sonuçla iddia edilemez. Gerçek sinek davranışı hakkında iddia yoktur.
* E1 sınıf-karıştırma kontrolü sürüyor (ana karar kuralının dışında).

Ayrıntılar: [`docs/evre2b_sonuclar.md`](docs/evre2b_sonuclar.md) · güç analizi: [`docs/evre2b_guc_analizi.md`](docs/evre2b_guc_analizi.md).

```powershell
# doğrulayıcı koşu (~3,5 saat, CPU, 2 iş parçacığı)
python -m sinek.experiments.evre2b --seed 30 --threads 2 --out results\evre2b_s30
```

## Yol haritası

| Evre | İçerik | Durum |
|---|---|---|
| 1 | Sentetik mantar cismi devresi, 2B dünya, koku/ödül öğrenme, tersine çevirme, bellek | **tamam** (6/6 ve 6/6) |
| 2 / 2b | Gerçek bağlantı verisi (MaleCNS v1.0): lisans ve sürüm doğrulaması, mantar cismi alt ağı, koku/ödül öğrenme | v1: ölçütler kısmen karşılandı (5/6 ve 4/6, ölçüm gücü sorunu); **Evre 2b (yeni ön-kayıt): 7/7 ve 7/7 geçti** |
| 2c | **Dört koku oyunu** (O1 iz, O2 yalnız final bölgesi, O3 yalnız temas, O4 yanıltıcı koku): koku algısı, kokuyla yön bulma, kokusuz arama, sönüm ayrı ayrı ölçülür | plan incelendi ve uygulandı ([`docs/dort_koku_oyunu_plani.md`](docs/dort_koku_oyunu_plani.md), kullanıcı taslağı: `docs/girdi/`); oyun dünyası, pilotlar ([`docs/odor_pilot_sonuclari.md`](docs/odor_pilot_sonuclari.md)), güç analizi ([`docs/odor_guc_analizi.md`](docs/odor_guc_analizi.md)) tamam; **O1 ve O2 ön-kayıtlı ve doğrulandı** (O1a, O1b, O2-yakın **BAŞARILI**, iki bağımsız popülasyonda; ayrıntı ve sınırlar [`docs/odor_o1_o2_sonuclari.md`](docs/odor_o1_o2_sonuclari.md): mutlak başarı düşük, referansın yaklaşık yarısı); O3/O4 ön-kayıtlı ([`docs/odor_o3_plani.md`](docs/odor_o3_plani.md), [`docs/odor_o4_plani.md`](docs/odor_o4_plani.md)), doğrulayıcı koşular sürüyor; başarıyı sınırlayan şey değer okuması gürültüsü (K-028) |
| 3 | Açlık/enerji ihtiyaçları, serbest keşif; seçilmiş devre birleştirme; 10–20 bin özel nöron + ablasyon deneyleri | planlı |
| 4 | FlyGym ile 3B beden | planlı |

`make_brain(cfg, ...)` (`src/sinek/brains.py`) sentetik (`MushroomBodyBrain`) ve bağlantı-tabanlı (`ConnectomeBrain`) beyinleri aynı arayüzün
(`step(glom, taste, touch, learn)` → değer, `state_dict`) arkasında verir; dünya, ajan ve deney kodu iki evrede de aynıdır.
Açık kalan: MBON→DAN geri beslemesinin veriden açılması (hata sinyalinin elle yazılı olmaması), tam-CNS'e gömme testi, diğer MB alt ağları ve GPU'ya geçiş hazırlığı.

Büyütme/birleştirme aşaması için hazırlık: [`docs/birlestirme_risk_analizi.md`](docs/birlestirme_risk_analizi.md) (uzman-panel riskleri, yedek planlar, kapılar) ·
kararlar, hata sicili ve değişiklik günlüğü: [`docs/karar_defteri.md`](docs/karar_defteri.md).

## Yapı

```
src/sinek/
  config.py        tüm parametreler
  world.py         toplu 2B dünya
  brain.py         sentetik spiking mantar cismi + öğrenme (Evre 1)
  brain_connectome.py  gerçek bağlantıdan mantar cismi + iki yönlü sınırlı plastisite (Evre 2)
  brains.py        beyin fabrikası
  agent.py         beyin + hareket (şeffaflık notu başlıkta)
  checkpoint.py    bellek kaydet/yükle (iki beyin türü için)
  connectome/      MaleCNS indirme (doğrulamalı), alt ağ çıkarma, model verisi, denetim raporu
  experiments/     protocol.py (eğitim, test, istatistik), evre1.py, evre2.py, evre2b*.py, evre2_posthoc.py, plots.py;
                   dört koku oyunu: odor_pretrain.py, odor_pilot.py, odor_session.py, games_blind_check.py
  games/           dört koku oyunu: sonlu destekli koku alanları, GameWorld, referans karşılaştırıcı, protokol (docs/dort_koku_oyunu_plani.md)
data/              çıkarılan mantar cismi alt ağı (processed/), ham veri indirilir (raw/, gitignore)
tests/             birim ve davranış testleri
docs/              proje raporu, plan, sonuçlar, veri denetimi
```
