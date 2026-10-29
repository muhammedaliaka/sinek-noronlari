"""E1 karıştırma koşusu kurtarma: A fazı bitmiş (`after_A.npz` yazılmış) ama B fazında ölmüş koşudan A-sonu stage'ini yeniden hesaplar.

    python -m sinek.experiments.evre2b_e1_recover --template results/evre2b_s30 --run results/evre2b_s30_shuffle1 --out results/evre2b_s30_shuffle1_recovered
    python -m sinek.experiments.evre2b_e1_recover --template results/evre2b_s30 --run results/evre2b_s30 --verify   # sıfır-etki sınaması

E1 yalnızca A-sonu `plastic` seçimlerini kullanır (`evre2b_e1._last_a`). Tam koşuda bu test, A eğitiminden hemen sonra aynı `choice_test(…, seed=12345+seed)` ile
yapılır ve `after_A.npz` yeniden yüklendiğinde sonuçların birebir aynı olduğu ayrıca denetlenir (`persistence.test_identical`). Bu betik o testi diskteki
duruma uygular. `--verify`: gerçek koşunun kendi `after_A.npz` dosyasından hesaplanan A-sonu n_a/n_b, gerçek `results.json`'daki ile birebir aynı mı?
Çıktı results.json `recovered_from_after_A: true` işaretini taşır; B fazı (tersine çevirme) içermez ve E1 için gerekmez.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .. import checkpoint
from . import protocol as P


def recompute_a_stage(run_dir: Path, args: dict) -> tuple[dict, dict]:
    ck = checkpoint.load(run_dir / "after_A.npz", device=args["device"])
    agents = args["agents"]
    conds = ["plastic"] * agents + ["frozen"] * agents + ["random"] * agents
    res = P.choice_test(ck, args["trials"], args["test_seconds"], seed=12345 + args["seed"])
    stage = {"name": "A sonrası (after_A.npz'den yeniden hesaplandı)", "episode": args["episodes"], "phase": "A",
             "summary": P.summarize(res, conds), "n_a": res.n_a.tolist(), "n_b": res.n_b.tolist()}
    return stage, ck.cfg.to_dict()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--template", required=True, help="tasarımı (args) alınacak gerçek-etiketli koşu dizini")
    ap.add_argument("--run", required=True, help="after_A.npz içeren koşu dizini")
    ap.add_argument("--out", default=None)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args(argv)
    import torch

    torch.set_num_threads(a.threads)
    tpl = json.loads((Path(a.template) / "results.json").read_text())
    stage, cfg = recompute_a_stage(Path(a.run), tpl["args"])
    if a.verify:
        real = next(s for s in reversed(tpl["stages"]) if s["phase"] == "A")
        same = bool(np.array_equal(real["n_a"], stage["n_a"]) and np.array_equal(real["n_b"], stage["n_b"]))
        print(f"A-sonu n_a/n_b gerçek results.json ile birebir aynı: {same}")
        if not same:
            raise SystemExit("kurtarma yöntemi sıfır-etki sınamasında BAŞARISIZ")
        return
    if not a.out:
        raise SystemExit("--out gerekli")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    args = dict(tpl["args"], out=str(out))
    res = {"args": args, "config": cfg, "balance": {"class_balance": cfg["cbrain"]["class_balance"]}, "stages": [stage],
           "recovered_from_after_A": True, "source_run": str(a.run)}
    (out / "results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"yazıldı: {out / 'results.json'}")


if __name__ == "__main__":
    main()
