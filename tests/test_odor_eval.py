"""Oyun değerlendiricileri (odor_eval): sıfır etkide geçmemeli, bilinen etkide geçmeli (R-6, CLAUDE.md kural 3)."""
import numpy as np

from sinek.experiments.odor_eval import Thr, eval_o1, eval_o3, eval_o4a, eval_o4c

THR = Thr(n_boot=800, n_perm=800)
A, T = 24, 16


def _h(rng, p, n=A, t=T, creature_sd=0.08):
    """Canlı başına değişen başarı olasılığı (kümelenme) ile Bernoulli isabetler."""
    pc = np.clip(p + creature_sd * rng.standard_normal(n), 0.01, 0.99)
    return (rng.random((n, t)) < pc[:, None]).astype(int), pc


def _paired(rng, p_by_arm):
    """Aynı canlı etkisi (CRN benzeri) tüm kollarda ortak: canlı başına sapma ortak, kola göre taban farklı."""
    dev = 0.08 * rng.standard_normal(A)
    return {k: (rng.random((A, T)) < np.clip(p + dev, 0.01, 0.99)[:, None]).astype(int) for k, p in p_by_arm.items()}


def test_o1_known_effect_passes_and_null_fails():
    rng = np.random.default_rng(0)
    hit = sum(eval_o1(_paired(rng, {"frozen": 0.7, "anosmic": 0.3, "random": 0.3, "reference": 0.9}), THR)["passed"] for _ in range(10))
    assert hit >= 9
    fp = sum(eval_o1(_paired(rng, {"frozen": 0.3, "anosmic": 0.3, "random": 0.3, "reference": 0.9}), THR)["passed"] for _ in range(60))
    assert fp == 0                                  # δ=0.15 ve α=0.01 birlikte: sıfır etkide geçmez


def test_o1_gate_failure_blocks_pass():
    rng = np.random.default_rng(1)
    r = eval_o1(_paired(rng, {"frozen": 0.7, "anosmic": 0.3, "random": 0.3, "reference": 0.5}), THR)
    assert not r["gates_ok"] and not r["passed"]


def _crn(rng, p_by_arm, indep):
    """CRN benzeri: tüm kollar aynı (canlı, deneme) tek tekdüze sayıyı paylaşır; `indep` oranında deneme bağımsız yeniden çekilir
    (kollar o denemede ayrışmış demektir). indep=0: iz bit-bit ortak; indep=1: bağımsız kollar (kötümser uç)."""
    dev = 0.08 * rng.standard_normal(A)
    u = rng.random((A, T))
    out = {}
    for k, p in p_by_arm.items():
        uu = np.where(rng.random((A, T)) < indep, rng.random((A, T)), u)
        out[k] = (uu < np.clip(p + dev, 0.01, 0.99)[:, None]).astype(int)
    return out


def test_o3_equivalence_null_passes_and_bias_fails():
    rng = np.random.default_rng(2)
    thr = Thr(n_boot=600, n_perm=100)
    arms = {k: 0.3 for k in "ABCD"}
    same = sum(eval_o3(_crn(rng, arms, 0.2), thr)["passed"] for _ in range(20))
    assert same >= 16                               # kollar çoğunlukla ortak izdeyken sıfır etkide eşdeğerlik geçer
    biased = sum(eval_o3(_crn(rng, {**arms, "D": 0.3 + thr.delta_eq}, 0.2), thr)["passed"] for _ in range(20))
    assert biased <= 1                              # fark marjda ise eşdeğerlik tanınmaz (yanlış-geçme ~0)


def test_o3_equivalence_is_underpowered_without_crn():
    """Bulgu (G4 girdisi): kollar bağımsız olsaydı δ_eq=0,10 ve 24x16 tasarımında sıfır etkide bile eşdeğerlik çoğunlukla GEÇMEZ.
    O3'ün anlamı CRN eşleşmesine bağlıdır; pilotta kol ayrışma oranı ölçülmeli (docs/odor_guc_analizi.md)."""
    rng = np.random.default_rng(5)
    thr = Thr(n_boot=600, n_perm=100)
    passed = sum(eval_o3(_crn(rng, {k: 0.3 for k in "ABCD"}, 1.0), thr)["passed"] for _ in range(20))
    assert passed <= 8


def test_o4a_gate_and_effect():
    rng = np.random.default_rng(3)
    ok = eval_o4a(_paired(rng, {"plastic": 0.2, "frozen": 0.7, "anosmic": 0.3}), THR)
    assert ok["gates_ok"] and ok["passed"]
    no_attraction = eval_o4a(_paired(rng, {"plastic": 0.2, "frozen": 0.35, "anosmic": 0.3}), THR)
    assert not no_attraction["gates_ok"] and not no_attraction["passed"]


def test_o4c_decoy_first_and_noninferiority():
    rng = np.random.default_rng(4)

    def slots(p_dec, p_real):
        u = rng.random((A, T))
        return np.where(u < p_dec, 1, np.where(u < p_dec + p_real, 0, -1))

    s = {"frozen": slots(0.7, 0.05), "anosmic": slots(0.15, 0.15), "plastic": slots(0.2, 0.15)}
    r = eval_o4c(s, THR)
    assert r["gates_ok"] and r["passed"]
    s["plastic"] = slots(0.2, 0.0)                  # decoy'dan kaçıyor ama gerçeği de bulamıyor: aşağı-tarafsızlık bozulur
    assert not eval_o4c(s, THR)["criteria"]["P2_gercek_ilk_asagi_tarafsiz"]["passed"]
