# Evre 2 — ek analizler (ön-kayıtlı DEĞİL)

Bu belge `python -m sinek.experiments.evre2_posthoc` ile üretilir. **Ön-kayıtlı ölçütlerin hükmünü değiştirmez**; koşular
bittikten sonra, ölçütlerin neden geçtiği/kaldığını anlamak için yapılmış betimsel çözümlemelerdir.

## 1. Seçim sayıları (A ve B ilk-temas toplamları)

### evre2_s20 (tohum 20)

| aşama | koşul | seçim yapan canlı | A / B ilk-temas | havuzlanmış A-oranı |
|---|---|---:|---|---:|
| naif | plastic | 8/16 | 6 / 5 | 0.55 |
| naif | frozen | 9/16 | 6 / 3 | 0.67 |
| naif | random | 16/16 | 21 / 23 | 0.48 |
| A sonrası bölüm 12 | plastic | 15/16 | 46 / 4 | 0.92 |
| A sonrası bölüm 12 | frozen | 9/16 | 6 / 3 | 0.67 |
| A sonrası bölüm 12 | random | 16/16 | 21 / 23 | 0.48 |
| B sonrası bölüm 24 | plastic | 15/16 | 14 / 30 | 0.32 |
| B sonrası bölüm 24 | frozen | 9/16 | 6 / 3 | 0.67 |
| B sonrası bölüm 24 | random | 16/16 | 21 / 23 | 0.48 |

### evre2_s21 (tohum 21)

| aşama | koşul | seçim yapan canlı | A / B ilk-temas | havuzlanmış A-oranı |
|---|---|---:|---|---:|
| naif | plastic | 4/16 | 4 / 0 | 1.00 |
| naif | frozen | 9/16 | 6 / 4 | 0.60 |
| naif | random | 16/16 | 23 / 23 | 0.50 |
| A sonrası bölüm 12 | plastic | 15/16 | 46 / 5 | 0.90 |
| A sonrası bölüm 12 | frozen | 9/16 | 6 / 4 | 0.60 |
| A sonrası bölüm 12 | random | 16/16 | 23 / 23 | 0.50 |
| B sonrası bölüm 24 | plastic | 15/16 | 7 / 40 | 0.15 |
| B sonrası bölüm 24 | frozen | 9/16 | 6 / 4 | 0.60 |
| B sonrası bölüm 24 | random | 16/16 | 23 / 23 | 0.50 |

## 2. Post-hoc karşılaştırmalar (havuzlanmış A-oranı, canlı-düzeyi permütasyon)

Ağırlık = canlının yaptığı seçim sayısı; birim = canlı (denemeler aynı canlı içinde bağımsız sayılmaz). Tek yönlü: ilk grup > ikinci grup.

| koşu | karşılaştırma | grup 1 | grup 2 | p |
|---|---|---|---|---:|
| evre2_s20 | eğitilmiş plastic > frozen (A2'nin havuzlanmış karşılığı) | 46A/4B (0.92) | 6A/3B (0.67) | 0.0011 |
| evre2_s20 | eğitilmiş plastic > naif (plastic+frozen, aynı ağ) | 46A/4B (0.92) | 12A/8B (0.60) | 0.0000 |
| evre2_s20 | eğitilmiş A-plastic > B-plastic (tersine çevirme) | 46A/4B (0.92) | 14A/30B (0.32) | 0.0001 |
| evre2_s20 | naif ağ (plastic+frozen) tercihi = 0.5? (tam iki terimli, denemeler bağımsız varsayılır) | 12A/8B | — | 0.5034 |
| evre2_s21 | eğitilmiş plastic > frozen (A2'nin havuzlanmış karşılığı) | 46A/5B (0.90) | 6A/4B (0.60) | 0.0009 |
| evre2_s21 | eğitilmiş plastic > naif (plastic+frozen, aynı ağ) | 46A/5B (0.90) | 10A/4B (0.71) | 0.0205 |
| evre2_s21 | eğitilmiş A-plastic > B-plastic (tersine çevirme) | 46A/5B (0.90) | 7A/40B (0.15) | 0.0000 |
| evre2_s21 | naif ağ (plastic+frozen) tercihi = 0.5? (tam iki terimli, denemeler bağımsız varsayılır) | 10A/4B | — | 0.1796 |

## 3. E1 — MBON yaklaş/kaçın etiketlerinin karıştırılması (tohum-20 kurulumu)

Ön-kayıtlı ölçüt: A eğitimi sonunda `plastic` A-tercihi gerçek-etiketli koşudan düşüktür (tek yönlü permütasyon, canlı başına tercih, p < 0.01).

| koşu | sınıf dengesi | naif plastic A-tercihi | eğitilmiş plastic A-tercihi [GA] | seçim yapan canlı | p (gerçek > karıştırılmış) | E1 |
|---|---:|---|---|---:|---:|---|
| gerçek etiketler (evre2_s20) | 1.210 | 0.56 | 0.92 [0.85, 0.98] | 15/16 | — | — |
| karıştırma tohum 1 (evre2_s20_shuffle1) | 1.258 | 0.83 | 0.17 [0.00, 0.50] | 3/16 | 0.0012 | PASS |
| karıştırma tohum 2 (evre2_s20_shuffle2) | 1.197 | 0.00 | 0.52 [0.24, 0.79] | 11/16 | 0.0054 | PASS |

