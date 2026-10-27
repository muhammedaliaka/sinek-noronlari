"""Ortak deney protokolü: canlı kurulumu, eğitim, seçim testi, istatistik.

Koşullar aynı batch içinde yan yana koşar (aynı kablolama, aynı dünya dağılımı):
  plastic : öğrenme açık
  frozen  : aynı deneyim, ama öğrenme kapalı (eta=0)
  random  : öğrenme açık, ama dönüş kazancı 0 (yalnızca rastgele gezinme)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
import torch

from ..agent import Creature
from ..brain import MushroomBodyBrain
from ..config import Config
from ..world import World

CONDITIONS = ("plastic", "frozen", "random")


def build(
    cfg: Config, conditions: Sequence[str], seed: int, device: str = "cpu"
) -> Creature:
    """`conditions`: eleman başına koşul adı listesi (uzunluk = batch)."""
    B = len(conditions)
    world = World(cfg.world, B, seed, device)
    brain = MushroomBodyBrain(cfg.brain, B, seed, device, cfg.world.dt, cfg.substeps)
    creature = Creature(cfg, brain, world)
    apply_conditions(creature, conditions)
    return creature


def apply_conditions(creature: Creature, conditions: Sequence[str]) -> None:
    dev = creature.world.device
    eta = torch.tensor([0.0 if c == "frozen" else 1.0 for c in conditions], device=dev)
    gain = torch.tensor(
        [0.0 if c == "random" else creature.cfg.motor.turn_gain for c in conditions], device=dev
    )
    creature.brain.eta_scale = eta
    creature.turn_gain = gain


@dataclass
class TrainLog:
    contacts: list = field(default_factory=list)   # her bölüm: (B, 2) A/B temas sayısı
    energy: list = field(default_factory=list)     # her bölüm sonu enerji (B,)

    def contact_array(self) -> np.ndarray:
        return np.stack(self.contacts) if self.contacts else np.zeros((0, 0, 2))


def train(
    creature: Creature,
    episodes: int,
    seconds: float,
    rewards: tuple[float, float] = (1.0, 0.0),
    progress: Callable[[int, int], None] | None = None,
) -> TrainLog:
    """Gezinme arenasında serbest keşif. Ödül `rewards` = (A, B)."""
    log = TrainLog()
    creature.world.set_rewards(*rewards)
    for ep in range(episodes):
        creature.reset_episode("forage")
        creature.run(seconds, learn=True)
        log.contacts.append(creature.world.n_contacts.cpu().numpy().copy())
        log.energy.append(creature.world.energy.cpu().numpy().copy())
        if progress:
            progress(ep + 1, episodes)
    return log


@dataclass
class ChoiceResult:
    n_a: np.ndarray        # (B,) A seçimi
    n_b: np.ndarray        # (B,) B seçimi
    n_trials: int
    latency: np.ndarray    # (B,) ortalama seçim süresi (s), seçim yoksa nan

    @property
    def n_none(self) -> np.ndarray:
        return self.n_trials - self.n_a - self.n_b

    @property
    def choice_rate(self) -> np.ndarray:
        return (self.n_a + self.n_b) / self.n_trials

    @property
    def preference(self) -> np.ndarray:
        """A tercih oranı = A/(A+B); hiç seçim yapmadıysa nan."""
        tot = (self.n_a + self.n_b).astype(float)
        out = np.full_like(tot, np.nan)
        np.divide(self.n_a, tot, out=out, where=tot > 0)
        return out


@torch.no_grad()
def choice_test(
    creature: Creature, trials: int, seconds: float = 40.0, seed: int = 12345
) -> ChoiceResult:
    """Öğrenme kapalı, kaynaklar tüketilmez, ilk temas seçimdir.

    Her canlı `trials` kez, her denemede yeni rastgele yön / A-B tarafı ile sınanır.
    """
    cfg, B = creature.cfg, creature.world.B
    world = World(cfg.world, B * trials, seed, str(creature.world.device))
    brain = creature.brain.expand(trials)
    test = Creature(cfg, brain, world)
    test.turn_gain = creature.turn_gain.repeat_interleave(trials)
    test.reset_episode("choice")
    test.run(seconds, learn=False, stop_when_done=True)

    ch = world.choice.view(B, trials)
    steps = world.choice_step.view(B, trials).float() * cfg.world.dt
    n_a = (ch == 0).sum(1).cpu().numpy()
    n_b = (ch == 1).sum(1).cpu().numpy()
    lat = torch.where(ch >= 0, steps, torch.full_like(steps, float("nan"))).nanmean(1).cpu().numpy()
    return ChoiceResult(n_a, n_b, trials, lat)


# ------------------------------------------------------------------ istatistik
def bootstrap_ci(x: np.ndarray, n: int = 5000, seed: int = 0, alpha: float = 0.05):
    """Ortalamanın yüzdelik bootstrap güven aralığı (nan'lar atılır)."""
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return float(x.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def permutation_p(a: np.ndarray, b: np.ndarray, n: int = 20000, seed: int = 0) -> float:
    """İki grup ortalaması farkı için iki yönlü permütasyon p değeri."""
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    rng = np.random.default_rng(seed)
    obs = abs(a.mean() - b.mean())
    pool = np.concatenate([a, b])
    count = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(pool[: len(a)].mean() - pool[len(a):].mean()) >= obs:
            count += 1
    return (count + 1) / (n + 1)


def summarize(res: ChoiceResult, conditions: Sequence[str]) -> dict:
    """Koşul başına özet: tercih (A oranı), seçim oranı, gecikme."""
    cond = np.array(conditions)
    out = {}
    for name in dict.fromkeys(conditions):
        m = cond == name
        pref = res.preference[m]
        mean, lo, hi = bootstrap_ci(pref)
        out[name] = {
            "n_agents": int(m.sum()),
            "pref_A_mean": mean,
            "pref_A_ci95": [lo, hi],
            "choice_rate": float(res.choice_rate[m].mean()),
            "latency_s": float(np.nanmean(res.latency[m])) if np.any(~np.isnan(res.latency[m])) else float("nan"),
            "pref_A_per_agent": [None if math.isnan(x) else float(x) for x in pref],
        }
    return out


@torch.no_grad()
def record_trajectories(
    creature: Creature, agents: Sequence[int], seconds: float = 40.0, seed: int = 4242
) -> dict:
    """Seçili canlıların seçim testindeki yollarını kaydeder (görselleştirme için)."""
    cfg = creature.cfg
    idx = torch.as_tensor(list(agents), dtype=torch.long)
    world = World(cfg.world, len(idx), seed, str(creature.world.device))
    test = Creature(cfg, creature.brain.select(idx), world)
    test.turn_gain = creature.turn_gain[idx.to(creature.turn_gain.device)].clone()
    test.reset_episode("choice")
    path = [world.pos.clone()]
    for _ in range(int(round(seconds / cfg.world.dt))):
        test.step(learn=False)
        path.append(world.pos.clone())
        if bool(world.done.all()):
            break
    return {
        "path": torch.stack(path).cpu().numpy(),         # (T+1, n, 2)
        "src_pos": world.src_pos.cpu().numpy(),          # (n, 2, 2): [A, B]
        "choice": world.choice.cpu().numpy(),
        "arena": cfg.world.arena,
        "contact_radius": cfg.world.contact_radius,
    }
