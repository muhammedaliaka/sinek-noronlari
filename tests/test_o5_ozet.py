"""o5_ozet: ön-kayıtlı hüküm kuralı (iki tohum da gerekir; biri geçip biri geçmezse KISMİ; eksik koşu BEKLİYOR, sessizce atlanmaz)."""
import json

from sinek.experiments import o5_ozet as O


def _run(passed: bool) -> dict:
    c = {k: {"mean": 0.12, "ci": [0.05, 0.2], "p": 0.001, "passed": passed} for k in O.CRIT}
    return {"eval": {"passed": passed, "gates_ok": True, "gates": {"referans_odul>=ref_min": True}, "criteria": c},
            "reward_rate": {"plastic": 0.4, "frozen": 0.25, "reference": 0.72}}


def test_verdict_rules():
    assert O.verdict({260: _run(True), 261: _run(True)}) == "BAŞARILI"
    assert O.verdict({260: _run(True), 261: _run(False)}).startswith("KISMİ")
    assert O.verdict({260: _run(False), 261: _run(False)}) == "BAŞARISIZ"
    assert O.verdict({260: _run(True), 261: None}) == "BEKLİYOR"
    assert O.verdict({260: _run(False), 261: None}) == "BAŞARISIZ"          # biri geçemediyse karar artık değişemez
    assert O.verdict({260: None, 261: None}) == "BEKLİYOR"


def test_main_reads_dir_and_marks_missing(tmp_path):
    (tmp_path / "s260").mkdir()
    (tmp_path / "s260" / "results.json").write_text(json.dumps(_run(True)), encoding="utf-8")
    text = O.main(["--dir", str(tmp_path), "--out", str(tmp_path / "ozet.md")])
    assert "BEKLİYOR" in text and "260" in text and (tmp_path / "ozet.md").exists()
