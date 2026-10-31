"""İş yöneticisi: kuyruk, süreç başlatma, durum kalıcılığı, yeniden başlatmadan sonra devam.

- Durum `results/ops/state.json` dosyasındadır (atomik yazılır). Sunucu yeniden başlarsa çalışan işler pid ile yeniden bağlanır;
  süreç ölmüşse iş `kesildi` olur ve `resumable` ise (betikler kontrol noktasından AYNI hesapla sürer) otomatik yeniden kuyruğa girer (en çok 3 deneme).
- Her süreç kendi oturumunda (setsid) koşar; çıkış kodu bir dosyaya yazılır, böylece sunucu ölse de kod kaybolmaz.
- Keyfi komut yok: yalnız registry.REGISTRY tanımları, doğrulanmış parametrelerle.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from . import registry as R

ROOT = R.ROOT
MAX_ATTEMPTS = 3


def now() -> float:
    return time.time()


IS_WIN = os.name == "nt"
# Sarmalayıcı (bash'ten bağımsız, her platformda): komutu koşturur, çıkış kodunu dosyaya yazar. Sinyalle ölürse 128+sinyal.
WRAPPER = ("import subprocess,sys;c=subprocess.call(sys.argv[2:]);"
           "open(sys.argv[1],'w').write(str(128-c if c<0 else c))")


def _alive(pid: int) -> bool:
    if IS_WIN:                                  # Windows'ta os.kill(pid, 0) süreci ÖLDÜRÜR; yalnız sorgu yap [denenmedi: Windows]
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259   # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:                                   # zombi (ölü ama toplanmamış) süreç yaşıyor sayılmaz
        st = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
        return st != "Z"
    except Exception:
        return True


class JobManager:
    def __init__(self, ops_dir: str | Path | None = None, registry: dict | None = None, max_running: int = 1, poll: float = 1.0):
        self.dir = Path(ops_dir) if ops_dir else ROOT / "results" / "ops"
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "jobs").mkdir(exist_ok=True)
        self.reg = registry if registry is not None else R.REGISTRY
        self.max_running = max_running
        self.poll = poll
        self.lock = threading.RLock()
        self.state = {"auto": False, "jobs": [], "max_running": max_running}
        self._load()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.reconcile()

    # ------------------------------------------------------------------ kalıcılık
    @property
    def path(self) -> Path:
        return self.dir / "state.json"

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.state = json.loads(self.path.read_text())
            except Exception:
                bad = self.path.with_suffix(".bozuk")
                self.path.replace(bad)
        self.state.setdefault("auto", False)
        self.state.setdefault("jobs", [])
        self.max_running = int(self.state.get("max_running", self.max_running))

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=1))
        tmp.replace(self.path)

    # ------------------------------------------------------------------ sorgular
    def get(self, jid: str) -> dict | None:
        for j in self.state["jobs"]:
            if j["id"] == jid:
                return j
        return None

    def running(self) -> list[dict]:
        return [j for j in self.state["jobs"] if j["status"] == "running"]

    def queued(self) -> list[dict]:
        return [j for j in self.state["jobs"] if j["status"] == "queued"]

    def view(self, j: dict) -> dict:
        out = dict(j)
        t = self.reg.get(j["test_id"])
        if t:
            out["title"] = t.title
            out["group"] = t.group
            out["validator"] = t.validator
            if t.progress and j["status"] in ("running", "queued"):
                try:
                    d, tot, txt = t.progress(j["params"])
                    out["progress"] = {"done": d, "total": tot, "text": txt}
                except Exception:
                    pass
        if j["status"] == "running":
            out["elapsed"] = now() - j.get("started", now())
        elif j.get("started") and j.get("ended"):
            out["elapsed"] = j["ended"] - j["started"]
        return out

    # ------------------------------------------------------------------ komutlar
    def enqueue(self, test_id: str, params: dict | None = None, source: str = "api", confirm: bool = False) -> dict:
        t = self.reg.get(test_id)
        if t is None:
            raise R.ParamError(f"bilinmeyen test: {test_id}")
        ok, why = t.runnable()
        if not ok:
            raise R.ParamError(f"çalıştırılamaz: {why}")
        vals = t.build_params(params)
        if t.validator and not confirm:
            raise R.ParamError("doğrulayıcı koşu: onay gerekir (confirm=true). Ölçütler koşudan sonra değişmez; ön-kayıt: " + str(t.prereg))
        with self.lock:
            if any(j["test_id"] == test_id and j["params"] == vals and j["status"] in ("queued", "running") for j in self.state["jobs"]):
                raise R.ParamError("aynı iş zaten kuyrukta/çalışıyor")
            jid = time.strftime("%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
            job = {"id": jid, "test_id": test_id, "params": vals, "status": "queued", "created": now(), "source": source,
                   "attempts": 0, "log": f"jobs/{jid}.log", "exit_file": f"jobs/{jid}.exit", "argv": t.argv(vals)}
            self.state["jobs"].append(job)
            self._save()
            return job

    def cancel(self, jid: str) -> dict:
        with self.lock:
            j = self.get(jid)
            if j is None:
                raise R.ParamError("iş yok")
            if j["status"] == "queued":
                j["status"], j["ended"] = "cancelled", now()
            elif j["status"] == "running":
                j["cancel_requested"] = True
                self._kill(j)
            self._save()
            return j

    def move(self, jid: str, direction: int) -> None:
        with self.lock:
            q = self.state["jobs"]
            idx = [i for i, j in enumerate(q) if j["status"] == "queued"]
            pos = next((k for k, i in enumerate(idx) if q[i]["id"] == jid), None)
            if pos is None:
                raise R.ParamError("iş kuyrukta değil")
            k = pos + (-1 if direction < 0 else 1)
            if 0 <= k < len(idx):
                q[idx[pos]], q[idx[k]] = q[idx[k]], q[idx[pos]]
                self._save()

    def start_now(self, jid: str) -> dict:
        """Kuyruktaki işi sırayı atlayıp (boş yer varsa) hemen başlatır."""
        with self.lock:
            j = self.get(jid)
            if j is None or j["status"] != "queued":
                raise R.ParamError("iş kuyrukta değil")
            if len(self.running()) >= self.max_running:
                raise R.ParamError(f"en çok {self.max_running} iş aynı anda çalışır; birini durdurun")
            self._launch(j)
            return j

    def set_auto(self, on: bool) -> None:
        with self.lock:
            self.state["auto"] = bool(on)
            self._save()

    def set_max_running(self, n: int) -> None:
        with self.lock:
            self.max_running = max(1, min(8, int(n)))
            self.state["max_running"] = self.max_running
            self._save()

    # ------------------------------------------------------------------ süreç
    def _launch(self, j: dict) -> None:
        logp, exitp = self.dir / j["log"], self.dir / j["exit_file"]
        exitp.unlink(missing_ok=True)
        t = self.reg[j["test_id"]]
        argv = t.argv(j["params"])
        j["argv"] = argv
        wrapper = [sys.executable, "-I", "-c", WRAPPER, str(exitp), *argv]
        kw = {"creationflags": 0x00000200 | 0x00000008} if IS_WIN else {"start_new_session": True}   # yeni süreç grubu / ayrık
        with open(logp, "ab") as lf:
            lf.write(f"\n=== {time.strftime('%F %T')} başlıyor (deneme {j['attempts'] + 1}): {' '.join(argv)}\n".encode())
            lf.flush()
            p = subprocess.Popen(wrapper, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kw)
        j.update(status="running", pid=p.pid, started=now(), attempts=j["attempts"] + 1)
        j.pop("ended", None)
        j.pop("exit_code", None)
        self._popen = getattr(self, "_popen", {})
        self._popen[j["id"]] = p
        self._save()

    def _kill(self, j: dict) -> None:
        pid = j.get("pid")
        if not pid:
            return
        if IS_WIN:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)    # [denenmedi: Windows]
            return
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        threading.Thread(target=self._hard_kill, args=(pid,), daemon=True).start()

    @staticmethod
    def _hard_kill(pid: int) -> None:
        for _ in range(50):
            if not _alive(pid):
                return
            time.sleep(0.1)
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def reconcile(self) -> None:
        """Çalışıyor görünen işleri gerçek duruma getir; biten/kesilenleri işle; gerekirse devam ettir."""
        with self.lock:
            changed = False
            for j in self.state["jobs"]:
                if j["status"] != "running":
                    continue
                exitp = self.dir / j["exit_file"]
                pid = j.get("pid")
                popen = getattr(self, "_popen", {}).get(j["id"])
                if popen is not None:
                    popen.poll()
                if exitp.exists() and (popen is None or popen.poll() is not None):
                    try:
                        code = int(exitp.read_text().strip())
                    except ValueError:
                        code = -1
                    j["exit_code"], j["ended"] = code, now()
                    t = self.reg.get(j["test_id"])
                    if j.get("cancel_requested"):
                        j["status"] = "cancelled"
                    elif code == 0:
                        j["status"] = "done"
                    elif t and t.resumable and code in (130, 137, 143) and j["attempts"] < MAX_ATTEMPTS:
                        j["status"] = "queued"                      # sinyalle kesildi: aynı hesapla devam
                        j["note"] = f"sinyal ({code}) ile kesildi; kontrol noktasından devam"
                    else:
                        j["status"] = "failed"
                    changed = True
                elif pid and not _alive(pid):
                    if j.get("cancel_requested"):
                        j["status"], j["ended"] = "cancelled", now()
                    else:
                        t = self.reg.get(j["test_id"])
                        if t and t.resumable and j["attempts"] < MAX_ATTEMPTS:
                            j["status"], j["note"] = "queued", "süreç beklenmedik ölü bulundu (yeniden başlatma?); kontrol noktasından devam"
                        else:
                            j["status"], j["ended"], j["note"] = "interrupted", now(), "süreç ölü bulundu; çıkış kodu yok. Elle yeniden kuyruğa alın."
                    changed = True
            if self.state["auto"]:
                for j in list(self.queued()):
                    if len(self.running()) >= self.max_running:
                        break
                    self._launch(j)
                    changed = True
            if changed:
                self._save()

    def retry(self, jid: str) -> dict:
        with self.lock:
            j = self.get(jid)
            if j is None or j["status"] not in ("failed", "interrupted", "cancelled"):
                raise R.ParamError("yalnız başarısız/kesilen/iptal işler yeniden kuyruğa alınır")
            j["status"] = "queued"
            j.pop("cancel_requested", None)
            j["note"] = "elle yeniden kuyruğa alındı"
            self._save()
            return j

    # ------------------------------------------------------------------ günlük
    def log_tail(self, jid: str, max_bytes: int = 20000) -> str:
        j = self.get(jid)
        if j is None:
            raise R.ParamError("iş yok")
        p = self.dir / j["log"]
        if not p.exists():
            return ""
        size = p.stat().st_size
        with open(p, "rb") as f:
            f.seek(max(0, size - max_bytes))
            return f.read().decode("utf-8", "replace")

    # ------------------------------------------------------------------ döngü
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ops-jobs")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.wait(self.poll):
            try:
                self.reconcile()
            except Exception as e:           # döngü ölmemeli
                print("iş döngüsü hatası:", repr(e), flush=True)
