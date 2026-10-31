# Uzak kontrol: arkadaşın (GPU'lu) bilgisayarında sunucu + canlı panel + akıllı kuyruk

Karar: K-059. Kod: `src/sinek/ops/`. Sınama: `tests/test_ops.py` (16 test). **Bu bir altyapıdır; bilimsel kanıt üretmez.**

## 1. Ne yapar (yalnız gerçek veri; sahte yüzde/çizim yok)
* **Makine durumu:** CPU çekirdeği/yük, RAM, boş disk, GPU adı/belleği/kullanımı (`nvidia-smi` varsa), kod sürümü (commit), PyTorch sürümü.
* **Şu an çalışan / sıra / önerilen 5 test:** her iş gerçek bir süreçtir; ilerleme çubuğu gerçek dosya sayımından gelir (O5c için ön-eğitim dosyaları, kol×parça kontrol noktaları, sonuç dosyaları). İlerlemesi ölçülemeyen işte “ölçülemiyor, yalnız süre” yazar.
* **Akıllı öneri:** bitmiş ya da kuyruktaki işler çıkarılır; ön koşulu eksik olanlar sona atılır; her satırın gerekçesi yazılıdır. “Sırayı otomatik çalıştır” açıksa sıradaki iş bitince sonraki kendiliğinden başlar. İşler istenen sırada ↑/↓ ile taşınır.
* **Canlı oyun izleme:** gerçek bir `Creature` seçilen oyunda koşar; arena başına konum, yön, iz, kaynaklar (+ ödül / − ısı tuzağı / 0 decoy; koku ve görsel desen etiketi), sol-sağ anten değeri, ilk temas ve bölüm sonu tablosu (hedef/diğer/yok, net tercih, öğrenilen ağırlık değişimi). Hız ayarlanır, duraklatılır. Yalnız geliştirme tohumları (100–149, R-2); **kanıt değildir**.
* **Sonuç dosyaları:** `results/` ve `docs/` salt-okunur gezilir.
* **Dayanıklılık:** durum `results/ops/state.json`’da; sunucu yeniden başlarsa çalışan süreçlere yeniden bağlanır; ölen işi, `devam edebilir` ise (O5c gibi: kol×parça kontrol noktası) AYNI hesapla yeniden başlatır (≤3 deneme), değilse “kesildi” der ve elle yeniden sıraya alınır.

## 2. Seçilen teknik ve arkadaşın yapacağı (≈10 dk)
**Teknik (K-060): git yayını.** Sunucu arkadaşın makinesinde yerel çalışır; dışarıya hiçbir port açılmaz. Makine GitHub'daki `ops-relay` dalına kendi durumunu/raporlarını/tekrarlarını yazar, aynı daldan imzalı komutları okur. Ben (uzaktaki ajan) de aynı daldan okur/yazarım. Neden bu: (1) bana açık olan tek yol GitHub; (2) güvenlik duvarı/NAT/CGNAT/uyku-uyanma sorunu yok, çünkü bağlantı hep arkadaşın makinesinden DIŞARI doğru; (3) imza ile korunur, TLS gerekmez; (4) makine kapansa komutlar dalda bekler, açılınca uygulanır; (5) tünel/VPN kurulumu ve hesap paylaşımı gerekmez. Bedeli: gecikme (komut ≈15 sn–1 dk) ve canlı izlemenin uzaktan **kare kare akmaması** — onun yerine canlı izleme her bölümde **tekrar dosyası** (gerçek karelerin seyreltilmiş kaydı, 40 KB/2 bölüm) olarak dala konur; arayüzdeki “Kayıtlı tekrarlar”dan oynatılır. Gerçek zamanlı canlı izleme arkadaşın kendi tarayıcısındaki yerel panelde vardır.
1. Python ≥3.10, git. NVIDIA sürücüsü varsa CUDA'lı PyTorch'u <https://pytorch.org/get-started/locally/> komutuyla kurun (CPU sürümü de çalışır).
2. `git clone <depo>` → `git checkout ccr-2e9cee22-nxwnkt` → `pip install -e .` (Windows'ta doğrulayıcı kuyruğu `bash` ister: **WSL2** önerilir).
3. Depoya **yazma yetkisi** verin (GitHub kişisel erişim jetonu ya da `gh auth login`).
4. `python3 -I -m sinek.ops.setup --autostart` — her şeyi denetler (torch/CUDA, git yayını gerçek bir deneme turuyla, jeton) ve eksikse ne yapılacağını söyler; Linux'ta açılışta otomatik başlatma kurar (Windows/mac için tek satırlık komut yazar). `--rotate-token` jetonu yeniler.
5. `scripts/ops_baslat.sh --relay origin:ops-relay` (autostart kurduysanız gerekmez). Panel: `http://127.0.0.1:8765/?token=…`.
6. Jetonu bana verin (komut imzası için). Sohbete yapıştırdıysanız iş bitince `--rotate-token`.
7. Bilgisayar uykuya geçmesin. Kapanırsa sunucuyu yeniden başlatmak yeter: işler kaldığı yerden sürer.

## 3. Benim (uzaktaki ajanın) kullanımı
* Durum + raporlar + tekrarlar: `python3 -I -m sinek.ops.client relay --token T status`
* Test başlatma: `… relay --token T send enqueue o5c_pretrain_validator --confirm` · `send enqueue gv0 --param n=8` · `send auto on` · `send cancel JOB` · `send update` (kodu çek).
* Komutun uygulandığı `status.json` içindeki `acked` bölümünden görülür (sonuç metniyle). Geçmiş sıkıştırması sırasında okunmamış bir komut kaybolabilir; `acked`'te görünmeyen komut yeniden gönderilir.
* Dal şişmesin diye: değişmeyen durumda commit yok (nabız 15 dk), ucuz yoklama (`git ls-remote`) 15 sn, 400 itmede dal tek commit'e sıkıştırılır, en fazla 8 küçük (≤600 KB) tekrar tutulur; ağır dosya (npz) asla itilmez.
* **Yedek yollar** (gerekirse): HTTP + tünel (`cloudflared tunnel --url http://127.0.0.1:8765`; adresi iletirsiniz; `client http …`); kullanıcının kendi hesabıyla `claude remote-control`. İkisi de **denenmedi**; git yayını yerelde (bare depoyla) uçtan uca sınandı, gerçek GitHub üzerinde arkadaşın makinesiyle **sınanmadı**.
Komutlar yalnız `src/sinek/ops/registry.py`'deki işleri başlatabilir (keyfi komut yok).

## 4. Güvenlik modeli
* Jeton olmadan hiçbir uç nokta açılmaz (ana sayfa dahil). Jeton ≥128 bit rastgele, dosyası `0600`. Yanlış jetonda 0,5 sn gecikme, IP başına dakikada 10 hatadan sonra kilit (429).
* Varsayılan dinleme `127.0.0.1`. `--host 0.0.0.0` ağdan erişim açar ama **TLS yoktur**: yalnız güvenilir ağ/VPN ya da şifreli tünel (B) ile kullanın; jeton düz HTTP’de dinlenebilir.
* Keyfi komut/kabuk uç noktası YOKTUR. İşler yalnız kayıt defterindeki tanımlardan, tür/aralık denetimli parametrelerle (`pre` parametresi yalnız `results/` altındaki var olan `.npz`; geliştirme tohumu 100–149) başlar. Süreçler kabuk yorumlamadan (argv listesi) çalıştırılır.
* Dosya okuma yalnız `results/` ve `docs/`, salt-okunur, 300 KB sınırı, ad içinde `token` geçenler gizli; `..`/mutlak yol reddedilir.
* POST istekleri başka kaynaktan (Origin) gelirse reddedilir; çerez `HttpOnly; SameSite=Strict`; CSP açık.
* **Kod güncelleme** (`/api/update` = `git pull --ff-only`) jetonlu kişiye, depoya yazabilen birinin koyduğu kodu çalıştırtma gücü verir. Jeton ve depo yazma yetkisi aynı güven alanında tutulmalıdır.
* Git yayını: komutlar HMAC-SHA256 imzalıdır (jetonla); imzasız/yanlış/3 günden eski/tekrar eden komut atılır. Dalı yazabilen kişi jetonsuz iş başlatamaz.
* Doğrulayıcı koşular (ön-kayıtlı): ön-kayıt belgesi git’te commit edilmemişse panel reddeder (R-1); başlatmak için ayrıca onay kutusu gerekir (“ölçütler koşudan sonra değişmez”).

## 5. GPU hakkında dürüst durum (K-059)
* GPU’yu **kullanabilenler:** canlı izleme (`cihaz: cuda`) ve `odor_pretrain --device` (demo popülasyonu). Altın koşu/verim eğrisi araçlarında zaten `--device` var (`docs/gpu_devri.md`).
* **Ön-kayıtlı doğrulayıcılar (O5c…) CPU’da koşar ve öyle kalır:** rastgele sayı akışları cihaza göre farklıdır; GPU’ya taşımak ön-kayıtlı ortak-rastgele-sayı eşlemesini ve önceki sonuçlarla karşılaştırılabilirliği bozar. GPU’da doğrulayıcı koşmak ayrı bir ön-kayıt (cihaz değişikliği notu + altın koşu eşdeğerlik denetimi) gerektirir. Bu yüzden panel O5c için “GPU: yok” yazar.
* Arkadaşın makinesinden beklenen kazanç şimdilik: daha çok çekirdek (paralel işçi sayısı panelden), 7/24 kalıcılık ve canlı izleme; GPU ivmesi ancak GPU’lu yeni araçlar yazılınca.

## 6. Bilinen sınırlar
* Canlı izleme tek oturumdur (bir kez bir oyun); bölümleri CPU’da yavaşsa kare hızı düşer (hız çubuğu işe yaramaz, yalnız hızlandırır).
* O6b/O6c koluyla ilk canlı başlatmada görsel kalibrasyon (`neutral_scale`) bir dakika sürebilir (“kuruluyor” görünür).
* “Gerileme denetimi (T=2,5)” ve “O6b öğrenme zamanı/işareti denetimi” kayıt defterinde **planlı/engelli** görünür: betikleri henüz yok; yazıldıkça kayda eklenir.
* Windows’ta `run_o5c_validators.sh` için bash gerekir (WSL2/Git Bash); yerel Windows’ta denenmedi.
* Arayüz tarayıcıda (Chromium, masaüstü ve telefon genişliği) bu ortamda görsel olarak denetlendi; başka tarayıcılar denenmedi.
