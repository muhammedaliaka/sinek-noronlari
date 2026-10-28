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


def test_session_validator_end_to_end_small(cfg):
    """O3/O4: oturum doğrulayıcısı küçük ölçekte uçtan uca çalışır; snapshot(reps) test örneğini büyütür ve kolları aynı yerleşimde tutar."""
    from sinek.experiments import odor_validate_s as VS
    from sinek.games.protocol import make_game_creature, snapshot

    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 2, seed=3, episodes=1, seconds=4.0)
    thr = Thr(n_boot=100, n_perm=100)
    r3 = VS.run_o3(pre, 150, agents=2, copies=2, trials=2, seconds=4.0, verbose=False)
    assert set(r3["hits"]) == set(VS.O3_TOKENS) and r3["hits"]["plastic:A"].shape == (2, 4) and r3["field_seen_trials"] == 0
    assert VS.evaluate("O3", r3, 2, thr)["criteria"]
    r4 = VS.run_o4(pre, "O4a", 150, agents=2, copies=2, trials=2, seconds=4.0, test_reps=2, snap_eps=(1,), verbose=False)
    assert r4["slots"]["plastic"][2].shape == (2, 4) and 1 in r4["slots"]["plastic"] and 1 not in r4["slots"]["frozen"]
    assert "G4_cekim_odasi" in VS.evaluate("O4a", r4, 2, thr)["gates"]
    c = make_game_creature(pre, "O4a", "frozen", [0, 1], 2, 150)
    t = snapshot(c, 9, reps=4)
    assert t.world.B == c.world.B * 4 and t.world.swap.tolist() == c.world.swap.repeat_interleave(4).tolist()
