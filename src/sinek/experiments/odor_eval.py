"""Dört koku oyunu: oyun başına karar kuralı (docs/dort_koku_oyunu_plani.md §5.1) — saf işlevler.

Girdi: kol adından (canlı, deneme) 0/1 isabet dizisine sözlük (`protocol.hits`/`stack_hits`) ya da ilk-temas yuvası dizisi (O4c).
Eşikler (`Thr`) ön-kayıtta dondurulur; bu modül eşik seçmez. Aynı işlev hem gerçek koşuyu hem güç benzetimini (`power_odor`) değerlendirir
— benzetim, değerlendiricinin kendisini sınar (Evre 2b dersi, R-6).

Geçti kuralı üstünlük ölçütlerinde: eşli işaret-çevirme p < alpha **ve** eşli %(1−alpha) kümeli GA alt sınırı > 0 **ve** ortalama fark ≥ delta.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .stats import paired_cluster_ci, paired_equivalent, paired_signflip_p


@dataclass(frozen=True)
class Thr:
    delta: float = 0.15          # üstünlük (O1/O2/O4) en küçük anlamlı fark — aday, güç analizinden önce keyfî (plan §5.1)
    delta_eq: float = 0.10       # eşdeğerlik / aşağı-tarafsızlık marjı — aday
    alpha: float = 0.01
    ref_min: float = 0.80        # referans karşılaştırıcı çözülebilirlik kapısı
    attract_mult: float = 1.0    # O4 çekim odası kapısı: frozen − anosmik ≥ attract_mult·δ (ön-kayıtta güç türetmesiyle dondurulur)
    anos_lo: float = 0.15        # anosmik (kör) düzey penceresi (O1)
    anos_hi: float = 0.45
    n_boot: int = 4000
    n_perm: int = 4000


def _sums(h) -> np.ndarray:
    return np.asarray(h).sum(1)


def _superior(x, y, n_trials: int, thr: Thr, delta: float | None = None, less: bool = False, seed: int = 0) -> dict:
    """x − y üstünlük (less=True ise y − x). Çıktı: ortalama, GA, p, geçti."""
    a, b = (y, x) if less else (x, y)
    d = thr.delta if delta is None else delta
    m, lo, hi = paired_cluster_ci(_sums(a), _sums(b), n_trials, n=thr.n_boot, seed=seed, alpha=thr.alpha)
    p = paired_signflip_p(_sums(a), _sums(b), n_trials, n=thr.n_perm, seed=seed, alternative="greater")
    sign = -1.0 if less else 1.0
    return {"mean": sign * m, "ci": [sign * lo, sign * hi] if not less else [-hi, -lo], "p": p,
            "passed": bool(p < thr.alpha and lo > 0 and m >= d)}


def _result(gates: dict, crit: dict) -> dict:
    return {"gates": gates, "criteria": crit, "gates_ok": all(gates.values()),
            "passed": all(gates.values()) and all(c["passed"] for c in crit.values())}


def eval_o1(h: dict, thr: Thr, extra_gates: dict | None = None) -> dict:
    """O1 (düz ya da dönüşlü iz). Kollar: frozen, anosmic, random, reference. P3: ayna yarılarının her ikisinde frozen−anosmic > 0."""
    T = np.asarray(h["frozen"]).shape[1]
    gates = {"referans_p_hit>=ref_min": bool(np.mean(h["reference"]) >= thr.ref_min),
             "anosmik_pencerede": bool(thr.anos_lo <= np.mean(h["anosmic"]) <= thr.anos_hi), **(extra_gates or {})}
    crit = {"P1_frozen-anosmik": _superior(h["frozen"], h["anosmic"], T, thr),
            "P2_frozen-random": _superior(h["frozen"], h["random"], T, thr, seed=1)}
    halves = []
    for sl in (slice(0, None, 2), slice(1, None, 2)):
        m, lo, hi = paired_cluster_ci(_sums(np.asarray(h["frozen"])[:, sl]), _sums(np.asarray(h["anosmic"])[:, sl]), T // 2,
                                      n=thr.n_boot, alpha=thr.alpha)
        halves.append({"mean": m, "ci": [lo, hi]})
    crit["P3_ayna_yarilari"] = {"halves": halves, "passed": bool(all(x["mean"] > 0 for x in halves))}
    return _result(gates, crit)


def eval_o2(h: dict, thr: Thr, extra_gates: dict | None = None) -> dict:
    """O2-yakın. Kollar: frozen (koku açık), anosmic, reference. extra_gates: CRN özdeşliği, kör bölge girişi aralığı."""
    T = np.asarray(h["frozen"]).shape[1]
    gates = {"referans_yakin_p_hit>=ref_min": bool(np.mean(h["reference"]) >= thr.ref_min), **(extra_gates or {})}
    crit = {"P1_yakin_koku-anosmik": _superior(h["frozen"], h["anosmic"], T, thr)}
    return _result(gates, crit)


def eval_o3(h: dict, thr: Thr, extra_gates: dict | None = None) -> dict:
    """O3: üstünlük ölçütü yoktur. Tüm kol çiftleri eşdeğerlik marjı içinde olmalı (E3); kör düzey raporlanır."""
    arms = sorted(h)
    T = np.asarray(h[arms[0]]).shape[1]
    gates = dict(extra_gates or {})
    crit, k = {}, 0
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            m, lo, hi, ok = paired_equivalent(_sums(h[a]), _sums(h[b]), T, thr.delta_eq, alpha=thr.alpha, n=thr.n_boot, seed=k)
            crit[f"E3_{a}~{b}"] = {"mean": m, "ci": [lo, hi], "passed": ok}
            k += 1
    r = _result(gates, crit)
    r["blind_level"] = {a: float(np.mean(h[a])) for a in arms}
    return r


def eval_o4a(h: dict, thr: Thr, extra_gates: dict | None = None) -> dict:
    """O4a (sönüm). Kollar: plastic, frozen, anosmic: decoy'a isabet. G4: frozen−anosmik ≥ attract_mult·δ (çekim odası)."""
    T = np.asarray(h["frozen"]).shape[1]
    att = _superior(h["frozen"], h["anosmic"], T, thr, delta=thr.attract_mult * thr.delta, seed=2)
    gates = {"G4_cekim_odasi": bool(att["passed"]), **(extra_gates or {})}
    crit = {"P1_plastic<frozen": _superior(h["plastic"], h["frozen"], T, thr, less=True)}
    r = _result(gates, crit)
    r["attraction"] = att
    return r


def eval_o4c(slots: dict, thr: Thr, extra_gates: dict | None = None) -> dict:
    """O4c (decoy + kokusuz gerçek hedef). slots: kol → (canlı, deneme) ilk-temas yuvası (0 gerçek, 1 decoy, −1 yok).
    Kollar: plastic, frozen, anosmic. P1 decoy-ilk: plastic < frozen−δ. P2 gerçek-ilk: plastic, anosmik (kör) düzeyin δ_eq altına düşmemeli."""
    T = np.asarray(slots["frozen"]).shape[1]
    dec = {k: (np.asarray(v) == 1).astype(int) for k, v in slots.items()}
    real = {k: (np.asarray(v) == 0).astype(int) for k, v in slots.items()}
    att = _superior(dec["frozen"], dec["anosmic"], T, thr, delta=thr.attract_mult * thr.delta, seed=2)
    gates = {"G4_cekim_odasi": bool(att["passed"]), **(extra_gates or {})}
    p1 = _superior(dec["plastic"], dec["frozen"], T, thr, less=True)
    m, lo, hi = paired_cluster_ci(_sums(real["plastic"]), _sums(real["anosmic"]), T, n=thr.n_boot, alpha=2 * thr.alpha, seed=3)
    crit = {"P1_decoy_ilk_plastic<frozen": p1,
            "P2_gercek_ilk_asagi_tarafsiz": {"mean": m, "ci": [lo, hi], "passed": bool(lo > -thr.delta_eq)}}
    r = _result(gates, crit)
    r["attraction"] = att
    return r


def eval_scale(h: dict, thr: Thr, extra_gates: dict | None = None) -> dict:
    """Ölçek ekseni doğrulayıcısı (topluluk K + kısa okuma süresi; docs/olcek_plani.md). Kollar: frozen (taban beyin), ens (topluluk beyni),
    anosmic (taban), anosmic_ens, reference. KARAR VEREN: P1 ens − frozen ≥ δ (ölçek kazancı); P2 ens − anosmic_ens ≥ δ (koku kaynaklı kazanç,
    eşleşmiş kör kol). BETİMSEL (karar vermez): P3 anosmic_ens ~ anosmic eşdeğerliği (±δ_eq) — güç benzetimi, eşdeğerlik testinin tek başına
    gerçek eşitlikte bile ≈%80 geçtiğini gösterdi (toplam gücü yarıya indirirdi); koruma P2'dir. P3 raporda yer alır."""
    T = np.asarray(h["frozen"]).shape[1]
    gates = {"referans_p_hit>=ref_min": bool(np.mean(h["reference"]) >= thr.ref_min), **(extra_gates or {})}
    crit = {"P1_ens-frozen": _superior(h["ens"], h["frozen"], T, thr, seed=4),
            "P2_ens-anosmic_ens": _superior(h["ens"], h["anosmic_ens"], T, thr, seed=5)}
    m, lo, hi, ok = paired_equivalent(_sums(h["anosmic_ens"]), _sums(h["anosmic"]), T, thr.delta_eq, alpha=thr.alpha, n=thr.n_boot, seed=6)
    r = _result(gates, crit)
    r["descriptive"] = {"P3_anosmic_ens~anosmic": {"mean": m, "ci": [lo, hi], "passed": ok}}
    return r


O5_BLOCKS = ((10, 20), (30, 40))      # geç faz-1 (bölüm 11-20) ve geç faz-2 (bölüm 31-40): 0-tabanlı yarı açık aralıklar


def eval_o5(h: dict, thr: Thr, extra_gates: dict | None = None, blocks=O5_BLOCKS) -> dict:
    """O5 (olasılıklı iki-kollu, oturum içi tersine çevirme; docs/odor_o5_plani.md). h: kol → (yaşam, bölüm) 0/1 ödül alındı; plastic, frozen, reference;
    net_plastic, net_frozen: (yaşam, bölüm) tercih skoru (+1 iyi koku seçildi, −1 kötü, 0 temas yok).
    Kapı: referans geç bloklarda ödül oranı ≥ ref_min. Karar veren: P1/P2 plastic − frozen ödül oranı (geç faz-1 / geç faz-2) ≥ δ;
    P3 özgüllük: net tercih skoru farkı (iki geç blok birlikte) için eşli işaret-çevirme p < α ve %99 GA alt sınırı > 0 (avantajın koku-ödül ayrımından geldiğini gösterir:
    yalnız 'her kokuya yaklaşma' ödül oranını yükseltebilir ama net tercihi yükseltmez)."""
    (a0, a1), (b0, b1) = blocks
    cols = np.r_[a0:a1, b0:b1]
    ref = np.asarray(h["reference"])[:, cols]
    gates = {"referans_odul>=ref_min": bool(ref.mean() >= thr.ref_min), **(extra_gates or {})}
    pl, fr = np.asarray(h["plastic"]), np.asarray(h["frozen"])
    crit = {"P1_odul_gec_faz1": _superior(pl[:, a0:a1], fr[:, a0:a1], a1 - a0, thr, seed=7),
            "P2_odul_gec_faz2": _superior(pl[:, b0:b1], fr[:, b0:b1], b1 - b0, thr, seed=8)}
    npl, nfr = np.asarray(h["net_plastic"])[:, cols], np.asarray(h["net_frozen"])[:, cols]
    m, lo, hi = paired_cluster_ci(_sums(npl), _sums(nfr), len(cols), n=thr.n_boot, seed=9, alpha=thr.alpha)
    p = paired_signflip_p(_sums(npl), _sums(nfr), len(cols), n=thr.n_perm, seed=9, alternative="greater")
    crit["P3_ozgullukte_net_tercih"] = {"mean": m, "ci": [lo, hi], "p": p, "passed": bool(p < thr.alpha and lo > 0)}
    return _result(gates, crit)


def eval_o5b(h: dict, thr: Thr, extra_gates: dict | None = None, blocks=O5_BLOCKS, delta_np: float = 0.10, delta_r: float = 0.08) -> dict:
    """O5b (docs/odor_o5b_plani.md; E-15 dersi): karar veren ölçüt YAKLAŞMADAN ARINDIRILMIŞ seçicilik. Girdi h: plastic, frozen, reference, [plastic_ens] (yaşam, bölüm) ödül ve
    net_plastic, net_frozen, [net_plastic_ens] (yaşam, bölüm) net tercih skoru (+1 iyi koku, −1 kötü koku, 0 temas yok).
    Net tercihin boş-model düzeyi her temas oranında ≈0'dır (iyi/kötü seçimi 0,5); bu yüzden `frozen` temas oranının popülasyondan popülasyona değişmesi ölçütü kaydırmaz (ödül oranı kaydırırdı).
    Kapı: referans geç bloklarda ödül oranı ≥ ref_min.
    N1: plastic − frozen net tercih farkı, iki geç blok birlikte (bölüm 11-20 ve 31-40) ≥ delta_np (üstünlük kuralı: p<α, %99 GA alt sınırı>0, ortalama ≥ δ).
    N2 (yeniden öğrenme): aynı fark yalnız geç faz-2 bloğunda (tersine çevirmeden sonra) > 0 (p<α, %99 GA alt sınırı>0; asgari etki büyüklüğü YOK — 10 bölümlük blokta 48 yaşamın gücü δ için yetmez).
    E1 (topluluk, yalnız plastic_ens varsa): plastic_ens − plastic ödül oranı (iki geç blok birlikte) ≥ delta_r. Betimsel (karar vermez): E2 aynı kural, net tercih, δ=delta_np."""
    (a0, a1), (b0, b1) = blocks
    cols = np.r_[a0:a1, b0:b1]
    gates = {"referans_odul>=ref_min": bool(np.asarray(h["reference"])[:, cols].mean() >= thr.ref_min), **(extra_gates or {})}
    npl, nfr = np.asarray(h["net_plastic"]), np.asarray(h["net_frozen"])
    crit = {"N1_secicilik_toplam": _superior(npl[:, cols], nfr[:, cols], len(cols), thr, delta=delta_np, seed=7),
            "N2_yeniden_ogrenme_faz2": _superior(npl[:, b0:b1], nfr[:, b0:b1], b1 - b0, thr, delta=0.0, seed=8)}
    desc = {}
    if "plastic_ens" in h:            # topluluk kolu yoksa (ör. yalnız düz O5 verisi) E ölçütleri atlanır
        nen, rpl, ren = np.asarray(h["net_plastic_ens"]), np.asarray(h["plastic"]), np.asarray(h["plastic_ens"])
        crit["E1_topluluk_odul"] = _superior(ren[:, cols], rpl[:, cols], len(cols), thr, delta=delta_r, seed=9)
        desc["E2_topluluk_net_tercih"] = _superior(nen[:, cols], npl[:, cols], len(cols), thr, delta=delta_np, seed=10)
    return {**_result(gates, crit), "descriptive": desc}

EVALUATORS = {"O1": eval_o1, "O2": eval_o2, "O3": eval_o3, "O4a": eval_o4a, "O4c": eval_o4c, "SC": eval_scale, "O5": eval_o5, "O5b": eval_o5b}
