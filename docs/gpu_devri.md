# GPU devir notu (bu sohbet kapanınca yeni ortamın ilk okuyacağı belge)

Hedef donanım: RTX 3070 Ti Mobile (8 GB VRAM) + 32 GB RAM. Kullanıcı "GPU kullanılacak" dediğinde bu sohbet kapanır; bağlam **yalnız depoda** yaşar. Önce şunları oku, sırayla: `CLAUDE.md` → `docs/karar_defteri.md` ("Değişmez kurallar", "Hata sicili", son kayıtlar) → bu belge → `docs/birlestirme_risk_analizi.md` (§5 kapılar, §9 devir listesi).
Dil: Türkçe, dürüst raporlama (başarısızlıklar da yazılır). Sinek beyni esinli "dijital canlı"; ilk hedef oyunlarda en zeki / en hızlı öğrenen beyin; nöron sayısı sınırı yok ama **nöron sayısı başarı ölçütü değildir**.

## 1. Şu an nerede (2026-10-28)
| konu | durum | belge |
|---|---|---|
| Evre 2b (gerçek MaleCNS mantar cismi, koku/ödül öğrenme) | 7/7 ve 7/7 ölçüt geçti (iki bağımsız tohum) | `docs/evre2b_sonuclar.md` |
| Dört koku oyunu O1a/O1b/O2-yakın | **BAŞARILI** (iki popülasyon); mutlak başarı düşük (frozen ≈0,47–0,72; referans 0,83–0,98) | `docs/odor_o1_o2_sonuclari.md` |
| O3 (yalnız temas), O4a/O4c (yanıltıcı koku, sönüm) | doğrulayıcılar koşuyor/ koştu — sonuç belgesi için `docs/` altında `odor_o3_o4_sonuclari.md` varsa oraya, yoksa `results/odor_val/*/summary.md` ve karar defterine bak | `docs/odor_o3_plani.md`, `docs/odor_o4_plani.md` |
| Başarıyı sınırlayan şey | **değer okumasının Poisson gürültüsü** (K→∞ gürültüsüz tablo 0,818 vs 0,510; K=4 yalnız 0,552) — K-028 | `docs/evre3_dan_plani.md` §6 |
| DAN devresi veriden | kapı 3.3 **karşılanmadı**: V1 etkisiz, V2/V3 ya kararsız (g ≥ 0,5) ya sönümü bozuyor (düşük g) | `docs/evre3_dan_plani.md` §5, `docs/dan_girdi_analizi.md` |
| Dış kaynaklar | BANC rakamları kısmen, lisanslar tablo halinde (FlyWire **CC BY-NC**) | `docs/dis_kaynak_dogrulamalari.md` |

## 2. Yeni makinede ilk komutlar (hepsi çalıştırılıp sonucu kaydedilecek)
Durum etiketi: **[denendi: Linux/CPU]** bu ortamda çalıştırıldı; **[denenmedi]** Windows/CUDA'da hiç çalıştırılmadı — çıktısı bu belgeye eklenecek.
1. `py -3.11 -m venv .venv; .venv\Scripts\activate; pip install -e ".[dev]"` — [denenmedi: Windows]. CUDA'lı PyTorch için <https://pytorch.org/get-started/locally/> komutu (CPU wheel kurulmuş olabilir: `python -c "import torch;print(torch.cuda.is_available())"` `True` vermeli) — [denenmedi].
2. `python -m pytest -q tests` — [denendi: Linux/CPU]; Windows'ta [denenmedi]. (Linux'ta `python3 -I -m pytest -q tests`.)
3. `python -m sinek.connectome.fetch` yalnız ham veri gerekiyorsa (~1 GB, md5 doğrular); çıkarılan alt ağ depoda hazır (`data/processed/`) — [denendi: Linux].
4. **Altın koşu (CPU)**: `python -m sinek.experiments.altin_kosu --device cpu --check docs/altin_kosu_referans.json` → "ALTIN KOŞU: GEÇTİ" — [denendi: Linux/CPU, ~25 sn]. Farklı torch sürümünde referans yeniden üretilir (`--write-ref`), sürüm farkı not edilir.
5. **Altın koşu (CUDA)**: `... --device cuda --check docs/altin_kosu_referans.json` — [denenmedi]. Beklenti: aynı cihazda tekrar bit-bit aynı; CPU↔GPU **istatistiksel** tolerans (K-030). KALDI çıkarsa tolerans gevşetilmez; neden araştırılır, hata sicilinde kayıt açılır.
6. **Verim eğrisi**: `... olcek_egrisi --device cuda --batches 64,256,1024,4096 --out results/olcek/cuda.md` — [denenmedi]. 8 GB VRAM sınırı bu ölçümden çıkar. Sonuç tablosu `docs/`a özet olarak geçirilir (`results/` git'te yok). `--device cpu` karşılaştırması da alınır.

## 3. GPU aşamasının öncelik sırası (dürüst gerekçe: K-028)
1. **Ölçek/gürültü ekseni**: `python -m sinek.experiments.scale_dev --pre results/odor_games/pre_s100.npz --game O1a --seed 110 --ks 8,16,32,64 --oracle` (ön-eğitim dosyası `results/` altındadır, git'te yok; yoksa `odor_pretrain` ile yeniden üretilir). Soru: K ile frozen p_hit 0,51 → 0,818 (K→∞) doğru yükseliyor mu, ve ne kadar K gerek? Dev tohumları 100–149, doğrulayıcı tohumları ≥200 **kullanılamaz** (R-2).
2. **τ_valence** (okuma entegrasyon süresi) taraması: K=1'de 0,3 → 0,448 (kötüleşti); 0,6 ve 1,2 koşuları kayıp (container yeniden başlaması), yeniden koşulacak.
3. **Paylaşılan ağırlıklı öğrenen topluluk**: `EnsembleBrain` kopyaları dondurulmuş okuma içindir. Plastik topluluk için tek W + K gürültü örneği tasarımı gerekir; sıfır-etki sınaması: K=1 birebir aynı.
4. **DAN sönüm yolu**: düşük kazançlı MBON→DAN plato yükseltiyor ama sönümü bozuyor; PPL1/aracı nöron yolu (`dan_girdi_analizi` bölüm D). Kapı: kararlılık (sahte öğretmen < 0,05, DAN tepe < 3×V0) **sönümden önce**.
5. Doğrulayıcıya girecek her yeni kural/ölçüt: önce ön-kayıt belgesi commit (kural 2), sıfır-etki + bilinen-etki benzetimi (kural 3, `python -m sinek.experiments.power2b`).

## 4. Bilinen tuzaklar
* Konteyner/işçi süreci yeniden başlayınca arka plan işleri ölür (bu oturumda ≥5 kez, ≈15–50 dk aralıkla; disk korunur): `scripts/run_validators.sh` ve O1–O4 doğrulayıcılarının kol-kol kontrol noktaları (K-029) bunun içindir. **Evre 1/2b eğitim hattında (`evre1.run`) bölüm-bölüm kontrol noktası yok**; yeni uzun koşular kontrol noktalı yazılmalı.
* `pkill -f <desen>` kendi kabuğunu öldürebilir; PID ile öldür.
* CUDA'da `torch.Generator(device=...)` farklı sayı üretir: CPU sonuçlarıyla nokta nokta eşleşme beklenmez (K-030).
* Rakamlar kural 4 etiketleriyle: [doğrulandı]/[doğrulanmadı]. FlyWire verisi proje lisansı belirlenmeden depoya alınmaz (K-031).
* Kayıp/yarım sonuç varsa karar defterine ve ilgili sonuç belgesine **olduğu gibi** yazılır; ölçütler koşudan sonra değişmez.

## 5. İş bittiğinde
`docs/arkadasa_ozet.md` içine bir arkadaşa verilecek **tek, basit paragraf** yazılır (kullanıcı isteği). Şu anki içerik taslaktır; tüm oyun doğrulayıcıları ve E1 karıştırma kontrolü bittiğinde güncellenir.
