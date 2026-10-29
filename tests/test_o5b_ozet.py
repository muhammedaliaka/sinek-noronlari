"""o5b_ozet: ön-kayıtlı iki iddia kuralı (A: N1 4/4 ∧ N2 ≥3/4; B: E1 ≥3/4), kapı, eksik koşu."""
import json

from sinek.experiments import o5b_ozet as O


def _run(n1=True, n2=True, e1=True, gate=True) -> dict:
    c = {"N1_secicilik_toplam": n1, "N2_yeniden_ogrenme_faz2": n2, "E1_topluluk_odul": e1}
    crit = {k: {"mean": 0.1, "ci": [0.0, 0.2], "p": 0.001, "passed": v} for k, v in c.items()}
    return {"eval": {"passed": all(c.values()) and gate, "gates_ok": gate, "gates": {}, "criteria": crit,
                     "descriptive": {"E2_topluluk_net_tercih": {"mean": 0.1, "ci": [0.0, 0.2], "p": 0.01, "passed": True}}},
            "reward_rate": {"plastic_ens": 0.5, "plastic": 0.4, "frozen": 0.25, "reference": 0.76}}


def test_claim_rules():
    S = O.SEEDS
    ok = {s: _run() for s in S}
    assert O.verdicts(ok) == {"A (seçicilik/öğrenme)": "BAŞARILI", "B (topluluk)": "BAŞARILI"}
    one_n2 = {**ok, S[0]: _run(n2=False)}                                   # N2 yalnız ≥3/4 ister
    assert O.verdicts(one_n2)["A (seçicilik/öğrenme)"] == "BAŞARILI"
    two_n2 = {**one_n2, S[1]: _run(n2=False)}
    assert O.verdicts(two_n2)["A (seçicilik/öğrenme)"] == "BAŞARISIZ" and O.verdicts(two_n2)["B (topluluk)"] == "BAŞARILI"
    one_n1 = {**ok, S[2]: _run(n1=False)}                                   # N1 4/4 ister
    assert O.verdicts(one_n1)["A (seçicilik/öğrenme)"] == "BAŞARISIZ"
    two_e1 = {**ok, S[0]: _run(e1=False), S[3]: _run(e1=False)}
    assert O.verdicts(two_e1)["B (topluluk)"] == "BAŞARISIZ"
    gate = {**ok, S[1]: _run(gate=False)}                                   # kapı eksik → iki iddia da yapılamaz
    assert set(O.verdicts(gate).values()) == {"BAŞARISIZ"}


def test_missing_runs_wait_and_main(tmp_path):
    S = O.SEEDS
    part = {S[0]: _run(), S[1]: _run(), S[2]: None, S[3]: None}
    assert set(O.verdicts(part).values()) == {"BEKLİYOR"}
    assert O.verdicts({**part, S[0]: _run(n1=False)})["A (seçicilik/öğrenme)"] == "BAŞARISIZ"      # çürütülen kural beklemez
    (tmp_path / f"b_s{S[0]}").mkdir()
    (tmp_path / f"b_s{S[0]}" / "results.json").write_text(json.dumps(_run()), encoding="utf-8")
    text = O.main(["--dir", str(tmp_path), "--out", str(tmp_path / "o.md")])
    assert "BEKLİYOR" in text and str(S[0]) in text
