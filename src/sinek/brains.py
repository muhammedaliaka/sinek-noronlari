"""Beyin fabrikası: yapılandırmadaki `brain_kind`a göre Evre 1 ya da Evre 2 beynini kurar."""
from __future__ import annotations

from .brain import MushroomBodyBrain
from .brain_connectome import ConnectomeBrain
from .config import Config


def make_brain(cfg: Config, batch: int, seed: int, device: str = "cpu"):
    if cfg.brain_kind == "synthetic":
        return MushroomBodyBrain(cfg.brain, batch, seed, device, cfg.world.dt, cfg.substeps)
    if cfg.brain_kind == "connectome":
        return ConnectomeBrain(cfg.cbrain, batch, seed, device, cfg.world.dt, cfg.substeps)
    raise ValueError(cfg.brain_kind)
