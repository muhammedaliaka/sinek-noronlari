"""kuram_iki_zaman: soyut öğrenici — biçim, tohum belirlenimi, sıfır-etki (öğrenmeyen = şans), bilinen etki (hızlı öğrenen şansı geçer)."""
import numpy as np

from sinek.experiments import kuram_iki_zaman as K


def test_shape_determinism_and_known_effects():
    a = K.play("tek", {"a_slow": 0.5}, 2000, np.random.default_rng(1))
    b = K.play("tek", {"a_slow": 0.5}, 2000, np.random.default_rng(1))
    assert a.shape == (2000, 40) and np.array_equal(a, b)
    none = K.summarize(K.play("tek", {"a_slow": 0.0}, 4000, np.random.default_rng(2)))          # öğrenmeyen: seçim 0,5 → ödül ≈ (0,8+0,2)/2
    assert abs(none["üçü ortalama"] - 0.5) < 0.03
    fast = K.summarize(K.play("tek", {"a_slow": 0.5}, 4000, np.random.default_rng(3)))
    assert fast["geç faz-1 (11-20)"] > 0.65 and fast["geç faz-2 (31-40)"] > 0.65               # bilinen etki: öğrenir ve tersine çevirmeden sonra yeniden öğrenir
