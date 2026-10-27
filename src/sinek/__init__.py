"""Sinek beyni esinli, koku/ödül öğrenen dijital canlı (Evre 1: sentetik, Evre 2: gerçek bağlantı)."""
from .agent import Creature
from .brain import MushroomBodyBrain
from .brain_connectome import ConnectomeBrain
from .config import BrainConfig, Config, ConnectomeBrainConfig, MotorConfig, WorldConfig
from .world import World

__all__ = [
    "BrainConfig",
    "Config",
    "ConnectomeBrain",
    "ConnectomeBrainConfig",
    "Creature",
    "MotorConfig",
    "MushroomBodyBrain",
    "World",
    "WorldConfig",
]
__version__ = "0.2.0"
