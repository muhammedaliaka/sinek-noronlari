# Dış kaynak doğrulamaları (V-01 BANC rakamları, V-02 lisans tablosu) — 2026-10-28

Yöntem: web araması + sayfa alıntısı. Etiketler CLAUDE.md kural 4'e göredir. Tam metin/PDF okunamadığı yerlerde açıkça "doğrulanmadı" yazılmıştır. **Bu belge hukuki görüş değildir**; ticari ya da dağıtım amaçlı kullanımdan önce resmî lisans dosyaları okunmalıdır.

## V-01 — BANC rakamları

| iddia | durum | kaynak / not |
|---|---|---|
| BANC Nature'da yayımlandı ("Distributed control circuits across a brain-and-cord connectome", 8 Haz 2026) | [doğrulandı: arama özeti; DOI 10.1038/s41586-026-10735-w] | tam metin açılmadı |
| BANC ≈ **158 262 nöron** / ≈160 bin | [doğrulandı: iki bağımsız haber/blog özeti] | yalnız ikincil kaynak |
| BANC ≈ **188 000 nöron, 199 milyon sinaps** (kullanıcı raporundaki rakam) | **[doğrulanmadı]** | aranan kaynaklarda bulunamadı; 188 000 sayısı muhtemelen farklı bir sayım ölçütüdür (parça dahil vb.) — kanıt yok |
| BANC "10⁸ sinaps" | [doğrulandı: yalnız anlam] | Nature girişi 10⁸'i **bütün sinek** için anıyor (bir haber metninde üs eksikti); BANC veri kümesi için kesin sinaps sayısı bulunamadı. Bir haberde ">3 milyon sinaptik bağlantı" geçiyor — bu BANC için güvenilmez görünüyor [doğrulanmadı] |
| veri çevrimiçi serbest | [doğrulandı: haber] | lisans türü bulunamadı |

**Sonuç:** karar değişmez (K-… birleştirme kararı nöron sayısına dayanmaz, kural 4). BANC için kesin nöron/sinaps rakamları ve lisans, Nature makalesi/FlyWire Codex indirme sayfasından elle doğrulanana dek "[doğrulanmadı]" kalır. Tuthill laboratuvarı PDF'i 10 MB sınırını aştığı için otomatik okunamadı.

## V-02 — Lisans tablosu

| kaynak | lisans | durum | türev iş için ne anlama gelir |
|---|---|---|---|
| **MaleCNS v1.0** (Janelia/Google) | CC BY | [doğrulandı: Evre 2'de sürüm+md5, `data/README.md`] | ticari dahil kullanım serbest, atıf zorunlu |
| **FlyWire** (yayımlanmış sürümler) | **CC BY-NC 4.0** | [doğrulandı: FlyWire Principles sayfası: "Published versions of FlyWire's data are available under CC BY-NC 4.0 license."] | **ticari kullanım yasak**; üçüncü taraf paketi (flyconn) CC BY 4.0 diyor — resmî kaynakla çelişir, **resmî olan esas alınır**. Hiçbir FlyWire verisi bu depoda yok |
| **BANC** | bulunamadı | [doğrulanmadı] | kullanılmadı; kullanmadan önce Codex indirme sayfasındaki koşul okunacak |
| **FlyGym / NeuroMechFly v2** | PyPI'ye göre **MPL 2.0** (kod); GitHub LICENSE dosyası okunamadı | [kısmen doğrulandı: arama özeti] | MPL 2.0 dosya-düzeyi kopyaleft: değiştirilen MPL dosyaları açık kalmalı; bizim kod ayrı dosyalarda kalırsa bağlanmaz. Henüz kullanılmıyor |
| **Eon Systems** (sinek emülasyonu, Mart 2026) | bulunamadı | [doğrulanmadı] | "GPL" iddiası (proje raporu) **doğrulanamadı**; kamuya açık kod/lisans araması sonuçsuz. Basında yöntem ve bağımsız doğrulama eksikliği eleştirisi var. Kopyalanmayacak (risk analizi R-A5: yalnız yöntem/çıktı karşılaştırması) |

**Önemli:** bu depodaki kod/veri MaleCNS (CC BY) üzerine kurulu; FlyWire'ın NC şartı yalnız FlyWire verisi eklenirse devreye girer. Karar defterine eklendi: FlyWire verisi **proje lisansı belirlenmeden** depoya alınmayacak.
