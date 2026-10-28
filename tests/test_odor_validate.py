"""Doğrulayıcı koşucu (odor_validate): uçtan uca küçük koşu, rapor biçimi ve doğrulayıcı/pilot tohum koruması."""
import pytest

from sinek.experiments import odor_validate as OV
from sinek.experiments.odor_eval import Thr
from sinek.games.protocol import pretrain
from sinek.world import odor_patterns


def test_validate_end_to_end_small(cfg):
    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 4, seed=3, episodes=1, seconds=4.0)
    thr = Thr(n_boot=100, n_perm=100)
    r = OV.validate(pre, "O2near", 150, agents=4, trials=4, seconds=6.0, thr=thr, verbose=False)
    assert set(r["p_hit"]) == set(OV.ARMS) and r["leak"]["violations"] == 0
    text = OV.report(r, thr, {"stamp": "PİLOT", "pre": "x", "pre_sha": "0", "git": "0"})
    assert "Kapılar" in text and "Karar (bu tohum)" in text


def test_seed_guard(tmp_path):
    with pytest.raises(SystemExit):
        OV.main(["--pre", "yok.npz", "--game", "O1a", "--seed", "150", "--out", str(tmp_path)])          # 200 altı, --pilot yok
    with pytest.raises(SystemExit):
        OV.main(["--pre", "yok.npz", "--game", "O1a", "--seed", "210", "--pilot", "--out", str(tmp_path)])   # doğrulayıcı + pilot
