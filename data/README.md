# Veri

Bu klasördeki gerçek bağlantı verisi **MaleCNS v1.0** erkek *Drosophila* sinir sistemi bağlantı haritasından (connectome) türetilmiştir.

- **Kaynak:** https://male-cns.janelia.org/ — FlyEM (HHMI Janelia), Cambridge Zoology, MRC LMB ve Google Research işbirliği
- **Sürüm:** `male-cns:v1.0` (yayın 2026-06-08)
- **Lisans:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) — **atıf zorunludur**
- **Makale:** https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6 (Cell, 2026); ön baskı doi:10.1101/2025.10.09.680999
- Yazar listesi ve tam atıf biçimi için makale sayfasına bakın. Bu depoyu ya da türev verisini kullanan çalışmalar bu makaleye atıf vermelidir.

## Klasörler

| Yol | İçerik | Git'te |
|---|---|---|
| `data/raw/malecns_v1.0/` | Ham dosyalar (~1.1 GB): açıklamalar, nörotransmitter tahminleri, bağlantı ağırlıkları | hayır (`.gitignore`) |
| `data/processed/malecns_v1.0_R/` | Türev: sağ yarımküre mantar cismi alt ağı (~2 MB): `neurons.feather`, `edges.feather`, `meta.json` | **evet** (CC BY türevi) |

## Yeniden üretme

```bash
python -m sinek.connectome.fetch                      # ham dosyaları indirir; boyut + md5 doğrulanır
python -m sinek.connectome.malecns                    # alt ağı çıkarır -> data/processed/malecns_v1.0_R
```

Ham dosyaların md5 değerleri `src/sinek/connectome/sources.py` içinde sabittir; indirilen dosya
bu değerlerle uyuşmazsa hata verilir (sessizce başka sürüm kullanılmaz). Çıkarım deterministiktir:
aynı ham dosyalarla `neurons.feather` / `edges.feather` birebir aynı çıkar.

`meta.json`, çıkarım ayarlarını (taraf, `min_syn`), kaynak sürümünü, ham dosya md5'lerini ve
popülasyon sayılarını kaydeder.

## Alt ağ ne içerir?

Seçim kuralları `src/sinek/connectome/malecns.py` başındaki belge dizisinde ve `docs/evre2_*.md`
içinde ayrıntılıdır. Özet (sağ yarımküre):

| Popülasyon | Nöron | Nasıl seçildi |
|---|---:|---|
| PN (projeksiyon nöronları) | 123 | tip adı "PN" ile biter, sağ KC'lere ≥ 20 sinaps |
| KC (Kenyon hücreleri) | 2045 | sınıf `Kenyon_Cell`, hücre gövdesi sağda |
| APL | 1 | tip `APL`, KC sinapslarının ≥ %50'si sağ KC'lerle |
| DPM | 1 | tip `DPM` (Evre 2 simülasyonunda kullanılmaz) |
| MBON | 48 | tip `MBON*`, KC girdisinin ≥ %50'si sağ KC'lerden (bağlantıya göre) |
| DAN | 161 | tip `PAM*` / `PPL1*`, çıktısının ≥ %50'si sağ KC + MBON'lara |

Nörotransmitter değerleri veri kümesinin **sınıflandırıcı tahminleridir**, ölçüm değildir
(ör. DPM için "dopamin" tahmini biyolojik olarak yanlıştır; DPM modelde kullanılmaz).
