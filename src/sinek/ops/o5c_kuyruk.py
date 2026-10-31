"""O5c doğrulayıcı kuyruğu — `scripts/run_o5c_validators.sh`'nin platformdan bağımsız (Windows dahil, bash'siz) eşi (K-062).

HESAP DEĞİŞMEDİ: aynı modüller, aynı bağımsız değişkenler, aynı tohum/popülasyon eşleşmesi, aynı sıra, aynı atlama kuralları
(biten iş atlanır; kesilen iş parça kontrol noktasından AYNI hesapla sürer). Yalnız yürütme dili bash/xargs'tan Python'a geçti.
Ön-kayıt: docs/odor_o5c_plani.md §8 (aşama 0: ön-eğitim 206-209; aşama 1: kol × parça işçileri + referans; aşama 2: değerlendirme).

    python -X utf8 -I -m sinek.ops.o5c_kuyruk --workers 4 [--dry-run]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEEDS = (("274", "206"), ("275", "207"), ("276", "208"), ("277", "209"))     # (oyun tohumu, ön-eğitim popülasyonu)
ARMS = ("plastic_t", "plastic", "frozen")
CHUNKS = 8
OUT = "results/o5_val"
PY = [sys.executable, "-X", "utf8", "-I", "-m"]


def plan(root: Path = ROOT) -> list[list[dict]]:
    """Üç aşama; her iş: {name, argv, log, log_mode, skip_if (var olan dosya), mkdir}."""
    pre_f = lambda pop: f"results/odor_val/pre_s{pop}.npz"          # noqa: E731
    s0 = [{"name": f"ön-eğitim {pop}", "argv": PY + ["sinek.experiments.odor_pretrain", "--seed", pop, "--threads", "1", "--out", pre_f(pop)],
           "log": f"results/odor_val/pre_s{pop}.log", "log_mode": "w", "skip_if": pre_f(pop), "mkdir": "results/odor_val"} for _, pop in SEEDS]

    def arm_job(seed, pop, arm, ch):
        d = f"{OUT}/c_s{seed}"
        only = ["--only-arms", arm] + ([] if ch == "all" else ["--only-chunks", str(ch)])
        return {"name": f"{seed} {arm} {ch}", "argv": PY + ["sinek.experiments.odor_validate_o5", "--o5c", "--pre", pre_f(pop), "--seed", seed, "--threads", "1", *only, "--out", d],
                "log": f"{d}.{arm}.{ch}.log", "log_mode": "a", "skip_if": f"{d}/results.json", "mkdir": d}

    s1 = [arm_job(seed, pop, arm, c) for arm in ARMS for c in range(CHUNKS) for seed, pop in SEEDS] + [arm_job(seed, pop, "reference", "all") for seed, pop in SEEDS]
    s2 = [{"name": f"değerlendirme {seed}", "argv": PY + ["sinek.experiments.odor_validate_o5", "--o5c", "--pre", pre_f(pop), "--seed", seed, "--threads", "1", "--out", f"{OUT}/c_s{seed}"],
           "log": f"{OUT}/c_s{seed}.log", "log_mode": "w", "skip_if": f"{OUT}/c_s{seed}/results.json", "mkdir": OUT} for seed, pop in SEEDS]
    return [s0, s1, s2]


def run_job(job: dict, root: Path = ROOT, say=print) -> int:
    if (root / job["skip_if"]).exists():
        say(f"atla {job['name']} (bitti)")
        return 0
    (root / job["mkdir"]).mkdir(parents=True, exist_ok=True)
    (root / job["log"]).parent.mkdir(parents=True, exist_ok=True)
    say(f"başla {job['name']}")
    with open(root / job["log"], job["log_mode"] + "b") as lf:
        code = subprocess.call(job["argv"], cwd=root, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    say(f"bitti {job['name']} çıkış={code}")
    return code


def execute(stages: list[list[dict]], workers: int, root: Path = ROOT, say=print, runner=run_job) -> int:
    """Aşamalar sırayla; aşama içinde `workers` paralel (xargs -P ile aynı); hata olsa da kalan işler sürer. 0 = hepsi başarılı."""
    lock, failures = threading.Lock(), []

    def one(job):
        code = runner(job, root, say)
        if code != 0:
            with lock:
                failures.append((job["name"], code))

    for i, stage in enumerate(stages):
        with ThreadPoolExecutor(max_workers=(4 if i == 2 else workers)) as ex:      # değerlendirme aşaması betikte -P 4
            list(ex.map(one, stage))
    for name, code in failures:
        say(f"BAŞARISIZ: {name} (çıkış {code})")
    return 1 if failures else 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true", help="yalnız iş listesini yaz")
    a = ap.parse_args(argv)
    stages = plan()
    if a.dry_run:
        for i, st in enumerate(stages):
            for j in st:
                print(f"aşama {i} | {' '.join(j['argv'][4:])}")
        return 0
    return execute(stages, max(1, a.workers), say=lambda m: print(m, flush=True))


if __name__ == "__main__":
    raise SystemExit(main())
