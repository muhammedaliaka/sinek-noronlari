"""Canlı oyun izleme: gerçek bir `Creature` bir iş parçacığında koşar; her karede GERÇEK dünya durumu (konum, yön, kaynaklar, temas, değer)
abonelere iletilir. Çizim için uydurma veri yoktur; aynı sayılar kayda geçen sonuçlarla (ilk temas yuvası) örtüşür.

Not: canlı izleme DOĞRULAYICI DEĞİLDİR (geliştirme tohumları 100-149; R-2). Sayılar kanıt sayılmaz.
"""
from __future__ import annotations

import gzip
import json
import re
import threading
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..games.protocol import ARMS, make_game_creature
from ..games.spec import GAMES
from . import registry as R

VIS_GAMES = ("O6b", "O6c")
LIVE_GAMES = tuple(g for g in GAMES if g in ("O1R", "O1a", "O1b", "O2full", "O2near", "O3", "O4a", "O4c", "O5", "O6a", "O6b", "O6c"))
LIVE_ARMS = tuple(ARMS)
SLOT_NAMES = {0: "hedef (yuva 0)", 1: "ikinci kaynak (yuva 1)"}


REPLAY_DIR = R.ROOT / "results" / "ops" / "replays"
REPLAY_KEEP_EVERY = 3            # her 3. kare kaydedilir (≈ 7 kare/sn; tekrar için yeter, dosya küçük kalır)
REPLAY_MAX_FRAMES = 4000


def replay_list() -> list[dict]:
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    return [{"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime} for p in sorted(REPLAY_DIR.glob("*.json.gz"), reverse=True)[:50]]


def replay_read(name: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+\.json\.gz", name) or name not in {r["name"] for r in replay_list()}:
        raise R.ParamError("tekrar yok")
    with gzip.open(REPLAY_DIR / name, "rt", encoding="utf-8") as f:
        return json.load(f)


class LiveSession:
    def __init__(self):
        self.cond = threading.Condition()
        self.seq = 0
        self.latest: bytes = b""         # akış için son mesaj (herhangi tür)
        self.frame: bytes = b""          # son kare (yalnız type=frame)
        self.layout: bytes = b""         # son bölüm yerleşimi: geç bağlanan izleyiciye ilk gönderilir
        self.thread: threading.Thread | None = None
        self.stop_flag = threading.Event()
        self.pause_flag = threading.Event()
        self.status = {"state": "boşta"}
        self.history: list[dict] = []
        self.cfg: dict = {}
        self.speed = 1.0
        self.start_lock = threading.Lock()
        self.rec: dict | None = None
        self.rec_path: Path | None = None
        self._nframe = 0

    # --------------------------------------------------------------------- kontrol
    def start(self, pre: str, game: str, arm: str, seed: int, agents: int = 2, trials: int = 2, seconds: float = 30.0,
              device: str = "cpu", fps: float = 20.0, threads: int = 2, episodes: int = 0) -> None:
        with self.start_lock:                 # iki eşzamanlı başlatma isteği iki iş parçacığı açmasın
            self._start(pre, game, arm, seed, agents, trials, seconds, device, fps, threads, episodes)

    def _start(self, pre, game, arm, seed, agents, trials, seconds, device, fps, threads, episodes) -> None:
        if self.thread and self.thread.is_alive():
            raise R.ParamError("canlı izleme zaten çalışıyor; önce durdurun")
        if game not in LIVE_GAMES:
            raise R.ParamError("oyun geçersiz")
        if arm not in LIVE_ARMS:
            raise R.ParamError("kol geçersiz")
        if not (100 <= seed <= R.DEV_SEED_MAX):
            raise R.ParamError("canlı izleme yalnız geliştirme tohumlarıyla (100-149) çalışır (R-2)")
        if not (1 <= agents <= 6 and trials in (2, 4) and 5 <= seconds <= 90 and 1 <= fps <= 60 and 0 <= episodes <= 500):
            raise R.ParamError("parametre aralığı geçersiz")
        if device not in ("cpu", "cuda"):
            raise R.ParamError("cihaz geçersiz")
        if device == "cuda" and not torch.cuda.is_available():
            raise R.ParamError("CUDA bu makinede yok")
        pre = R.safe_results_file(pre, ".npz")
        self.stop_flag.clear()
        self.pause_flag.clear()
        self.history = []
        self.cfg = dict(pre=pre, game=game, arm=arm, seed=seed, agents=agents, trials=trials, seconds=seconds, device=device, fps=fps, episodes=episodes)
        self.status = {"state": "kuruluyor"}
        name = f"{time.strftime('%m%d-%H%M%S')}_{game}_{arm}_s{seed}.json.gz"
        self.rec = {"format": 1, "cfg": dict(self.cfg), "started": time.time(), "n": 0, "episodes": []}
        self.rec_path = REPLAY_DIR / name
        self._nframe = 0
        self.thread = threading.Thread(target=self._run, args=(threads,), daemon=True, name="ops-live")
        self.thread.start()

    def stop(self) -> None:
        self.stop_flag.set()
        self.pause_flag.clear()

    def pause(self, on: bool) -> None:
        (self.pause_flag.set if on else self.pause_flag.clear)()

    def set_speed(self, x: float) -> None:
        self.speed = max(0.1, min(20.0, float(x)))

    # --------------------------------------------------------------------- yayın
    def _record(self, obj: dict) -> None:
        """Gerçek yayın akışının seyreltilmiş kaydı: uzaktan/sonradan izlenebilsin (sahte üretim yok, aynı kareler)."""
        if self.rec is None:
            return
        t = obj.get("type")
        if t == "layout":
            self.rec["episodes"].append({"layout": obj, "frames": [], "end": None})
        elif t == "frame" and self.rec["episodes"]:
            self._nframe += 1
            ep = self.rec["episodes"][-1]
            if (self._nframe % REPLAY_KEEP_EVERY == 0 or obj.get("done") and all(obj["done"])) and self.rec["n"] < REPLAY_MAX_FRAMES:
                ep["frames"].append(obj)
                self.rec["n"] += 1
        elif t == "episode_end" and self.rec["episodes"]:
            self.rec["episodes"][-1]["end"] = obj
            self._save_replay()

    def _save_replay(self) -> None:
        if self.rec is None or self.rec_path is None:
            return
        self.rec_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.rec_path.with_suffix(".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
            json.dump(self.rec, f, separators=(",", ":"))
        tmp.replace(self.rec_path)

    def _publish(self, obj: dict) -> None:
        self._record(obj)
        data = json.dumps(obj, separators=(",", ":")).encode()
        with self.cond:
            self.seq += 1
            self.latest = data
            if obj.get("type") == "layout":
                self.layout = data
            elif obj.get("type") == "frame":
                self.frame = data
            self.cond.notify_all()

    def wait_frame(self, last_seq: int, timeout: float = 15.0) -> tuple[int, bytes] | None:
        with self.cond:
            if self.seq == last_seq:
                self.cond.wait(timeout)
            if self.seq == last_seq:
                return None
            return self.seq, self.latest

    def snapshot(self) -> tuple[int, list[bytes]]:
        """Yeni bağlanan izleyici için: son yerleşim + son kare (varsa)."""
        with self.cond:
            out = [b for b in (self.layout, self.frame) if b]
            return self.seq, list(dict.fromkeys(out))

    def state(self) -> dict:
        return {"status": self.status, "cfg": self.cfg, "history": self.history[-200:], "speed": self.speed,
                "paused": self.pause_flag.is_set(), "running": bool(self.thread and self.thread.is_alive()),
                "options": {"games": list(LIVE_GAMES), "arms": list(LIVE_ARMS), "pre_files": R.find_pre_files(), "cuda": torch.cuda.is_available()}}

    # --------------------------------------------------------------------- koşu
    def _build(self):
        c = self.cfg
        torch.set_num_threads(2)
        pre = checkpoint.load(c["pre"], device=c["device"])
        ids = list(range(min(c["agents"], pre.world.B)))
        vis = 6 if c["game"] in VIS_GAMES else 0
        cr = make_game_creature(pre, c["game"], c["arm"], ids, c["trials"], c["seed"], vis_feat=vis)
        return cr

    def _frame(self, cr, ep: int, step: int, learn: bool, dt: float) -> dict:
        w = cr.world
        d = lambda t: t.detach().cpu().numpy()          # noqa: E731
        val = d(cr.last_valence)
        fr = {
            "type": "frame", "ep": ep, "step": step, "t": round(step * dt, 2),
            "x": np.round(d(w.pos)[:, 0], 2).tolist(), "y": np.round(d(w.pos)[:, 1], 2).tolist(),
            "h": np.round(d(w.heading), 3).tolist(), "done": d(w.done).astype(int).tolist(),
            "feed": (d(w.feed_timer) > 0).astype(int).tolist(), "slot": d(w.first_contact_slot).tolist(),
            "vl": np.round(val[:, 0], 3).tolist(), "vr": np.round(val[:, 1], 3).tolist(),
        }
        return fr

    def _layout(self, cr, ep: int) -> dict:
        w = cr.world
        d = lambda t: t.detach().cpu().numpy()          # noqa: E731
        spec = w.spec
        return {"type": "layout", "ep": ep, "arena": w.cfg.arena, "contact_radius": w.cfg.contact_radius, "B": w.B,
                "src": np.round(d(w.src_pos), 2).tolist(), "active": d(w.src_active).astype(int).tolist(),
                "odor": d(w.src_odor).tolist(), "vis": d(w.src_vis).tolist(), "reward": d(w.src_reward).tolist(),
                "game": spec.name, "slot_reward": [spec.target.reward, spec.decoy.reward],
                "swap": d(w.swap).astype(int).tolist() if hasattr(w, "swap") else []}

    def _weight_shift(self, cr) -> float | None:
        b = cr.brain
        if hasattr(b, "W") and hasattr(b, "W0"):
            return float((b.W - b.W0).abs().mean())
        return None

    @torch.no_grad()
    def _run(self, threads: int) -> None:
        try:
            torch.set_num_threads(threads)
            cr = self._build()
            c, dt = self.cfg, cr.cfg.world.dt
            learn = ARMS[c["arm"]].eta > 0
            self.status = {"state": "çalışıyor"}
            ep = 0
            while not self.stop_flag.is_set() and (c["episodes"] == 0 or ep < c["episodes"]):
                ep += 1
                cr.reset_episode("game", test=False)
                self._publish(self._layout(cr, ep))
                n = int(round(c["seconds"] / dt))
                t_next = time.time()
                for i in range(n):
                    if self.stop_flag.is_set():
                        break
                    while self.pause_flag.is_set() and not self.stop_flag.is_set():
                        time.sleep(0.1)
                    cr.step(learn=learn)
                    if i % max(1, int(round(1 / (c["fps"] * dt)))) == 0:
                        self._publish(self._frame(cr, ep, i + 1, learn, dt))
                        t_next += 1.0 / (c["fps"] * self.speed)
                        sl = t_next - time.time()
                        if sl > 0:
                            time.sleep(min(sl, 1.0))
                        else:
                            t_next = time.time()
                    if bool(cr.world.done.all()):
                        break
                out = {k: v.cpu().numpy() for k, v in cr.world.outcome().items()}
                slots = out["slot"].tolist()
                good = [int(s == 0) for s in slots]
                bad = [int(s == 1) for s in slots]
                rec = {"ep": ep, "slots": slots, "first_good": float(np.mean(good)), "first_other": float(np.mean(bad)),
                       "none": float(np.mean([s < 0 for s in slots])), "w_shift": self._weight_shift(cr)}
                self.history.append(rec)
                self._publish(self._frame(cr, ep, i + 1, learn, dt))
                self._publish({"type": "episode_end", **rec})
                time.sleep(0.6)
            self._save_replay()
            self.status = {"state": "durdu" if self.stop_flag.is_set() else "bitti", "episodes": ep, "replay": self.rec_path.name if self.rec_path else None}
        except Exception as e:                      # arayüze gerçek hatayı göster
            self.status = {"state": "hata", "error": f"{type(e).__name__}: {e}"}
            self._publish({"type": "error", "error": self.status["error"]})
