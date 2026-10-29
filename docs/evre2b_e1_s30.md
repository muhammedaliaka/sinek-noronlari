# Evre 2b E1 — MBON sınıf etiketi karıştırma kontrolü

Gerçek-etiketli koşu: `evre2b_s30` (tohum 30). Ölçüt: karıştırılmış `plastic` A-oranı gerçekten düşük (p < 0.01) VE karıştırılmış ağın seçim oranı >= 0.4.

| koşul | sınıf dengesi | eğitilmiş plastic A-oranı [GA] | seçim sayısı (oran) | p (gerçek > karıştırılmış) | E1 |
|---|---:|---|---|---:|---|
| gerçek etiketler | 1.210 | 0.72 [0.67, 0.76] | — | — | — |
| karıştırma tohum 1 (`evre2b_s30_shuffle1_recovered`) | 1.258 | 0.47 [0.38, 0.56] | 177 (0.46) | 0.0000 | PASS |
| karıştırma tohum 2 (`evre2b_s30_shuffle2_recovered`) | 1.197 | 0.64 [0.58, 0.70] | 318 (0.83) | 0.0299 | FAIL |

**E1 genel: FAIL** (her karıştırma geçmeli). E1 bir yapısal kontroldür; Evre 2b ana karar kuralına girmez, ama FAIL ise 'gerçek sınıf yapısı işe yarıyor' iddiası kurulamaz.

## Nasıl elde edildi (kurtarma) — önemli
Karıştırma koşuları (`class_shuffle_seed` 1 ve 2) A fazını bitirdi (`after_A.npz` yazıldı) ancak B fazında (tersine çevirme) işçi süreci yeniden başlamalarıyla öldü; Evre 2b hattında kontrol noktası yoktur (E-14). E1 ölçütü yalnız **A-sonu `plastic` seçimlerini** kullandığından, A-sonu testi `after_A.npz` durumundan yeniden hesaplandı (`sinek.experiments.evre2b_e1_recover`; K-033). **Sıfır-etki sınaması:** aynı yöntem gerçek koşunun (`evre2b_s30`) kendi `after_A.npz` dosyasında A-sonu n_a/n_b'yi `results.json` ile birebir aynı verdi. Karşılaştırma kodu ve eşikler değişmedi.
Kurtarılan koşular tersine çevirme fazı içermez (E1 için gerekmez). Karıştırma koşularının kendi bellek-içi A-sonu testi kaybolduğundan ilk-elden doğrulanamaz; eşdeğerlik, gerçek koşudaki `persistence.test_identical=True` ve yukarıdaki sıfır-etki sınamasına dayanır.

## Hüküm ve dürüst yorum
* **E1 genel: FAIL** (ön-kayıt: her karıştırma geçmeli). Ölçütler koşudan sonra değişmedi.
* Karıştırma 1: **PASS** — plastic A-oranı 0,47 [0,38; 0,56] (gerçek 0,72), seçim oranı 0,46 (≥0,40; geçerli), p<0,0001.
* Karıştırma 2: **FAIL** — plastic A-oranı **0,64** [0,58; 0,70], seçim oranı 0,83; gerçeğe göre fark küçük, p=0,0299 (eşik 0,01). Geçerli bir karşılaştırma (seçim oranı yüksek) ve ölçüt sağlanmadı.
* **Sonuç (ön-kayıt cümlesi):** "gerçek sınıf yapısı işe yarıyor" iddiası bu kontrolle **kurulamaz**. Bu, Evre 2b ana karar kuralını etkilemez (E1 onun parçası değildir; 7/7 ve 7/7 geçti), ama sınıf türetiminin (yaklaş/kaçın) öğrenme için gerekli olduğu da gösterilmemiştir.
* **Gözlem (SINANMADI, hipotez):** karıştırma yalnız MBON yaklaş/kaçın *okuma* sınıflarını değiştirir; DAN bölme eşlemesi ve plastisite aynı kalır. Rastgele bir sınıf bölünmesi gerçeğe kısmen örtüşebileceğinden öğrenilen tercih kısmen korunabilir (0,64). İki karıştırma arasındaki fark (0,47 vs 0,64) etiketlerin gerçekleşmeye bağlı olduğunu gösterir; yalnız 2 karıştırma vardır, gerçek-etiket ile rastgele-etiket arasında genel bir sıralama için yetersiz. Bunu sınamak için çok sayıda karıştırma (ör. 20) ve karıştırma-başına bağımsız ölçüm gerekir; yeni ön-kayıt olmadan eklenmedi.
* Evre 2 (v1) E1'i "formel geçti ama karıştırılmış ağ neredeyse hiç seçim yapmadı" diye bırakmıştı; burada karşılaştırma geçerli ve sonuç karışık.
