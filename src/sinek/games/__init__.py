"""Dört koku oyunu (docs/dort_koku_oyunu_plani.md): sonlu destekli koku alanları, oyun dünyası, referans karşılaştırıcı."""
from .reference import NullBrain, ReferenceBrain
from .spec import GAMES, GameSpec, SlotSpec
from .world import GameWorld

__all__ = ["GAMES", "GameSpec", "SlotSpec", "GameWorld", "NullBrain", "ReferenceBrain"]
