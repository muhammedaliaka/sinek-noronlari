"""Evre 2 deney hattı: gerçek mantar cismi bağlantısı (MaleCNS v1.0) ile A -> C -> B.

    python -m sinek.experiments.evre2 --out results/evre2

Evre 1 ile aynı protokol ve aynı başarı ölçütleri. Tek fark: beyin, gerçek bağlantıdan
çıkarılmış alt ağdır ve koku çifti (A, B) önce EĞİTİMSİZ ağın iç eğilimine göre seçilir
(bkz. `calibrate_odors`); böylece naif canlının tercihi bağlantının rastlantısal yan etkisi olmaz.
"""
from __future__ import annotations

import time

import numpy as np
import torch

from ..brains import make_brain
from ..config import Config
from ..connectome import mbmodel
from ..world import odor_patterns
from . import evre1

CONCS = (1.0, 0.5, 0.25)


@torch.no_grad()
def naive_valence(cfg: Config, patterns: torch.Tensor, concs=CONCS, seed: int = 9000,
                  replicas: int = 4, seconds: float = 1.0, device: str = "cpu") -> np.ndarray:
    """Eğitimsiz ağın değeri V[koku, derişim] (öğrenme kapalı, iki anten aynı derişim)."""
    brain = make_brain(cfg, replicas, seed, device)
    z = torch.zeros(replicas, device=device)
    n = int(round(seconds / cfg.world.dt))
    out = np.zeros((patterns.shape[0], len(concs)))
    for i, pat in enumerate(patterns):
        for j, c in enumerate(concs):
            brain.reset_state()
            g = (c * pat).to(device).view(1, 1, -1).expand(replicas, 2, -1).contiguous()
            vs = [brain.step(g, z, z, learn=False).mean() for _ in range(n)]
            out[i, j] = torch.stack(vs[n // 2:]).mean().item()
    return out


def calibrate_odors(cfg: Config, n_candidates: int = 40, seed0: int = 5000, device: str = "cpu"):
    """Aday (A, B) çiftleri arasından, eğitimsiz ağın iç değer farkı |V_A - V_B| en küçük olanı seçer.

    Ölçüm yalnızca eğitimsiz ağ üzerindedir (hiçbir öğrenme / davranış sonucu kullanılmaz) ve
    deney tohumlarından bağımsız tohumlarla yapılır. Seçilen çift ve tüm adayların dağılımı raporlanır.
    """
    scores, cands = [], []
    for k in range(n_candidates):
        pat = odor_patterns(cfg.world, seed0 + k)
        v = naive_valence(cfg, pat, device=device)
        scores.append(float(np.abs(v[0] - v[1]).max()))
        cands.append(pat)
    best = int(np.argmin(scores))
    v = naive_valence(cfg, cands[best], device=device)
    info = {
        "n_candidates": n_candidates, "pattern_seed": seed0 + best, "chosen_score": scores[best],
        "scores_quantiles": {q: float(np.quantile(scores, q)) for q in (0.0, 0.25, 0.5, 0.75, 1.0)},
        "glomeruli_A": [mbmodel_name for mbmodel_name in _names(cfg, cands[best][0])],
        "glomeruli_B": [mbmodel_name for mbmodel_name in _names(cfg, cands[best][1])],
        "naive_V": {"concs": list(CONCS), "A": v[0].tolist(), "B": v[1].tolist()},
    }
    return cands[best], info


def _names(cfg: Config, pat: torch.Tensor) -> list[str]:
    names = mbmodel.load(cfg.cbrain.data_dir).glom_names
    return [names[i] for i in pat.nonzero().flatten().tolist()]


def apply_override(cfg: Config, item: str) -> None:
    key, _, val = item.partition("=")
    section, _, name = key.partition(".")
    obj = getattr(cfg, section)
    if not hasattr(obj, name):
        raise SystemExit(f"bilinmeyen alan: {key}")
    setattr(obj, name, type(getattr(obj, name))(val))


def main(argv=None) -> dict:
    ap = evre1.build_parser(description=__doc__, default_out="results/evre2")
    ap.add_argument("--calib-candidates", type=int, default=40, help="aday koku çifti sayısı")
    ap.add_argument("--data-dir", default=mbmodel.DEFAULT_DIR)
    ap.add_argument("--set", action="append", default=[], metavar="BÖLÜM.ALAN=DEĞER",
                    help="yapılandırma geçersiz kılma, ör. cbrain.valence_gain=20 (sonuç dosyasına yazılır)")
    a = ap.parse_args(argv)
    cfg = mbmodel.connectome_config(a.data_dir)
    for item in a.set:
        apply_override(cfg, item)
    t0 = time.time()
    patterns, info = calibrate_odors(cfg, a.calib_candidates, device=a.device)
    evre1.log(f"koku çifti: tohum {info['pattern_seed']}, eğitimsiz iç fark skoru {info['chosen_score']:.3f} "
              f"(aday medyanı {info['scores_quantiles'][0.5]:.3f}); A={info['glomeruli_A']} B={info['glomeruli_B']}", t0)
    d = mbmodel.load(cfg.cbrain.data_dir)
    extra = {"calibration": info, "connectome": d.summary,
             "connectome_meta": __import__("json").loads((mbmodel.resolve_dir(cfg.cbrain.data_dir) / "meta.json").read_text())}
    return evre1.run(a, cfg, patterns=patterns, title="Evre 2 (gerçek mantar cismi)", extra=extra)


if __name__ == "__main__":
    main()
