"""Kontrol sisteminin denetim testleri (K-061): hata avında bulunan sorunların regresyonları + sınır/saldırı/dayanıklılık durumları."""
import http.client
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from sinek.ops import client as CL
from sinek.ops import jobs as JB
from sinek.ops import live as LV
from sinek.ops import registry as R
from sinek.ops import relay as RM
from sinek.ops import server as S
from sinek.ops.jobs import JobManager
from sinek.ops.live import LiveSession
from sinek.ops.registry import ParamError, TestDef
from sinek.ops.relay import Relay, ensure_clone, git, sign

TOK = "s" * 24
PYC = [sys.executable, "-c"]


def mk(i, code, **kw):
    return TestDef(i, i, "sahte", "arac", lambda v, code=code: PYC + [code], **kw)


def wait(cond, timeout=20.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if cond():
            return True
        time.sleep(0.1)
    return False


def sh(*a, cwd=None):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True, check=True)


@pytest.fixture()
def remote(tmp_path):
    bare = tmp_path / "remote.git"
    sh("git", "init", "--bare", "-b", "main", str(bare))
    seed = tmp_path / "seed"
    sh("git", "init", "-b", "main", str(seed))
    (seed / "x").write_text("1")
    sh("git", "add", ".", cwd=seed)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "i", cwd=seed)
    sh("git", "remote", "add", "origin", str(bare), cwd=seed)
    sh("git", "push", "origin", "main", cwd=seed)
    return str(bare)


def push_cmd(remote, tmp_path, cmd, name="cli"):
    cl = ensure_clone(tmp_path / name, "origin", "ops-relay", url=remote)
    cmd = dict(cmd)
    cmd.setdefault("ts", time.time())
    cmd.setdefault("sig", sign(TOK, cmd))
    (cl / "commands").mkdir(exist_ok=True)
    (cl / "commands" / f"{cmd['id']}.json").write_text(json.dumps(cmd))
    git(cl, "config", "user.name", "c"), git(cl, "config", "user.email", "c@c")
    git(cl, "add", "-A"), git(cl, "commit", "-m", "k"), git(cl, "push", "origin", "HEAD:ops-relay")


def relay_for(tmp_path, remote, reg, **kw):
    jm = JobManager(tmp_path / "ops", registry=reg, **kw)
    app = S.App(TOK, jm, LiveSession())
    return jm, app, Relay(app, "origin:ops-relay", TOK, url=remote, workdir=tmp_path / "srv")


def sc(c):
    c = dict(c)
    c["ts"] = c.get("ts", time.time())
    c["sig"] = sign(TOK, c)
    return c


# =========================================================================== git yayını
def test_REGRESYON_rejected_push_does_not_reapply_command(tmp_path, remote, monkeypatch):
    """Bulgu D-1: itme reddedilince yerel onay kaybolup komut ikinci kez uygulanıyordu (iş bittiyse tekrar kuyruğa giriyordu)."""
    jm, app, rl = relay_for(tmp_path, remote, {"ok": mk("ok", "print(1)")}, poll=0.1)
    jm.set_auto(True)
    jm.start()
    rl.cycle_once()
    push_cmd(remote, tmp_path, {"id": "k1", "action": "enqueue", "test_id": "ok", "params": {}, "confirm": False})
    real, n = RM.git, {"v": 0}

    def flaky(cwd, *a, **k):
        if a and a[0] == "push" and n["v"] == 0:
            n["v"] = 1
            raise RuntimeError("push reddedildi")
        return real(cwd, *a, **k)

    monkeypatch.setattr(RM, "git", flaky)
    with pytest.raises(RuntimeError):
        rl.cycle_once()
    monkeypatch.setattr(RM, "git", real)
    assert wait(lambda: all(j["status"] == "done" for j in jm.state["jobs"]) and jm.state["jobs"])
    rl.cycle_once()
    rl.cycle_once()
    assert len(jm.state["jobs"]) == 1
    jm.stop()


def test_REGRESYON_old_signed_commands_stay_acked_beyond_300(tmp_path, remote):
    """Bulgu D-2: onay listesi sayıya göre (300) kırpılıyordu; süresi dolmamış eski imzalı komut yeniden oynatılabilirdi."""
    jm, app, rl = relay_for(tmp_path, remote, {"ok": mk("ok", "print(1)")})
    rl.cycle_once()
    cl = ensure_clone(tmp_path / "cli", "origin", "ops-relay", url=remote)
    (cl / "commands").mkdir(exist_ok=True)
    for i in range(340):
        c = sc({"id": f"a{i}", "action": "auto", "on": bool(i % 2)})
        (cl / "commands" / f"a{i}.json").write_text(json.dumps(c))
    git(cl, "config", "user.name", "c"), git(cl, "config", "user.email", "c@c")
    git(cl, "add", "-A"), git(cl, "commit", "-m", "k"), git(cl, "push", "origin", "HEAD:ops-relay")
    rl.cycle_once()
    st = json.loads((tmp_path / "srv" / "status.json").read_text())
    assert len(st["acked"]) == 340 and "a0" in st["acked"]
    jm.set_auto(False)
    # a0 ('auto kapalı' değil 'kapalı' = on False) yeniden oynatılırsa auto=True olurdu; oynatılmamalı
    cl = ensure_clone(tmp_path / "cli", "origin", "ops-relay", url=remote)                 # sunucunun son durumunu çek
    (cl / "commands" / "a1.json").write_text(json.dumps(sc({"id": "a1", "action": "auto", "on": True})))   # farklı gövde, aynı id → yine reddedilmeli
    git(cl, "add", "-A"), git(cl, "commit", "-m", "tekrar"), git(cl, "push", "origin", "HEAD:ops-relay")
    rl.cycle_once()
    assert jm.state["auto"] is False


def test_malformed_and_hostile_command_files_do_not_break_cycle(tmp_path, remote):
    jm, app, rl = relay_for(tmp_path, remote, {"ok": mk("ok", "print(1)")})
    rl.cycle_once()
    cl = ensure_clone(tmp_path / "cli", "origin", "ops-relay", url=remote)
    (cl / "commands").mkdir(exist_ok=True)
    (cl / "commands" / "bozuk.json").write_text("{bu json degil")
    (cl / "commands" / "liste.json").write_text("[1,2,3]")
    (cl / "commands" / "bos.json").write_text("{}")
    (cl / "commands" / "imzasiz.json").write_text(json.dumps({"id": "x1", "ts": time.time(), "action": "enqueue", "test_id": "ok"}))
    (cl / "commands" / "gelecek.json").write_text(json.dumps(sc({"id": "g1", "ts": time.time() + 10 * 86400, "action": "auto", "on": True})))
    (cl / "commands" / "bilinmeyen.json").write_text(json.dumps(sc({"id": "b1", "action": "rm_rf"})))
    (cl / "commands" / "yol.json").write_text(json.dumps(sc({"id": "../../etc/x", "action": "auto", "on": True})))
    git(cl, "config", "user.name", "c"), git(cl, "config", "user.email", "c@c")
    git(cl, "add", "-A"), git(cl, "commit", "-m", "k"), git(cl, "push", "origin", "HEAD:ops-relay")
    rl.cycle_once()
    st = json.loads((tmp_path / "srv" / "status.json").read_text())
    res = {k: v["result"] for k, v in st["acked"].items()}
    assert res["x1"].startswith("RET") and res["g1"].startswith("RET") and res["b1"].startswith("HATA")
    assert jm.state["jobs"] == []
    # 'yol.json' geçerli imzalıdır (jeton sahibi); kimliği yol gibi görünse de yalnız sözlük anahtarıdır: dosya yazılmaz
    assert "../../etc/x" in res and not (tmp_path / "etc").exists() and not Path("/tmp/etc/x").exists()


def test_relay_apply_all_actions(tmp_path, remote):
    jm, app, rl = relay_for(tmp_path, remote, {"ok": mk("ok", "print(1)"), "slow": mk("slow", "import time;time.sleep(60)")})
    j = jm.enqueue("slow")
    assert "başladı" in rl.apply({"action": "start", "job_id": j["id"]})
    assert "iptal" in rl.apply({"action": "cancel", "job_id": j["id"]})
    assert wait(lambda: (jm.reconcile(), jm.get(j["id"])["status"])[1] == "cancelled")
    assert "yeniden sırada" in rl.apply({"action": "retry", "job_id": j["id"]})
    assert "otomatik=açık" in rl.apply({"action": "auto", "on": True})
    assert rl.apply({"action": "enqueue", "test_id": "yok"}).startswith("HATA")
    assert rl.apply({"action": "start", "job_id": "yok"}).startswith("HATA")
    jm.set_auto(False)
    jm.cancel(j["id"])


def test_relay_update_refused_while_job_running(tmp_path, remote):
    jm, app, rl = relay_for(tmp_path, remote, {"slow": mk("slow", "import time;time.sleep(60)")})
    j = jm.enqueue("slow")
    jm.start_now(j["id"])
    assert "çalışan iş var" in rl.apply({"action": "update"})
    jm.cancel(j["id"])


def test_client_relay_send_end_to_end_and_push_race(tmp_path, remote, monkeypatch, capsys):
    jm, app, rl = relay_for(tmp_path, remote, {"ok": mk("ok", "print(1)")})
    rl.cycle_once()
    monkeypatch.setattr(CL.tempfile, "mkdtemp", lambda prefix="": str(tmp_path / "istemci"))
    # sunucu araya durum itsin: istemcinin ilk itmesi reddedilir, yeniden temellendirip başarmalı
    real = CL.git
    state = {"n": 0}

    def racing(cwd, *a, **k):
        if a and a[0] == "push" and state["n"] == 0:
            state["n"] = 1
            jm.set_auto(True)
            rl.cycle_once()                                  # sunucu dalı ilerletti
        return real(cwd, *a, **k)

    monkeypatch.setattr(CL, "git", racing)
    CL.main(["relay", "--token", TOK, "--url", remote, "send", "enqueue", "ok"])
    assert "komut gönderildi" in capsys.readouterr().out and state["n"] == 1
    rl.cycle_once()
    assert [j["test_id"] for j in jm.state["jobs"]] == ["ok"]


def test_client_status_reads_branch(tmp_path, remote, monkeypatch, capsys):
    jm, app, rl = relay_for(tmp_path, remote, {"ok": mk("ok", "print(1)")})
    rl.cycle_once()
    monkeypatch.setattr(CL.tempfile, "mkdtemp", lambda prefix="": str(tmp_path / "istemci2"))
    CL.main(["relay", "--token", TOK, "--url", remote, "status"])
    assert '"hardware"' in capsys.readouterr().out


def test_relay_adaptive_polling_skips_when_nothing_changed(tmp_path, remote):
    jm, app, rl = relay_for(tmp_path, remote, {"ok": mk("ok", "print(1)")})
    assert rl.due() is True
    rl.cycle_once()
    rl.last_head = rl.remote_head()
    rl.last_full = time.time()
    rl.last_sig = rl.local_sig()
    assert rl.due() is False                                   # değişen yok → tam döngü yok
    jm.enqueue("ok")
    assert rl.due() is True                                    # yerel durum değişti
    rl.last_sig = rl.local_sig()
    push_cmd(remote, tmp_path, {"id": "z", "action": "auto", "on": False})
    assert rl.due() is True                                    # uzak dal ilerledi


# =========================================================================== iş yöneticisi
def test_exit_codes_signal_kill_resumable_requeues_nonresumable_fails(tmp_path):
    reg = {
        "term": mk("term", "import os,signal;os.kill(os.getpid(),signal.SIGTERM)", resumable=True),
        "term2": mk("term2", "import os,signal;os.kill(os.getpid(),signal.SIGTERM)"),
        "kill9": mk("kill9", "import os,signal;os.kill(os.getpid(),signal.SIGKILL)", resumable=True),
    }
    jm = JobManager(tmp_path, registry=reg, poll=0.1)
    a, b = jm.enqueue("term"), jm.enqueue("term2")
    jm.max_running = 2
    jm.start_now(a["id"]), jm.start_now(b["id"])
    assert wait(lambda: (jm.reconcile(), jm.get(b["id"])["status"])[1] == "failed")
    assert jm.get(b["id"])["exit_code"] == 143
    assert jm.get(a["id"])["status"] == "queued" and "devam" in jm.get(a["id"])["note"]
    c = jm.enqueue("kill9")
    jm.start_now(c["id"])
    assert wait(lambda: (jm.reconcile(), jm.get(c["id"])["status"])[1] == "queued")


def test_max_attempts_then_failed(tmp_path):
    jm = JobManager(tmp_path, registry={"t": mk("t", "import os,signal;os.kill(os.getpid(),signal.SIGTERM)", resumable=True)}, poll=0.1)
    j = jm.enqueue("t")
    for _ in range(JB.MAX_ATTEMPTS):
        jm.start_now(j["id"])
        assert wait(lambda: (jm.reconcile(), jm.get(j["id"])["status"])[1] != "running")
    assert jm.get(j["id"])["status"] == "failed" and jm.get(j["id"])["attempts"] == JB.MAX_ATTEMPTS


def test_job_finished_while_manager_down_is_collected(tmp_path):
    reg = {"hizli": mk("hizli", "import time;time.sleep(0.5);print('bitti')")}
    jm = JobManager(tmp_path, registry=reg)
    j = jm.enqueue("hizli")
    jm.start_now(j["id"])
    del jm                                                     # sunucu çöktü; süreç bağımsız koşmaya devam eder
    time.sleep(1.5)
    jm2 = JobManager(tmp_path, registry=reg)
    assert jm2.get(j["id"])["status"] == "done" and jm2.get(j["id"])["exit_code"] == 0 and "bitti" in jm2.log_tail(j["id"])


def test_corrupt_state_file_starts_clean_and_keeps_evidence(tmp_path):
    (tmp_path / "state.json").write_text("{yarım yazılmış")
    jm = JobManager(tmp_path, registry={"ok": mk("ok", "print(1)")})
    assert jm.state["jobs"] == [] and (tmp_path / "state.bozuk").exists()
    jm.enqueue("ok")
    assert json.loads((tmp_path / "state.json").read_text())["jobs"]


def test_cancel_retry_move_edge_cases(tmp_path):
    jm = JobManager(tmp_path, registry={"ok": mk("ok", "print(1)"), "p": mk("p", "print(2)")})
    a, b = jm.enqueue("ok"), jm.enqueue("p")
    with pytest.raises(ParamError):
        jm.cancel("yok")
    with pytest.raises(ParamError):
        jm.retry(a["id"])                                      # kuyruktaki iş yeniden sıraya alınamaz
    jm.move(a["id"], -1)                                       # zaten ilk: sessizce yerinde
    assert [j["id"] for j in jm.queued()][0] == a["id"]
    jm.cancel(a["id"])
    assert jm.get(a["id"])["status"] == "cancelled" and jm.retry(a["id"])["status"] == "queued"
    with pytest.raises(ParamError):
        jm.start_now(b["id"] + "x")
    with pytest.raises(ParamError):
        jm.move("yok", 1)
    with pytest.raises(ParamError):
        jm.log_tail("yok")


def test_alive_handles_zombie_and_missing_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    time.sleep(0.5)                                            # çıktı ama toplanmadı → zombi
    assert JB._alive(p.pid) is False
    p.wait()
    assert JB._alive(2 ** 22 + 99) is False
    assert JB._alive(os.getpid()) is True


def test_wrapper_writes_exit_code_conventions(tmp_path):
    f = tmp_path / "e"
    subprocess.run([sys.executable, "-I", "-c", JB.WRAPPER, str(f), sys.executable, "-c", "import sys;sys.exit(7)"])
    assert f.read_text() == "7"
    subprocess.run([sys.executable, "-I", "-c", JB.WRAPPER, str(f), sys.executable, "-c", "import os,signal;os.kill(os.getpid(),signal.SIGKILL)"])
    assert f.read_text() == "137"


def test_cancel_kills_whole_process_tree(tmp_path):
    code = ("import subprocess,sys,time;c=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)']);"
            "open(sys.argv[1] if len(sys.argv)>1 else r'%s','w').write(str(c.pid));time.sleep(120)" % (tmp_path / "child.pid"))
    jm = JobManager(tmp_path / "o", registry={"tree": mk("tree", code)})
    j = jm.enqueue("tree")
    jm.start_now(j["id"])
    assert wait(lambda: (tmp_path / "child.pid").exists() and (tmp_path / "child.pid").read_text())
    child = int((tmp_path / "child.pid").read_text())
    jm.cancel(j["id"])
    assert wait(lambda: not JB._alive(child), 10), "alt süreç (torun) açık kaldı"


def test_many_jobs_overview_is_bounded_and_fast(tmp_path):
    jm = JobManager(tmp_path, registry={"ok": mk("ok", "print(1)")})
    now = time.time()
    for i in range(600):
        jm.state["jobs"].append({"id": f"j{i}", "test_id": "ok", "params": {}, "status": "done", "created": now, "attempts": 1, "log": "x", "exit_file": "y",
                                 "argv": [], "source": "t", "started": now, "ended": now})
    jm._save()
    app = S.App(TOK, jm, LiveSession())
    t0 = time.time()
    ov = app.overview()
    assert len(ov["jobs"]) == 150 and time.time() - t0 < 2.0


# =========================================================================== kayıt defteri / öneri
def test_suggest_orders_by_prereq_excludes_queued_and_finished(monkeypatch):
    a = mk("a", "1", priority=30)
    b = mk("b", "1", priority=10, after=("a",))
    c = mk("c", "1", priority=20, done_when=lambda v: True)
    d = mk("d", "1", priority=40, disabled_reason="yok")
    e = mk("e", "1", priority=50)
    monkeypatch.setattr(R, "REGISTRY", {t.id: t for t in (a, b, c, d, e)})
    ids = [r["id"] for r in R.suggest(set(), set())]
    assert ids == ["a", "e", "b", "d"] and "c" not in ids      # b ön koşulu (a) bitmediği için sonda; engelli en sonda
    assert [r["id"] for r in R.suggest({"a"}, set())][0] == "b"  # a bitince b öne geçer
    assert "a" not in [r["id"] for r in R.suggest(set(), {"a"})]  # kuyruktaki önerilmez


def test_o5c_progress_counts_real_files(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "ROOT", tmp_path)
    d, tot, _ = R.o5c_progress({})
    assert d == 0 and tot > 0 and not R.o5c_done({})
    (tmp_path / "results/odor_val").mkdir(parents=True)
    for p in ("206", "207"):
        (tmp_path / f"results/odor_val/pre_s{p}.npz").write_bytes(b"x")
    part = tmp_path / "results/o5_val/c_s274/partial"
    part.mkdir(parents=True)
    for i in range(5):
        (part / f"o5_plastic_c{i}.npz").write_bytes(b"x")
    d2, _, txt = R.o5c_progress({})
    assert d2 == 7 and "ön-eğitim 2/4" in txt and "5/100" in txt
    for s, _ in R.O5C_SEEDS:
        (tmp_path / f"results/o5_val/c_s{s}").mkdir(parents=True, exist_ok=True)
        (tmp_path / f"results/o5_val/c_s{s}/results.json").write_text("{}")
    assert R.o5c_done({}) and R.o5c_progress({})[0] <= R.o5c_progress({})[1]


def test_param_edge_cases():
    t = R.REGISTRY["gv0"]
    for bad in ({"n": 0}, {"n": 129}, {"n": "abc"}, {"n": None, "reps": 99}, {"n": [1]}, {"n": True and "1e3"}):
        with pytest.raises(ParamError):
            t.build_params(bad)
    assert t.build_params({})["n"] == 32 and t.build_params({"n": "5"})["n"] == 5
    with pytest.raises(ParamError):
        R.REGISTRY["demo_pre"].build_params({"device": "tpu"})
    assert R.REGISTRY["demo_pre"].build_params({"device": "cuda"})["device"] == "cuda"


def test_registry_commands_never_contain_shell_metacharacter_injection():
    t = R.REGISTRY["o6_pilot"]
    pre = next(iter(R.find_pre_files()), None)
    if pre is None:
        pytest.skip("ön-eğitim dosyası yok")
    v = t.build_params({"pre": pre, "seed": 120})
    argv = t.argv(v)
    assert all(isinstance(a, str) for a in argv) and not any(";" in a or "&&" in a or "|" in a for a in argv if not a.startswith("-") and a != sys.executable and "/" not in a)


# =========================================================================== sunucu
@pytest.fixture()
def srv(tmp_path):
    jm = JobManager(tmp_path / "ops", registry={"ok": mk("ok", "print(1)"), "slow": mk("slow", "import time;time.sleep(60)")})
    server, app = S.make_server("127.0.0.1", 0, TOK, jm, LiveSession())
    app.FAIL_DELAY = 0.0
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1], app
    server.shutdown()


def call(port, method, path, body=None, raw=None, token=TOK, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    h = {"Authorization": f"Bearer {token}"} if token else {}
    h.update(headers or {})
    data = raw if raw is not None else (json.dumps(body) if body is not None else None)
    if data is not None:
        h["Content-Type"] = "application/json"
    c.request(method, path, data, h)
    r = c.getresponse()
    return r.status, r.read()


def test_server_rejects_malformed_requests_without_crashing(srv):
    port, _ = srv
    assert call(port, "POST", "/api/queue", raw="{bozuk")[0] == 400
    assert call(port, "POST", "/api/queue", raw="[1,2]")[0] in (400, 500)
    assert call(port, "POST", "/api/queue", raw="x" * 200_000)[0] == 400
    assert call(port, "POST", "/api/auto", {"on": "x"})[0] == 200
    assert call(port, "POST", "/api/max_running", {"n": "abc"})[0] == 400
    assert call(port, "POST", "/api/jobs/a")[0] in (400, 404)
    assert call(port, "POST", "/api/jobs/yok/cancel")[0] == 400
    assert call(port, "GET", "/api/jobs/yok/log")[0] == 400
    assert call(port, "GET", "/api/jobs/../../../etc/passwd/log")[0] in (400, 404)
    assert call(port, "GET", "/api/yok")[0] == 404
    assert call(port, "POST", "/api/yok", {})[0] == 404
    assert call(port, "PUT", "/api/queue", {})[0] in (501, 405)
    assert call(port, "DELETE", "/api/queue")[0] in (501, 405)
    assert call(port, "GET", "/api/overview")[0] == 200          # hâlâ ayakta


def test_log_bytes_parameter_validated_and_clamped(srv):
    port, app = srv
    j = app.jobs.enqueue("ok")
    app.jobs.start_now(j["id"])
    assert wait(lambda: (app.jobs.reconcile(), app.jobs.get(j["id"])["status"])[1] == "done")
    assert call(port, "GET", f"/api/jobs/{j['id']}/log?bytes=abc")[0] == 400
    st, body = call(port, "GET", f"/api/jobs/{j['id']}/log?bytes=99999999999")
    assert st == 200 and b"=== " in body
    assert call(port, "GET", f"/api/jobs/{j['id']}/log?bytes=-5")[0] == 200


def test_concurrent_requests_and_enqueue_are_consistent(srv):
    port, app = srv
    codes = []

    def hit(i):
        codes.append(call(port, "GET", "/api/overview")[0])
        codes.append(call(port, "POST", "/api/queue", {"test_id": "ok"})[0])

    th = [threading.Thread(target=hit, args=(i,)) for i in range(30)]
    [t.start() for t in th]
    [t.join() for t in th]
    assert codes.count(200) >= 31 and set(codes) <= {200, 400}   # aynı iş zaten kuyrukta → 400
    assert len([j for j in app.jobs.state["jobs"] if j["status"] == "queued"]) == 1   # çift kayıt yok


def test_sse_new_viewer_gets_layout_then_frame_and_pings(srv):
    port, app = srv
    live = app.live
    live._publish({"type": "layout", "ep": 1, "B": 1, "arena": 40.0})
    live._publish({"type": "frame", "ep": 1, "step": 1, "x": [1.0]})
    live._publish({"type": "episode_end", "ep": 1})            # son mesaj çerçeve değil; yine de layout+frame gelmeli
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request("GET", "/api/live/stream", headers={"Authorization": f"Bearer {TOK}"})
    r = c.getresponse()
    assert r.status == 200 and r.getheader("Content-Type") == "text/event-stream"
    got = []
    while len(got) < 2:
        line = r.fp.readline().decode()
        if line.startswith("data: "):
            got.append(json.loads(line[6:])["type"])
    assert got == ["layout", "frame"]
    live._publish({"type": "frame", "ep": 1, "step": 2, "x": [2.0]})
    while True:
        line = r.fp.readline().decode()
        if line.startswith("data: "):
            assert json.loads(line[6:])["step"] == 2
            break
    c.close()
    assert call(port, "GET", "/api/overview")[0] == 200         # kopan istemci sunucuyu bozmadı


def test_sse_requires_auth(srv):
    port, _ = srv
    assert call(port, "GET", "/api/live/stream", token=None)[0] == 401


def test_files_listing_survives_broken_symlink(srv):
    port, _ = srv
    d = R.ROOT / "results" / "ops"
    d.mkdir(parents=True, exist_ok=True)
    link = d / "_kirik_link"
    link.symlink_to("/yok/boyle/bir/dosya")
    try:
        st, body = call(port, "GET", "/api/files?path=results/ops")
        assert st == 200 and b"_kirik_link" not in body
    finally:
        link.unlink()


def test_files_symlink_escape_blocked(srv):
    port, _ = srv
    d = R.ROOT / "results" / "ops"
    d.mkdir(parents=True, exist_ok=True)
    link = d / "_kacis_link"
    link.symlink_to("/etc/hostname")
    try:
        assert call(port, "GET", "/api/files?path=results/ops/_kacis_link")[0] == 400
    finally:
        link.unlink()


def test_update_refused_with_running_job_and_hardware_is_cached(srv):
    port, app = srv
    j = app.jobs.enqueue("slow")
    app.jobs.start_now(j["id"])
    st, body = call(port, "POST", "/api/update", {})
    assert st == 400 and "çalışan iş" in body.decode()
    app.jobs.cancel(j["id"])
    t0 = time.time()
    for _ in range(20):
        S.hardware()
    assert time.time() - t0 < 1.0                               # 5 sn önbellek: alt süreç yağmuru yok


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
@pytest.mark.parametrize("ignore_sigint", [False, True])
def test_server_process_startup_auth_and_graceful_stop(tmp_path, sig, ignore_sigint):
    """Gerçek süreç: CLI açılışı, jeton zorunluluğu, yerel dinleme, SIGINT/SIGTERM ile düzgün kapanış (arka plan işlerinde SIGINT yok sayılsa bile)."""
    env = dict(os.environ, SINEK_OPS_TOKEN_FILE=str(tmp_path / "tok"))
    p = subprocess.Popen([sys.executable, "-I", "-m", "sinek.ops.server", "--port", "0", "--token", TOK, "--ops-dir", str(tmp_path / "o")],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=R.ROOT,
                         preexec_fn=(lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)) if ignore_sigint else None)
    try:
        line = p.stdout.readline()
        assert "127.0.0.1" in line and f"token={TOK}" in line
        port = int(line.split("127.0.0.1:")[1].split("/")[0])
        assert call(port, "GET", "/api/overview", token=None)[0] == 401
        assert call(port, "GET", "/api/overview")[0] == 200
        p.send_signal(sig)
        assert p.wait(timeout=15) == 0
    finally:
        if p.poll() is None:
            p.kill()


def test_server_refuses_short_token():
    r = subprocess.run([sys.executable, "-I", "-m", "sinek.ops.server", "--port", "0", "--token", "kisa"], capture_output=True, text=True, cwd=R.ROOT, timeout=30)
    assert r.returncode != 0 and "16" in (r.stdout + r.stderr)


# =========================================================================== canlı izleme
@pytest.fixture()
def live_pre(cfg):
    from sinek import checkpoint
    from sinek.games.protocol import pretrain
    from sinek.world import odor_patterns
    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 2, seed=3, episodes=1, seconds=4.0)
    rel = f"results/ops/_t_pre_{os.getpid()}.npz"
    path = R.ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.save(pre, path)
    yield rel
    path.unlink(missing_ok=True)
    Path(str(path) + ".json").unlink(missing_ok=True)
    for f in LV.REPLAY_DIR.glob("*_s12[0-9].json.gz"):
        f.unlink()


def test_live_stop_pause_speed_and_double_start(live_pre):
    ls = LiveSession()
    ls.start(live_pre, "O2near", "plastic", 121, agents=1, trials=2, seconds=30, fps=30, episodes=0)
    assert wait(lambda: ls.status.get("state") == "çalışıyor", 120)
    with pytest.raises(ParamError, match="zaten"):
        ls.start(live_pre, "O2near", "plastic", 121)
    s0 = ls.seq
    ls.pause(True)
    time.sleep(0.5)
    s1 = ls.seq
    time.sleep(1.0)
    assert ls.seq == s1                                         # duraklatılmışken yayın durur
    ls.pause(False)
    assert wait(lambda: ls.seq > s1)
    ls.set_speed(1000)
    assert ls.speed == 20.0
    ls.set_speed(-3)
    assert ls.speed == 0.1
    ls.stop()
    assert wait(lambda: not ls.thread.is_alive(), 30) and ls.status["state"] == "durdu"
    assert s0 <= ls.seq


def test_live_stop_while_paused_does_not_hang(live_pre):
    ls = LiveSession()
    ls.start(live_pre, "O2near", "plastic", 122, agents=1, trials=2, seconds=30, fps=30)
    assert wait(lambda: ls.status.get("state") == "çalışıyor", 120)
    ls.pause(True)
    time.sleep(0.4)
    ls.stop()
    assert wait(lambda: not ls.thread.is_alive(), 30)


def test_live_corrupt_checkpoint_reports_error_not_crash(tmp_path):
    rel = f"results/ops/_t_bozuk_{os.getpid()}.npz"
    path = R.ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"bu bir npz degil")
    try:
        ls = LiveSession()
        ls.start(rel, "O2near", "plastic", 123)
        assert wait(lambda: ls.status.get("state") == "hata", 60)
        assert "Error" in ls.status["error"] or "error" in ls.status["error"].lower()
        ls.start(rel, "O2near", "plastic", 123)                 # hatadan sonra yeniden başlatılabilir
        assert wait(lambda: ls.status.get("state") == "hata", 60)
    finally:
        path.unlink(missing_ok=True)


def test_live_parameter_bounds(live_pre):
    ls = LiveSession()
    for kw in ({"agents": 0}, {"agents": 7}, {"trials": 3}, {"seconds": 1}, {"seconds": 500}, {"fps": 0}, {"episodes": -1}, {"device": "tpu"}):
        with pytest.raises(ParamError):
            ls.start(live_pre, "O2near", "plastic", 120, **kw)
    with pytest.raises(ParamError):
        ls.start(live_pre, "O2near", "plastic", 99)             # 100'ün altı
    with pytest.raises(ParamError):
        ls.start(live_pre, "YOK", "plastic", 120)
    with pytest.raises(ParamError):
        ls.start(live_pre, "O2near", "yok", 120)
    if not LV.torch.cuda.is_available():
        with pytest.raises(ParamError, match="CUDA"):
            ls.start(live_pre, "O2near", "plastic", 120, device="cuda")


def test_live_replay_is_bounded_and_matches_published_frames(live_pre, monkeypatch):
    monkeypatch.setattr(LV, "REPLAY_MAX_FRAMES", 25)
    ls = LiveSession()
    ls.start(live_pre, "O2near", "plastic", 124, agents=1, trials=2, seconds=8, fps=60, episodes=1)
    assert wait(lambda: ls.status.get("state") == "bitti", 120)
    rp = LV.replay_read(ls.status["replay"])
    assert rp["n"] <= 25 and sum(len(e["frames"]) for e in rp["episodes"]) == rp["n"]
    for e in rp["episodes"]:
        for f in e["frames"]:
            assert len(f["x"]) == e["layout"]["B"] and all(0 <= v <= e["layout"]["arena"] for v in f["x"])
    assert rp["episodes"][0]["end"]["slots"] == ls.history[0]["slots"]


def test_replay_names_are_whitelisted():
    for bad in ("../x.json.gz", "a/b.json.gz", "x.json", "..", "", "x.json.gz\0", "%2e%2e%2fx.json.gz"):
        with pytest.raises(ParamError):
            LV.replay_read(bad)


# =========================================================================== kurulum aracı
def test_setup_autostart_writes_valid_systemd_unit(tmp_path, monkeypatch):
    from sinek.ops import setup as SU
    monkeypatch.setattr(SU.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(SU.platform, "system", lambda: "Linux")
    calls = []
    monkeypatch.setattr(SU.subprocess, "run", lambda *a, **k: calls.append(a) or subprocess.CompletedProcess(a, 0, "", ""))
    SU.autostart("origin:ops-relay")
    unit = (tmp_path / ".config/systemd/user/sinek-ops.service").read_text()
    assert f"WorkingDirectory={R.ROOT}" in unit and "sinek.ops.ekran --headless --relay origin:ops-relay --auto" in unit and "Restart=always" in unit
    assert "WantedBy=default.target" in unit and calls and "systemctl --user" in calls[0][0]


def test_setup_without_git_remote_reports_clear_error(tmp_path, monkeypatch, capsys):
    from sinek.ops import setup as SU
    monkeypatch.setattr(SU, "ROOT", tmp_path)                  # git deposu olmayan klasör
    assert SU.check_git_relay("origin:ops-relay") is False
    assert "git uzak adresi" in capsys.readouterr().out


# =========================================================================== Windows uyumu (K-062): bash yok, UTF-8, çapraz platform kuyruk
def test_no_registered_command_needs_bash_and_all_run_in_utf8_mode():
    for t in R.REGISTRY.values():
        if t.disabled_reason:
            continue
        vals = {p.name: (p.default if p.kind != "pre" else "results/x.npz") for p in t.params}
        argv = t.argv(vals)
        assert argv[0] == sys.executable and "bash" not in argv[:3]
        assert argv[1:4] == ["-X", "utf8", "-I"], argv[:5]            # Windows varsayılan kodlaması UTF-8 değil


def test_all_text_io_in_ops_is_explicit_utf8():
    """Windows'ta open()/read_text()/write_text() varsayılanı yerel kodlamadır (cp1252/cp1254): Türkçe, →, ≥ yazılırken çöker."""
    import re
    bad = []
    for f in sorted((R.ROOT / "src" / "sinek" / "ops").glob("*.py")):
        lines = f.read_text(encoding="utf-8").splitlines()
        for no, l in enumerate(lines, 1):
            window = " ".join(lines[no - 1:no + 3])                       # çok satırlı çağrılar
            if re.search(r"\.(read_text|write_text)\(", l) and "encoding=" not in window:
                bad.append(f"{f.name}:{no}: {l.strip()[:80]}")
            if re.search(r"\bopen\(", l) and "encoding=" not in l and not re.search(r"""['"][rwa]b['"]|"ab"|"rb"|"wb"|\+ "b"|\['"]w['"]\)\.write""", l):
                if "WRAPPER" not in l and "sys.argv" not in l and "job[" not in l:
                    bad.append(f"{f.name}:{no}: {l.strip()[:80]}")
    assert not bad, "\n".join(bad)


def test_o5c_queue_plan_matches_preregistered_structure(tmp_path):
    from sinek.ops import o5c_kuyruk as K
    s0, s1, s2 = K.plan()
    assert (len(s0), len(s1), len(s2)) == (4, 4 * (3 * 8 + 1), 4)
    pops = {j["argv"][-1] for j in s0}
    assert pops == {f"results/odor_val/pre_s{p}.npz" for p in ("206", "207", "208", "209")}
    seeds = {j["argv"][j["argv"].index("--seed") + 1] for j in s1}
    assert seeds == {"274", "275", "276", "277"}
    arms = [j["argv"][j["argv"].index("--only-arms") + 1] for j in s1]
    assert arms[:32] == ["plastic_t"] * 32 and arms[-4:] == ["reference"] * 4 and set(arms) == {"plastic_t", "plastic", "frozen", "reference"}
    for j in s1 + s2:                                                  # her iş ön-kayıtlı O5c kipinde ve tek iş parçacığında
        assert "--o5c" in j["argv"] and j["argv"][j["argv"].index("--threads") + 1] == "1"
    # ön-eğitim popülasyonu ↔ oyun tohumu eşleşmesi (274↔206 … 277↔209)
    for j in s1 + s2:
        seed = j["argv"][j["argv"].index("--seed") + 1]
        pre = j["argv"][j["argv"].index("--pre") + 1]
        assert pre == f"results/odor_val/pre_s{int(seed) - 68}.npz"


def test_o5c_queue_skips_finished_resumes_and_reports_failures(tmp_path):
    from sinek.ops import o5c_kuyruk as K
    stages = K.plan()
    done = tmp_path / "results/o5_val/c_s274"
    done.mkdir(parents=True)
    (done / "results.json").write_text("{}")
    calls, said = [], []

    def fake(job, root, say):
        if (root / job["skip_if"]).exists():
            return 0
        calls.append(job["name"])
        return 3 if job["name"] == "275 frozen 2" else 0

    code = K.execute(stages, 4, root=tmp_path, say=said.append, runner=fake)
    assert code == 1 and any("275 frozen 2" in m and "BAŞARISIZ" in m for m in said)
    assert not any(n.startswith("274 ") for n in calls if not n.startswith("değerlendirme") and not n.startswith("ön-eğitim"))   # bitmiş tohum atlandı
    assert len(calls) == 108 - 25 - 1 + 0 or len(calls) > 70           # kalan işler hata sonrası da sürdü
    assert any(n.startswith("değerlendirme 277") for n in calls)       # son aşamaya ulaşıldı


def test_o5c_run_job_real_subprocess_skip_log_modes(tmp_path):
    from sinek.ops import o5c_kuyruk as K
    job = {"name": "x", "argv": [sys.executable, "-c", "print('merhaba ı → ≥')"], "log": "l/x.log", "log_mode": "a", "skip_if": "bitti.txt", "mkdir": "d"}
    msgs = []
    assert K.run_job(job, tmp_path, msgs.append) == 0 and K.run_job(job, tmp_path, msgs.append) == 0
    assert (tmp_path / "l/x.log").read_text(encoding="utf-8").count("merhaba") == 2        # 'a' kipi: kontrol noktalı işte günlük birikir
    (tmp_path / "bitti.txt").write_text("1")
    assert K.run_job(job, tmp_path, msgs.append) == 0 and "atla x (bitti)" in msgs[-1]
    bad = dict(job, argv=[sys.executable, "-c", "import sys;sys.exit(5)"], skip_if="yok.txt")
    assert K.run_job(bad, tmp_path, msgs.append) == 5


def test_setup_windows_autostart_writes_bat_and_schedules_task(tmp_path, monkeypatch):
    from sinek.ops import setup as SU
    monkeypatch.setattr(SU.platform, "system", lambda: "Windows")
    monkeypatch.setattr(SU, "ROOT", tmp_path)
    calls = []
    monkeypatch.setattr(SU.subprocess, "run", lambda a, **k: calls.append(a) or subprocess.CompletedProcess(a, 0, "", ""))
    SU.autostart("origin:ops-relay")
    bat = (tmp_path / "results/ops/ekran_baslat.bat").read_bytes().decode("utf-8")
    assert "\r\n" in bat and f'cd /d "{tmp_path}"' in bat and "-X utf8 -I -m sinek.ops.ekran --relay origin:ops-relay --auto" in bat
    assert calls[0][0] == "schtasks" and "/SC" in calls[0] and "ONLOGON" in calls[0] and str(tmp_path / "results/ops/ekran_baslat.bat") in calls[0][-2]


def test_windows_launcher_has_no_bash_and_finds_python():
    bat = (R.ROOT / "scripts" / "ops_baslat.bat").read_text(encoding="utf-8")
    assert "bash" not in bat.replace("bash/WSL", "") and "-X utf8 -I -m sinek.ops.server" in bat and ".venv" in bat


def test_server_main_uses_utf8_streams():
    src = (R.ROOT / "src/sinek/ops/server.py").read_text(encoding="utf-8")
    assert 'stream.reconfigure(encoding="utf-8"' in src


def test_registry_o5c_command_is_runnable_python_module():
    t = R.REGISTRY["o5c_pretrain_validator"]
    argv = t.argv(t.build_params({"workers": 2})) + ["--dry-run"]
    r = subprocess.run(argv, capture_output=True, text=True, cwd=R.ROOT, timeout=60)
    assert r.returncode == 0 and r.stdout.count("aşama 1 |") == 100
