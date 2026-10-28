"""Kör (kokusuz) gezginin hedefi bulma olasılığı: `World` fiziğinin sayısal kopyası (kuram/hesap kontrolü, R-8).

    python -m sinek.experiments.games_blind_check --n 20000 --dmin 14

Amaç (docs/dort_koku_oyunu_plani.md, Z-02): oyun süre sınırını, kör başarının tavana/tabana yapışmayacağı bir değere ayarlamak
ve O2 koku bölgesine kör girişin ölçeğini bilmek. Hareket modeli `agent.Creature.motor` ile `World.step`'in kokusuz özetidir:
sabit hız, yönelimde `wander_sigma*sqrt(dt)` Gauss adımı, duvarda yansıma + kıstırma. Beyin yoktur.

Bu betik `GameWorld` ile **çapraz doğrulanır** (tests/test_games_world.py): iki bağımsız uygulama aynı sayıları vermelidir.
"""
from __future__ import annotations

import argparse

import numpy as np

from ..config import MotorConfig, WorldConfig

ZONES = (3.0, 5.0, 8.0)
T_GRID = (10, 15, 20, 30, 45, 60, 90, 120)


def blind_search(n: int = 20000, dmin: float = 14.0, t_max: float = 120.0, seed: int = 1, margin: float = 3.0,
                 target_margin: float | None = None, zones=ZONES, world: WorldConfig | None = None,
                 motor: MotorConfig | None = None) -> dict:
    """Her deneme için ilk hedef-temas süresi ve (anten tabanlı) bölgeye ilk giriş süresi (bulunamazsa inf)."""
    w, m = world or WorldConfig(), motor or MotorConfig()
    rng = np.random.default_rng(seed)
    L, dt = w.arena, w.dt
    tm = margin if target_margin is None else target_margin
    tgt = tm + (L - 2 * tm) * rng.random((n, 2))
    start = margin + (L - 2 * margin) * rng.random((n, 2))
    bad = np.linalg.norm(start - tgt, axis=1) < dmin
    while bad.any():
        start[bad] = margin + (L - 2 * margin) * rng.random((int(bad.sum()), 2))
        bad = np.linalg.norm(start - tgt, axis=1) < dmin
    pos, head = start.copy(), rng.random(n) * 2 * np.pi
    hit = np.full(n, np.inf)
    enter = {R: np.full(n, np.inf) for R in zones}
    sig = m.wander_sigma * np.sqrt(dt)
    for k in range(int(round(t_max / dt))):
        d = np.stack([np.cos(head), np.sin(head)], -1)
        perp = np.stack([-d[:, 1], d[:, 0]], -1)
        base = pos + w.antenna_fwd * d
        d_min_ant = np.minimum(np.linalg.norm(base + w.antenna_side * perp - tgt, axis=1),
                               np.linalg.norm(base - w.antenna_side * perp - tgt, axis=1))
        for R, e in enter.items():
            e[(d_min_ant < R) & np.isinf(e)] = k * dt
        head = head + sig * rng.standard_normal(n)
        pos = pos + m.speed * dt * np.stack([np.cos(head), np.sin(head)], -1)
        hx = (pos[:, 0] < 0) | (pos[:, 0] > L)
        hy = (pos[:, 1] < 0) | (pos[:, 1] > L)
        head = np.where(hx, np.pi - head, head)
        head = np.where(hy, -head, head)
        pos = np.clip(pos, 0.0, L)
        hit[(np.linalg.norm(pos - tgt, axis=1) < w.contact_radius) & np.isinf(hit)] = (k + 1) * dt
    return {"hit_time": hit, "enter_time": enter}


def table(res: dict, t_grid=T_GRID) -> list[dict]:
    rows = []
    for t in t_grid:
        row = {"T": t, "p_hit": float(np.mean(res["hit_time"] <= t))}
        for R, e in res["enter_time"].items():
            row[f"p_enter_R{int(R)}"] = float(np.mean(e <= t))
        rows.append(row)
    return rows


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--dmin", type=float, default=14.0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    res = blind_search(a.n, a.dmin, seed=a.seed)
    print(f"kör gezgin, n={a.n}, başlangıç–hedef ≥ {a.dmin}")
    for r in table(res):
        print(f"T={r['T']:4d} sn  p_hit={r['p_hit']:.3f}  " + "  ".join(f"p_giriş(R={R})={r[f'p_enter_R{R}']:.3f}" for R in (3, 5, 8)))


if __name__ == "__main__":
    main()
