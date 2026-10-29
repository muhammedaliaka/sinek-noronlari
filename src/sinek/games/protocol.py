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


def bandit_schedule(better: torch.Tensor, n_episodes: int, switch: int | None, p_hi: float = 0.8, p_lo: float = 0.2) -> list[torch.Tensor]:
    """O5 ödül olasılıkları: bölüm başına (B,2) tensör (yuva 0 = koku A, yuva 1 = koku B). `better` (B,) fazın ilk yarısında iyi olan koku dizini;
    `switch`: bu bölümden itibaren iyi koku tersine çevrilir (None = hiç)."""
    better = better.long()
    out = []
    for ep in range(n_episodes):
        b = better if (switch is None or ep < switch) else 1 - better
        hi = torch.arange(2).view(1, 2) == b.view(-1, 1)
        out.append(torch.where(hi, torch.full(hi.shape, p_hi), torch.full(hi.shape, p_lo)))
    return out


def play_sequence(creature: Creature, schedule: list[torch.Tensor], seconds: float, learn: bool = True) -> dict:
    """Aynı canlılar ardışık bölümler oynar (ağırlıklar bölümler arasında korunur). Çıktı: bölüm × eleman dizileri.
    slot: ilk temas edilen yuva (−1 yok); got: o temasta ödül alındı mı; time: ilk temas süresi (sn, yoksa nan)."""
    B = creature.world.B
    idx = torch.arange(B)
    rec = {"slot": [], "got": [], "time": []}
    for p in schedule:
        creature.world.reward_p = p.to(creature.world.device).clone()
        creature.reset_episode("game", test=False)
        creature.run(seconds, learn=learn, stop_when_done=True)
        o = creature.world.outcome()
        slot = o["slot"].cpu()
        ok = slot >= 0
        got = torch.zeros(B)
        u = creature.world.reward_u.cpu()
        got[ok] = (u[idx[ok], slot[ok]] < p.cpu()[idx[ok], slot[ok]]).float()
        rec["slot"].append(slot.numpy()); rec["got"].append(got.numpy()); rec["time"].append(o["time"].cpu().numpy())
    return {k: np.stack(v) for k, v in rec.items()}


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


def snapshot(creature: Creature, seed: int, game: str | GameSpec | None = None, spec: GameSpec | None = None, reps: int = 1) -> Creature:
    """Eğitim sürerken test için: aynı ağırlıkların öğrenmesi kapalı bağımsız kopyası (yeni GameWorld, ayrı tohum).

    Eğitim dünyası ve gürültü akışı etkilenmez (Evre 2b `make_test_creature` ile aynı fikir). `reps` > 1: her eleman `reps` kez
    kopyalanır (eleman-major; çift olmalı: ardışık kopyalar ayna çiftidir) — test örneğini büyütmek için."""
    w = creature.world
    sp = spec or (GAMES[game] if isinstance(game, str) else (game or w.spec))
    if reps % 2 and reps != 1:
        raise ValueError("reps çift olmalı (ayna çiftleri)")
    idx = torch.arange(w.B).repeat_interleave(reps)
    world = GameWorld(w.cfg, sp, w.B * reps, seed, str(w.device), patterns=w.patterns, swap=w.swap[idx.to(w.swap.device)])
    world.set_anosmic(w.anosmic[idx.to(w.anosmic.device)])
    brain = creature.brain.select(idx) if hasattr(creature.brain, "select") else creature.brain
    if hasattr(brain, "eta_scale"):
        brain.eta_scale = torch.zeros_like(brain.eta_scale)
    c = Creature(creature.cfg, brain, world)
    c.turn_gain = creature.turn_gain[idx.to(creature.turn_gain.device)].clone()
    return c


def run_session(creature: Creature, seconds: float, n_trials: int, learn: bool, test: bool = False) -> list[dict]:
    """Ardışık denemeler (ağırlıklar denemeler arasında korunur): O3 oturumları ve O4 aldatıcı eğitim bölümleri."""
    return [play(creature, seconds, learn=learn, test=test) for _ in range(n_trials)]


def stack_hits(outs: list[dict], slot: int = 0) -> np.ndarray:
    """run_session çıktısından (eleman, deneme) 0/1 isabet dizisi."""
    return np.stack([(o["slot"] == slot).astype(int) for o in outs], axis=1)
