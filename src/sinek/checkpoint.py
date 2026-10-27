"""Kaydet / yükle: öğrenilmiş sinaptik durum (bellek) diske yazılır.

Bellek = plastik KC->MBON ağırlıkları (`brain.state_dict()` neyse o yazılır) ve canlının
koku desenleri. Dinamik durum (membran gerilimleri, izler) kasıtlı olarak kaydedilmez: canlı yeniden başladığında bu değişkenler sıfırdan
başlar; geriye kalan şey gerçekten öğrenilmiş sinaptik bilgidir.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from .agent import Creature
from .brains import make_brain
from .config import Config
from .world import World, odor_patterns

FORMAT_VERSION = 1


def save(creature: Creature, path: str | Path, extra: dict | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    st = creature.brain.state_dict()
    meta = {
        "format": FORMAT_VERSION,
        "config": creature.cfg.to_dict(),
        "seed": st["seed"],
        "extra": extra or {},
    }
    arrays = {k: np.asarray(v) for k, v in st.items() if k != "seed"}
    arrays["W"] = arrays["W"].astype(np.float32)
    np.savez_compressed(
        path,
        **arrays,
        patterns=creature.world.patterns.cpu().numpy(),
        eta_scale=creature.brain.eta_scale.cpu().numpy(),
        turn_gain=creature.turn_gain.cpu().numpy(),
        meta=np.frombuffer(json.dumps(meta).encode("utf-8"), dtype=np.uint8),
    )
    return path if path.suffix == ".npz" else path.with_suffix(path.suffix + ".npz")


def load(path: str | Path, device: str = "cpu", world_seed: int | None = None) -> Creature:
    """Diskteki durumdan sıfırdan yeni bir canlı kurar (yeni beyin + yeni dünya)."""
    z = np.load(Path(path), allow_pickle=False)
    meta = json.loads(bytes(z["meta"]).decode("utf-8"))
    if meta["format"] != FORMAT_VERSION:
        raise ValueError(f"Desteklenmeyen checkpoint sürümü: {meta['format']}")
    cfg = Config.from_dict(meta["config"])
    B = z["W"].shape[0]
    seed = meta["seed"]
    patterns = torch.from_numpy(z["patterns"]) if "patterns" in z.files else odor_patterns(cfg.world, seed)
    world = World(cfg.world, B, seed if world_seed is None else world_seed, device, patterns=patterns)
    brain = make_brain(cfg, B, seed, device)
    reserved = {"meta", "eta_scale", "turn_gain", "patterns"}
    brain.load_state_dict({**{k: torch.from_numpy(z[k]) for k in z.files if k not in reserved}, "seed": seed})
    creature = Creature(cfg, brain, world)
    brain.eta_scale = torch.from_numpy(z["eta_scale"]).to(world.device)
    creature.turn_gain = torch.from_numpy(z["turn_gain"]).to(world.device)
    return creature
