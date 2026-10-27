import pytest
import torch

from sinek import Config, MushroomBodyBrain
from sinek.world import odor_patterns

torch.set_num_threads(2)


@pytest.fixture(scope="session")
def cfg() -> Config:
    return Config()


def make_brain(cfg: Config, batch: int = 2, seed: int = 0) -> MushroomBodyBrain:
    return MushroomBodyBrain(cfg.brain, batch, seed, "cpu", cfg.world.dt, cfg.substeps)


def present(brain, cfg, odor, secs, batch, seed=0, strength=0.95, feed_from=None, reward=1.0, learn=True):
    """Beyne sabit koku sun; `feed_from` sn sonrasından itibaren tat+temas ver. Son yarının ortalama V'si."""
    pat = odor_patterns(cfg.world, seed)
    z, o = torch.zeros(batch), torch.ones(batch)
    g = (pat[odor] * strength).expand(batch, 2, -1).contiguous()
    vs = []
    for i in range(int(secs / cfg.world.dt)):
        fed = feed_from is not None and i * cfg.world.dt >= feed_from
        brain.step(g, reward * o if fed else z, o if fed else z, learn=learn)
        vs.append(brain.valence.view(batch, 2).mean(1).clone())
    return torch.stack(vs[len(vs) // 2:]).mean(0)


def probe(brain, cfg, odor, batch, seed=0):
    brain.reset_state()
    return present(brain, cfg, odor, 1.2, batch, seed, learn=False)
