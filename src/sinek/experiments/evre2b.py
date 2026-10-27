"""Evre 2b: gerçek mantar cismi bağlantısıyla, artırılmış ölçüt gücüyle doğrulama (ön-kayıt: docs/evre2b_plan.md).

    python -m sinek.experiments.evre2b --seed 30 --out results/evre2b_s30

Evre 2 v1'den farkları (nedenleri ve ön-kayıtlı karar kuralları plan belgesinde):
  * hareket okuması (`evre2.V2_SET`), eğitimsiz ağın az seçim yapmasını gidermek için;
  * koku kimliği dengelemesi (`--swap-roles`): her koşulda canlıların yarısında A rolü koku 1'dir;
  * seçim sayısı ağırlıklı, canlı-düzeyi (küme) bootstrap / permütasyon istatistikleri (`stats.py`);
  * G geçerlilik kapısı: eğitimsiz ve eğitilmiş seçim oranı >= 0.40 değilse A2/A3 değerlendirilemez (FAIL sayılır);
  * eğitimsiz karşılaştırma için `plastic` + `frozen` (aynı ağ) havuzlanır.
"""
from __future__ import annotations

import numpy as np

from . import evre2
from . import protocol as P
from .stats import cluster_bootstrap_ci, cluster_permutation_p, pooled_fraction

ALPHA = 0.01
GATE_MIN_RATE = 0.40
STAT_SEED = 0


def agent_counts(stage: dict, agents: int, cond: str) -> tuple[np.ndarray, np.ndarray]:
    i = P.CONDITIONS.index(cond)
    return (np.array(stage["n_a"])[i * agents:(i + 1) * agents], np.array(stage["n_b"])[i * agents:(i + 1) * agents])


def kind0_counts(stage: dict, agents: int, cond: str, swap) -> tuple[np.ndarray, np.ndarray]:
    """Rol (A/B) yerine koku kimliğine göre sayılar: (koku 0 seçimi, koku 1 seçimi)."""
    a, b = agent_counts(stage, agents, cond)
    i = P.CONDITIONS.index(cond)
    sw = np.asarray(swap, bool)[i * agents:(i + 1) * agents]
    return np.where(sw, b, a), np.where(sw, a, b)


def _pooled(*groups):
    return np.concatenate([g[0] for g in groups]), np.concatenate([g[1] for g in groups])


def _fmt(g, n_trials=None) -> str:
    m, lo, hi = cluster_bootstrap_ci(*g, seed=STAT_SEED)
    return f"{m:.2f} [{lo:.2f}, {hi:.2f}]"


def evaluate2(stages, a, conds, persisted: bool) -> dict:
    """docs/evre2b_plan.md §5'teki ön-kayıtlı ölçütler."""
    n, T = a.agents, a.trials
    last_a = next(s for s in reversed(stages) if s["phase"] == "A")
    last_b = next(s for s in reversed(stages) if s["phase"] == "B")
    naive = stages[0]
    cnt = lambda st, c: agent_counts(st, n, c)    # noqa: E731
    pl_a, fr_a, rn_a, pl_b = cnt(last_a, "plastic"), cnt(last_a, "frozen"), cnt(last_a, "random"), cnt(last_b, "plastic")
    naive_pool = _pooled(cnt(naive, "plastic"), cnt(naive, "frozen"))

    def rate(g):
        return float((g[0].sum() + g[1].sum()) / (len(g[0]) * T))

    r_naive, r_trained = rate(naive_pool), rate(pl_a)
    gate = r_naive >= GATE_MIN_RATE and r_trained >= GATE_MIN_RATE
    v: dict = {}
    v["G geçerlilik: seçim oranı eğitimsiz (plastic+frozen) ve eğitilmiş plastic >= 0.40"] = {
        "pass": bool(gate), "detail": f"eğitimsiz {r_naive:.2f} ({int(naive_pool[0].sum() + naive_pool[1].sum())} seçim), eğitilmiş {r_trained:.2f}"}

    f_pl, lo, hi = cluster_bootstrap_ci(*pl_a, seed=STAT_SEED)
    v["A1 öğrenme: eğitilmiş A-tercihi > 0.5 (havuzlanmış oran, GA alt sınırı)"] = {
        "pass": bool(lo > 0.5), "detail": f"plastic {f_pl:.2f} [{lo:.2f}, {hi:.2f}] ({int(pl_a[0].sum())} A / {int(pl_a[1].sum())} B)"}

    p_fr = cluster_permutation_p(pl_a, fr_a, seed=STAT_SEED)
    p_rn = cluster_permutation_p(pl_a, rn_a, seed=STAT_SEED)
    f_fr, f_rn = pooled_fraction(*fr_a), pooled_fraction(*rn_a)
    ok2 = bool(gate and f_pl > f_fr and f_pl > f_rn and p_fr < ALPHA and p_rn < ALPHA)
    v["A2 öğrenme: plastic > frozen ve > random (tek yönlü küme permütasyonu, p<0.01; G gerekli)"] = {
        "pass": ok2, "detail": (f"p(frozen)={p_fr:.4f}, p(random)={p_rn:.4f}; oranlar plastic {f_pl:.2f}, frozen {f_fr:.2f}, random {f_rn:.2f}"
                                + ("" if gate else " — G başarısız: değerlendirilemez"))}

    f_nv, nlo, nhi = cluster_bootstrap_ci(*naive_pool, seed=STAT_SEED)
    v["A3 eğitimsiz canlının rol tercihi yok (plastic+frozen havuzlanmış, GA 0.5'i kapsar; G gerekli)"] = {
        "pass": bool(gate and nlo <= 0.5 <= nhi),
        "detail": f"eğitimsiz {f_nv:.2f} [{nlo:.2f}, {nhi:.2f}]" + ("" if gate else " — G başarısız: değerlendirilemez")}

    v["C bellek: yeniden yüklenen canlı birebir aynı davranır"] = {
        "pass": bool(persisted), "detail": "ağırlıklar ve test sonuçları birebir eşit" if persisted else "FARK VAR"}

    p_rev = cluster_permutation_p(pl_a, pl_b, seed=STAT_SEED)
    f_b, blo, bhi = cluster_bootstrap_ci(*pl_b, seed=STAT_SEED)
    v["B1 tersine çevirme: A-tercihi anlamlı düştü (tek yönlü küme permütasyonu, p<0.01)"] = {
        "pass": bool(p_rev < ALPHA and f_b < f_pl), "detail": f"{f_pl:.2f} -> {f_b:.2f}, p={p_rev:.4f}"}
    v["B2 tersine çevirme: B artık tercih edilir (havuzlanmış oran, GA üst sınırı < 0.5)"] = {
        "pass": bool(bhi < 0.5), "detail": f"plastic {f_b:.2f} [{blo:.2f}, {bhi:.2f}]"}
    return v


def render_summary2(r: dict) -> str:
    a = r["args"]
    n, T = a["agents"], a["trials"]
    swap = r.get("swap") or [0] * (3 * n)
    L = [f"# {r.get('title', 'Evre 2b')} sonuç özeti", ""]
    L.append(f"- Canlı başına nöron: **{r['neurons_per_creature']}**; koşul başına **{n}** canlı "
             f"({'rol-dengeli: yarısında A rolü = koku 1' if a.get('swap_roles') else 'rol dengelemesi yok'}), canlı başına **{T}** deneme")
    L.append(f"- Eğitim: A için {a['episodes']} bölüm, tersine çevirmede {a['reversal_episodes']} bölüm, bölüm = {a['episode_seconds']:.0f} sanal sn")
    L.append(f"- Toplam çalışma süresi: {r['wall_seconds'] / 60:.1f} dk, tohum: {a['seed']}")
    L += ["", "## Ölçütler (ön-kayıtlı: docs/evre2b_plan.md)", ""]
    for k, v in r["verdict"].items():
        L.append(f"- **{'PASS' if v['pass'] else 'FAIL'}** — {k}: {v['detail']}")
    L += ["", "## Seçim testi: A tercih oranı (havuzlanmış, küme bootstrap %95 GA)", "",
          "Havuzlanmış oran = Σ A / Σ (A+B); GA canlılar yerine koyarak yeniden örneklenir. 0.5 = tercih yok. "
          "Seçim sayısı = o koşulda toplam ilk-temas sayısı; seçim oranı = seçim sayısı / deneme sayısı.", "",
          "| Aşama | Bölüm | plastic | frozen | random | seçim sayısı (p/f/r) | seçim oranı (p/f/r) |", "|---|---:|---|---|---|---|---|"]
    for s in r["stages"]:
        sm = s["summary"]
        cells = []
        for c in P.CONDITIONS:
            d = sm[c]
            cells.append(f"{d['pooled_A_mean']:.2f} [{d['pooled_A_ci95'][0]:.2f}, {d['pooled_A_ci95'][1]:.2f}]")
        nch = "/".join(str(sm[c]["n_choices"]) for c in P.CONDITIONS)
        rts = "/".join(f"{sm[c]['choice_rate']:.2f}" for c in P.CONDITIONS)
        L.append(f"| {s['name']} | {s['episode']} | {cells[0]} | {cells[1]} | {cells[2]} | {nch} | {rts} |")
    nv = r["stages"][0]
    k0 = _pooled(kind0_counts(nv, n, "plastic", swap), kind0_counts(nv, n, "frozen", swap))
    L += ["", "## Betimsel: eğitimsiz ağın koku-kimliği yanlılığı", "",
          f"Eğitimsiz `plastic`+`frozen` (aynı ağ) ilk-temaslarında koku-0 oranı: {_fmt(k0)} "
          f"({int(k0[0].sum())} koku-0 / {int(k0[1].sum())} koku-1). Rol dengelemesi sayesinde bu yanlılık A-tercihi ölçütlerini bozmaz; "
          "yalnızca canlılar arası değişkenliği artırır.", "",
          "## Notlar", "",
          "- `frozen`: aynı deneyimi yaşar ama sinapslar değişmez; `random`: dönüş kazancı 0.",
          "- Seçim testlerinde tüm aşamalar aynı rastgele düzenleri kullanır; aşamalar bağımsız örneklem değildir.",
          "- Bu sonuçlar sanal ortam ve bu model için geçerlidir; gerçek sinek davranışı hakkında iddia taşımaz."]
    return "\n".join(L) + "\n"


def main(argv=None) -> dict:
    return evre2.main(argv, v2=True)


if __name__ == "__main__":
    main()
