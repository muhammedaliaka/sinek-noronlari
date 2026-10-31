"""SUNUCUSUZ test ekranı (K-063): tarayıcı, port, HTTP yok. Tek terminal penceresinde: makine durumu, çalışan iş + ilerleme, sıra,
SIRADAKİ 5 ÖNERİ (rakam tuşuyla sıraya ekle), canlı oyun (ASCII arena; gerçek dünya durumu) ve tuş yardımı.
Uzaktan erişim (isteğe bağlı) yine git yayını ile: `--relay origin:ops-relay` (gelen kapı yok; imzalı komutlar GitHub dalından okunur).

    python -X utf8 -I -m sinek.ops.ekran                       # ekran (pencere açık kalmalı)
    python -X utf8 -I -m sinek.ops.ekran --relay origin:ops-relay --auto
    python -X utf8 -I -m sinek.ops.ekran --once                # tek kare yaz ve çık (günlük/sınama)
    python -X utf8 -I -m sinek.ops.ekran --headless --relay …  # ekransız (arka plan; yalnız iş yöneticisi + git yayını)

Tuşlar: 1-5 öneriyi sıraya ekle · a otomatik sıra · g canlı oyunu başlat · o oyun değiştir · k kol değiştir · p duraklat · x canlıyı durdur ·
c çalışan işi durdur · y/n onay · q çık.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import sys
import time

from . import registry as R
from .jobs import JobManager
from .live import LIVE_ARMS, LIVE_GAMES, LiveSession
from .server import App, load_or_create_token

DIRS = ">/^\\</v\\"          # 8 yön (ASCII): 0°=sağ, 45°=yukarı-sağ …; Windows eski konsolunda da görünür


def bar(done: float, total: float, width: int = 24) -> str:
    f = 0 if total <= 0 else max(0.0, min(1.0, done / total))
    n = int(round(f * width))
    return "[" + "#" * n + "-" * (width - n) + f"] {100 * f:3.0f}%"


def dur(s: float) -> str:
    s = int(s)
    h, m = s // 3600, s % 3600 // 60
    return f"{h} sa {m} dk" if h else f"{m} dk {s % 60} sn" if m else f"{s} sn"


def render_arena(layout: dict, frame: dict | None, trail: list, i: int, w: int = 22, h: int = 10) -> list[str]:
    """Bir canlının arenası (gerçek konumlar). Kaynaklar: + ödül, - ceza (ısı tuzağı), 0 ödülsüz; canlı: yön oku; iz: ."""
    L = float(layout["arena"])
    g = [[" "] * w for _ in range(h)]

    def put(x, y, ch):
        cx = min(w - 1, max(0, int(x / L * w)))
        cy = min(h - 1, max(0, h - 1 - int(y / L * h)))
        g[cy][cx] = ch

    for x, y in trail:
        put(x, y, ".")
    for s in range(2):
        if layout["active"][i][s]:
            r = layout["reward"][i][s]
            put(*layout["src"][i][s], "+" if r > 0 else "-" if r < 0 else "0")
    if frame:
        import math
        a = frame["h"][i] % (2 * math.pi)
        ch = "X" if frame["done"][i] else DIRS[int(round(a / (math.pi / 4))) % 8]
        put(frame["x"][i], frame["y"][i], ch)
    return ["+" + "-" * w + "+"] + ["|" + "".join(r) + "|" for r in g] + ["+" + "-" * w + "+"]


class Ui:
    def __init__(self, app: App):
        self.app = app
        self.msg, self.msg_t = "", 0.0
        self.pending: dict | None = None        # onay bekleyen doğrulayıcı
        self.sug: list[dict] = []
        self.game_i = LIVE_GAMES.index("O6a") if "O6a" in LIVE_GAMES else 0
        self.arm_i = LIVE_ARMS.index("plastic")
        self.trails: dict[int, list] = {}
        self.last_layout_ep = None
        self.quit = False

    # ------------------------------------------------------------- eylemler
    def say(self, m: str) -> None:
        self.msg, self.msg_t = m, time.time()

    def defaults(self, t: R.TestDef) -> dict:
        pres = R.find_pre_files()
        pre = next((p for p in pres if "demo" in p), pres[0] if pres else None)
        return {p.name: pre for p in t.params if p.kind == "pre" and pre}

    def add(self, k: int, confirm: bool = False) -> None:
        if not 1 <= k <= len(self.sug):
            return self.say(f"{k}. öneri yok")
        s = self.sug[k - 1]
        t = R.REGISTRY[s["id"]]
        try:
            j = self.app.jobs.enqueue(t.id, self.defaults(t), source="ekran", confirm=confirm)
            self.say(f"sıraya eklendi: {t.title} ({j['id']})")
        except R.ParamError as e:
            if t.validator and not confirm and "onay" in str(e):
                self.pending = {"k": k, "title": t.title}
                self.say(f"DOĞRULAYICI KOŞU: {t.title} — ölçütler koşudan sonra değişmez. Onaylıyor musunuz? (y/n)")
            else:
                self.say(f"eklenemedi: {e}")

    def live_start(self) -> None:
        pres = R.find_pre_files()
        if not pres:
            return self.say("ön-eğitim dosyası yok: önce 'Hızlı demo popülasyonu' önerisini ekleyin")
        pre = next((p for p in pres if "demo" in p), pres[0])
        self.trails.clear()
        try:
            self.app.live.start(pre, LIVE_GAMES[self.game_i], LIVE_ARMS[self.arm_i], 140, agents=2, trials=2, seconds=30.0, fps=20.0, threads=2)
            self.say(f"canlı oyun başlıyor: {LIVE_GAMES[self.game_i]} / {LIVE_ARMS[self.arm_i]}")
        except R.ParamError as e:
            self.say(f"başlatılamadı: {e}")

    def key(self, k: str) -> None:
        k = k.lower()
        if self.pending:
            p, self.pending = self.pending, None
            if k == "y":
                return self.add(p["k"], confirm=True)
            return self.say("iptal edildi")
        jobs, live = self.app.jobs, self.app.live
        if k in "12345" and k:
            self.add(int(k))
        elif k == "a":
            jobs.set_auto(not jobs.state["auto"])
            self.say("otomatik sıra " + ("AÇIK" if jobs.state["auto"] else "kapalı"))
        elif k == "g":
            self.live_start()
        elif k == "o":
            self.game_i = (self.game_i + 1) % len(LIVE_GAMES)
            self.say(f"oyun: {LIVE_GAMES[self.game_i]} (g ile başlatın)")
        elif k == "k":
            self.arm_i = (self.arm_i + 1) % len(LIVE_ARMS)
            self.say(f"kol: {LIVE_ARMS[self.arm_i]} (g ile başlatın)")
        elif k == "p":
            live.pause(not live.pause_flag.is_set())
        elif k == "x":
            live.stop()
            self.say("canlı oyun durduruluyor")
        elif k == "c":
            run = jobs.running()
            if run:
                jobs.cancel(run[0]["id"])
                self.say("çalışan iş durduruluyor")
            else:
                self.say("çalışan iş yok")
        elif k == "q":
            self.quit = True

    # ------------------------------------------------------------- çizim
    def frames(self):
        seq, msgs = self.app.live.snapshot()
        lay = fr = None
        for b in msgs:
            d = json.loads(b)
            if d["type"] == "layout":
                lay = d
            elif d["type"] == "frame":
                fr = d
        return lay, fr

    def lines(self, width: int = 100, height: int = 40) -> list[str]:
        a = self.app
        ov = a.overview()
        hw = ov["hardware"]
        self.sug = ov["suggested"]
        jobs = ov["jobs"]
        run = [j for j in jobs if j["status"] == "running"]
        que = [j for j in jobs if j["status"] == "queued"]
        L: list[str] = []
        gpu = ", ".join(g["name"] for g in hw["gpus"]) if hw["cuda"] else "yok (yalnız CPU)"
        L.append(f"SİNEK TEST EKRANI   kod {hw['git']['commit']}   CPU {hw['cpu_count']}   RAM {'/'.join(map(str, hw['ram_gb'])) if hw.get('ram_gb') else '?'} GB   GPU {gpu}")
        rl = ov.get("relay") or {}
        L.append(f"otomatik sıra: {'AÇIK' if ov['auto'] else 'kapalı'}   uzak yol (git yayını): " +
                 ("kapalı" if not rl else f"{rl.get('branch')} — " + ("HATA: " + rl['error'] if rl.get("error") else "çalışıyor")))
        L.append("=" * min(width, 100))
        L.append("ŞU AN ÇALIŞAN")
        if not run:
            L.append("  (iş yok)" + ("   — sırada iş var; 'a' ile otomatiği açın" if que and not ov["auto"] else ""))
        for j in run:
            p = j.get("progress")
            L.append(f"  {j['title']}  {dur(j.get('elapsed', 0))}  deneme {j['attempts']}")
            L.append("  " + (bar(p["done"], p["total"]) + "  " + p["text"] if p else "ilerleme ölçülemiyor (yalnız geçen süre)"))
            tail = [l for l in a.jobs.log_tail(j["id"], 3000).splitlines() if l.strip()][-2:]
            L += ["  | " + t[:width - 6] for t in tail]
        L.append("SIRA")
        L += [f"  {i + 1}. {j['title']}" for i, j in enumerate(que[:6])] or ["  (boş)"]
        fin = [j for j in jobs if j["status"] in ("done", "failed", "interrupted")][-3:]
        if fin:
            L.append("SON BİTENLER: " + " | ".join(f"{j['test_id']} {j['status']}" + (f" (çıkış {j['exit_code']})" if j.get('exit_code') not in (None, 0) else "") for j in fin))
        L.append("SIRADAKİ 5 ÖNERİ  (rakam tuşu = sıraya ekle)")
        for i, s in enumerate(self.sug):
            note = "" if s["runnable"] else f"   [engelli: {s['blocked_reason']}]"
            wait = f"   [önce: {', '.join(s['waiting_for'])}]" if s["waiting_for"] else ""
            L.append(f"  [{i + 1}] {s['title']}{note}{wait}")
            L.append(f"      {s['why']}"[:width])
        L.append("-" * min(width, 100))
        st = a.live.status
        lc = a.live.cfg or {}
        L.append(f"CANLI OYUN  seçili: {LIVE_GAMES[self.game_i]} / {LIVE_ARMS[self.arm_i]}   durum: {st.get('state')}" + (f" ({st['error'][:60]})" if st.get("error") else "") +
                 ("   [DURAKLATILDI]" if a.live.pause_flag.is_set() else ""))
        lay, fr = self.frames()
        if lay and fr:
            if self.last_layout_ep != (lay["ep"], lay["game"]):
                self.trails.clear()
                self.last_layout_ep = (lay["ep"], lay["game"])
            for i in range(lay["B"]):
                t = self.trails.setdefault(i, [])
                if not t or t[-1] != [fr["x"][i], fr["y"][i]]:
                    t.append([fr["x"][i], fr["y"][i]])
                    del t[:-70]
            per = max(1, min(lay["B"], width // 26))
            panels = []
            for i in range(lay["B"]):
                ar = render_arena(lay, fr, self.trails[i], i)
                sl = fr["slot"][i]
                cap = f"canlı {i + 1}: " + ("bitti" if fr["done"][i] else "yiyor" if fr["feed"][i] else "geziyor") + ("" if sl < 0 else f" · ilk temas yuva {sl}")
                panels.append(ar + [cap[:24].ljust(24)])
            for s0 in range(0, len(panels), per):
                grp = panels[s0:s0 + per]
                for r in range(len(grp[0])):
                    L.append("  ".join(p[r].ljust(24) for p in grp))
            L.append(f"  bölüm {fr['ep']}  t={fr['t']} sn   gösterge: + ödül · - ceza (ısı tuzağı) · 0 ödülsüz · ok=canlı · .=iz · X=bitti")
        else:
            L.append("  (canlı oyun yok — 'g' ile başlatın; ön-eğitim dosyası gerekir)")
        h = a.live.history
        if h:
            n = len(h)
            L.append(f"  {n} bölüm: ilk temas hedef %{100 * sum(r['first_good'] for r in h) / n:.0f} · diğer %{100 * sum(r['first_other'] for r in h) / n:.0f} · yok %{100 * sum(r['none'] for r in h) / n:.0f}   (gözlem, kanıt değil)")
        L.append("=" * min(width, 100))
        if self.msg and time.time() - self.msg_t < 15:
            L.append(">> " + self.msg)
        L.append("TUŞLAR: 1-5 ekle · a otomatik · g canlı başlat · o oyun · k kol · p duraklat · x canlıyı durdur · c işi durdur · q çık")
        return [l[:width] for l in L]


# ============================================================ terminal G/Ç
class Keys:
    """Bloklamadan tek tuş okur (Windows: msvcrt; POSIX: termios+select). TTY değilse hiç tuş yok."""

    def __init__(self):
        self.win = os.name == "nt"
        self.ok = sys.stdin.isatty()
        self.old = None

    def __enter__(self):
        if self.ok and not self.win:
            import termios
            import tty
            self.old = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, *a):
        if self.old is not None:
            import termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old)

    def get(self) -> str | None:
        if not self.ok:
            return None
        if self.win:
            import msvcrt
            return msvcrt.getwch() if msvcrt.kbhit() else None
        import select
        return sys.stdin.read(1) if select.select([sys.stdin], [], [], 0)[0] else None


def enable_ansi() -> None:
    if os.name == "nt":
        os.system("")          # Windows 10+ konsolunda ANSI/VT işlemeyi açar


def run_screen(ui: Ui, fps: float = 4.0, out=None) -> None:
    out = out or sys.stdout
    enable_ansi()
    out.write("\x1b[?1049h\x1b[?25l")
    try:
        with Keys() as keys:
            while not ui.quit:
                size = shutil.get_terminal_size((100, 40))
                text = "\x1b[H" + "\x1b[K\n".join(ui.lines(size.columns, size.lines)[:size.lines - 1]) + "\x1b[K\x1b[J"
                out.write(text)
                out.flush()
                t_end = time.time() + 1.0 / fps
                while time.time() < t_end and not ui.quit:
                    k = keys.get()
                    if k:
                        ui.key(k)
                        break
                    time.sleep(0.03)
    finally:
        out.write("\x1b[?25h\x1b[?1049l")
        out.flush()


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ops-dir", default=None)
    ap.add_argument("--auto", action="store_true", help="otomatik sırayı aç")
    ap.add_argument("--relay", default=None, help="uzak yol: uzak:dal (ör. origin:ops-relay); gelen bağlantı yok")
    ap.add_argument("--max-running", type=int, default=1)
    ap.add_argument("--once", action="store_true", help="tek kare yaz ve çık")
    ap.add_argument("--headless", action="store_true", help="ekransız: yalnız iş yöneticisi + (varsa) git yayını; satır satır günlük")
    a = ap.parse_args(argv)
    token = load_or_create_token()
    jobs = JobManager(a.ops_dir, max_running=a.max_running)
    if a.auto:
        jobs.set_auto(True)
    jobs.start()
    app = App(token, jobs, LiveSession())
    if a.relay:
        from .relay import Relay
        Relay(app, a.relay, token).start()
    ui = Ui(app)
    if a.once:
        print("\n".join(ui.lines(shutil.get_terminal_size((100, 40)).columns)))
        jobs.stop()
        return 0
    stop = {"v": False}
    signal.signal(signal.SIGINT, lambda *_: (setattr(ui, "quit", True), stop.update(v=True)))
    signal.signal(signal.SIGTERM, lambda *_: (setattr(ui, "quit", True), stop.update(v=True)))
    if a.headless:
        last = None
        print("ekransız mod: iş yöneticisi" + (" + git yayını" if a.relay else "") + " çalışıyor (Ctrl-C ile çık; işler yaşar)", flush=True)
        while not stop["v"]:
            sig = [(j["id"], j["status"]) for j in jobs.state["jobs"]]
            if sig != last:
                last = sig
                print(time.strftime("%F %T"), "|", ", ".join(f"{j['test_id']}:{j['status']}" for j in jobs.state["jobs"][-5:]) or "iş yok", flush=True)
            time.sleep(1.0)
        jobs.stop()
        return 0
    try:
        run_screen(ui)
    finally:
        jobs.stop()
    print("ekran kapandı (çalışan işler arka planda sürer; ekranı yeniden açınca bağlanır)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
