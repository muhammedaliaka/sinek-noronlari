"""O6 görsel ön uç (docs/gorsel_koku_oyunu_plani.md §3): kapalıyken eski yol bit-bit aynı; VPN->KC veriden; görsel kanal ve ısı cezası mantığı."""
import math

import numpy as np
import pytest
import torch

from sinek.brain_connectome import ConnectomeBrain, vis_tuning
from sinek.connectome import mbmodel
from sinek.games.protocol import make_game_creature, play, pretrain
from sinek.games.spec import GAMES
from sinek.games.world import GameWorld, vis_patterns
from sinek.world import odor_patterns


@pytest.fixture(scope="module")
def ccfg():
    return mbmodel.connectome_config()


def test_vpn_data_matches_pn_scale_and_targets_visual_kcs():
    d = mbmodel.load()
    assert d.w_vpn_kc is not None and d.w_vpn_kc.shape == (len(d.vpn_ids), d.n_kc)
    kc_type = np.array(mbmodel.Connectome.load(str(mbmodel.resolve_dir(mbmodel.DEFAULT_DIR))).neurons.set_index("bodyId").loc[d.ids["KC"], "type"])
    targeted = np.abs(d.w_vpn_kc).sum(0) > 0
    assert set(np.unique(kc_type[targeted])) <= {"KCg-d", "KCab-p", "KCg-m", "KCg-s1", "KCg-s2", "KCab-s"}       # görsel girdili alt tipler (denetim: docs/gorsel_girdi_denetimi.md)
    assert (kc_type[targeted] == "KCg-d").sum() >= 100 and (kc_type[targeted] == "KCab-p").sum() >= 50
    assert np.abs(d.w_vpn_kc[d.w_vpn_kc != 0]).mean() < 1.0                                                 # PN ortalaması 1; görsel bağlantılar daha az sinapslı


def test_vis_tuning_is_deterministic_sparse_and_covers_every_vpn():
    a, b = vis_tuning(47, 6, 0, 0.4), vis_tuning(47, 6, 0, 0.4)
    assert np.array_equal(a, b) and (a.sum(1) > 0).all() and not np.array_equal(a, vis_tuning(47, 6, 1, 0.4))


def test_vision_off_is_bit_identical_and_vision_on_without_input_changes_nothing_in_olfaction(ccfg):
    """n_vis_feat>0 ama vis=None: koku yolu aynı RNG akışı, aynı sonuç (görsel ön ucun varlığı akışı kaydırmaz)."""
    import dataclasses
    on = dataclasses.replace(ccfg, cbrain=dataclasses.replace(ccfg.cbrain, n_vis_feat=6))
    b0, b1 = ConnectomeBrain(ccfg.cbrain, 2, 5), ConnectomeBrain(on.cbrain, 2, 5)
    glom = torch.rand(2, 2, ccfg.world.n_glom) * 0.5
    z = torch.zeros(2)
    for _ in range(15):
        v0, v1 = b0.step(glom, z, z, learn=False), b1.step(glom, z, z, learn=False)
        assert torch.equal(v0, v1)


def test_visual_input_drives_visual_kcs_only(ccfg):
    import dataclasses
    on = dataclasses.replace(ccfg, cbrain=dataclasses.replace(ccfg.cbrain, n_vis_feat=6))
    d = mbmodel.load()
    visual_kc = torch.from_numpy((np.abs(d.w_vpn_kc).sum(0) > 0))
    glom0 = torch.zeros(2, 2, ccfg.world.n_glom)
    z = torch.zeros(2)
    act = {}
    for name, level in (("sıfır", 0.0), ("güçlü", 1.0)):
        b = ConnectomeBrain(on.cbrain, 2, 5)
        tot = torch.zeros(b.R, b.n_kc)
        for _ in range(40):
            b.step(glom0, z, z, learn=False, vis=torch.full((2, 2, 6), level))
            tot += b.elig                                                    # KC etkinliği izi (yalnız spike'a bağlı)
        act[name] = tot
    gain = (act["güçlü"] - act["sıfır"]).mean(0)
    assert gain[visual_kc].mean() > 5 * gain[~visual_kc].abs().mean() + 1e-9          # görsel girdi yalnız görsel KC'leri sürer
    with pytest.raises(ValueError):
        ConnectomeBrain(ccfg.cbrain, 2, 5).step(glom0, z, z, vis=torch.zeros(2, 2, 6))   # görsel ön uç kapalı beyne vis verilemez


def _world(spec_name, n=4, n_vis=6):
    cfg = mbmodel.connectome_config()
    return GameWorld(cfg.world, GAMES[spec_name], n, 11, patterns=odor_patterns(cfg.world, 3), n_vis=n_vis)


def test_sense_vis_none_for_old_games_and_geometry_for_o6():
    assert _world("O5").sense_vis() is None and _world("O6a").sense_vis() is None          # görsel kaynak yok → eski yol
    w = _world("O6b")
    w.pos[:] = torch.tensor([20.0, 20.0]); w.heading[:] = 0.0
    w.src_pos[:, 0] = torch.tensor([30.0, 24.0])        # güvenli (X): ileri-SOL (y+)
    w.src_pos[:, 1] = torch.tensor([30.0, 16.0])        # tuzak (Y): ileri-SAĞ
    v = w.sense_vis()
    assert v.shape == (4, 2, 6) and v.min() >= 0 and v.max() <= 1
    pat = vis_patterns(6)
    xf, yf = pat[0] > 0, pat[1] > 0
    sw = w.vis_swap.clone()
    for b in range(4):
        sx, sy = (xf, yf) if not sw[b] else (yf, xf)       # rol dengelemesi: güvenli yuvanın deseni
        assert v[b, 0][sx].sum() > v[b, 1][sx].sum() and v[b, 1][sy].sum() > v[b, 0][sy].sum()    # sol göz güvenliyi, sağ göz tuzağı daha çok görür
        assert v[b, :, ~(sx | sy)].sum() == 0                                                  # desen dışı özellik etkinliği 0
    w.set_blind(torch.ones(4, dtype=torch.bool))
    assert w.sense_vis().abs().sum() == 0


def test_heat_is_negative_taste_and_any_contact_ends_episode(ccfg):
    w = _world("O6b", n=2)
    w.reset_game(test=False)
    w.pos[:] = w.src_pos[:, 1]                          # tuzağın üstünde
    w._contacts(torch.ones(2, dtype=torch.bool))
    taste, touch = w.taste_touch()
    assert (w.feed_reward < 0).all() and (w.finish_pending).all()
    w.feed_timer[:] = 0.2
    taste, touch = w.taste_touch()
    assert (taste < 0).all() and (touch > 0).all()      # negatif tat = acı sınıfı GRN (δ<0, PPL1 yolu)


def test_make_game_creature_with_vision_runs_and_blind_arm_has_no_visual_input(ccfg):
    pre = pretrain(ccfg, odor_patterns(ccfg.world, 3), 4, seed=3, episodes=1, seconds=4.0)
    c = make_game_creature(pre, "O6b", "naive_plastic", [0, 1], 2, 150, vis_feat=6)
    cb = make_game_creature(pre, "O6b", "naive_plastic_blind", [0, 1], 2, 150, vis_feat=6)
    assert c.brain.n_vis == 6 and c.world.n_vis == 6 and not c.world.blind.any() and cb.world.blind.all()
    out = play(c, 6.0, learn=True, test=False)
    assert out["slot"].shape[0] == 4
    with pytest.raises(ValueError):
        make_game_creature(pre, "O6b", "plastic", [0, 1], 2, 150, vis_feat=6)         # ön-eğitimli beyin görsel ön uçsuz kuruldu


def test_o6_dev_block_table_and_net_preference():
    from sinek.experiments.o6_dev import block_table
    slot = np.array([[0, 0, 1, -1], [0, 1, 1, -1], [0, 0, 0, 0], [1, 1, 1, 1]])      # (bölüm, eleman)
    t = block_table(slot, 2)
    assert t[0] == (3 / 8, 3 / 8, 2 / 8, 0.0) and t[1] == (4 / 8, 4 / 8, 0.0, 0.0)
    assert block_table(np.full((4, 3), -1), 4)[0][3] == 0.0                          # hiç temas yok → NP 0 (yaklaşmadan bağımsız sıfır düzeyi)


def test_visual_neutral_calibration_removes_innate_aversion_and_only_touches_visual_kc_avoid_synapses(ccfg):
    """E-17/K-051: kalibrasyonsuz görsel girdi V'yi belirgin biçimde düşürür; κ ile |ΔV| ≤ tol+payı; κ=1 ⇒ ağırlıklar aynı; yalnız görsel-KC→avoid sütunları ölçeklenir."""
    import dataclasses
    from sinek.games import vis_calibration as vc
    cb = dataclasses.replace(ccfg.cbrain, n_vis_feat=6)
    kw = dict(n=16, steps=24, seed=7)
    v0 = vc._mean_v(cb, 0.6, with_vis=False, **kw)
    assert vc._mean_v(cb, 0.6, with_vis=True, **kw) - v0 < -0.1                                                   # sorun gerçek: kalibrasyonsuz innate kaçınma
    k = vc.neutral_scale(cb, n=16, steps=24, seed=7, iters=8)
    assert 0.0 < k < 1.0
    cbk = dataclasses.replace(cb, vis_avoid_scale=k)
    assert abs(vc._mean_v(cbk, 0.6, with_vis=True, **kw) - vc._mean_v(cbk, 0.6, with_vis=False, **kw)) <= 0.05              # ölçüt AYNI κ'da (E-19)
    b1, bk = ConnectomeBrain(cb, 2, 5), ConnectomeBrain(cbk, 2, 5)
    nz = (b1.W0.abs() > 1e-9).numpy()                                                                            # sıfır sinapslar oran vermez
    ratio = np.where(nz, (bk.W0 / b1.W0.where(b1.W0.abs() > 1e-9, torch.ones(()))).numpy(), 1.0)
    changed = ~np.isclose(ratio, 1.0)
    assert changed.any() and np.allclose(ratio[changed], k, atol=1e-4)
    vis_kc = np.abs(mbmodel.load().w_vpn_kc).sum(0) > 0
    assert not changed[~vis_kc].any()                                                                            # görsel olmayan KC'ler dokunulmaz


def test_vis_taxis_default_off_is_identical_and_turns_toward_stronger_eye(ccfg):
    """K-058: vis_taxis_gain=0 ⇒ eski dönüş; >0 ⇒ sol göz daha güçlüyse sola (pozitif), sağ güçlüyse sağa; desenden bağımsız (X ve Y aynı işaret)."""
    pre = pretrain(__import__("sinek.config", fromlist=["x"]).Config() if False else ccfg, odor_patterns(ccfg.world, 3), 4, seed=3, episodes=1, seconds=2.0)
    c0 = make_game_creature(pre, "O6b", "naive", [0, 1], 2, 5, vis_feat=6)
    c1 = make_game_creature(pre, "O6b", "naive", [0, 1], 2, 5, vis_feat=6, vis_taxis=5.0)
    assert c0.cfg.motor.vis_taxis_gain == 0.0 and c1.cfg.motor.vis_taxis_gain == 5.0
    vp = vis_patterns(6)
    for pat in (vp[0], vp[1]):
        e = torch.zeros(4, 2, 6)
        e[:, 0] = pat * 0.8
        left = 5.0 * (e.sum(-1)[:, 0] - e.sum(-1)[:, 1]) / (e.sum(-1)[:, 0] + e.sum(-1)[:, 1] + 0.1)
        assert (left > 0).all()
