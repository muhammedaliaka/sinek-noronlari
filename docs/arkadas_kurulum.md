# Arkadaş için kurulum (Windows, adım adım — WSL/Linux GEREKMEZ)

Amaç: bu bilgisayar, arkadaşın (Claude'un) GitHub üzerinden vereceği testleri çalıştırsın ve sonucu geri yazsın. **Sunucu YOKTUR, port açılmaz, tarayıcı gerekmez** (K-063): her şey tek bir konsol penceresinde (“test ekranı”) görünür; uzak bağlantı yalnızca bilgisayarın GitHub'a *dışarı* bağlanmasıyla olur.

## Başlamadan (bir kez)
* Python 3.10+ : <https://www.python.org/downloads/> — kurarken **"Add python.exe to PATH"** kutusunu işaretleyin.
* Git : <https://git-scm.com/download/win>
* Proje sahibi sizi GitHub'da `muhammedaliaka/sinek-n-ronlar-` deposuna **Collaborator (yazma yetkisi)** olarak eklemiş olmalı; e-postadaki daveti kabul edin.
* NVIDIA sürücüsü normal şekilde kuruluysa yeterli (CUDA'yı ilk kurulumda atlayabilirsiniz, aşağıda).

## Adımlar (PowerShell'de; Başlat → "PowerShell")
```
git clone https://github.com/muhammedaliaka/sinek-n-ronlar-.git
cd sinek-n-ronlar-
git checkout ccr-2e9cee22-nxwnkt
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -X utf8 -I -m sinek.ops.setup --autostart
```
* `git clone` sırasında GitHub girişi isteyebilir (tarayıcı açılır): kendi hesabınızla girin.
* Son komut her şeyi denetler. **`[ TAMAM ] git yayını: 'ops-relay' dalına YAZILDI`** satırını görmelisiniz. `[ HATA ]` görürseniz mesajı olduğu gibi kopyalayıp gönderin.
* Aynı ekranda bir **jeton** yazar; `--autostart` test ekranını Windows Görev Zamanlayıcı ile kurar (oturum açılınca pencere kendiliğinden açılır). Hemen açmak için: `schtasks /Run /TN SinekOps` ya da `scripts\ekran_ac.bat --relay origin:ops-relay --auto` dosyasına çift tıklayın.

## Çalıştığını görmek
1. Açılan siyah **“SİNEK TEST EKRANI”** penceresinde üstte makine durumu, ortada çalışan iş, altında **“SIRADAKİ 5 ÖNERİ”** görünür. Pencere açık kalmalı.
2. Tuşlar: **1–5** = o öneriyi sıraya ekle (doğrulayıcılar `y/n` onayı ister) · **a** = otomatik sıra aç/kapat · **g** = canlı oyun (arena ASCII olarak çizilir: `+` ödül, `-` ceza, ok = canlı) · **p** duraklat · **x** durdur · **c** çalışan işi iptal · **q** çık.
3. Önce **1** (birim testleri), sonra “Hızlı demo popülasyonu”nu ekleyin, **a** ile otomatik sırayı açın. İkisi de yeşil bitmeli.
4. GitHub'da depoda **`ops-relay`** adlı yeni bir dal belirir (içinde `status.json`) — bu, uzak bağlantının çalıştığının kanıtıdır.

## Claude'a bağlamak
5. **Jetonu** proje sahibine (Claude'la konuşan kişi) gönderin; o sohbete yazar. Jeton, komutları imzalayan anahtardır: başkasına vermeyin.
6. Bundan sonra Claude testleri sıraya atar; siz yalnızca bilgisayarı **açık ve uykuya geçmeyecek** şekilde bırakırsınız (Ayarlar → Sistem → Güç ve pil → Ekran ve uyku: "Hiçbir zaman", prize takılı).
7. İşler bitince jetonu yenileyin: `.venv\Scripts\python.exe -X utf8 -I -m sinek.ops.setup --rotate-token` ve ekranı yeniden açın (pencereyi kapatıp `schtasks /Run /TN SinekOps`).

## Sonradan (isteğe bağlı) GPU
Canlı izleme ve demo ön-eğitimi ekran kartını kullanabilir; bilimsel doğrulayıcılar bilerek işlemcide (CPU) koşar. GPU'lu PyTorch için <https://pytorch.org/get-started/locally/> sayfasında Windows + Pip + CUDA seçip verdiği `pip` komutunu `.venv\Scripts\python.exe -m` ile çalıştırın. [GPU'lu kurulum Windows'ta denenmedi.]

## Sorun giderme
* `py` bulunamadı → Python'u "Add to PATH" ile yeniden kurun ya da `py` yerine `python` yazın.
* Ekran bozuk karakter gösteriyorsa: pencereyi “Windows Terminal” ile açın ya da pencereyi büyütün (en az 100 sütun). Ekran hiç açılmıyorsa `scripts\ekran_ac.bat --once` komutunun çıktısını gönderin.
* Linux/Mac: aynı adımlar; `py -3` yerine `python3`, `.venv\Scripts\python.exe` yerine `.venv/bin/python`.
