"""Oyun koşuları: ön-eğitim, kol kurulumu (CRN eşli), deneme grupları, sızıntı denetimi (docs/dort_koku_oyunu_plani.md §2, §4).

Kollar AYRI koşulardır ama aynı tohum, aynı canlı sırası ve aynı deneme sayısıyla kurulur: yerleşim akışı, gürültü akışı ve beyin
akışı eşit olduğundan kollar yalnızca karşılaştırılan etkende ayrışır (ortak rastgele sayılar). Koku olmayan her denemede
koku-açık ve anosmik kolların sonuçları bit-bit aynı olmak zorundadır (`leak_check`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import torch

from ..agent import Creature
from ..brains import make_brain
from ..config import Config
from ..experiments import protocol as P
from .reference import ReferenceBrain
from .spec import GAMES, GameSpec
from .world import GameWorld


@dataclass(frozen=True)
class Arm:
    eta: float                 # 0: öğrenme kapalı
    gain: float | None         # None: yapılandırmadaki dönüş kazancı; 0: yönelimsiz
    anosmic: bool = False
    brain: str = "trained"     # trained | naive | reference


ARMS: dict[str, Arm] = {
    "plastic": Arm(1.0, None),
    "frozen": Arm(0.0, None),
    "random": Arm(0.0, 0.0),
    "anosmic": Arm(0.0, None, anosmic=True),
    "reference": Arm(0.0, None, brain="reference"),
    "naive": Arm(0.0, None, brain="naive"),
    "naive_plastic": Arm(1.0, None, brain="naive"),
}


def pretrain(cfg: Config, patterns: torch.Tensor, agents: int, seed: int, episodes: int = 12, seconds: float = 60.0,
             device: str = "cpu", log=None) -> Creature:
    """A fazı ön-eğitimi (Evre 2b ile aynı: ödül = koku A, rol dengelemeli yarı yarıya). Hepsi `plastic`."""
    if agents % 2:
        raise ValueError("rol dengelemesi için canlı sayısı çift olmalı")
    creature = P.build(cfg, ["plastic"] * agents, seed=seed, device=device, patterns=patterns)
    swap = np.zeros(agents, bool)
    swap[agents // 2:] = True
    creature.world.set_swap(torch.as_tensor(swap))
    for ep in range(episodes):
        P.train(creature, 1, seconds, (1.0, 0.0))
        if log:
            log(f"ön-eğitim bölüm {ep + 1}/{episodes}")
    return creature


O3_ARMS = {"A": (True, True), "B": (True, False), "C": (False, True), "D": (False, False)}   # (hedefte ödül, hedefte koku)


def make_game_creature(pre: Creature, game: str | GameSpec, arm: str, agents: Sequence[int], trials: int, seed: int,
                       spec: GameSpec | None = None, o3: str | None = None) -> Creature:
    """Ön-eğitimli canlılardan (her biri `trials` kez kopyalanır) oyun koşusu kurar. Eleman = canlı·trials + deneme.

    `trials` çift olmalı: ardışık deneme çiftleri aynı yerleşimin ayna çiftidir.
    """
    a = ARMS[arm]
    sp = spec or (GAMES[game] if isinstance(game, str) else game)
    idx = torch.as_tensor(list(agents), dtype=torch.long).repeat_interleave(trials)
    B, cfg, dev = len(idx), pre.cfg, str(pre.world.device)
    if trials % 2:
        raise ValueError("trials çift olmalı (ayna çiftleri)")
    world = GameWorld(cfg.world, sp, B, seed, dev, patterns=pre.world.patterns, swap=pre.world.swap[idx.to(pre.world.swap.device)])
    if a.brain == "trained":
        brain = pre.brain.select(idx)
    elif a.brain == "naive":
        brain = make_brain(cfg, B, pre.brain.seed, dev)
    else:
        brain = ReferenceBrain(world)
    creature = Creature(cfg, brain, world)
    if a.brain != "reference":
        brain.eta_scale = torch.full((B,), a.eta, device=world.device)
    creature.turn_gain = torch.full((B,), cfg.motor.turn_gain if a.gain is None else a.gain, device=world.device)
    world.set_anosmic(torch.full((B,), a.anosmic))
    if o3 is not None:
        r_on, o_on = O3_ARMS[o3]
        world.set_arms(torch.full((B,), r_on), torch.full((B,), o_on))
    return creature


def play(creature: Creature, seconds: float, learn: bool = False, test: bool = True, n_agents: int | None = None) -> dict:
    """Bir deneme grubu: yeni yerleşim, `seconds` sanal sn (ya da hepsi bitene dek). Çıktı (canlı, deneme) biçiminde numpy."""
    creature.reset_episode("game", test=test)
    creature.run(seconds, learn=learn, stop_when_done=True)
    out = {k: v.cpu().numpy() for k, v in creature.world.outcome().items()}
    out["first_odor_step"] = creature.world.first_odor_step.cpu().numpy()
    if n_agents is not None:
        out = {k: v.reshape(n_agents, -1, *v.shape[1:]) for k, v in out.items()}
    return out


def leak_check(odor_arm: dict, anosmic_arm: dict) -> dict:
    """Koku hiç alınmayan denemelerde iki kolun sonucu bit-bit aynı olmalı. Dönen: ihlal sayısı ve denetlenen deneme sayısı."""
    none = (odor_arm["first_odor_step"] < 0) & (anosmic_arm["first_odor_step"] < 0)
    same_events = bool(np.array_equal(odor_arm["first_odor_step"], anosmic_arm["first_odor_step"]))
    keys = ("slot", "time", "path_len")
    bad = np.zeros_like(none)
    for k in keys:
        a, b = odor_arm[k], anosmic_arm[k]
        bad |= ~((a == b) | (np.isnan(a.astype(float)) & np.isnan(b.astype(float))))
    return {"checked": int(none.sum()), "violations": int((bad & none).sum()), "events_identical": same_events}


def hits(out: dict, slot: int = 0) -> np.ndarray:
    """(canlı, deneme) 0/1: ilk temas `slot` yuvasıyla mı."""
    return (out["slot"] == slot).astype(int)


def snapshot(creature: Creature, seed: int, game: str | GameSpec | None = None, spec: GameSpec | None = None) -> Creature:
    """Eğitim sürerken test için: aynı ağırlıkların öğrenmesi kapalı bağımsız kopyası (yeni GameWorld, ayrı tohum).

    Eğitim dünyası ve gürültü akışı etkilenmez (Evre 2b `make_test_creature` ile aynı fikir)."""
    w = creature.world
    sp = spec or (GAMES[game] if isinstance(game, str) else (game or w.spec))
    world = GameWorld(w.cfg, sp, w.B, seed, str(w.device), patterns=w.patterns, swap=w.swap)
    world.set_anosmic(w.anosmic)
    brain = creature.brain.select(torch.arange(w.B)) if hasattr(creature.brain, "select") else creature.brain
    if hasattr(brain, "eta_scale"):
        brain.eta_scale = torch.zeros_like(brain.eta_scale)
    c = Creature(creature.cfg, brain, world)
    c.turn_gain = creature.turn_gain.clone()
    return c


def run_session(creature: Creature, seconds: float, n_trials: int, learn: bool, test: bool = False) -> list[dict]:
    """Ardışık denemeler (ağırlıklar denemeler arasında korunur): O3 oturumları ve O4 aldatıcı eğitim bölümleri."""
    return [play(creature, seconds, learn=learn, test=test) for _ in range(n_trials)]


def stack_hits(outs: list[dict], slot: int = 0) -> np.ndarray:
    """run_session çıktısından (eleman, deneme) 0/1 isabet dizisi."""
    return np.stack([(o["slot"] == slot).astype(int) for o in outs], axis=1)
