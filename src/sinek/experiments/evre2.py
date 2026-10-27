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


@torch.no_grad()
def calibrate_balance(cfg: Config, n_patterns: int = 30, seed0: int = 20000, concs=(1.0, 0.5), device: str = "cpu") -> dict:
    """Eğitimsiz ağda yaklaş / kaçın sınıf hızlarını eşitleyen `class_balance` değerini ölçer.

    Sınıf boyutları ve bağlantı yoğunlukları farklı olduğundan, düzeltme olmadan her koku iç olarak
    hep aynı yönde (ör. negatif) değer taşırdı. Ölçüm rastgele kokular üzerinde, öğrenme kapalıyken yapılır;
    sonuç yapılandırmaya yazılır ve kaydedilir. (Biyolojik gerekçe: naif sineklerde MBON çıktısının
    yaklaş/kaçın yönünde dengeli olduğu varsayılır.)
    """
    replicas = 8
    brain = make_brain(cfg, replicas, 9100, device)
    z = torch.zeros(replicas, device=device)
    n = int(round(1.5 / cfg.world.dt))
    app, avo = [], []
    for k in range(n_patterns):
        pat = odor_patterns(cfg.world, seed0 + k)
        for odor in pat:
            for c in concs:
                brain.reset_state()
                g = (c * odor).to(device).view(1, 1, -1).expand(replicas, 2, -1).contiguous()
                ra = []
                for _ in range(n):
                    brain.step(g, z, z, learn=False)
                    ra.append(brain.rate.mean(0))
                r = torch.stack(ra[n // 2:]).mean(0)
                app.append(r[0].item()); avo.append(r[1].item())
    bal = float(np.mean(avo) / np.mean(app))
    return {"class_balance": bal, "mean_rate_approach": float(np.mean(app)), "mean_rate_avoid": float(np.mean(avo)),
            "n_stimuli": len(app), "seed0": seed0}


def calibrate_odors(cfg: Config, n_candidates: int = 40, seed0: int = 5000, device: str = "cpu",
                    n_finalists: int = 6):
    """Aday (A, B) çiftleri arasından, eğitimsiz ağın iç değer farkı |V_A - V_B| en küçük olanı seçer.

    İki aşamalı: (1) tüm adaylar hızlı ölçülür (az tekrar), (2) en iyi `n_finalists` aday çok tekrarla
    yeniden ölçülür ve nihai seçim bu ikinci, daha az gürültülü ölçüme göre yapılır. (Tek aşamalı seçim,
    gürültünün en düşük çıktığı adayı seçer ve gerçek iç farkı olduğundan küçük gösterir.)
    Ölçümler yalnızca eğitimsiz ağ üzerindedir (hiçbir öğrenme / davranış sonucu kullanılmaz) ve
    deney tohumlarından bağımsız tohumlarla yapılır. Seçilen çift ve tüm adayların dağılımı raporlanır.
    """
    cands, quick = [], []
    for k in range(n_candidates):
        pat = odor_patterns(cfg.world, seed0 + k)
        v = naive_valence(cfg, pat, device=device)
        quick.append(float(np.abs(v[0] - v[1]).max()))
        cands.append(pat)
    order = np.argsort(quick)[:n_finalists]
    final = {}
    for k in order:
        v = naive_valence(cfg, cands[k], seed=9500, replicas=24, seconds=2.0, device=device)
        final[int(k)] = (float(np.abs(v[0] - v[1]).max()), v)
    best = min(final, key=lambda k: final[k][0])
    info = {
        "n_candidates": n_candidates, "pattern_seed": seed0 + best,
        "chosen_score": final[best][0], "chosen_score_first_pass": quick[best],
        "scores_quantiles": {q: float(np.quantile(quick, q)) for q in (0.0, 0.25, 0.5, 0.75, 1.0)},
        "finalists": {seed0 + k: {"first_pass": quick[k], "second_pass": final[k][0]} for k in final},
        "glomeruli_A": _names(cfg, cands[best][0]),
        "glomeruli_B": _names(cfg, cands[best][1]),
        "naive_V": {"concs": list(CONCS), "A": final[best][1][0].tolist(), "B": final[best][1][1].tolist()},
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
    cur = getattr(obj, name)
    if isinstance(cur, bool):  # bool("false") True olurdu
        low = val.strip().lower()
        if low not in ("true", "false", "1", "0"):
            raise SystemExit(f"{key}: true/false bekleniyor, '{val}' verildi")
        setattr(obj, name, low in ("true", "1"))
    else:
        setattr(obj, name, type(cur)(val))


def _git_commit() -> str | None:
    import subprocess

    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=__file__.rsplit("/", 1)[0]).stdout.strip()
    except Exception:
        return None


# Evre 2b (docs/evre2b_plan.md) hareket okuması: Evre 2 v1'den farkı; geliştirme tohumlarında seçildi.
V2_SET = []


def main(argv=None, v2: bool = False) -> dict:
    ap = evre1.build_parser(description=__doc__, default_out="results/evre2b" if v2 else "results/evre2")
    if v2:   # Evre 2b varsayılanları (ön-kayıt: docs/evre2b_plan.md)
        ap.set_defaults(agents=24, episodes=12, reversal_episodes=12, test_every=6, trials=8, swap_roles=True)
    ap.add_argument("--calib-candidates", type=int, default=40, help="aday koku çifti sayısı")
    ap.add_argument("--pattern-seed", type=int, default=None,
                    help="koku çifti aramasını atla, bu tohumun desenini kullan (kontrol koşuları ana koşuyla aynı çifti kullanır)")
    ap.add_argument("--threads", type=int, default=None, help="torch CPU iş parçacığı sayısı")
    ap.add_argument("--data-dir", default=mbmodel.DEFAULT_DIR)
    ap.add_argument("--set", action="append", default=[], metavar="BÖLÜM.ALAN=DEĞER",
                    help="yapılandırma geçersiz kılma, ör. cbrain.valence_gain=20 (sonuç dosyasına yazılır)")
    a = ap.parse_args(argv)
    if a.threads:
        torch.set_num_threads(a.threads)
    cfg = mbmodel.connectome_config(a.data_dir)
    for item in (V2_SET if v2 else []) + a.set:
        apply_override(cfg, item)
    t0 = time.time()
    balance = calibrate_balance(cfg, device=a.device)
    cfg.cbrain.class_balance = balance["class_balance"]
    evre1.log(f"sınıf dengesi: class_balance={balance['class_balance']:.3f} "
              f"(ham hızlar: yaklaş {balance['mean_rate_approach']:.1f} Hz, kaçın {balance['mean_rate_avoid']:.1f} Hz)", t0)
    if a.pattern_seed is None:
        patterns, info = calibrate_odors(cfg, a.calib_candidates, seed0=5000 + 100 * a.seed, device=a.device)
    else:
        patterns = odor_patterns(cfg.world, a.pattern_seed)
        v = naive_valence(cfg, patterns, seed=9500, replicas=24, seconds=2.0, device=a.device)
        info = {"pattern_seed": a.pattern_seed, "given": True, "chosen_score": float(np.abs(v[0] - v[1]).max()),
                "chosen_score_first_pass": None, "scores_quantiles": {0.5: float("nan")},
                "glomeruli_A": _names(cfg, patterns[0]), "glomeruli_B": _names(cfg, patterns[1]),
                "naive_V": {"concs": list(CONCS), "A": v[0].tolist(), "B": v[1].tolist()}}
    evre1.log(f"koku çifti: tohum {info['pattern_seed']}, eğitimsiz iç fark skoru {info['chosen_score']:.3f} "
              f"(ilk geçiş {info['chosen_score_first_pass']}, aday medyanı {info['scores_quantiles'][0.5]:.3f}); "
              f"A={info['glomeruli_A']} B={info['glomeruli_B']}", t0)
    d = mbmodel.load(cfg.cbrain.data_dir)
    extra = {"git_commit": _git_commit(), "calibration": info, "balance": balance, "connectome": d.summary,
             "connectome_meta": __import__("json").loads((mbmodel.resolve_dir(cfg.cbrain.data_dir) / "meta.json").read_text())}
    if v2:
        from . import evre2b

        extra["protocol"] = "evre2b"
        return evre1.run(a, cfg, patterns=patterns, title="Evre 2b (gerçek mantar cismi, artırılmış ölçüt gücü)", extra=extra,
                         evaluator=evre2b.evaluate2, renderer=evre2b.render_summary2, curve_key="pooled_A")
    return evre1.run(a, cfg, patterns=patterns, title="Evre 2 (gerçek mantar cismi)", extra=extra)


if __name__ == "__main__":
    main()
