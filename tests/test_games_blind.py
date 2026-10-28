"""Kör gezgin hesabı (docs/dort_koku_oyunu_plani.md Z-02): tavan etkisi bulgusunu sabitler."""
import numpy as np

from sinek.experiments.games_blind_check import blind_search, table


def test_blind_search_ceiling_at_60s_and_headroom_at_short_limits():
    res = blind_search(n=3000, dmin=14.0, t_max=60.0, seed=3)
    rows = {r["T"]: r for r in table(res, (20, 30, 60))}
    # 60 sn'de kör başarı yüksek (≈0.58), kısa sınırda düşük: süre sınırı kör başarıyı 0.20-0.40 aralığına çekmeli
    assert 0.50 < rows[60]["p_hit"] < 0.66
    assert 0.18 < rows[20]["p_hit"] < 0.30
    assert 0.28 < rows[30]["p_hit"] < 0.40
    # R=5 bölgesine kör giriş 60 sn'de neredeyse kesin (tavan)
    assert rows[60]["p_enter_R5"] > 0.92
    # monotonluk
    assert rows[20]["p_hit"] < rows[30]["p_hit"] < rows[60]["p_hit"]


def test_blind_search_is_deterministic_and_zone_entry_precedes_hit():
    a = blind_search(n=500, t_max=20.0, seed=7)
    b = blind_search(n=500, t_max=20.0, seed=7)
    assert np.array_equal(a["hit_time"], b["hit_time"])
    hit = np.isfinite(a["hit_time"])
    assert np.all(a["enter_time"][5.0][hit] <= a["hit_time"][hit])   # temas yarıçapı (1.5) < bölge: önce giriş
