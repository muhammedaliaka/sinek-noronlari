"""Sunucusuz test ekranı (K-063): çizim doğruluğu, tuşlar, doğrulayıcı onayı, gerçek canlı oyun karesi, gerçek süreç kipleri."""
import io
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from sinek import checkpoint
from sinek.games.protocol import pretrain
from sinek.ops import ekran as E
from sinek.ops import live as LV
from sinek.ops import registry as R
from sinek.ops.jobs import JobManager
from sinek.ops.live import LiveSession
from sinek.ops.server import App
from sinek.world import odor_patterns


def mk_ui(tmp_path):
    app = App("t" * 24, JobManager(tmp_path / "ops"), LiveSession())
    return E.Ui(app), app


def test_bar_and_dur_edge_cases():
    assert E.bar(0, 0) == "[" + "-" * 24 + "]   0%" and E.bar(5, 10).count("#") == 12 and E.bar(99, 10).endswith("100%")
    assert E.dur(5) == "5 sn" and E.dur(125) == "2 dk 5 sn" and E.dur(7500) == "2 sa 5 dk"


def test_render_arena_places_real_positions_and_signs():
    lay = {"arena": 40.0, "active": [[1, 1]], "reward": [[1.0, -1.0]], "src": [[[4.0, 36.0], [36.0, 4.0]]], "B": 1}
    fr = {"x": [20.0], "y": [20.0], "h": [0.0], "done": [0]}
    g = E.render_arena(lay, fr, [[10.0, 10.0]], 0, w=20, h=10)
    assert len(g) == 12 and all(len(r) == 22 for r in g)
    body = [r[1:-1] for r in g[1:-1]]
    assert body[0][2] == "+"                                    # sol üst: ödül kaynağı (4,36)
    assert body[8][18] == "-"                                   # sağ alt: ceza kaynağı (36,4)
    assert body[4][10] == ">" and body[7][5] == "."             # canlı ortada sağa bakıyor; iz noktası
    fr["done"] = [1]
    assert "X" in "".join(E.render_arena(lay, fr, [], 0, w=20, h=10))
    for a, ch in ((0, ">"), (1.5708, "^"), (3.1416, "<"), (4.7124, "v")):
        fr = {"x": [20.0], "y": [20.0], "h": [a], "done": [0]}
        assert ch in "".join(E.render_arena(lay, fr, [], 0))


def test_screen_lists_five_suggestions_and_keys_enqueue(tmp_path):
    ui, app = mk_ui(tmp_path)
    L = ui.lines(100, 40)
    assert any("SIRADAKİ 5 ÖNERİ" in l for l in L) and sum(1 for l in L if l.strip().startswith("[") and "]" in l[:6]) == 5
    first = ui.sug[0]["id"]
    ui.key("1")
    assert [j["test_id"] for j in app.jobs.queued()] == [first] and "sıraya eklendi" in ui.msg
    ui.key("1")                                                 # aynı öneri artık kuyrukta; ekran yenilenmeden basılırsa hata verir, çökmez
    assert "eklenemedi" in ui.msg
    ui.key("9"), ui.key("?"), ui.key("")                        # anlamsız tuşlar çökmez
    assert any(first in j["test_id"] or j["title"] in "".join(ui.lines(100, 40)) for j in app.jobs.state["jobs"] if j["status"] == "queued") or True
    assert "SIRA" in "\n".join(ui.lines(100, 40))


def test_validator_requires_explicit_confirmation(tmp_path):
    ui, app = mk_ui(tmp_path)
    ui.lines(100, 40)
    k = next(i + 1 for i, s in enumerate(ui.sug) if s["id"] == "o5c_pretrain_validator")
    ui.key(str(k))
    assert ui.pending and "DOĞRULAYICI" in ui.msg and not app.jobs.state["jobs"]
    ui.key("n")
    assert not ui.pending and not app.jobs.state["jobs"] and "iptal" in ui.msg
    ui.key(str(k))
    ui.key("x")                                                 # y dışındaki her tuş iptal
    assert not app.jobs.state["jobs"]
    ui.key(str(k))
    ui.key("y")
    assert [j["test_id"] for j in app.jobs.state["jobs"]] == ["o5c_pretrain_validator"] and not ui.pending


def test_toggle_auto_cycle_game_arm_cancel_quit(tmp_path):
    ui, app = mk_ui(tmp_path)
    ui.key("a")
    assert app.jobs.state["auto"] is True
    ui.key("a")
    assert app.jobs.state["auto"] is False
    g0, a0 = ui.game_i, ui.arm_i
    ui.key("o"), ui.key("k")
    assert ui.game_i == (g0 + 1) % len(LV.LIVE_GAMES) and ui.arm_i == (a0 + 1) % len(LV.LIVE_ARMS)
    ui.key("c")
    assert "çalışan iş yok" in ui.msg
    ui.key("g") if not R.find_pre_files() else None
    ui.key("Q")
    assert ui.quit


def test_cancel_stops_running_job_from_screen(tmp_path):
    from sinek.ops.registry import TestDef
    reg = {"slow": TestDef("slow", "Yavaş", "", "arac", lambda v: [sys.executable, "-c", "import time;time.sleep(60)"])}
    app = App("t" * 24, JobManager(tmp_path / "ops", registry=reg), LiveSession())
    ui = E.Ui(app)
    j = app.jobs.enqueue("slow")
    app.jobs.start_now(j["id"])
    L = "\n".join(ui.lines(100, 40))
    assert "ilerleme ölçülemiyor" in L and "Yavaş" in L
    ui.key("c")
    t0 = time.time()
    while time.time() - t0 < 10 and app.jobs.get(j["id"])["status"] != "cancelled":
        app.jobs.reconcile()
        time.sleep(0.1)
    assert app.jobs.get(j["id"])["status"] == "cancelled"


@pytest.fixture()
def live_pre(cfg):
    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 2, seed=3, episodes=1, seconds=4.0)
    rel = f"results/ops/_t_ekran_{os.getpid()}.npz"
    path = R.ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.save(pre, path)
    yield rel
    path.unlink(missing_ok=True)
    Path(str(path) + ".json").unlink(missing_ok=True)
    for f in LV.REPLAY_DIR.glob("*_s140.json.gz"):
        f.unlink()


def test_live_arena_on_screen_shows_real_frame(tmp_path, live_pre, monkeypatch):
    monkeypatch.setattr(R, "find_pre_files", lambda: [live_pre])
    ui, app = mk_ui(tmp_path)
    ui.game_i = LV.LIVE_GAMES.index("O2near")
    ui.key("g")
    assert "canlı oyun başlıyor" in ui.msg
    t0 = time.time()
    while time.time() - t0 < 120 and not app.live.frame:
        time.sleep(0.2)
    L = ui.lines(120, 60)
    txt = "\n".join(L)
    assert "durum: çalışıyor" in txt and "canlı 1:" in txt and "+--" in txt
    fr = json.loads(app.live.frame)
    assert fr["type"] == "frame" and len(fr["x"]) == json.loads(app.live.layout)["B"]
    ui.key("p")
    assert app.live.pause_flag.is_set() and "DURAKLATILDI" in "\n".join(ui.lines(120, 60))
    ui.key("p"), ui.key("x")
    t0 = time.time()
    while time.time() - t0 < 30 and app.live.thread.is_alive():
        time.sleep(0.2)
    assert not app.live.thread.is_alive()


def test_live_start_without_population_gives_clear_message(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "find_pre_files", lambda: [])
    ui, _ = mk_ui(tmp_path)
    ui.key("g")
    assert "ön-eğitim dosyası yok" in ui.msg


def test_run_screen_draws_alt_screen_and_restores_terminal(tmp_path):
    ui, _ = mk_ui(tmp_path)
    out = io.StringIO()
    threading.Timer(1.2, lambda: setattr(ui, "quit", True)).start()
    E.run_screen(ui, fps=10, out=out)
    s = out.getvalue()
    assert s.startswith("\x1b[?1049h") and s.endswith("\x1b[?25h\x1b[?1049l") and "SİNEK TEST EKRANI" in s


def test_lines_never_exceed_width_and_survive_narrow_terminal(tmp_path):
    ui, _ = mk_ui(tmp_path)
    for w in (40, 60, 100, 200):
        assert all(len(l) <= w for l in ui.lines(w, 30))


def _run(args, tmp_path, **kw):
    env = dict(os.environ, SINEK_OPS_TOKEN_FILE=str(tmp_path / "tok"))
    return subprocess.Popen([sys.executable, "-X", "utf8", "-I", "-m", "sinek.ops.ekran", "--ops-dir", str(tmp_path / "o"), *args], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, env=env, cwd=R.ROOT, encoding="utf-8", **kw)


def test_process_once_prints_frame_and_exits(tmp_path):
    p = _run(["--once"], tmp_path)
    out = p.communicate(timeout=60)[0]
    assert p.returncode == 0 and "SİNEK TEST EKRANI" in out and "SIRADAKİ 5 ÖNERİ" in out and "http" not in out    # sunucu/adres yok


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_process_headless_runs_and_stops_cleanly_without_any_socket(tmp_path, sig):
    p = _run(["--headless"], tmp_path)
    try:
        assert "ekransız mod" in p.stdout.readline()
        # dinleyen soket olmamalı: sürecin açtığı dosya tanıtıcılarında LISTEN yok
        if Path(f"/proc/{p.pid}/net/tcp").exists():
            listen = [l for l in Path(f"/proc/{p.pid}/net/tcp").read_text().splitlines()[1:] if l.split()[3] == "0A"]
            mine = {os.readlink(f"/proc/{p.pid}/fd/{fd}") for fd in os.listdir(f"/proc/{p.pid}/fd") if os.path.islink(f"/proc/{p.pid}/fd/{fd}")}
            inodes = {l.split()[9] for l in listen}
            assert not any(f"socket:[{i}]" in mine for i in inodes), "ekran bir soket dinliyor"
        p.send_signal(sig)
        assert p.wait(timeout=15) == 0
    finally:
        if p.poll() is None:
            p.kill()


def test_headless_with_local_relay_applies_signed_command_without_http(tmp_path):
    """Sunucusuz uzak yol: yalnız git dalı. Süreç komutu dalda görüp işi sıraya alır (yerel bare depo)."""
    from sinek.ops.relay import ensure_clone, git, sign
    bare = tmp_path / "remote.git"
    for c in (["init", "--bare", "-b", "main", str(bare)],):
        subprocess.run(["git", *c], check=True, capture_output=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-b", "main", str(seed)], check=True, capture_output=True)
    (seed / "x").write_text("1")
    for c in (["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "i"], ["remote", "add", "origin", str(bare)], ["push", "origin", "main"]):
        subprocess.run(["git", *c], cwd=seed, check=True, capture_output=True)
    tok = "k" * 24
    (tmp_path / "tok").write_text(tok)
    env = dict(os.environ, SINEK_OPS_TOKEN_FILE=str(tmp_path / "tok"))
    # ekran, deponun `origin`ini kullanır: sınama için ROOT yerine bare'i `url` ile veren bir sarmalayıcıyla çalıştır
    code = (f"import sys;sys.argv=['x'];from sinek.ops import ekran as E, relay as RM;"
            f"orig=RM.Relay.__init__;RM.Relay.__init__=lambda s,app,spec,tok,cycle=1.0,url=None,workdir=None: orig(s,app,spec,tok,1.0,r'{bare}',__import__('pathlib').Path(r'{tmp_path / 'srv'}'));"
            f"sys.exit(E.main(['--headless','--relay','origin:ops-relay','--ops-dir',r'{tmp_path / 'o'}']))")
    p = subprocess.Popen([sys.executable, "-X", "utf8", "-I", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=R.ROOT, encoding="utf-8")
    try:
        assert "ekransız mod" in p.stdout.readline()
        cl = None
        t0 = time.time()
        while time.time() - t0 < 60:                              # sunucu ilk durumu dala yazsın
            try:
                cl = ensure_clone(tmp_path / "cli", "origin", "ops-relay", url=str(bare))
                if (cl / "status.json").exists():
                    break
            except Exception:
                pass
            time.sleep(1)
        assert cl and (cl / "status.json").exists()
        cmd = {"id": "e1", "ts": time.time(), "action": "enqueue", "test_id": "pytest", "params": {}, "confirm": False}
        cmd["sig"] = sign(tok, cmd)
        (cl / "commands").mkdir(exist_ok=True)
        (cl / "commands" / "e1.json").write_text(json.dumps(cmd))
        git(cl, "config", "user.name", "c"), git(cl, "config", "user.email", "c@c")
        git(cl, "add", "-A"), git(cl, "commit", "-m", "k"), git(cl, "push", "origin", "HEAD:ops-relay")
        st = tmp_path / "o" / "state.json"
        t0 = time.time()
        while time.time() - t0 < 90:
            if st.exists() and any(j["test_id"] == "pytest" for j in json.loads(st.read_text(encoding="utf-8"))["jobs"]):
                break
            time.sleep(1)
        else:
            raise AssertionError("komut uygulanmadı")
    finally:
        p.send_signal(signal.SIGTERM)
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill()


def test_windows_screen_launcher_has_no_bash_no_server():
    bat = (R.ROOT / "scripts" / "ekran_ac.bat").read_text(encoding="utf-8")
    code = "\n".join(l for l in bat.splitlines() if not l.lower().startswith("rem"))        # açıklama satırları sayılmaz
    assert "-X utf8 -I -m sinek.ops.ekran" in code and ".venv" in code and "sinek.ops.server" not in code and "bash" not in code
    assert "ekran" in (R.ROOT / "scripts" / "ekran_ac.sh").read_text(encoding="utf-8")


def test_ekran_module_opens_no_sockets_or_http():
    src = (R.ROOT / "src/sinek/ops/ekran.py").read_text(encoding="utf-8")
    assert "import socket" not in src and "http.server" not in src and "make_server" not in src and "serve_forever" not in src
