import json

import pytest

from sinek.experiments import altin_kosu


@pytest.fixture
def tiny(monkeypatch):
    monkeypatch.setattr(altin_kosu, "N_CREAT", 2)
    monkeypatch.setattr(altin_kosu, "ACQ", 1)
    monkeypatch.setattr(altin_kosu, "STEPS", 20)
    monkeypatch.setattr(altin_kosu, "REW", (8, 16))


def test_same_device_repeat_is_bit_identical(tiny):
    a, b = altin_kosu.one_run("cpu", 0), altin_kosu.one_run("cpu", 0)
    assert all(a[k] == b[k] for k in ("sel", "dw", "kc_active"))


def test_check_rejects_out_of_tolerance_reference(tiny, tmp_path):
    r = altin_kosu.one_run("cpu", 0)
    good = {k: {"mean": r[k], "sd": 0.0, "by_seed": [r[k]]} for k in altin_kosu.MIN_TOL}
    p = tmp_path / "ref.json"
    p.write_text(json.dumps(good))
    altin_kosu.main(["--device", "cpu", "--check", str(p)])           # kendi referansına karşı geçer
    bad = {k: {"mean": r[k] + 1.0, "sd": 0.0, "by_seed": [0.0]} for k in altin_kosu.MIN_TOL}
    p.write_text(json.dumps(bad))
    with pytest.raises(SystemExit):
        altin_kosu.main(["--device", "cpu", "--check", str(p)])
