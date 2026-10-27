# Sinek Nöronları — koku/ödül öğrenen dijital canlı

Sinek beyninden esinlenen, **algılayan, hareket eden, deneyimle öğrenen ve öğrendiğini koruyan** sanal bir canlı.
Bu depo uzun vadeli bir projenin **Evre 1** çıktısıdır. Proje bağlamı ve hedefler: [`docs/proje_raporu.md`](docs/proje_raporu.md).

> **Dürüstlük notu:** Evre 1'de gerçek sinek bağlantı verisi (FlyWire / MaleCNS) **henüz kullanılmıyor**.
> Ağ, sineğin mantar cismi (*mushroom body*) mimarisinden esinlenen sentetik bir devredir. Öğrenmenin
> çalıştığını kontrollü deneylerle kanıtlamak için bilinçli olarak küçük ve tam kontrol edilebilir tutuldu.
> Gerçek bağlantı verisi Evre 2'dir. Bu sonuçlar gerçek sinek davranışı hakkında iddia taşımaz.

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

Gerçek koşunun sayıları: [`docs/evre1_sonuclar.md`](docs/evre1_sonuclar.md).

## Yol haritası

| Evre | İçerik | Durum |
|---|---|---|
| 1 | Sentetik mantar cismi devresi, 2B dünya, koku/ödül öğrenme, tersine çevirme, bellek | **bu depo** |
| 2 | Gerçek bağlantı verisi (FlyWire / MaleCNS): lisans ve sürüm doğrulaması, seyrek motor, mantar cismi alt ağı | sırada |
| 3 | Açlık/enerji ihtiyaçları, serbest keşif; seçilmiş devre birleştirme; 10–20 bin özel nöron + ablasyon deneyleri | planlı |
| 4 | FlyGym ile 3B beden | planlı |

Evre 2'de `MushroomBodyBrain` arayüzünün (`step(glom, taste, touch, learn)` → değer, `state_dict`) arkasına
genel seyrek bir motor konacak. Dünya, ajan ve deney kodu değişmeden kalacak şekilde tasarlandı.

## Yapı

```
src/sinek/
  config.py        tüm parametreler
  world.py         toplu 2B dünya
  brain.py         spiking mantar cismi + öğrenme
  agent.py         beyin + hareket (şeffaflık notu başlıkta)
  checkpoint.py    bellek kaydet/yükle
  experiments/     protocol.py (eğitim, test, istatistik), evre1.py (hat), plots.py
tests/             birim ve davranış testleri
docs/              proje raporu, sonuçlar
```
