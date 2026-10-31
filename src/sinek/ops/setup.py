"""Arkadaşın makinesinde tek komutla kurulum denetimi + isteğe bağlı otomatik başlatma:

    python3 -I -m sinek.ops.setup                 # denetle (hiçbir şeyi değiştirmez; jeton yoksa üretir)
    python3 -I -m sinek.ops.setup --autostart     # Linux: systemd kullanıcı servisi yazar (açılışta sunucu + git yayını)
    python3 -I -m sinek.ops.setup --rotate-token  # jetonu yenile (jeton sohbete/başkasına gittiyse işi bitince yenileyin)

Denetler: Python/torch/CUDA, git uzak adresi + dala YAZMA (git yayını gerçek bir deneme turuyla sınanır), jeton, kendi kendine sınama.
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

from . import registry as R
from .server import TOKEN_FILE, load_or_create_token

ROOT = R.ROOT
OK, BAD, WARN = "[ TAMAM ]", "[ HATA  ]", "[ UYARI ]"


def line(tag: str, msg: str) -> None:
    print(f"{tag} {msg}", flush=True)


def check_python_torch() -> bool:
    ok = sys.version_info >= (3, 10)
    line(OK if ok else BAD, f"Python {platform.python_version()} (≥3.10 gerekir)")
    try:
        import torch
        cu = torch.cuda.is_available()
        line(OK, f"torch {torch.__version__}; CUDA {'VAR: ' + ', '.join(torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())) if cu else 'YOK (yalnız CPU)'}")
        if not cu:
            line(WARN, "GPU görünmüyor. NVIDIA sürücüsü + CUDA'lı PyTorch (https://pytorch.org/get-started/locally/) kurulu değilse yalnız CPU kullanılır; "
                       "ön-kayıtlı doğrulayıcılar zaten CPU'da koşar (docs/uzak_kontrol.md §5).")
    except Exception as e:
        line(BAD, f"torch yüklenemedi: {e}")
        return False
    return ok


def check_git_relay(spec: str) -> bool:
    from .relay import Relay
    from .jobs import JobManager
    from .server import App
    remote, _, branch = spec.partition(":")
    try:
        url = subprocess.run(["git", "remote", "get-url", remote], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        line(BAD, f"git uzak adresi '{remote}' yok: bu klasör git deposu mu?")
        return False
    line(OK, f"uzak depo: {url}")
    try:
        app = App("setup-denemesi-" + "x" * 8, JobManager(ROOT / "results" / "ops_setup_tmp"))
        Relay(app, spec, "setup-denemesi-" + "x" * 8).cycle_once()
        line(OK, f"git yayını: '{branch}' dalına YAZILDI (yazma yetkisi var). Uzaktan komut/durum yolu açık.")
        return True
    except Exception as e:
        line(BAD, f"git yayını çalışmadı: {str(e)[:300]}")
        line(WARN, "Büyük olasılıkla depoya yazma yetkisi yok. GitHub'da bu depo için yazma yetkili kişisel erişim jetonu oluşturup "
                   "`git remote set-url origin https://<KULLANICI>:<JETON>@github.com/<sahip>/<depo>.git` ya da `gh auth login` ile giriş yapın.")
        return False
    finally:
        import shutil
        shutil.rmtree(ROOT / "results" / "ops_setup_tmp", ignore_errors=True)


def autostart(relay: str) -> None:
    if platform.system() != "Linux":
        cmd = f'schtasks /Create /SC ONLOGON /TN SinekOps /TR "py -3 -I -m sinek.ops.server --relay {relay} --auto" /F' if platform.system() == "Windows" else "launchd/Login Items ile `scripts/ops_baslat.sh --relay …` ekleyin"
        line(WARN, f"Otomatik başlatma bu işletim sisteminde kendiliğinden kurulmaz. Elle: {cmd}")
        return
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / "sinek-ops.service").write_text(
        f"[Unit]\nDescription=Sinek kontrol sunucusu\nAfter=network-online.target\n\n[Service]\nWorkingDirectory={ROOT}\n"
        f"ExecStart={sys.executable} -I -m sinek.ops.server --relay {relay} --auto\nRestart=always\nRestartSec=10\n\n[Install]\nWantedBy=default.target\n")
    r = subprocess.run("systemctl --user daemon-reload && systemctl --user enable --now sinek-ops.service", shell=True, capture_output=True, text=True)
    line(OK if r.returncode == 0 else WARN, "systemd kullanıcı servisi yazıldı ve başlatıldı" if r.returncode == 0 else f"servis dosyası yazıldı ama etkinleştirilemedi: {r.stderr.strip()[:200]}")
    line(WARN, "Oturum kapansa da çalışsın istiyorsanız bir kez: `loginctl enable-linger $USER`. Bilgisayarın uykuya geçmesini kapatın.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--relay", default="origin:ops-relay")
    ap.add_argument("--autostart", action="store_true")
    ap.add_argument("--rotate-token", action="store_true")
    ap.add_argument("--no-relay-check", action="store_true")
    a = ap.parse_args(argv)
    if a.rotate_token:
        TOKEN_FILE.unlink(missing_ok=True)
        line(OK, "eski jeton silindi; yenisi aşağıda")
    ok = check_python_torch()
    tok = load_or_create_token()
    line(OK, f"jeton dosyası: {TOKEN_FILE} (yalnız sahibi okur)")
    ok = (a.no_relay_check or check_git_relay(a.relay)) and ok
    if a.autostart:
        autostart(a.relay)
    print("\n--- Sonraki adımlar ---")
    print(f"1) Sunucu: scripts/ops_baslat.sh --relay {a.relay}   (Windows: scripts\\ops_baslat.bat --relay {a.relay})")
    print(f"2) Panel: http://127.0.0.1:8765/?token={tok}")
    print("3) Uzaktaki Claude'un komut verebilmesi için JETONU ona verin (sohbete yapıştırdıysanız iş bitince: `python3 -I -m sinek.ops.setup --rotate-token`).")
    print("4) Panelde önce 'Birim testleri', sonra 'Hızlı demo popülasyonu' işlerini çalıştırın.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
