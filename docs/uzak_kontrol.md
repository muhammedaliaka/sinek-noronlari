# Uzak kontrol: arkadaşın (GPU'lu) bilgisayarında sunucu + canlı panel + akıllı kuyruk

Karar: K-059. Kod: `src/sinek/ops/`. Sınama: `tests/test_ops.py` (15 test). **Bu bir altyapıdır; bilimsel kanıt üretmez.**

## 1. Ne yapar (yalnız gerçek veri; sahte yüzde/çizim yok)
* **Makine durumu:** CPU çekirdeği/yük, RAM, boş disk, GPU adı/belleği/kullanımı (`nvidia-smi` varsa), kod sürümü (commit), PyTorch sürümü.
* **Şu an çalışan / sıra / önerilen 5 test:** her iş gerçek bir süreçtir; ilerleme çubuğu gerçek dosya sayımından gelir (O5c için ön-eğitim dosyaları, kol×parça kontrol noktaları, sonuç dosyaları). İlerlemesi ölçülemeyen işte “ölçülemiyor, yalnız süre” yazar.
* **Akıllı öneri:** bitmiş ya da kuyruktaki işler çıkarılır; ön koşulu eksik olanlar sona atılır; her satırın gerekçesi yazılıdır. “Sırayı otomatik çalıştır” açıksa sıradaki iş bitince sonraki kendiliğinden başlar. İşler istenen sırada ↑/↓ ile taşınır.
* **Canlı oyun izleme:** gerçek bir `Creature` seçilen oyunda koşar; arena başına konum, yön, iz, kaynaklar (+ ödül / − ısı tuzağı / 0 decoy; koku ve görsel desen etiketi), sol-sağ anten değeri, ilk temas ve bölüm sonu tablosu (hedef/diğer/yok, net tercih, öğrenilen ağırlık değişimi). Hız ayarlanır, duraklatılır. Yalnız geliştirme tohumları (100–149, R-2); **kanıt değildir**.
* **Sonuç dosyaları:** `results/` ve `docs/` salt-okunur gezilir.
* **Dayanıklılık:** durum `results/ops/state.json`’da; sunucu yeniden başlarsa çalışan süreçlere yeniden bağlanır; ölen işi, `devam edebilir` ise (O5c gibi: kol×parça kontrol noktası) AYNI hesapla yeniden başlatır (≤3 deneme), değilse “kesildi” der ve elle yeniden sıraya alınır.

## 2. Arkadaşın yapacağı (≈10 dk)
1. Python ≥3.10, git. NVIDIA sürücüsü yüklüyse CUDA’lı PyTorch’u <https://pytorch.org/get-started/locally/> adresindeki komutla kurun (CPU sürümü de çalışır).
2. `git clone <depo>` → `git checkout ccr-2e9cee22-nxwnkt` → `pip install -e .` (Windows’ta doğrulayıcı kuyruğu `bash` ister: **WSL2** önerilir; CUDA WSL2’de de çalışır).
3. `scripts/ops_baslat.sh` (Windows: `scripts\ops_baslat.bat`). Ekranda `http://127.0.0.1:8765/?token=…` çıkar; tarayıcıda açın (jeton çereze alınır, adresten silinir). Jeton `~/.sinek_ops_token` dosyasındadır (yalnız sahibi okur).
4. Panelden “Birim testleri”ni ve “Hızlı demo popülasyonu”nu çalıştırın → kurulum sağlam mı görünür; sonra canlı izlemeyi deneyin.
5. Bilgisayar uykuya geçmesin (kapak/güç ayarı). Kapanırsa sunucuyu yeniden başlatmak yeter: işler kaldığı yerden sürer.

## 3. Benim (uzaktaki ajanın) bağlanma yolları — dürüst durum
Bulut oturumumdan arkadaşın bilgisayarına doğrudan ağ yolu yoktur; üç yol var. **Hiçbirini bu ortamdan uçtan uca sınayamadım** (arkadaşın makinesi yok; çıkış ağı kısıtlı). Yerel sınama: sunucu, canlı izleme, kuyruk ve git yayını (yerel bare depoyla) `tests/test_ops.py` ile sınandı.
| yol | nasıl | gereken | not |
|---|---|---|---|
| **A. Git yayını** (önerilen başlangıç) | sunucu `--relay origin:ops-relay` ile açılır; `ops-relay` dalına imzalı komut yazarım, makine dakikada bir okur, durumu/raporları aynı dala yazar | arkadaşın makinesinde depoya **yazma yetkisi** olan git girişi (ör. kişisel erişim jetonu) | bağlantı kabul etmek gerekmez; ≤1 dk gecikme; yalnız metin raporu iletilir |
| **B. Tünel** | `cloudflared tunnel --url http://127.0.0.1:8765` (ya da `ssh -R`, ngrok) verdiği https adresini bana iletirsiniz; `python3 -I -m sinek.ops.client http --url … --token … summary` | tünel aracı | adres dışarı açılır: jeton uzun/gizli kalmalı; bu ortamın çıkış ağı bu adrese izin vermeyebilir [denenmedi] |
| **C. Claude Remote Control** | arkadaşın bilgisayarında kullanıcının kendi hesabıyla `claude remote-control` (depo klasöründe) | kullanıcı hesabı | oturuma o klasör bağlanır (kullanıcı onaylar); bu araç yalnız KULLANICININ kendi bilgisayarları içindir |
Komutlar yalnız `src/sinek/ops/registry.py`’deki işleri başlatabilir (keyfi komut yok).

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
