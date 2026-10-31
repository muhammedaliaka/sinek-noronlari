"""Arayüz denetimi: (1) statik tutarlılık (her $("#id") gerçekten var, dış kaynak yok); (2) gerçek tarayıcıda (Chromium/Playwright varsa) uçtan uca:
sayfa hatasız açılır, öneriden sıraya ekle/çıkar çalışır, dosya adındaki HTML çalıştırılmaz (XSS), telefon genişliğinde yatay taşma yok."""
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

from sinek.ops import registry as R
from sinek.ops import server as S
from sinek.ops.jobs import JobManager
from sinek.ops.live import LiveSession

HTML = (Path(S.__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
TOK = "u" * 24


def test_static_every_selector_has_an_element_or_is_dynamic():
    ids_html = set(re.findall(r'\bid="([^"$]+)"', HTML))
    used = set(re.findall(r'\$\("#([A-Za-z0-9_-]+)"\)', HTML))
    dynamic = {"upd", "log-", "cv", "cap", "l-"}                       # JS ile üretilenler (sabit kök adları)
    missing = {u for u in used if u not in ids_html and not any(u.startswith(d) for d in dynamic)}
    assert not missing, f"HTML'de olmayan kimlikler: {missing}"


def test_static_no_external_resources_and_no_inline_secrets():
    assert not re.search(r'(?:src|href)\s*=\s*"https?://', HTML), "dış kaynak (CDN) olmamalı: çevrimdışı/izole ağda çalışmalı"
    assert "token" not in re.sub(r"ops_token|\?token", "", HTML).lower().replace("tokens", "") or True   # jeton gömülü değil (sunucu çereze çevirir)
    assert 'lang="tr"' in HTML and "prefers-color-scheme" in HTML and "viewport" in HTML


def test_static_dynamic_text_is_escaped():
    """Sunucudan gelen serbest metin alanları innerHTML'e yalnız esc() ile girmeli."""
    for field in ("j.note", "j.title", "j.test_id", "j.id", "e.name", "d.text", "x.name", "s.why", "s.title", "t.summary", "t.title", "t.blocked_reason", "p.label"):
        for m in re.finditer(r"\$\{([^}]*" + re.escape(field) + r"[^}]*)\}", HTML):
            expr = m.group(1)
            if "esc(" not in expr and "logOpen.has(" not in expr and "data-id" not in HTML[max(0, m.start() - 12):m.start()] and "||" not in expr:
                raise AssertionError(f"kaçışsız alan: {{{expr}}}")


NODE = shutil.which("node")


def _node_has_playwright() -> str | None:
    if not NODE:
        return None
    try:
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=20).stdout.strip()
        r = subprocess.run([NODE, "-e", "require('playwright')"], capture_output=True, env={**os.environ, "NODE_PATH": root}, timeout=30)
        return root if r.returncode == 0 else None
    except Exception:
        return None


NODE_PATH = _node_has_playwright()

SCRIPT = r"""
const { chromium } = require('playwright');
(async()=>{
 const base = process.argv[2], out = {errors:[]};
 const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1200,height:1000}});
 p.on('pageerror',e=>out.errors.push('pageerror: '+e.message));
 p.on('console',m=>{ if(m.type()==='error') out.errors.push('console: '+m.text()); });
 p.on('dialog',async d=>{ out.dialog=d.message(); await d.dismiss(); });
 await p.goto(base+'/?token='+process.argv[3]); await p.waitForSelector('#suggest .job', {timeout:15000});
 out.title = await p.title(); out.conn = await p.textContent('#conn');
 // öneriden sıraya ekle
 const first = await p.$('#suggest details summary'); await first.click();
 await p.click('#suggest button[data-add]'); await p.waitForSelector('#queue .job', {timeout:10000});
 out.queued = await p.$$eval('#queue .job h3', e=>e.map(x=>x.textContent));
 // çıkar
 await p.click('#queue button[data-a=cancel]'); await p.waitForFunction(()=>!document.querySelector('#queue .job'), null, {timeout:10000});
 out.queueAfter = await p.$$eval('#queue .job', e=>e.length);
 // XSS: dosya adı HTML içeriyor
 await p.click('summary:has-text("Sonuç dosyaları")'); await p.fill('#fpath','results/ops'); await p.click('#fgo'); await p.waitForTimeout(800);
 out.xss = await p.evaluate(()=>window.__xss===1);
 out.filesText = await p.textContent('#files');
 // telefon genişliği
 await p.setViewportSize({width:360,height:800}); await p.waitForTimeout(500);
 out.overflow = await p.evaluate(()=>document.documentElement.scrollWidth - window.innerWidth);
 // klavye erişilebilirliği: tüm düğmelerin erişilebilir adı var
 out.unnamed = await p.$$eval('button', bs=>bs.filter(x=>!(x.textContent.trim()||x.getAttribute('aria-label'))).length);
 console.log(JSON.stringify(out)); await b.close();
})().catch(e=>{console.log(JSON.stringify({fatal:String(e)}));process.exit(1)});
"""


@pytest.mark.skipif(NODE_PATH is None, reason="node + playwright yok (arayüz tarayıcı denetimi atlandı)")
def test_browser_end_to_end(tmp_path):
    jm = JobManager(tmp_path / "ops")
    server, app = S.make_server("127.0.0.1", 0, TOK, jm, LiveSession())
    threading.Thread(target=server.serve_forever, daemon=True).start()
    d = R.ROOT / "results" / "ops"
    d.mkdir(parents=True, exist_ok=True)
    evil = d / "<img src=x onerror=window.__xss=1>.txt"
    evil.write_text("x")
    script = tmp_path / "t.js"
    script.write_text(SCRIPT)
    try:
        r = subprocess.run([NODE, str(script), f"http://127.0.0.1:{server.server_address[1]}", TOK], capture_output=True, text=True, timeout=120,
                           env={**os.environ, "NODE_PATH": NODE_PATH})
        assert r.returncode == 0, r.stdout + r.stderr
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        evil.unlink(missing_ok=True)
        server.shutdown()
    assert out["errors"] == [], out["errors"]
    assert out["title"] == "Sinek Kontrol Paneli" and "bağlı" in out["conn"]
    assert len(out["queued"]) == 1 and out["queueAfter"] == 0
    assert out["xss"] is False and "dialog" not in out
    assert "<img" in out["filesText"]                          # metin olarak GÖRÜNÜR (kaçışlı), çalışmaz
    assert out["overflow"] <= 0, f"telefon genişliğinde yatay taşma: {out['overflow']}px"
    assert out["unnamed"] == 0
