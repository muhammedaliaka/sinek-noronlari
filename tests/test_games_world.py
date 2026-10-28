"""Oyun fiziği (docs/dort_koku_oyunu_plani.md G1): sıfır-sızıntı, temas sırası, yerleşim değişmezleri, RNG ayrımı, bilgi sınırı, CRN."""
import math

import numpy as np
import pytest
import torch

from sinek import Config, MushroomBodyBrain
from sinek.agent import Creature
from sinek.games import GAMES, GameWorld, NullBrain, ReferenceBrain, fields
from sinek.games.world import REARM_MARGIN

ANT_REACH = math.hypot(0.6, 1.2)      # gövde merkezinden en uzak anten (varsayılan anten ofsetleri)


def make(cfg, game, batch=8, seed=3, brain="null", test=True, swap=None):
    w = GameWorld(cfg.world, GAMES[game], batch, seed)
    if swap is not None:
        w.set_swap(swap)
    w.reset_game(test=test)
    b = NullBrain(batch) if brain == "null" else MushroomBodyBrain(cfg.brain, batch, seed, "cpu", cfg.world.dt, cfg.substeps)
    return Creature(cfg, b, w)


# ------------------------------------------------------------------ alan fonksiyonları
def test_bump_exact_zero_outside_support_and_c2_edge():
    R = 5.0
    d = torch.cat([torch.rand(200_000) * 60, torch.tensor([R, R + 1e-6, R * 1.0000001, 100.0, 1e6])])
    c = fields.bump(d, R)
    assert bool((c[d >= R] == 0.0).all())
    assert bool((c[d < R] > 0.0).all())
    assert float(fields.bump(torch.tensor([R - 1e-3]), R)) < 1e-9            # C² kenar: değer ve türevler ~0
    assert float(fields.bump(torch.tensor([0.0]), R, amp=2.0)) == 2.0


def test_trail_zero_outside_tube_matches_bruteforce_and_increases_toward_target():
    rng = np.random.default_rng(0)
    poly = torch.tensor([[[5.0, 5.0], [20.0, 30.0], [35.0, 10.0]]])         # (1,3,2) tek dönüşlü
    pts = torch.tensor(rng.uniform(-5, 45, size=(1, 4000, 2)), dtype=torch.float32)
    n, rem = fields.polyline_geometry(pts, poly)
    P, Q = poly[0, :-1].numpy(), poly[0, 1:].numpy()
    best_n = np.full(4000, np.inf); best_rem = np.zeros(4000)
    seg_len = np.linalg.norm(Q - P, axis=1)
    for k in range(2):
        ab = Q[k] - P[k]
        t = np.clip(((pts[0].numpy() - P[k]) @ ab) / (ab @ ab), 0, 1)
        proj = P[k] + t[:, None] * ab
        dist = np.linalg.norm(pts[0].numpy() - proj, axis=1)
        rem_k = (1 - t) * seg_len[k] + seg_len[k + 1:].sum()
        better = dist < best_n
        best_n[better], best_rem[better] = dist[better], rem_k[better]
    assert np.allclose(n[0].numpy(), best_n, atol=1e-4) and np.allclose(rem[0].numpy(), best_rem, atol=1e-3)
    c = fields.trail(pts, poly, width=4.0, lam=12.0)
    assert bool((c[0][n[0] >= 4.0] == 0.0).all()) and bool((c[0][n[0] < 4.0] >= 0).all())
    axis = torch.tensor([[[6.0, 7.0], [10.0, 15.0], [20.0, 30.0], [28.0, 20.0], [34.0, 11.0]]])   # iz üstünde, hedefe doğru
    ca = fields.trail(axis, poly, width=4.0, lam=12.0)[0]
    assert bool((ca[1:] > ca[:-1]).all())


# ------------------------------------------------------------------ yerleşim değişmezleri
@pytest.mark.parametrize("game", list(GAMES))
def test_layout_invariants_and_mirror_pairs(cfg, game):
    sp, L = GAMES[game], cfg.world.arena
    for seed in range(5):
        w = GameWorld(cfg.world, sp, 64, seed)
        s, tg, dc = w.pos, w.src_pos[:, 0], w.src_pos[:, 1]
        assert bool(((s >= sp.start_margin) & (s <= L - sp.start_margin)).all())
        if sp.target.active:
            assert bool(((tg >= sp.src_margin) & (tg <= L - sp.src_margin)).all())
            if sp.start != "ring":
                assert float((s - tg).norm(dim=-1).min()) >= sp.dmin
        if sp.decoy.active:
            assert float((s - dc).norm(dim=-1).min()) >= sp.dmin
        if sp.target.active and sp.decoy.active:
            assert float((tg - dc).norm(dim=-1).min()) >= sp.dmin
        # ayna çiftleri: eleman 2k+1 = eleman 2k'nın x-aynası
        assert torch.allclose(s[1::2, 0], L - s[0::2, 0]) and torch.equal(s[1::2, 1], s[0::2, 1])
        assert torch.allclose(torch.cos(w.heading[1::2]), -torch.cos(w.heading[0::2]), atol=1e-5)
        assert torch.allclose(torch.sin(w.heading[1::2]), torch.sin(w.heading[0::2]), atol=1e-5)
        if sp.target.active:
            assert torch.allclose(tg[1::2, 0], L - tg[0::2, 0])
        if sp.bend is not None:
            assert bool(((w.poly >= 2.0) & (w.poly <= L - 2.0)).all())


def test_layout_is_independent_of_noise_stream_and_reproducible(cfg):
    a, b = GameWorld(cfg.world, GAMES["O4c"], 16, 9), GameWorld(cfg.world, GAMES["O4c"], 16, 9)
    torch.randn(1000, generator=b.noise_gen)                   # gürültü akışını tüket: yerleşim etkilenmemeli
    a.reset_game(); b.reset_game()
    assert torch.equal(a.pos, b.pos) and torch.equal(a.src_pos, b.src_pos) and torch.equal(a.heading, b.heading)
    c = GameWorld(cfg.world, GAMES["O4c"], 16, 10)
    assert not torch.equal(a.pos, c.pos)


def test_o2_start_is_outside_every_antenna_reach(cfg):
    for game in ("O2full", "O2near"):
        sp = GAMES[game]
        w = GameWorld(cfg.world, sp, 256, 1)
        R = sp.target.radius
        assert float((w.pos - w.src_pos[:, 0]).norm(dim=-1).min()) > R + ANT_REACH      # başlangıçta her yönelimde C=0
        s = w.sense()
        assert float(s.abs().max()) == 0.0


def test_o2near_all_headings_start_with_zero_odor(cfg):
    w = GameWorld(cfg.world, GAMES["O2near"], 8, 2)
    for h in np.linspace(0, 2 * np.pi, 73):
        w.heading[:] = float(h)
        assert float(w.sense().abs().max()) == 0.0


# ------------------------------------------------------------------ sıfır-sızıntı ve temas sırası
def test_o3_prefield_is_exactly_zero_whole_trial_and_odor_follows_contact(cfg):
    c = make(cfg, "O3", batch=64, seed=4, test=False)
    w = c.world
    w.set_arms(torch.ones(64, dtype=torch.bool), torch.ones(64, dtype=torch.bool))
    first_nonzero = torch.full((64,), -1)
    contact_seen_step = torch.full((64,), -1)
    for k in range(int(round(40.0 / cfg.world.dt))):
        g = w.sense()
        nz = g.flatten(1).abs().sum(-1) > 0
        first_nonzero[nz & (first_nonzero < 0)] = k
        c.step(learn=False)
        newly = (w.first_contact_slot >= 0) & (contact_seen_step < 0)
        contact_seen_step[newly] = k
        if bool(w.done.all()):
            break
    hit = contact_seen_step >= 0
    assert int(hit.sum()) > 5                                   # test anlamlı: yeterince temas oldu
    # temasa dek glom ≡ 0; koku temas adımından ENAZ BİR adım sonra görülür (sözleşme)
    assert bool((first_nonzero[~hit] < 0).all())
    assert bool((first_nonzero[hit] == contact_seen_step[hit] + 1).all())
    assert bool((w.first_odor_step < 0).all())                  # alandan hiç koku gelmedi


def test_o3_arms_control_reward_and_contact_odor(cfg):
    for reward_on, odor_on in [(True, True), (True, False), (False, True), (False, False)]:
        c = make(cfg, "O3", batch=2, seed=1, test=False)
        w = c.world
        w.set_arms(torch.tensor([reward_on] * 2), torch.tensor([odor_on] * 2))
        w.pos[:] = w.src_pos[:, 0] + torch.tensor([0.5, 0.0])
        assert float(w.sense().abs().max()) == 0.0
        w.step(torch.zeros(2), 0.0)                              # temas bu adımda saptanır
        taste, touch = w.taste_touch()
        assert bool((touch == 1).all()) and bool((taste == (1.0 if reward_on else 0.0)).all())
        assert (float(w.sense().max()) > 0.9) == odor_on


def test_anosmic_zeroes_everything_and_field_events_still_recorded(cfg):
    c = make(cfg, "O2near", batch=4, seed=2)
    w = c.world
    w.set_anosmic(torch.tensor([True, False, True, False]))
    w.pos[:] = w.src_pos[:, 0] + torch.tensor([2.0, 0.0])        # bölgenin içinde
    g = w.sense()
    assert float(g[0].abs().max()) == 0.0 and float(g[1].abs().max()) > 0
    assert bool((w.first_odor_step >= 0).all())                  # olay ikisinde de kaydedildi (anosmikte de)


def test_decoy_touch_has_no_reward_and_rearms(cfg):
    c = make(cfg, "O4a", batch=2, seed=1, test=False)
    w = c.world
    w.pos[:] = w.src_pos[:, 1] + torch.tensor([0.5, 0.0])
    w.step(torch.zeros(2), 0.0)
    taste, touch = w.taste_touch()
    assert bool((touch == 1).all()) and bool((taste == 0).all()) and bool((w.contact_count[:, 1] == 1).all())
    for _ in range(25):                                          # yeme süresi boyunca yeniden temas sayılmaz
        w.step(torch.zeros(2), 0.0)
    assert bool((w.contact_count[:, 1] == 1).all()) and not bool(w.done.any())
    w.pos[:] = w.src_pos[:, 1] + torch.tensor([1.5 + REARM_MARGIN + 0.5, 0.0])
    w.step(torch.zeros(2), 0.0)                                  # yeterince uzaklaşınca yeniden etkinleşir
    w.pos[:] = w.src_pos[:, 1] + torch.tensor([0.5, 0.0])
    w.step(torch.zeros(2), 0.0)
    assert bool((w.contact_count[:, 1] == 2).all())


def test_test_mode_first_contact_ends_trial_and_records_slot(cfg):
    c = make(cfg, "O4c", batch=2, seed=1, test=True)
    w = c.world
    w.pos[:] = w.src_pos[:, 1] + torch.tensor([0.5, 0.0])
    w.step(torch.zeros(2), 0.0)
    assert bool(w.done.all()) and bool((w.first_contact_slot == 1).all())
    p = w.pos.clone()
    w.step(torch.zeros(2), 8.0)
    assert torch.equal(p, w.pos)                                  # bitti: hareket yok
    out = w.outcome()
    assert bool((out["slot"] == 1).all()) and not bool(torch.isnan(out["time"]).any())


def test_target_contact_in_train_mode_finishes_after_feeding(cfg):
    c = make(cfg, "O1R", batch=2, seed=1, test=False)
    w = c.world
    w.pos[:] = w.src_pos[:, 0] + torch.tensor([0.5, 0.0])
    w.step(torch.zeros(2), 0.0)
    assert not bool(w.done.any()) and bool((w.feed_timer > 0).all())
    for _ in range(int(round(cfg.world.feed_time / cfg.world.dt)) + 2):
        w.step(torch.zeros(2), 0.0)
    assert bool(w.done.all())


# ------------------------------------------------------------------ bilgi sınırı ve RNG
def test_brain_receives_only_glom_taste_touch(cfg):
    calls = []

    class Spy(NullBrain):
        def step(self, *args, **kw):
            calls.append((args, kw))
            return super().step(*args, **kw)

    w = GameWorld(cfg.world, GAMES["O1a"], 4, 1)
    cr = Creature(cfg, Spy(4), w)
    cr.step(learn=False)
    (args, kw), = calls
    assert len(args) == 3 and set(kw) == {"learn"}
    glom, taste, touch = args
    assert glom.shape == (4, 2, cfg.world.n_glom) and taste.shape == (4,) and touch.shape == (4,)


def test_noise_stream_is_separate_from_layout_stream(cfg):
    c = make(cfg, "O3", batch=4, seed=6)
    st = c.world.layout_gen.get_state().clone()
    for _ in range(50):
        c.step(learn=False)
    assert torch.equal(st, c.world.layout_gen.get_state())       # adımlar yerleşim akışını tüketmez


def test_crn_odor_and_anosmic_arms_identical_until_first_odor(cfg):
    T = 150
    runs = []
    for anos in (False, True):
        c = make(cfg, "O2near", batch=8, seed=11, brain="snn", test=True)
        c.world.set_anosmic(torch.full((8,), anos))
        hist = [c.world.pos.clone()]
        for _ in range(T):
            c.step(learn=False)
            hist.append(c.world.pos.clone())
        runs.append((torch.stack(hist), c.world.first_odor_step.clone()))
    (pa, fa), (pb, fb) = runs
    assert torch.equal(fa, fb)                                    # alan olayları iki kolda aynı yerde
    saw = fa >= 0
    assert int(saw.sum()) >= 2                                    # test boş değil: koku alınan canlılar var
    for i in range(8):
        k = int(fa[i]) if fa[i] >= 0 else T
        assert torch.equal(pa[: k + 1, i], pb[: k + 1, i])        # ilk koku alımına dek bit-bit aynı
    assert any(not torch.equal(pa[:, i], pb[:, i]) for i in range(8) if saw[i])   # sonra ayrışabiliyor (bozulmamış yapı)


# ------------------------------------------------------------------ iki bağımsız uygulamanın çapraz doğrulaması
def test_blind_agents_match_independent_numpy_simulation(cfg):
    from sinek.experiments.games_blind_check import blind_search

    T, n = 30.0, 2000
    ref = blind_search(n=20000, dmin=14.0, t_max=T, seed=5, target_margin=6.0)
    w = GameWorld(cfg.world, GAMES["O2full"], n, 21)
    c = Creature(cfg, NullBrain(n), w)
    c.run(T, learn=False, stop_when_done=True)
    p_hit_world = float((w.first_contact_slot >= 0).float().mean())
    p_enter_world = float((w.first_odor_step >= 0).float().mean())
    p_hit_ref = float(np.mean(ref["hit_time"] <= T))
    p_enter_ref = float(np.mean(ref["enter_time"][5.0] <= T))
    assert abs(p_hit_world - p_hit_ref) < 0.04
    assert abs(p_enter_world - p_enter_ref) < 0.04
    # ayna simetrisi: ayna yarılarında kör başarı eşit (duvar gizli işaret olmasın, Z-04)
    hit = (w.first_contact_slot >= 0).float()
    assert abs(float(hit[0::2].mean()) - float(hit[1::2].mean())) < 0.05
