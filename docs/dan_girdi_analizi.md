# DAN girdi ve MBON→DAN geri bildirim analizi (R-8 veri kontrolü)

Betimsel veri kontrolü (`python3 -I -m sinek.experiments.dan_girdi_analizi`); karar ölçütü değildir. Kaynak: MaleCNS v1.0 (CC BY 4.0). Nörotransmitter işaretleri **tahmindir** [doğrulanmadı].

## A. DAN girdi bileşimi (tam bağlantı grafı; alt ağdaki 161 sağ-yarımküre DAN'ın aldığı sinapslar)

Toplam 271,801 sinaps. Sütunlar: tüm DAN / PAM / PPL1 (sinaps payı).

| öncül sınıfı | tüm DAN | PAM | PPL1 |
|---|---|---|---|
| KC | 0.585 | 0.681 | 0.464 |
| diğer: cb_intrinsic | 0.323 | 0.220 | 0.453 |
| açıklamasız | 0.032 | 0.035 | 0.028 |
| MBON | 0.025 | 0.022 | 0.029 |
| DAN (hepsi) | 0.019 | 0.028 | 0.009 |
| DPM | 0.009 | 0.009 | 0.007 |
| APL | 0.003 | 0.004 | 0.003 |
| diğer: descending_neuron | 0.002 | 0.001 | 0.004 |
| diğer: ascending_neuron | 0.002 | 0.001 | 0.003 |
| diğer: visual_projection | 0.000 | 0.000 | 0.000 |
| diğer: visual_centrifugal | 0.000 | 0.000 | 0.000 |

KC = Kenyon hücresi (tüm yarımküreler), MBON/DAN (hepsi) = ad önekine göre. `diğer: cb_intrinsic` = mantar cismi dışında kalan merkez-beyin içi nöronlar (aracılar).

## B. Doğrudan MBON→DAN (alt ağ; sağ yarımküre)

MBON→DAN: 3,971 sinaps, 799 kenar. Karşılaştırma: KC→DAN 96,023 sinaps (modelde yok), DAN→MBON 12,688.
MBON sınıfı (modelin u değeri): yaklaş 26, kaçın 17, karışık 5. DAN: PAM 149, PPL1 12.

İşaretli sinaps toplamı (satır MBON sınıfı → sütun DAN sınıfı; mutlak toplam parantezde). Glutamat işareti belirsiz olduğundan iki varsayım:

| glutamat | yaklaş→PAM | yaklaş→PPL1 | kaçın→PAM | kaçın→PPL1 |
|---|---|---|---|---|
| inhibitör (−1) | -138 (958) | -98 (982) | -741 (927) | +50 (330) |
| eksitatör (+1) | +428 (958) | +486 (982) | +761 (927) | +184 (330) |

Çıkarım için tek başına okuma: çıkarıcı hata devresi (yaklaş→PAM <0 ve kaçın→PPL1 <0) yalnız kısmen görülür; sonuç glutamat varsayımına bağlıdır.

## C. MBON↔DAN karşılıklılığı

Karşılıklı (j→i ve i→j) MBON-DAN çifti: **327** (MBON→DAN 799 kenar, DAN→MBON 811 kenar). Boş model (DAN etiketi karıştırma, her iki yönün derecesi korunur, 2000 tekrar): 125.1 ± 10.4; gözlenenden büyük ya da eşit boş değer oranı 0.0000 (alt sınır 1/2000). Log-sinaps korelasyonu r=0.40.
Not: boş model bölme (compartment) yapısını da bozar; bu yüzden 'karşılıklılık var' demenin ötesinde bir şey (ör. bölme-içi döngü) söylemez.

## D. İki adımlı MBON→X→DAN (X: DAN dışı aracı nöron)

Toplam DAN girdisi 271,801 sinaps. Doğrudan MBON→DAN (48 sağ MBON): 3,971 sinaps = **0.0146** pay.
MBON'dan girdi alıp DAN'a çıktı veren aracı nöron: 5,150. 'Atfedilebilir DAN girdisi' = Σ (w_jx / X'in toplam girdisi) · (X→DAN sinapsı) / DAN toplam girdisi:

| aracı sınıfı | aracı sayısı | atfedilebilir DAN girdisi payı |
|---|---|---|
| APL | 2 | 0.0000 |
| DAN (hepsi) | 146 | 0.0000 |
| DPM | 2 | 0.0000 |
| KC | 1,871 | 0.0017 |
| MBON | 94 | 0.0007 |
| açıklamasız | 274 | 0.0005 |
| diğer sınıflar | 38 | 0.0000 |
| diğer: cb_intrinsic | 2,723 | 0.0070 |

Karşılaştırma için doğrudan yol payı yukarıdadır. KC aracılığı (MBON→KC→DAN) mantar cismi içi bir döngüdür; cb_intrinsic aracılar dış yapılara açılır.

### İşaretli iki adımlı sınıf matrisi (yalnız cb_intrinsic aracılar; payda DAN toplam girdisi; ×10⁴)

Aracı işareti nt tahminiyle (asetilkolin +, GABA −, glutamat ±); dopamin/oktopamin/serotonin/belirsiz aracılar işaretsiz sayılır ve hariç tutulur.

| glutamat | yaklaş→PAM | yaklaş→PPL1 | kaçın→PAM | kaçın→PPL1 |
|---|---|---|---|---|
| inhibitör (−1) | -0.53 | +0.03 | -2.88 | -0.12 |
| eksitatör (+1) | +8.21 | +13.19 | +3.93 | +6.72 |

İşaretsiz (dopamin/oktopamin/serotonin/belirsiz) aracıların cb_intrinsic yol kütlesindeki payı: 0.017.
Yorum sınırı: yol payı sinaps sayısı üzerinden yapısal ölçüdür; işlevsel etki (işaret, nonlineerlik, bölme) içermez.

