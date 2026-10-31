"""Uzak kontrol istemcisi (uzaktaki ajan/kullanıcı için). İki yol:

  HTTP (sunucuya ulaşılabiliyorsa):
    python3 -I -m sinek.ops.client http --url https://… --token T summary
    python3 -I -m sinek.ops.client http --url … --token T enqueue gv0 --param n=8 --param reps=2
    … overview | log JOB | cancel JOB | start JOB | auto on|off | files results/ops | update
  Git yayını (sunucu bağlantı kabul etmiyorsa; sunucu `--relay origin:ops-relay` ile açılmış olmalı):
    python3 -I -m sinek.ops.client relay --token T send enqueue gv0 --param n=8
    python3 -I -m sinek.ops.client relay --token T status        # durum + biten işlerin raporları
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from . import registry as R
from .relay import ensure_clone, git, sign


def http(url: str, token: str, path: str, body: dict | None = None):
    req = urllib.request.Request(url.rstrip("/") + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read().decode()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:300]}")
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return data


def parse_params(items: list[str]) -> dict:
    out = {}
    for it in items or []:
        k, _, v = it.partition("=")
        out[k] = v
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    h = sub.add_parser("http")
    h.add_argument("--url", required=True)
    h.add_argument("--token", required=True)
    h.add_argument("cmd")
    h.add_argument("arg", nargs="?")
    h.add_argument("--param", action="append")
    h.add_argument("--confirm", action="store_true")
    r = sub.add_parser("relay")
    r.add_argument("--token", required=True)
    r.add_argument("--spec", default="origin:ops-relay")
    r.add_argument("--url", default=None, help="uzak depo adresi (verilmezse bu deponun `origin` adresi)")
    r.add_argument("what", choices=["send", "status"])
    r.add_argument("action", nargs="?")
    r.add_argument("arg", nargs="?")
    r.add_argument("--param", action="append")
    r.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)
    if a.mode == "http":
        c = a.cmd
        if c == "summary":
            print(http(a.url, a.token, "/api/summary"))
        elif c in ("overview", "tests"):
            print(json.dumps(http(a.url, a.token, f"/api/{c}"), ensure_ascii=False, indent=1))
        elif c == "enqueue":
            print(json.dumps(http(a.url, a.token, "/api/queue", {"test_id": a.arg, "params": parse_params(a.param), "confirm": a.confirm, "source": "client"}), ensure_ascii=False, indent=1))
        elif c == "log":
            print(http(a.url, a.token, f"/api/jobs/{a.arg}/log"))
        elif c in ("cancel", "start", "retry"):
            print(json.dumps(http(a.url, a.token, f"/api/jobs/{a.arg}/{c}", {}), ensure_ascii=False))
        elif c == "auto":
            print(http(a.url, a.token, "/api/auto", {"on": a.arg == "on"}))
        elif c == "files":
            print(json.dumps(http(a.url, a.token, f"/api/files?path={a.arg or 'results'}"), ensure_ascii=False, indent=1))
        elif c == "update":
            print(http(a.url, a.token, "/api/update", {}))
        else:
            raise SystemExit("bilinmeyen komut")
        return
    remote, _, branch = a.spec.partition(":")
    work = Path(tempfile.mkdtemp(prefix="ops_relay_"))
    d = ensure_clone(work / "r", remote, branch or "ops-relay", url=a.url or git(R.ROOT, "remote", "get-url", remote).strip())
    if a.what == "status":
        print((d / "status.json").read_text(encoding="utf-8") if (d / "status.json").exists() else "status.json yok (sunucu henüz yazmadı)")
        for p in sorted((d / "reports").glob("*.md"))[-3:] if (d / "reports").exists() else []:
            print("\n" + "=" * 70 + f"\n{p.name}\n" + p.read_text(encoding="utf-8")[:6000])
        return
    cmd = {"id": uuid.uuid4().hex[:10], "ts": time.time(), "action": a.action, "confirm": a.confirm}
    if a.action == "enqueue":
        cmd.update(test_id=a.arg, params=parse_params(a.param))
    elif a.action in ("cancel", "start", "retry"):
        cmd["job_id"] = a.arg
    elif a.action == "auto":
        cmd["on"] = a.arg == "on"
    elif a.action != "update":
        raise SystemExit("eylem: enqueue|cancel|start|retry|auto|update")
    cmd["sig"] = sign(a.token, cmd)
    br = branch or "ops-relay"
    git(d, "config", "user.name", "sinek-ops-client")
    git(d, "config", "user.email", "sinek-ops-client@users.noreply.github.com")
    for attempt in range(6):          # sunucu aynı anda durum itmiş olabilir: dalı sıfırla, komutu yeniden yaz, yeniden dene (sığ klonda rebase güvenilmez)
        (d / "commands").mkdir(exist_ok=True)
        (d / "commands" / f"{cmd['id']}.json").write_text(json.dumps(cmd, ensure_ascii=False, indent=1), encoding="utf-8")
        git(d, "add", "-A")
        git(d, "commit", "-m", f"ops: komut {cmd['id']} {a.action}")
        try:
            git(d, "push", "origin", f"HEAD:{br}")
            break
        except RuntimeError:
            if attempt == 5:
                raise
            git(d, "fetch", "--depth", "1", "origin", f"+{br}:refs/remotes/origin/{br}")
            git(d, "reset", "--hard", f"origin/{br}")
            time.sleep(0.5 + attempt)
    # doğrulama: komut dosyası gerçekten uzak dalda mı?
    git(d, "fetch", "--depth", "1", "origin", f"+{br}:refs/remotes/origin/{br}")
    if f"commands/{cmd['id']}.json" not in git(d, "ls-tree", "-r", "--name-only", f"origin/{br}").split():
        raise SystemExit("komut uzak dalda görünmüyor; yeniden gönderin")
    print("komut gönderildi:", cmd["id"], "— sunucu ≤1 dk içinde uygular; sonuç: `relay status` içinde acked")


if __name__ == "__main__":
    main()
