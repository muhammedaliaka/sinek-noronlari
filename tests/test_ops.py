"""Uzak kontrol sistemi (src/sinek/ops): kayıt defteri doğrulaması, iş yöneticisi, sunucu güvenliği, git yayını, canlı izleme."""
import http.client
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from sinek import checkpoint
from sinek.games.protocol import pretrain
from sinek.ops import registry as R
from sinek.ops import server as S
from sinek.ops.jobs import JobManager
from sinek.ops import live as LV
from sinek.ops.live import LiveSession
from sinek.ops.registry import Param, ParamError, TestDef
from sinek.ops.relay import Relay, sign, verify
from sinek.world import odor_patterns

PY = [sys.executable, "-c"]


def fake_registry() -> dict:
    def mk(i, code, **kw):
        return TestDef(i, i, "sahte", "arac", lambda v, code=code: PY + [code.format(**v)], **kw)
    return {
        "ok": mk("ok", "print('merhaba')"),
        "bad": mk("bad", "import sys; sys.exit(3)"),
        "slow": mk("slow", "import time; time.sleep(60)"),
        "p": mk("p", "print({x})", params=(Param("x", "x", "int", 1, 0, 5),)),
        "res": mk("res", "print(1)", resumable=True),
        "val": mk("val", "print(2)", validator=True),
    }


def wait(cond, timeout=15.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if cond():
            return True
        time.sleep(0.1)
    return False


# --------------------------------------------------------------------------- kayıt defteri
def test_param_validation_blocks_bad_values_and_paths():
    t = R.REGISTRY["o6_pilot"]
    with pytest.raises(ParamError):
        t.build_params({"seed": 200, "pre": "results/ops/x.npz"})          # doğrulayıcı tohumu yasak (R-2)
    with pytest.raises(ParamError):
        t.build_params({"pre": "../etc/passwd"})
    with pytest.raises(ParamError):
        t.build_params({"pre": "/etc/passwd"})
    with pytest.raises(ParamError):
        t.build_params({"bilinmeyen": 1, "pre": "results/ops/x.npz"})
    with pytest.raises(ParamError):
        R.REGISTRY["gv0"].build_params({"n": "1; rm -rf /"})
    with pytest.raises(ParamError):
        R.REGISTRY["gv0"].build_params({"n": float("nan")})
    assert R.REGISTRY["gv0"].build_params({"n": "8"})["n"] == 8


def test_every_registered_command_is_a_list_of_known_entrypoints():
    for t in R.REGISTRY.values():
        if t.disabled_reason:
            continue
        vals = {p.name: (p.default if p.kind != "pre" else "x") for p in t.params}
        argv = t.argv(vals)
        assert isinstance(argv, list) and all(isinstance(a, str) for a in argv)
        assert argv[0] in (sys.executable, "bash")
        if argv[0] == "bash":
            assert (R.ROOT / argv[1]).exists()
        else:
            mod = argv[argv.index("-m") + 1]
            assert mod == "pytest" or (R.ROOT / "src" / mod.replace(".", "/")).with_suffix(".py").exists()


def test_validator_needs_committed_prereg_and_confirmation(tmp_path):
    t = R.REGISTRY["o5c_pretrain_validator"]
    assert t.validator and t.prereg and R.git_tracked_commit(t.prereg), "ön-kayıt commit edilmiş olmalı (R-1)"
    jm = JobManager(tmp_path, registry=R.REGISTRY)
    with pytest.raises(ParamError, match="onay"):
        jm.enqueue("o5c_pretrain_validator")
    missing = TestDef("v", "v", "", "dogrulayici", lambda v: [], prereg="docs/yok_olmayan_plan.md", validator=True)
    assert not missing.runnable()[0]


# --------------------------------------------------------------------------- iş yöneticisi
def test_job_lifecycle_done_failed_cancel(tmp_path):
    jm = JobManager(tmp_path, registry=fake_registry(), poll=0.1)
    jm.set_auto(True)
    jm.start()
    a = jm.enqueue("ok")
    assert wait(lambda: jm.get(a["id"])["status"] == "done")
    assert jm.get(a["id"])["exit_code"] == 0 and "merhaba" in jm.log_tail(a["id"])
    b = jm.enqueue("bad")
    assert wait(lambda: jm.get(b["id"])["status"] == "failed") and jm.get(b["id"])["exit_code"] == 3
    c = jm.enqueue("slow")
    assert wait(lambda: jm.get(c["id"])["status"] == "running")
    jm.cancel(c["id"])
    assert wait(lambda: jm.get(c["id"])["status"] == "cancelled")
    jm.stop()


def test_queue_order_limits_and_no_duplicates(tmp_path):
    jm = JobManager(tmp_path, registry=fake_registry(), max_running=1)
    j1, j2 = jm.enqueue("slow"), jm.enqueue("p", {"x": 2})
    with pytest.raises(ParamError, match="zaten"):
        jm.enqueue("slow")
    with pytest.raises(ParamError):
        jm.enqueue("p", {"x": 99})
    jm.move(j2["id"], -1)
    assert [j["id"] for j in jm.queued()] == [j2["id"], j1["id"]]
    jm.start_now(j2["id"])
    jm.reconcile()
    with pytest.raises(ParamError, match="aynı anda"):
        jm.start_now(j1["id"])                               # max_running=1
    jm.cancel(j1["id"])


def test_orphaned_job_resumes_if_resumable_else_interrupted(tmp_path):
    jm = JobManager(tmp_path, registry=fake_registry())
    r, n = jm.enqueue("res"), jm.enqueue("ok")
    for j in (r, n):                                          # sunucu çökmüş gibi: çalışıyor görünür, pid yok
        j.update(status="running", pid=2 ** 22 + 12345, started=time.time(), attempts=1)
    jm._save()
    jm2 = JobManager(tmp_path, registry=fake_registry())      # yeniden başlatma
    assert jm2.get(r["id"])["status"] == "queued" and "devam" in jm2.get(r["id"])["note"]
    assert jm2.get(n["id"])["status"] == "interrupted"
    assert jm2.retry(n["id"])["status"] == "queued"


def test_state_survives_restart_and_reattaches_to_live_process(tmp_path):
    jm = JobManager(tmp_path, registry=fake_registry())
    j = jm.enqueue("slow")
    jm.start_now(j["id"])
    jm2 = JobManager(tmp_path, registry=fake_registry())      # sunucu yeniden başladı; süreç yaşıyor
    assert jm2.get(j["id"])["status"] == "running"
    jm2.cancel(j["id"])
    assert wait(lambda: (jm2.reconcile(), jm2.get(j["id"])["status"])[1] == "cancelled")


# --------------------------------------------------------------------------- sunucu
@pytest.fixture()
def srv(tmp_path):
    jm = JobManager(tmp_path / "ops", registry=fake_registry())
    server, app = S.make_server("127.0.0.1", 0, "t" * 24, jm, LiveSession())
    app.FAIL_DELAY = 0.0
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1], app
    server.shutdown()


def call(port, method, path, body=None, token="t" * 24, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    h = {"Authorization": f"Bearer {token}"} if token else {}
    h.update(headers or {})
    if body is not None:
        h["Content-Type"] = "application/json"
    c.request(method, path, json.dumps(body) if body is not None else None, h)
    r = c.getresponse()
    data = r.read()
    return r.status, data, dict(r.getheaders())


def test_server_requires_token_everywhere(srv):
    port, app = srv
    for path in ("/", "/api/overview", "/api/summary", "/api/files?path=results", "/api/live/state", "/api/tests"):
        assert call(port, "GET", path, token=None)[0] == 401, path
        app.fails.clear()                                    # kilit ayrı testte sınanır
        assert call(port, "GET", path, token="yanlis" * 5)[0] == 401, path
        app.fails.clear()
    assert call(port, "POST", "/api/queue", {"test_id": "ok"}, token=None)[0] == 401
    assert call(port, "GET", "/api/overview")[0] == 200
    st, _, h = call(port, "GET", "/?token=" + "t" * 24, token=None)
    assert st == 303 and "HttpOnly" in h["Set-Cookie"] and "SameSite=Strict" in h["Set-Cookie"]
    assert call(port, "GET", "/", token=None, headers={"Cookie": "ops_token=" + "t" * 24})[0] == 200


def test_server_locks_out_repeated_failures(srv):
    port, _ = srv
    codes = [call(port, "GET", "/api/overview", token="x" * 24)[0] for _ in range(12)]
    assert codes[:10] == [401] * 10 and codes[10] == 429
    assert call(port, "GET", "/api/overview")[0] == 429       # kilit doğru jetonu da bir süre durdurur (kaba kuvveti sınırlar)


def test_files_endpoint_is_readonly_sandboxed(srv):
    port, _ = srv
    assert call(port, "GET", "/api/files?path=../../etc/passwd")[0] == 400
    assert call(port, "GET", "/api/files?path=/etc/passwd")[0] == 400
    assert call(port, "GET", "/api/files?path=src")[0] == 400
    assert call(port, "GET", "/api/files?path=docs/karar_defteri.md")[0] == 200
    assert call(port, "GET", "/api/files?path=results/ops/token")[0] == 400
    assert call(port, "GET", "/api/files?path=.git/config")[0] == 400


def test_post_cross_origin_rejected_and_no_arbitrary_command(srv):
    port, app = srv
    assert call(port, "POST", "/api/queue", {"test_id": "ok"}, headers={"Origin": "http://evil.example"})[0] == 403
    st, data, _ = call(port, "POST", "/api/queue", {"test_id": "rm -rf /"})
    assert st == 400 and b"bilinmeyen test" in data
    st, data, _ = call(port, "POST", "/api/queue", {"test_id": "ok", "params": {"komut": "x"}})
    assert st == 400
    assert call(port, "POST", "/api/queue", {"test_id": "ok"})[0] == 200
    assert call(port, "POST", "/api/queue", {"test_id": "val"})[0] == 400      # doğrulayıcı onaysız
    assert call(port, "POST", "/api/queue", {"test_id": "val", "confirm": True})[0] == 200
    assert not hasattr(S.Handler, "do_PUT") and not hasattr(S.Handler, "do_DELETE")


def test_load_token_generates_strong_private_token(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "TOKEN_FILE", tmp_path / "tok")
    monkeypatch.delenv("SINEK_OPS_TOKEN", raising=False)
    t = S.load_or_create_token()
    assert len(t) >= 32 and oct((tmp_path / "tok").stat().st_mode)[-3:] == "600" and S.load_or_create_token() == t
    with pytest.raises(SystemExit):
        S.load_or_create_token("kisa")


# --------------------------------------------------------------------------- git yayını
def test_relay_signature_and_replay():
    cmd = {"id": "a1", "ts": time.time(), "action": "enqueue", "test_id": "ok", "params": {}}
    cmd["sig"] = sign("s" * 20, cmd)
    assert verify("s" * 20, cmd) is None
    assert verify("baska" * 5, cmd) == "imza geçersiz"
    tampered = dict(cmd, test_id="gv0")
    assert verify("s" * 20, tampered) == "imza geçersiz"
    old = dict(cmd, ts=time.time() - 10 * 86400)
    old["sig"] = sign("s" * 20, old)
    assert "eski" in verify("s" * 20, old)


def test_relay_roundtrip_with_local_bare_remote(tmp_path):
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-b", "main", str(seed)], check=True, capture_output=True)
    (seed / "x").write_text("1")
    for c in (["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "i"], ["remote", "add", "origin", str(bare)], ["push", "origin", "main"]):
        subprocess.run(["git", *c], cwd=seed, check=True, capture_output=True)
    jm = JobManager(tmp_path / "ops", registry=fake_registry())
    app = S.App("s" * 20, jm, LiveSession())
    rl = Relay(app, "origin:ops-relay", "s" * 20, url=str(bare), workdir=tmp_path / "srv_clone")
    rl.cycle_once()                                                    # ilk döngü: dalı oluşturur, durum yazar
    from sinek.ops.relay import ensure_clone, git
    cl = ensure_clone(tmp_path / "cli", "origin", "ops-relay", url=str(bare))
    assert (cl / "status.json").exists()
    good = {"id": "c1", "ts": time.time(), "action": "enqueue", "test_id": "ok", "params": {}, "confirm": False}
    good["sig"] = sign("s" * 20, good)
    forged = {"id": "c2", "ts": time.time(), "action": "enqueue", "test_id": "slow", "params": {}, "sig": "0" * 64}
    (cl / "commands").mkdir()
    for c in (good, forged):
        (cl / "commands" / f"{c['id']}.json").write_text(json.dumps(c))
    git(cl, "config", "user.name", "c"), git(cl, "config", "user.email", "c@c")
    git(cl, "add", "-A"), git(cl, "commit", "-m", "k"), git(cl, "push", "origin", "HEAD:ops-relay")
    rl.cycle_once()
    assert [j["test_id"] for j in jm.state["jobs"]] == ["ok"]          # imzasız komut uygulanmadı
    st = json.loads((tmp_path / "srv_clone" / "status.json").read_text())
    assert st["acked"]["c1"]["result"].startswith("sıraya alındı") and st["acked"]["c2"]["result"].startswith("RET")
    rl.cycle_once()
    assert len(jm.state["jobs"]) == 1                                   # tekrar uygulanmaz
    # değişen yokken boşuna commit yok (depo şişmesin)
    head = git(tmp_path / "srv_clone", "rev-parse", "HEAD")
    rl.cycle_once()
    assert git(tmp_path / "srv_clone", "rev-parse", "HEAD") == head
    # tekrar dosyası dala kopyalanır, ağır dosya kopyalanmaz
    from sinek.ops import live as LV
    LV.REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    small, big = LV.REPLAY_DIR / "_t_kucuk.json.gz", LV.REPLAY_DIR / "_t_buyuk.json.gz"
    try:
        small.write_bytes(b"x" * 100)
        big.write_bytes(b"y" * 700_000)
        rl.cycle_once()
        names = {p.name for p in (tmp_path / "srv_clone" / "replays").glob("*")}
        assert "_t_kucuk.json.gz" in names and "_t_buyuk.json.gz" not in names
    finally:
        small.unlink(missing_ok=True)
        big.unlink(missing_ok=True)
    # geçmiş sıkıştırma: eşik aşılınca dal tek commit'e iner, durum korunur
    import sinek.ops.relay as RM
    old = RM.PRUNE_AFTER
    RM.PRUNE_AFTER = 1
    try:
        jm.enqueue("p", {"x": 3})
        rl.cycle_once()
    finally:
        RM.PRUNE_AFTER = old
    cl2 = ensure_clone(tmp_path / "cli2", "origin", "ops-relay", url=str(bare))
    assert int(git(cl2, "rev-list", "--count", "HEAD").strip()) == 1
    assert json.loads((cl2 / "status.json").read_text())["acked"]["c1"]["result"].startswith("sıraya alındı")


# --------------------------------------------------------------------------- canlı izleme
def test_live_session_streams_real_world_state(cfg, tmp_path):
    pre = pretrain(cfg, odor_patterns(cfg.world, 3), 2, seed=3, episodes=1, seconds=4.0)
    rel = f"results/ops/_test_pre_{os.getpid()}.npz"
    path = R.ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.save(pre, path)
    try:
        ls = LiveSession()
        with pytest.raises(ParamError):
            ls.start(rel, "O2near", "plastic", 200)                      # doğrulayıcı tohumu
        with pytest.raises(ParamError):
            ls.start("../x.npz", "O2near", "plastic", 120)
        ls.start(rel, "O2near", "plastic", 120, agents=1, trials=2, seconds=5, fps=60, episodes=1)
        assert wait(lambda: ls.status.get("state") in ("bitti", "hata"), 120), ls.status
        assert ls.status["state"] == "bitti", ls.status
        seq, snap = ls.snapshot()
        lay = json.loads(snap[0])
        assert lay["type"] == "layout" and lay["B"] == 2 and lay["arena"] == 40.0
        assert len(ls.history) == 1 and len(ls.history[0]["slots"]) == 2
        rp = LV.replay_read(ls.status["replay"])                          # kayıt = yayınlanan gerçek kareler
        assert rp["episodes"][0]["layout"]["B"] == 2 and rp["episodes"][0]["frames"] and rp["episodes"][0]["end"]["slots"] == ls.history[0]["slots"]
        with pytest.raises(ParamError):
            LV.replay_read("../../../etc/passwd")
        with pytest.raises(ParamError):
            LV.replay_read("yok.json.gz")
        fr = json.loads(snap[-1])
        assert fr["type"] == "frame" and all(0 <= x <= 40 for x in fr["x"]) and len(fr["vl"]) == 2
    finally:
        for rp_ in LV.REPLAY_DIR.glob("*_O2near_plastic_s120.json.gz"):
            rp_.unlink()
        path.unlink(missing_ok=True)
        Path(str(path) + ".json").unlink(missing_ok=True)


def test_setup_check_rotates_token_without_touching_remote(tmp_path, monkeypatch, capsys):
    from sinek.ops import setup as SU
    monkeypatch.setattr(S, "TOKEN_FILE", tmp_path / "tok")
    monkeypatch.setattr(SU, "TOKEN_FILE", tmp_path / "tok")
    monkeypatch.delenv("SINEK_OPS_TOKEN", raising=False)
    assert SU.main(["--no-relay-check"]) == 0
    t1 = (tmp_path / "tok").read_text().strip()
    assert SU.main(["--no-relay-check", "--rotate-token"]) == 0
    t2 = (tmp_path / "tok").read_text().strip()
    assert t1 != t2 and len(t2) >= 32 and t2 in capsys.readouterr().out
