"""Git yayını (relay): makine dışarıdan bağlantı KABUL edemiyorsa (güvenlik duvarı/NAT/tünel yok), sunucu GitHub'daki bir dalı (varsayılan `ops-relay`)
dakikada bir yoklar: oradaki imzalı komutları uygular, durum ve biten işlerin raporlarını aynı dala yazar. Uzaktaki ajan/kullanıcı aynı dalı okur-yazar.

Güvenlik: komutlar jeton ile HMAC-SHA256 imzalıdır; imzasız/yanlış imzalı/eski (>3 gün)/tekrar eden komut atılır. Dalı yazabilen biri jetonu bilmeden iş başlatamaz.
Yalnız registry'deki işler ve doğrulanmış parametreler çalışır. Ağır dosyalar (npz) ASLA push edilmez; yalnız metin raporu (≤60 KB) ve günlük kuyruğu.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import threading
import time
from pathlib import Path

from . import registry as R

ROOT = R.ROOT
MAX_AGE = 3 * 86400
CYCLE = 15.0                 # ucuz kontrol (git ls-remote) aralığı; tam döngü yalnız uzak dal değişince/yerel durum değişince/5 dk'da bir
FULL_EVERY = 300.0
HEARTBEAT = 900.0            # durum değişmese de en az 15 dk'da bir nabız yazılır
PRUNE_AFTER = 400            # bu kadar itmeden sonra dal tek commit'e sıkıştırılır (depo şişmesin)
REPLAY_PUSH_MAX = 600_000
REPLAY_PUSH_KEEP = 8


def canon(cmd: dict) -> bytes:
    keys = ("id", "ts", "action", "test_id", "params", "confirm", "job_id", "on")
    return json.dumps({k: cmd.get(k) for k in keys}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sign(token: str, cmd: dict) -> str:
    return hmac.new(token.encode(), canon(cmd), hashlib.sha256).hexdigest()


def verify(token: str, cmd: dict, now: float | None = None) -> str | None:
    """None = geçerli; aksi halde ret nedeni."""
    sig = cmd.get("sig")
    if not isinstance(sig, str) or not hmac.compare_digest(sig, sign(token, cmd)):
        return "imza geçersiz"
    ts = cmd.get("ts")
    if not isinstance(ts, (int, float)) or abs((now or time.time()) - ts) > MAX_AGE:
        return "komut çok eski/zaman damgası geçersiz"
    return None


def git(cwd: Path, *args: str, check: bool = True, timeout: float = 90) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


def ensure_clone(path: Path, remote: str, branch: str, url: str | None = None) -> Path:
    """Dalın yerel kopyası (kullanıcının çalışma ağacından AYRI dizin). Dal yoksa yetim (orphan) olarak başlatılır."""
    if not (path / ".git").exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        url = url or git(ROOT, "remote", "get-url", remote).strip()
        subprocess.run(["git", "clone", "--no-checkout", "--depth", "1", url, str(path)], check=True, capture_output=True, timeout=180)
        git(path, "config", "user.name", "sinek-ops")
        git(path, "config", "user.email", "sinek-ops@users.noreply.github.com")
    has = bool(git(path, "ls-remote", "--heads", "origin", branch, check=False).strip())
    if has:
        git(path, "fetch", "--depth", "1", "origin", f"+{branch}:refs/remotes/origin/{branch}")
        git(path, "checkout", "-B", branch, f"origin/{branch}", "--force")
    else:
        git(path, "checkout", "--orphan", branch, check=False)
        git(path, "rm", "-rf", "--quiet", ".", check=False)
    return path


class Relay:
    def __init__(self, app, spec: str, token: str, cycle: float = CYCLE, url: str | None = None, workdir: Path | None = None):
        self.app, self.token, self.cycle, self.url = app, token, cycle, url
        self.remote, _, self.branch = spec.partition(":")
        self.branch = self.branch or "ops-relay"
        self.dir = workdir or ROOT / "results" / "ops" / "relay"
        self.reported: set[str] = set()
        self.stop = threading.Event()
        self.last_head = None
        self.last_full = 0.0
        self.last_sig = None
        self.last_push = 0.0

    def start(self) -> None:
        threading.Thread(target=self._loop, daemon=True, name="ops-relay").start()

    def _loop(self) -> None:
        while not self.stop.is_set():
            try:
                if self.due():
                    self.cycle_once()
                self.app.relay_info = {"branch": f"{self.remote}:{self.branch}", "last_sync": time.time(), "error": None}
            except Exception as e:
                self.app.relay_info = {"branch": f"{self.remote}:{self.branch}", "last_sync": time.time(), "error": str(e)[:300]}
            self.stop.wait(self.cycle)

    def remote_head(self) -> str | None:
        try:
            url = self.url or git(ROOT, "remote", "get-url", self.remote).strip()
            out = subprocess.run(["git", "ls-remote", url, f"refs/heads/{self.branch}"], capture_output=True, text=True, timeout=30).stdout.split()
            return out[0] if out else None
        except Exception:
            return self.last_head

    def due(self) -> bool:
        """Ucuz yoklama: uzak dal değiştiyse (yeni komut), yerel iş durumu değiştiyse ya da süre dolduysa tam döngü."""
        now = time.time()
        head = self.remote_head()
        changed = head != self.last_head
        local = self.local_sig() != self.last_sig
        if changed or local or now - self.last_full > FULL_EVERY:
            self.last_head, self.last_full = head, now
            return True
        return False

    def local_sig(self) -> str:
        jobs = [(j["id"], j["status"], j["attempts"], (j.get("progress") or {}).get("done")) for j in self.app.jobs.state["jobs"][-40:]]
        return json.dumps([jobs, self.app.jobs.state["auto"]], default=str)

    # ------------------------------------------------------------------
    def apply(self, cmd: dict) -> str:
        """Tek komutu uygula; sonucu metin olarak döndür (hata = 'HATA: ...')."""
        j = self.app.jobs
        try:
            a = cmd.get("action")
            if a == "enqueue":
                job = j.enqueue(cmd.get("test_id", ""), cmd.get("params"), source="relay", confirm=bool(cmd.get("confirm")))
                return f"sıraya alındı: {job['id']}"
            if a == "cancel":
                return "iptal: " + j.cancel(cmd.get("job_id", ""))["status"]
            if a == "start":
                return "başladı: " + j.start_now(cmd.get("job_id", ""))["id"]
            if a == "retry":
                return "yeniden sırada: " + j.retry(cmd.get("job_id", ""))["id"]
            if a == "auto":
                j.set_auto(bool(cmd.get("on")))
                return f"otomatik={'açık' if cmd.get('on') else 'kapalı'}"
            if a == "update":
                from .server import update_code
                r = update_code(self.app)
                return f"güncelleme: {r['before']}→{r['after']} ({r['note']})"
            return "HATA: bilinmeyen eylem"
        except Exception as e:
            return f"HATA: {e}"

    def cycle_once(self) -> None:
        d = ensure_clone(self.dir, self.remote, self.branch, self.url)
        st_path = d / "status.json"
        prev = json.loads(st_path.read_text()) if st_path.exists() else {}
        acked: dict = prev.get("acked", {})
        for p in sorted((d / "commands").glob("*.json")) if (d / "commands").exists() else []:
            try:
                cmd = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            cid = str(cmd.get("id", p.stem))
            if cid in acked:
                continue
            why = verify(self.token, cmd)
            acked[cid] = {"at": time.time(), "result": ("RET: " + why) if why else self.apply(cmd)}
        acked = dict(sorted(acked.items(), key=lambda kv: kv[1]["at"])[-300:])
        ov = self.app.overview()
        jobs = [{k: j.get(k) for k in ("id", "test_id", "status", "attempts", "created", "started", "ended", "exit_code", "progress", "note", "params")} for j in ov["jobs"][-40:]]
        hw = ov["hardware"]
        status = {"time": time.time(), "auto": ov["auto"], "hardware": {k: hw.get(k) for k in ("cpu_count", "load", "cuda", "gpus", "ram_gb", "disk_free_gb", "git", "torch")},
                  "jobs": jobs, "suggested": [s["id"] for s in ov["suggested"]], "acked": acked}
        (d / "reports").mkdir(exist_ok=True)
        for j in ov["jobs"]:
            if j["status"] in ("done", "failed") and j["id"] not in self.reported and not (d / "reports" / f"{j['id']}.md").exists():
                (d / "reports" / f"{j['id']}.md").write_text(self.report(j), encoding="utf-8")
            self.reported.add(j["id"])
        self.sync_replays(d)
        sig = self.local_sig() + json.dumps(acked, sort_keys=True) + json.dumps(sorted(p.name for p in (d / "replays").glob("*")) if (d / "replays").exists() else [])
        now = time.time()
        if sig == self.last_sig and now - self.last_push < HEARTBEAT and prev:
            return                                               # değişen yok: boşuna commit yok
        status["pushes"] = int(prev.get("pushes", 0)) + 1
        st_path.write_text(json.dumps(status, ensure_ascii=False, indent=1, default=str))
        git(d, "add", "-A")
        if git(d, "status", "--porcelain").strip():
            if status["pushes"] > PRUNE_AFTER:                    # geçmişi sıkıştır: tek commit, zorla it (okunmamış komut kaybolabilir; istemci ack'e bakar)
                status["pushes"] = 1
                st_path.write_text(json.dumps(status, ensure_ascii=False, indent=1, default=str))
                git(d, "checkout", "--orphan", "_yeni")
                git(d, "add", "-A")
                git(d, "commit", "-m", "ops: sıkıştırılmış durum")
                git(d, "push", "--force", "origin", f"HEAD:{self.branch}")
                git(d, "branch", "-M", self.branch)
            else:
                git(d, "commit", "-m", f"ops: durum {time.strftime('%F %T')}")
                git(d, "push", "origin", f"HEAD:{self.branch}")
        self.last_sig, self.last_push = sig, now
        self.last_head = self.remote_head()

    def sync_replays(self, d: Path) -> None:
        """En yeni küçük canlı-izleme tekrarlarını dala koyar (uzaktan izlenebilsin); ağır dosya yok."""
        from .live import REPLAY_DIR
        src = sorted(REPLAY_DIR.glob("*.json.gz"), key=lambda p: p.stat().st_mtime, reverse=True) if REPLAY_DIR.exists() else []
        keep = [p for p in src if p.stat().st_size <= REPLAY_PUSH_MAX][:REPLAY_PUSH_KEEP]
        (d / "replays").mkdir(exist_ok=True)
        want = {p.name for p in keep}
        for old in (d / "replays").glob("*.json.gz"):
            if old.name not in want:
                old.unlink()
        for p in keep:
            t = d / "replays" / p.name
            if not t.exists() or t.stat().st_size != p.stat().st_size:
                t.write_bytes(p.read_bytes())

    def report(self, j: dict) -> str:
        t = self.app.jobs.reg.get(j["test_id"])
        parts = [f"# {j.get('title', j['test_id'])} — {j['id']} [{j['status']}] çıkış={j.get('exit_code')}", f"parametreler: {j['params']}", "",
                 "## Günlük (son 150 satır)", "```", *self.app.jobs.log_tail(j["id"], 30000).splitlines()[-150:], "```"]
        for pat in (t.report_files if t else ()):
            for f in sorted(ROOT.glob(pat))[:5]:
                parts += ["", f"## {f.relative_to(ROOT)}", f.read_text(encoding="utf-8", errors="replace")[:60000]]
        return "\n".join(parts)[:120000]
