# Evre 2 — veri denetimi (MaleCNS v1.0, sağ yarımküre mantar cismi)

Kaynak: MaleCNS connectome (erkek Drosophila beyin + ventral sinir kordonu), `male-cns:v1.0 (yayın: 2026-06-08)`, lisans CC-BY (atıf zorunlu). FlyEM (HHMI Janelia), Cambridge Zoology, MRC LMB ve Google Research işbirliği; CC BY 4.0. Makale: https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6 (Cell, 2026); ön baskı: doi:10.1101/2025.10.09.680999. Yazar listesi için makale sayfasına bakın; veriyi kullanan her yayın bu çalışmaya atıf vermelidir.

Bu rapor `python -m sinek.connectome.audit` ile üretilir; sayılar çıkarılan alt ağdan hesaplanır.

## 1. Popülasyonlar

| popülasyon | nöron | tip | soma R | soma L |
|---|---|---|---|---|
| PN | 123 | 60 | 118 | 5 |
| KC | 2045 | 14 | 2045 | 0 |
| APL | 1 | 1 | 1 | 0 |
| DPM | 1 | 1 | 1 | 0 |
| MBON | 48 | 36 | 40 | 8 |
| DAN | 161 | 23 | 132 | 29 |

Kenar: 468206, toplam sinaps: 1485307. Soma tarafı L olan nöronlar bağlantıya göre sağ yarımküreye atanmıştır (aşağıda ayrıntı).

## 2. Nörotransmitter (sınıflandırıcı tahmini; ölçüm değil)

| popülasyon | acetylcholine | dopamine | gaba | glutamate |
|---|---|---|---|---|
| PN | 120 | 0 | 3 | 0 |
| KC | 2045 | 0 | 0 | 0 |
| APL | 0 | 0 | 1 | 0 |
| DPM | 0 | 1 | 0 | 0 |
| MBON | 25 | 0 | 11 | 12 |
| DAN | 0 | 161 | 0 | 0 |

Beklenti: KC = asetilkolin, APL = GABA, DAN = dopamin, MBON karışık. DPM için gerçekte serotonin / GABA beklenir; 'dopamin' tahmini yanlıştır ve DPM bu nedenle simülasyona alınmaz. 3 PN'nin GABA tahmini (bazı PN'lerin GABAerjik olduğu bilinir; çelişmez) işaret olarak simülasyonda korunur, ama bu tahmin doğrulanmamıştır.

## 3. PN → KC bağlantısı

- KC başına PN (benzersiz): ortalama 5.33, medyan 5, yüzdelikler 5/95: 0/9
- Bağlantı başına ortalama sinaps: 17.8 (maks 89)
- PN girdisi olmayan KC: 141/2045 — tipleri: {'KCg-d': 90, 'KCab-p': 48, "KCa'b'-ap1": 1, 'KCab-s': 1, 'KCg-s1': 1} (görsel girdili KC alt tipleri beklenir)
- Glomerül (PN grubu) sayısı: 58; glomerül başına PN: {1: 27, 2: 12, 3: 10, 4: 6, 5: 1, 6: 1, 7: 1} (PN sayısı: glomerül sayısı)

## 4. Yarımküre ataması: soma tarafı ↔ bağlantı

MBON ve DAN'larda soma tarafı ile bağlantıya dayalı atama farklıdır; bağlantı esas alınmıştır:

| tip | soma L |
|---|---|
| DAN PAM03 | 2 |
| DAN PAM09 | 3 |
| DAN PAM10 | 5 |
| DAN PAM11 | 7 |
| DAN PAM12 | 1 |
| DAN PAM13 | 4 |
| DAN PAM14 | 1 |
| DAN PPL101 | 1 |
| DAN PPL102 | 1 |
| DAN PPL103 | 1 |
| DAN PPL106 | 1 |
| DAN PPL107 | 1 |
| DAN PPL108 | 1 |
| MBON MBON03 | 1 |
| MBON MBON04 | 1 |
| MBON MBON05 | 1 |
| MBON MBON06 | 1 |
| MBON MBON25 | 1 |
| MBON MBON25-like | 2 |
| MBON MBON34 | 1 |
| PN VL1_ilPN | 1 |
| PN VP1d_il2PN | 1 |
| PN VP1m+VP5_ilPN | 1 |
| PN VP3+VP1l_ivPN | 1 |
| PN V_ilPN | 1 |

### Eşik duyarlılığı (`min_syn`)

| min_syn | PN | KC | APL | DPM | MBON | DAN |
|---|---:|---:|---:|---:|---:|---:|
| 10 | 124 | 2045 | 1 | 1 | 48 | 161 |
| 20 | 123 | 2045 | 1 | 1 | 48 | 161 |
| 50 | 119 | 2045 | 1 | 1 | 47 | 159 |

## 5. Bölme eşlemesi: MBON tipi ↔ DAN sınıfı

Her MBON'un aldığı DAN sinapslarının PPL1 payı. `u` = PPL1 payı − PAM payı (u→+1: PPL1 bölmesi, **yaklaş** sınıfı; u→−1: PAM bölmesi, **kaçın** sınıfı). Bu eşleme bir **model varsayımıdır**.

| MBON tipi | nöron | nt | u | sınıf |
|---|---|---|---|---|
| MBON01 | 1 | glutamate | -0.99 | kaçın |
| MBON03 | 1 | glutamate | -0.99 | kaçın |
| MBON04 | 1 | glutamate | -0.46 | karışık |
| MBON05 | 1 | glutamate | -0.95 | kaçın |
| MBON06 | 1 | glutamate | -0.99 | kaçın |
| MBON07 | 2 | glutamate | -0.99 | kaçın |
| MBON09 | 2 | gaba | -0.98 | kaçın |
| MBON10 | 5 | gaba | -0.6 | kaçın |
| MBON11 | 1 | gaba | 0.86 | yaklaş |
| MBON12 | 2 | acetylcholine | 0.92 | yaklaş |
| MBON13 | 1 | acetylcholine | 1 | yaklaş |
| MBON14 | 2 | acetylcholine | 1 | yaklaş |
| MBON15 | 2 | acetylcholine | 0.92 | yaklaş |
| MBON15-like | 2 | acetylcholine | 0.93 | yaklaş |
| MBON16 | 1 | acetylcholine | 1 | yaklaş |
| MBON17 | 1 | acetylcholine | 1 | yaklaş |
| MBON17-like | 1 | acetylcholine | 1 | yaklaş |
| MBON18 | 1 | acetylcholine | 1 | yaklaş |
| MBON19 | 2 | acetylcholine | 1 | yaklaş |
| MBON20 | 1 | gaba | 0.89 | yaklaş |
| MBON21 | 1 | acetylcholine | -0.97 | kaçın |
| MBON22 | 1 | acetylcholine | -1 | kaçın |
| MBON23 | 1 | acetylcholine | 0.94 | yaklaş |
| MBON24 | 1 | acetylcholine | -0.98 | kaçın |
| MBON25 | 1 | glutamate | 1 | yaklaş |
| MBON25-like | 2 | glutamate | 1 | yaklaş |
| MBON26 | 1 | acetylcholine | -0.87 | kaçın |
| MBON27 | 1 | acetylcholine | -0.9 | kaçın |
| MBON28 | 1 | acetylcholine | 1 | yaklaş |
| MBON29 | 1 | acetylcholine | -0.91 | kaçın |
| MBON30 | 1 | glutamate | 0.65 | yaklaş |
| MBON31 | 1 | gaba | 0.89 | yaklaş |
| MBON32 | 1 | gaba | 0.98 | yaklaş |
| MBON33 | 1 | acetylcholine | 0.42 | karışık |
| MBON34 | 1 | glutamate | 0.5 | karışık |
| MBON35 | 1 | acetylcholine | 0.97 | yaklaş |

Keskin eşleme (|u| > 0.8): 41/48 MBON. Sınıf sayıları: yaklaş 28, kaçın 20.

Sınıf × nörotransmitter (MBON sayısı):

| sınıf | acetylcholine | gaba | glutamate |
|---|---|---|---|
| kaçın (PAM) | 6 | 7 | 7 |
| yaklaş (PPL1) | 19 | 4 | 5 |

Nörotransmitter ile sınıf tam örtüşmez (ör. PAM bölmelerinde asetilkolinli ve GABA'lı MBON'lar da vardır); bu yüzden sınıf, nörotransmitter işaretinden değil DAN bölme payından türetilmiştir ve sonuçlar bu varsayıma bağlıdır (karıştırma kontrolü: `docs/evre2_sonuclar.md`).

## 6. Kapsam dışı bırakılanlar (bilinçli)

- KC → KC (586 648 sinaps), MBON → MBON, MBON → DAN, DAN → KC: simülasyonda yok (DAN → KC bölme bilgisi taşımaz; bölme DAN → MBON'dan çıkarılır).
- PPL2 / PPM3 gibi diğer dopamin nöronları, MB-C1 gibi MB ilişkili diğer tipler, DPM.
- Açıklanmamış nöron parçaları (KC girdisinin ~%4'ü).
