"""evre2 --set anahtar=değer geçersiz kılmaları."""
import pytest

from sinek.config import Config
from sinek.experiments.evre2 import apply_override


def test_bool_override_is_parsed_not_truthy():
    cfg = Config()
    assert cfg.cbrain.restore is True
    apply_override(cfg, "cbrain.restore=false")
    assert cfg.cbrain.restore is False
    apply_override(cfg, "cbrain.restore=True")
    assert cfg.cbrain.restore is True


def test_numeric_override_keeps_type():
    cfg = Config()
    apply_override(cfg, "cbrain.class_shuffle_seed=3")
    apply_override(cfg, "cbrain.eta=2.5")
    assert cfg.cbrain.class_shuffle_seed == 3 and isinstance(cfg.cbrain.class_shuffle_seed, int)
    assert cfg.cbrain.eta == 2.5


def test_bad_override_exits():
    cfg = Config()
    with pytest.raises(SystemExit):
        apply_override(cfg, "cbrain.restore=maybe")
    with pytest.raises(SystemExit):
        apply_override(cfg, "cbrain.yok=1")


def test_v2_refuses_to_run_without_frozen_motor_readout(monkeypatch):
    """V2_SET boşken (donmamış okuma) ve açık motor.* geçersiz kılması yokken Evre 2b koşusu başlamaz."""
    import pytest

    from sinek.experiments import evre2

    monkeypatch.setattr(evre2, "V2_SET", [])
    with pytest.raises(SystemExit):
        evre2.main(["--seed", "30", "--out", "/tmp/unused_evre2b_guard"], v2=True)
