"""O6 (görsel + koku, ısı tuzağı) GELİŞTİRME pilotu (kanıt değildir; tohum <200): ardışık bölümlerde öğrenme eğrisi.

    python3 -I -m sinek.experiments.o6_dev --pre results/odor_games/pre_s102.npz --game O6b --seed 140 --arms naive_plastic,naive_plastic_blind,naive --out results/o6_dev/b140.md

Her eleman bağımsız bir yaşam (ÖĞRENMEMİŞ "naive" beyin; ağırlıklar bölümler arasında korunur). Yuva 0 = güvenli (ödül +1), yuva 1 = ısı tuzağı (−1); herhangi bir temas bölümü bitirir.
Çıktı (bloklar): güvenli ilk temas oranı / tuzak ilk temas oranı / temas-yok oranı ve NET TERCİH NP = güvenli − tuzak (temas yoksa 0; yaklaşmadan arındırılmış, E-15).
Kollar: naive_plastic (öğrenen; O6b/c'de görsel açık), naive_plastic_blind (görsel girdi sıfır; aynı beyin ve RNG tüketimi), naive (öğrenme kapalı). Görsel ön uç yalnız O6b/O6c oyunlarında açıktır (O6a koku-yalnız).

ÖNCEDEN YAZILMIŞ TAHMİN (R-8, 2026-10-30, koşudan önce; belirsizliği açık):
 O6a (yalnız koku; yuva 0 koku A ödül, yuva 1 koku B ısı): öğrenen kolda NP son blokta ≥ +0,30 (O5'te 0,8/0,2 olasılıkla ≈ +0,2…0,3 görülmüştü; burada ödül/ısı kesin olduğundan daha yüksek beklenir); naive (öğrenmesiz) ≈ 0 (|NP| < 0,10).
 O6b (iki yuvada AYNI koku; ayrım yalnız görsel X/Y): naive_plastic_blind NP ≈ 0 (|NP| < 0,10; bilgi yok); naive_plastic (görsel) NP son blokta pozitif ama O6a'dan DÜŞÜK (görsel girdili KC ≈%8, VPN→KC bağlantıları PN'den ≈2× zayıf): NP ∈ [+0,10, +0,30].
 Yanlışlanma: görsel NP < +0,10 ise "görsel yol bu hâliyle yetersiz" (G-V0 ayrılabilirlik gösterse bile öğrenilen MBON okuması çok zayıf); NP ≥ O6a ise tahminim (görsel girdi daha zayıf) yanlış.
 Her iki durumda ayar sürüsü YAPILMAZ (E-08); önce kuram kontrolü ve karar defteri kaydı.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import ARMS, make_game_creature, play

VIS_GAMES = ("O6b", "O6c")


def run_arm(pre, game: str, arm: str, seed: int, agents: int, copies: int, episodes: int, seconds: float, n_vis: int = 6) -> np.ndarray:
    """(bölüm, eleman) ilk temas yuvası (−1 yok)."""
    ids = list(range(min(agents, pre.world.B)))
    c = make_game_creature(pre, game, arm, ids, copies, seed, vis_feat=n_vis if game in VIS_GAMES else 0)
    learn = ARMS[arm].eta > 0
    return np.stack([play(c, seconds, learn=learn, test=False)["slot"] for _ in range(episodes)])


def block_table(slot: np.ndarray, block: int) -> list[tuple[float, float, float, float]]:
    """Blok başına (güvenli, tuzak, temas-yok, NP)."""
    out = []
    for s in range(0, slot.shape[0], block):
        b = slot[s:s + block]
        safe, trap, none = float((b == 0).mean()), float((b == 1).mean()), float((b < 0).mean())
        out.append((safe, trap, none, safe - trap))
    return out


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--game", required=True, choices=["O6a", "O6b", "O6c"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--arms", default="naive_plastic,naive_plastic_blind,naive")
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--copies", type=int, default=2)
    ap.add_argument("--episodes", type=int, default=24)
    ap.add_argument("--block", type=int, default=4)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--n-vis", type=int, default=6)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.seed >= 200:
        raise SystemExit("geliştirme aracı: doğrulayıcı tohumları (≥200) yasak (R-2)")
    torch.set_num_threads(a.threads)
    pre = checkpoint.load(a.pre)
    t0 = time.time()
    nb = -(-a.episodes // a.block)
    L = [f"# {a.game} geliştirme pilotu (kanıt değildir)", "",
         f"{a.agents} canlı × {a.copies} kopya, {a.episodes} bölüm × {a.seconds:g} sn, oyun tohumu {a.seed}; kollar aynı dünyalarda (CRN).",
         "Hücre: güvenli / tuzak / temas-yok oranı → NP (= güvenli − tuzak). Bloklar bölüm sırasıyla.", "",
         "| kol | " + " | ".join(f"b{i + 1} ({i * a.block + 1}-{min((i + 1) * a.block, a.episodes)})" for i in range(nb)) + " |", "|---|" + "---|" * nb]
    for arm in a.arms.split(","):
        slot = run_arm(pre, a.game, arm, a.seed, a.agents, a.copies, a.episodes, a.seconds, a.n_vis)
        bl = block_table(slot, a.block)
        L.append(f"| {arm} | " + " | ".join(f"{s:.2f} / {t:.2f} / {n:.2f} → **{np_:+.2f}**" for s, t, n, np_ in bl) + " |")
        print(f"[{time.time() - t0:5.0f}s] {L[-1]}", flush=True)
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
