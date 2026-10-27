"""Doğrulamalı indirme: boyut + md5, kesilen indirme kaldığı yerden sürer.

    python -m sinek.connectome.fetch                      # tüm dosyalar
    python -m sinek.connectome.fetch --only annotations   # ad parçasıyla seç
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .sources import DATASETS, MALE_CNS, Dataset, RemoteFile

DEFAULT_DIR = Path("data/raw")
CHUNK = 1 << 20


def md5_b64(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


def is_valid(f: RemoteFile, path: Path) -> bool:
    return path.exists() and path.stat().st_size == f.size and md5_b64(path) == f.md5_b64


def _download(f: RemoteFile, part: Path, log) -> None:
    have = part.stat().st_size if part.exists() else 0
    if have > f.size:
        part.unlink()
        have = 0
    if have == f.size:
        return
    req = urllib.request.Request(f.url)
    if have:
        req.add_header("Range", f"bytes={have}-")
        log(f"  kaldığı yerden devam: {have / 1e6:.0f} MB")
    with urllib.request.urlopen(req, timeout=60) as r:
        if have and r.status != 206:                       # sunucu aralık desteklemedi
            have = 0
        mode = "ab" if have else "wb"
        t0, got, last = time.time(), have, 0.0
        with open(part, mode) as out:
            while chunk := r.read(CHUNK):
                out.write(chunk)
                got += len(chunk)
                if time.time() - last > 10:
                    last = time.time()
                    rate = (got - have) / max(time.time() - t0, 1e-6) / 1e6
                    log(f"  {got / 1e6:8.0f} / {f.size / 1e6:.0f} MB  ({rate:.1f} MB/s)")


def fetch_file(f: RemoteFile, dest_dir: Path, log=print, retries: int = 5) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path, part = dest_dir / f.name, dest_dir / (f.name + ".part")
    if is_valid(f, path):
        log(f"[tamam] {f.name}")
        return path
    log(f"[indir] {f.name} ({f.size / 1e6:.0f} MB)")
    for attempt in range(1, retries + 1):
        try:
            _download(f, part, log)
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            log(f"  hata: {e!r} (deneme {attempt}/{retries})")
            time.sleep(min(2 ** attempt, 30))
    else:
        raise RuntimeError(f"{f.name} indirilemedi")
    if part.stat().st_size != f.size or md5_b64(part) != f.md5_b64:
        raise RuntimeError(f"{f.name}: boyut/md5 doğrulaması BAŞARISIZ; dosya bozuk ya da sürüm değişmiş")
    part.replace(path)
    log(f"[doğrulandı] {f.name}  md5={f.md5_hex}")
    return path


def fetch(ds: Dataset = MALE_CNS, root: Path = DEFAULT_DIR, only: str | None = None, log=print) -> dict[str, Path]:
    dest = Path(root) / ds.key
    out = {}
    for f in ds.files:
        if only and only not in f.name:
            continue
        out[f.name] = fetch_file(f, dest, log)
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default=MALE_CNS.key, choices=sorted(DATASETS))
    ap.add_argument("--root", default=str(DEFAULT_DIR))
    ap.add_argument("--only", default=None, help="dosya adında geçen metin")
    a = ap.parse_args(argv)
    ds = DATASETS[a.dataset]
    print(f"{ds.title}\n  sürüm: {ds.version}\n  lisans: {ds.license}\n  {ds.citation_note}\n")
    fetch(ds, Path(a.root), a.only)


if __name__ == "__main__":
    sys.exit(main())
