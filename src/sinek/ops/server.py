"""Kontrol sunucusu: HTTP API + tek dosya arayüz + canlı yayın (SSE). Yalnız standart kütüphane.

    python3 -I -m sinek.ops.server                       # yalnız bu bilgisayardan (127.0.0.1:8765), jeton otomatik
    python3 -I -m sinek.ops.server --host 0.0.0.0        # ağdan erişim (jeton ZORUNLU; TLS yok → tünel/VPN önerilir, docs/uzak_kontrol.md)

Güvenlik: jeton (≥128 bit) olmadan hiçbir uç nokta açılmaz; keyfi komut uç noktası YOKTUR (yalnız registry'deki işler, doğrulanmış parametrelerle);
dosya okuma yalnız results/ ve docs/ altında, salt-okunur. Yanlış jeton denemeleri yavaşlatılır ve IP başına kilitlenir.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import secrets
import shutil
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import registry as R
from .jobs import JobManager
from .live import LiveSession, replay_list, replay_read

ROOT = R.ROOT
STATIC = Path(__file__).parent / "static"
TOKEN_FILE = Path(os.environ.get("SINEK_OPS_TOKEN_FILE", Path.home() / ".sinek_ops_token"))
FILE_ROOTS = ("results", "docs")
MAX_READ = 300_000
START = time.time()


def load_or_create_token(explicit: str | None = None) -> str:
    if explicit:
        tok = explicit
    elif os.environ.get("SINEK_OPS_TOKEN"):
        tok = os.environ["SINEK_OPS_TOKEN"]
    elif TOKEN_FILE.exists():
        tok = TOKEN_FILE.read_text().strip()
    else:
        tok = secrets.token_urlsafe(24)
        TOKEN_FILE.write_text(tok + "\n")
        os.chmod(TOKEN_FILE, 0o600)
    if len(tok) < 16:
        raise SystemExit("jeton en az 16 karakter olmalı")
    return tok


def sh(cmd: list[str], timeout: float = 5.0) -> str:
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


def hardware() -> dict:
    import torch
    info = {"cpu_count": os.cpu_count(), "load": os.getloadavg() if hasattr(os, "getloadavg") else None, "torch": torch.__version__,
            "cuda": torch.cuda.is_available(), "gpus": [], "uptime_s": round(time.time() - START)}
    try:
        mem = {k.strip(): int(v.split()[0]) for k, v in (l.split(":", 1) for l in Path("/proc/meminfo").read_text().splitlines())}
        info["ram_gb"] = [round((mem["MemTotal"] - mem["MemAvailable"]) / 1048576, 1), round(mem["MemTotal"] / 1048576, 1)]
    except Exception:
        pass
    du = shutil.disk_usage(ROOT)
    info["disk_free_gb"] = round(du.free / 1e9, 1)
    if info["cuda"]:
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            info["gpus"].append({"name": p.name, "mem_gb": round(p.total_memory / 1e9, 1)})
        q = sh(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"])
        if q:
            try:
                u, mu, mt, tmp = [float(x) for x in q.splitlines()[0].split(",")]
                info["gpu_live"] = {"util": u, "mem_used_mb": mu, "mem_total_mb": mt, "temp_c": tmp}
            except ValueError:
                pass
    info["git"] = {"commit": sh(["git", "rev-parse", "--short", "HEAD"]), "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
                   "dirty": bool(sh(["git", "status", "--porcelain", "--untracked-files=no"]))}
    return info


def list_files(rel: str) -> dict:
    p = (ROOT / rel).resolve()
    ok = any(((ROOT / r).resolve() == p) or ((ROOT / r).resolve() in p.parents) for r in FILE_ROOTS)
    if not ok or "token" in p.name.lower():
        raise R.ParamError("yalnız results/ ve docs/ okunabilir")
    if p.is_dir():
        rows = []
        for c in sorted(p.iterdir()):
            if "token" in c.name.lower():
                continue
            rows.append({"name": c.name, "dir": c.is_dir(), "size": c.stat().st_size if c.is_file() else None, "mtime": c.stat().st_mtime})
        return {"path": str(p.relative_to(ROOT)), "entries": rows[:500]}
    if p.is_file():
        data = p.read_bytes()
        if b"\0" in data[:2000]:
            return {"path": str(p.relative_to(ROOT)), "binary": True, "size": len(data)}
        tail = len(data) > MAX_READ
        return {"path": str(p.relative_to(ROOT)), "size": len(data), "truncated": tail, "text": data[-MAX_READ:].decode("utf-8", "replace")}
    raise R.ParamError("yok")


class App:
    FAIL_DELAY = 0.5

    def __init__(self, token: str, jobs: JobManager | None = None, live: LiveSession | None = None):
        self.token = token
        self.jobs = jobs or JobManager()
        self.live = live or LiveSession()
        self.fails: dict[str, list[float]] = {}
        self.lock = threading.Lock()
        self.relay_info: dict = {}

    # --- kimlik
    def check(self, supplied: str | None) -> bool:
        return bool(supplied) and hmac.compare_digest(supplied.encode(), self.token.encode())

    def locked(self, ip: str) -> bool:
        with self.lock:
            now = time.time()
            self.fails[ip] = [t for t in self.fails.get(ip, []) if now - t < 60]
            return len(self.fails[ip]) >= 10

    def fail(self, ip: str) -> None:
        with self.lock:
            self.fails.setdefault(ip, []).append(time.time())
        time.sleep(self.FAIL_DELAY)

    # --- API iş mantığı (kuyruk görünümü vb.)
    def overview(self) -> dict:
        self.jobs.reconcile()
        jobs = [self.jobs.view(j) for j in self.jobs.state["jobs"]]
        done_ids = {j["test_id"] for j in jobs if j["status"] == "done"}
        queued_ids = {j["test_id"] for j in jobs if j["status"] in ("queued", "running")}
        return {"time": time.time(), "hardware": hardware(), "auto": self.jobs.state["auto"], "max_running": self.jobs.max_running,
                "jobs": jobs, "suggested": R.suggest(done_ids, queued_ids), "relay": self.relay_info}

    def summary_text(self) -> str:
        """Uzaktaki ajanın tek istekle okuyacağı özet (gerçek durum)."""
        o = self.overview()
        hw = o["hardware"]
        L = [f"# Sunucu özeti ({time.strftime('%F %T')})", f"commit {hw['git']['commit']} ({hw['git']['branch']}){' — kirli' if hw['git']['dirty'] else ''}; "
             f"CPU {hw['cpu_count']} çekirdek; CUDA {'var: ' + ', '.join(g['name'] for g in hw['gpus']) if hw['cuda'] else 'yok'}; otomatik kuyruk {'AÇIK' if o['auto'] else 'kapalı'}", ""]
        for j in o["jobs"][-12:]:
            pr = f" — {j['progress']['text']}" if j.get("progress") else ""
            L.append(f"- {j['id']} {j['test_id']} [{j['status']}] deneme {j['attempts']}{pr}")
        L.append("")
        L.append("Önerilen sıradaki işler: " + ", ".join(s["id"] + ("" if s["runnable"] else f" (engelli: {s['blocked_reason']})") for s in o["suggested"]))
        return "\n".join(L)


class Handler(BaseHTTPRequestHandler):
    server_version = "SinekOps/1"
    app: App

    def log_message(self, fmt, *args):                     # sessiz; kimlik bilgisi günlüğe girmesin
        pass

    # --- yardımcılar
    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8", extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200, extra: dict | None = None) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode(), extra=extra)

    def _token(self, qs: dict) -> str | None:
        h = self.headers.get("Authorization", "")
        if h.startswith("Bearer "):
            return h[7:].strip()
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "ops_token":
                return v
        return None

    def _auth(self, qs: dict) -> bool:
        ip = self.client_address[0]
        if self.app.locked(ip):
            self._json({"error": "çok fazla yanlış deneme; 1 dk bekleyin"}, 429)
            return False
        tok = self._token(qs)
        if self.app.check(tok):
            return True
        self.app.fail(ip)
        self._json({"error": "yetkisiz: geçerli jeton gerekli"}, 401)
        return False

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 100_000:
            raise R.ParamError("gövde çok büyük")
        if n == 0:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except json.JSONDecodeError:
            raise R.ParamError("geçersiz JSON")

    def _same_origin(self) -> bool:
        o = self.headers.get("Origin")
        return o is None or urlparse(o).netloc == self.headers.get("Host")

    # --- GET
    def do_GET(self):
        u = urlparse(self.path)
        qs = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/" and "token" in qs:                 # tarayıcı girişi: jetonu çereze çevir, adres çubuğundan sil
                if self.app.check(qs["token"]):
                    return self._send(303, b"", extra={"Location": "/", "Set-Cookie": f"ops_token={qs['token']}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000"})
                self.app.fail(self.client_address[0])
                return self._json({"error": "yetkisiz"}, 401)
            if u.path in ("/", "/index.html"):
                if not self.app.check(self._token(qs)):
                    return self._send(401, "<meta charset=utf-8><p>Jeton gerekli. Adres: <code>/?token=…</code></p>".encode(), "text/html; charset=utf-8")
                return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            if not self._auth(qs):
                return
            a = self.app
            if u.path == "/api/overview":
                return self._json(a.overview())
            if u.path == "/api/summary":
                return self._send(200, a.summary_text().encode(), "text/plain; charset=utf-8")
            if u.path == "/api/tests":
                return self._json([t.public() for t in R.REGISTRY.values()])
            if u.path.startswith("/api/jobs/") and u.path.endswith("/log"):
                jid = u.path.split("/")[3]
                return self._send(200, a.jobs.log_tail(jid, int(qs.get("bytes", 20000))).encode(), "text/plain; charset=utf-8")
            if u.path == "/api/files":
                return self._json(list_files(qs.get("path", "results")))
            if u.path == "/api/replays":
                return self._json(replay_list())
            if u.path == "/api/replay":
                return self._json(replay_read(qs.get("name", "")))
            if u.path == "/api/live/state":
                return self._json(a.live.state())
            if u.path == "/api/live/stream":
                return self._stream()
            return self._json({"error": "yok"}, 404)
        except R.ParamError as e:
            return self._json({"error": str(e)}, 400)
        except Exception as e:                                  # ayrıntıyı sızdırma; türü ver
            return self._json({"error": f"sunucu hatası: {type(e).__name__}"}, 500)

    def _stream(self) -> None:
        live = self.app.live
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        try:
            last, first = live.snapshot()
            for data in first:
                self.wfile.write(b"data: " + data + b"\n\n")
            self.wfile.flush()
            while True:
                r = live.wait_frame(last, 15.0)
                if r is None:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                last, data = r
                self.wfile.write(b"data: " + data + b"\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    # --- POST
    def do_POST(self):
        u = urlparse(self.path)
        qs = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if not self._auth(qs):
                return
            if not self._same_origin():
                return self._json({"error": "başka kaynaktan istek reddedildi"}, 403)
            b, a, p = self._body(), self.app, u.path
            if p == "/api/queue":
                j = a.jobs.enqueue(b.get("test_id", ""), b.get("params"), source=b.get("source", "api"), confirm=bool(b.get("confirm")))
                return self._json(a.jobs.view(j))
            if p.startswith("/api/jobs/"):
                _, _, _, jid, act = p.split("/")
                if act == "cancel":
                    return self._json(a.jobs.view(a.jobs.cancel(jid)))
                if act == "start":
                    return self._json(a.jobs.view(a.jobs.start_now(jid)))
                if act == "retry":
                    return self._json(a.jobs.view(a.jobs.retry(jid)))
                if act in ("up", "down"):
                    a.jobs.move(jid, -1 if act == "up" else 1)
                    return self._json({"ok": True})
            if p == "/api/auto":
                a.jobs.set_auto(bool(b.get("on")))
                return self._json({"auto": a.jobs.state["auto"]})
            if p == "/api/max_running":
                a.jobs.set_max_running(int(b.get("n", 1)))
                return self._json({"max_running": a.jobs.max_running})
            if p == "/api/update":
                return self._json(update_code(a))
            if p == "/api/live/start":
                a.live.start(b.get("pre", ""), b.get("game", ""), b.get("arm", ""), int(b.get("seed", 140)), int(b.get("agents", 2)), int(b.get("trials", 2)),
                             float(b.get("seconds", 30)), b.get("device", "cpu"), float(b.get("fps", 20)), int(b.get("threads", 2)), int(b.get("episodes", 0)))
                return self._json({"ok": True})
            if p == "/api/live/stop":
                a.live.stop()
                return self._json({"ok": True})
            if p == "/api/live/pause":
                a.live.pause(bool(b.get("on", True)))
                return self._json({"ok": True})
            if p == "/api/live/speed":
                a.live.set_speed(float(b.get("x", 1)))
                return self._json({"ok": True})
            return self._json({"error": "yok"}, 404)
        except R.ParamError as e:
            return self._json({"error": str(e)}, 400)
        except (ValueError, TypeError) as e:
            return self._json({"error": f"geçersiz girdi: {e}"}, 400)
        except Exception as e:
            return self._json({"error": f"sunucu hatası: {type(e).__name__}"}, 500)


def update_code(app: App) -> dict:
    """Kodu güncelle (git pull --ff-only). Çalışan iş varken reddedilir (komut dosyaları iş sırasında değişmesin)."""
    if app.jobs.running():
        raise R.ParamError("çalışan iş var; bitmesini bekleyin ya da durdurun")
    before = sh(["git", "rev-parse", "--short", "HEAD"])
    branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    r = subprocess.run(["git", "pull", "--ff-only", "origin", branch], cwd=ROOT, capture_output=True, text=True, timeout=120)
    after = sh(["git", "rev-parse", "--short", "HEAD"])
    return {"ok": r.returncode == 0, "before": before, "after": after, "output": (r.stdout + r.stderr)[-1500:],
            "note": "arayüz/sunucu kodu değiştiyse sunucuyu yeniden başlatın" if before != after else "değişiklik yok"}


def make_server(host: str, port: int, token: str, jobs: JobManager | None = None, live: LiveSession | None = None) -> tuple[ThreadingHTTPServer, App]:
    app = App(token, jobs, live)
    handler = type("H", (Handler,), {"app": app})
    srv = ThreadingHTTPServer((host, port), handler)
    srv.daemon_threads = True
    return srv, app


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default=None, help="verilmezse SINEK_OPS_TOKEN ya da ~/.sinek_ops_token (yoksa üretilir)")
    ap.add_argument("--auto", action="store_true", help="açılışta otomatik kuyruğu aç (kuyruktaki işler sırayla koşar)")
    ap.add_argument("--max-running", type=int, default=1)
    ap.add_argument("--relay", default=None, help="git yayını için uzak:dal (ör. origin:ops-relay) — bağlantı kabul edemeyen makineler için (docs/uzak_kontrol.md)")
    a = ap.parse_args(argv)
    token = load_or_create_token(a.token)
    jobs = JobManager(max_running=a.max_running)
    if a.auto:
        jobs.set_auto(True)
    jobs.start()
    srv, app = make_server(a.host, a.port, token, jobs)
    if a.relay:
        from .relay import Relay
        Relay(app, a.relay, token).start()
    print(f"Sinek kontrol sunucusu: http://{a.host}:{a.port}/?token={token}", flush=True)
    if a.host not in ("127.0.0.1", "localhost", "::1"):
        print("UYARI: ağdan erişime açık ve TLS yok. İnternet üzerinden doğrudan açmayın; tünel/VPN kullanın (docs/uzak_kontrol.md).", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("kapatılıyor (çalışan işler devam eder; yeniden başlatınca bağlanır)")


if __name__ == "__main__":
    main()
