"""O6b KAPALI ÇEVRİMDE ÖĞRENME ANI DENETİMİ (geliştirme tanısı, kanıt değildir; tohum < 200; K-058 açık ipucu iii).

    python3 -I -m sinek.experiments.o6_ogrenme_ani --pre results/odor_games/pre_s102.npz --seed 146 --out results/o6_dev/ani146.md

Soru: oyun döngüsünde öğrenme gerçekten TEMAS ANINDA ve DOĞRU İŞARETLE mi gerçekleşiyor? (R-4: sezgiye ters sonuçta önce yazılım hatası aranır.)
Her adımda, her eleman için brain.step'in W üzerinde yaptığı değişim ölçülür (dünya bilgisi yalnız ölçüm içindir; beyne verilmez):
  dApp / dAvo = Σ_k,m ΔW · sınıf ağırlığı (yaklaş / kaçın MBON sınıfı); net değer değişimi dNet = dApp·class_balance − dAvo  (V ile aynı işaret kuralı).
Beklenti (kuramdan, koşudan önce): güvenli temas (ödül +1) → dNet > 0; tuzak temas (−1) → dNet < 0; yeme penceresi dışında |ΔW| ≈ 0.
Çıktı: (1) olay başına işaret doğruluğu (bölüm blokları ayrı), (2) ΔW'nin yeme penceresi içi/dışı payı, (3) yeme anında δ'nın medyanı ve V'nin (temas öncesi / yeme sonu) değişimi,
(4) güvenli ve tuzak olaylarında dNet büyüklükleri (asimetri), (5) ilk bölümlerde aynı sayılar.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import make_game_creature


def instrument(c, log: dict) -> None:
    brain, world = c.brain, c.world
    orig = brain.step
    cls = brain.cls_w                                  # (n_mbon, 2)
    cb = float(brain.cfg.class_balance)
    H = 2

    def step(glom, taste, touch, learn=True, **kw):
        W0 = brain.W.clone()
        eating = (world.feed_timer > 0)                # adım başında yeme penceresi (dünya taste_touch bunu kullanır)
        v = orig(glom, taste, touch, learn=learn, **kw)
        dW = (brain.W - W0)                            # (R, n_kc, n_mbon)
        dc = torch.einsum("rkm,mc->rc", dW, cls)       # (R, 2)
        dnet = (cb * dc[:, 0] - dc[:, 1]).view(-1, H).sum(1)          # (B,)
        mag = dW.abs().sum((1, 2)).view(-1, H).sum(1)                 # (B,)
        log["dnet"].append(dnet); log["mag"].append(mag); log["eat"].append(eating.clone())
        log["delta"].append(brain.last_delta.view(-1, H).mean(1))
        log["val"].append(v.mean(1)); log["active"].append(~world.done)
        return v
    brain.step = step


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=12)
    ap.add_argument("--copies", type=int, default=2)
    ap.add_argument("--episodes", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--reward-target", type=float, default=None)
    ap.add_argument("--vis-taxis", type=float, default=0.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.seed >= 200:
        raise SystemExit("geliştirme aracı: doğrulayıcı tohumları (≥200) yasak (R-2)")
    torch.set_num_threads(1)
    pre = checkpoint.load(a.pre)
    c = make_game_creature(pre, "O6b", "naive_plastic", list(range(min(a.agents, pre.world.B))), a.copies, a.seed, vis_feat=6, vis_taxis=a.vis_taxis, reward_target=a.reward_target)
    log = {k: [] for k in ("dnet", "mag", "eat", "delta", "val", "active")}
    instrument(c, log)
    ev = []         # (bölüm, eleman, slot, dnet_yeme, mag_yeme, mag_dışı, delta_med, v_önce, v_sonra, n_yeme)
    for ep in range(a.episodes):
        for k in log:
            log[k].clear()
        c.reset_episode("game", test=False)
        c.run(a.seconds, learn=True, stop_when_done=True)
        slot = c.world.outcome()["slot"].cpu().numpy()
        T = len(log["dnet"])
        if T == 0:
            continue
        S = {k: torch.stack(v).cpu().numpy() for k, v in log.items()}     # (T, B)
        for b in range(S["dnet"].shape[1]):
            e = S["eat"][:, b]
            if slot[b] < 0 or not e.any():
                ev.append((ep, b, int(slot[b]), np.nan, np.nan, float(S["mag"][:, b].sum()), np.nan, np.nan, np.nan, 0))
                continue
            i0 = int(np.argmax(e))
            ev.append((ep, b, int(slot[b]), float(S["dnet"][e, b].sum()), float(S["mag"][e, b].sum()), float(S["mag"][~e, b].sum()),
                       float(np.median(S["delta"][e, b])), float(S["val"][max(0, i0 - 5):i0 + 1, b].mean()), float(S["val"][e, b][-1]), int(e.sum())))
        print(f"bölüm {ep + 1}/{a.episodes}: temas {(slot >= 0).mean():.2f}", flush=True)
    E = np.array(ev, dtype=float)
    L = ["# O6b kapalı çevrimde öğrenme anı denetimi (geliştirme tanısı, kanıt değil)", "",
         f"tohum {a.seed}, {a.agents}×{a.copies} canlı, {a.episodes} bölüm × {a.seconds:g} sn; T={a.reward_target}, refleks={a.vis_taxis}.", ""]
    contact = ~np.isnan(E[:, 3])
    mag_in, mag_out = np.nansum(E[:, 4]), np.nansum(E[:, 5])
    L += [f"* Temas olayı: {int(contact.sum())} / {len(E)} eleman-bölümü. ΔW büyüklüğünün yeme penceresindeki payı: **{mag_in / max(mag_in + mag_out, 1e-12):.3f}** (pencere dışı |ΔW| payı {mag_out / max(mag_in + mag_out, 1e-12):.3f}).", ""]
    L += ["| bölüm bloğu | yuva | olay | dNet>0 oranı | dNet medyan | δ medyan | V önce | V yeme sonu | yeme adımı |", "|---|---|---|---|---|---|---|---|---|"]
    for lo, hi in ((0, 2), (2, 4), (4, a.episodes)):
        for slot, name in ((0, "güvenli(+)"), (1, "tuzak(−)")):
            m = contact & (E[:, 0] >= lo) & (E[:, 0] < hi) & (E[:, 2] == slot)
            if not m.any():
                continue
            x = E[m]
            good = (x[:, 3] > 0) if slot == 0 else (x[:, 3] < 0)
            L.append(f"| {lo + 1}-{hi} | {name} | {int(m.sum())} | doğru işaret **{good.mean():.2f}** | {np.median(x[:, 3]):+.3g} | {np.median(x[:, 6]):+.3f} | {np.nanmean(x[:, 7]):+.3f} | {np.nanmean(x[:, 8]):+.3f} | {np.median(x[:, 9]):.0f} |")
    # geçiş tablosu: aynı yaşamın bir önceki bölümde İLK temas ettiği yuva → bu bölümde ilk temas (yuva: 0 güvenli, 1 tuzak, −1 yok); NP katkısı
    n_b = int(E[:, 1].max()) + 1
    sl = np.full((a.episodes, n_b), -9.0)
    for r in E:
        sl[int(r[0]), int(r[1])] = r[2]
    L += ["", "**Geçiş tablosu** (satır: önceki bölümde ilk temas; sütun: sonraki bölümde ilk temas; yüzde satır içi):", "", "| önceki → sonraki | güvenli | tuzak | yok | n |", "|---|---|---|---|---|"]
    for prev, name in ((0, "güvenli(+)"), (1, "tuzak(−)"), (-1, "temas yok")):
        nxt = [sl[e + 1, b] for e in range(a.episodes - 1) for b in range(n_b) if sl[e, b] == prev and sl[e + 1, b] > -9]
        if nxt:
            nxt = np.array(nxt)
            L.append(f"| {name} | {(nxt == 0).mean():.2f} | {(nxt == 1).mean():.2f} | {(nxt < 0).mean():.2f} | {len(nxt)} |")
    L += ["", "Bölüm başına NP (güvenli − tuzak oranı, tüm elemanlar): " + ", ".join(f"{((sl[e] == 0).mean() - (sl[e] == 1).mean()):+.2f}" for e in range(a.episodes))]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    main()
