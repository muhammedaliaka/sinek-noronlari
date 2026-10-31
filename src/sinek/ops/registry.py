"""Çalıştırılabilir test/iş kayıt defteri. YALNIZ burada tanımlı komutlar çalışır (keyfi komut yok): sunucuya uzaktan erişen biri
(ben ya da kullanıcı) en fazla bu listedeki işleri, doğrulanmış parametrelerle kuyruğa koyabilir.

Her kayıt gerçek bir betiğe/modüle bağlıdır; ilerleme ve bitiş durumu gerçek dosyalardan okunur (sahte yüzde yok).
"""
from __future__ import annotations

import glob
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
DEV_SEED_MAX = 149           # R-2: geliştirme tohumları 100-149; ≥200 doğrulayıcıya ayrılmıştır


class ParamError(ValueError):
    pass


@dataclass(frozen=True)
class Param:
    name: str
    label: str
    kind: str                      # int | float | choice | pre
    default: object = None
    lo: float | None = None
    hi: float | None = None
    choices: tuple = ()
    flag: str | None = None        # komut satırı bayrağı (None: konumsal değil, yalnız bağlam için)
    help: str = ""

    def coerce(self, v):
        if v is None or v == "":
            v = self.default
        if self.kind == "int":
            try:
                v = int(v)
            except (TypeError, ValueError):
                raise ParamError(f"{self.name}: tamsayı olmalı")
        elif self.kind == "float":
            try:
                v = float(v)
            except (TypeError, ValueError):
                raise ParamError(f"{self.name}: sayı olmalı")
            if v != v or v in (float("inf"), float("-inf")):
                raise ParamError(f"{self.name}: sonlu sayı olmalı")
        elif self.kind == "choice":
            if v not in self.choices:
                raise ParamError(f"{self.name}: {list(self.choices)} içinden biri olmalı")
        elif self.kind == "pre":
            v = safe_results_file(str(v), ".npz")
        if self.kind in ("int", "float"):
            if self.lo is not None and v < self.lo or self.hi is not None and v > self.hi:
                raise ParamError(f"{self.name}: [{self.lo}, {self.hi}] aralığında olmalı")
        return v


def safe_results_file(rel: str, suffix: str | None = None) -> str:
    """results/ altında VAR OLAN bir dosyanın göreli yolu (yol atlatma ve mutlak yol reddedilir)."""
    p = (ROOT / rel).resolve()
    base = (ROOT / "results").resolve()
    if base not in p.parents or not p.is_file() or (suffix and p.suffix != suffix):
        raise ParamError(f"results/ altında var olan bir {suffix or 'dosya'} olmalı: {rel}")
    return str(p.relative_to(ROOT))


_PRE_CACHE: dict = {"t": 0.0, "v": []}


def find_pre_files() -> list[str]:
    """Bulunan ön-eğitimli popülasyon dosyaları (gerçek dosyalar). results/ büyükse yinelenen taramayı önlemek için 10 sn önbellek."""
    if time.time() - _PRE_CACHE["t"] < 10.0:
        return list(_PRE_CACHE["v"])
    out = sorted(glob.glob(str(ROOT / "results" / "**" / "pre_*.npz"), recursive=True))
    _PRE_CACHE.update(t=time.time(), v=[str(Path(p).relative_to(ROOT)) for p in out])
    return list(_PRE_CACHE["v"])


def git_tracked_commit(path: str) -> str | None:
    """Dosyanın git'te izlendiği (commit edilmiş) en son commit kısa kodu; yoksa None."""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%h", "--", path], cwd=ROOT, capture_output=True, text=True, timeout=10)
        h = r.stdout.strip()
        return h or None
    except Exception:
        return None


@dataclass
class TestDef:
    __test__ = False                   # pytest bu sınıfı test sanmasın
    id: str
    title: str
    summary: str
    group: str                         # dogrulayici | gelistirme | kapi | arac | test | planli
    base: Callable[[dict], list[str]]  # parametrelerden argv (her zaman bu Python ile başlar; bash gerekmez)
    params: tuple = ()
    prereg: str | None = None          # doğrulayıcı koşular için ön-kayıt belgesi (R-1): commit edilmiş olmalı
    requires: tuple = ()               # var olması gereken dosyalar (kök göreli)
    done_when: Callable[[dict], bool] | None = None
    progress: Callable[[dict], tuple[int, int, str]] | None = None
    resumable: bool = False            # yeniden başlatılırsa kontrol noktasından AYNI hesapla sürer
    gpu: str = "yok"                   # yok | var | kısmi — gerçek durum, iddia değil
    gpu_note: str = ""
    priority: int = 50                 # küçük = önce
    cost: str = ""
    report_files: tuple = ()           # iş bitince özetlenecek metin çıktıları (kök göreli glob)
    disabled_reason: str | None = None
    validator: bool = False
    after: tuple = ()                  # bu işlerden SONRA önerilir (id)
    why: str = ""                      # akıllı öneride gösterilen gerekçe

    def runnable(self) -> tuple[bool, str]:
        if self.disabled_reason:
            return False, self.disabled_reason
        miss = [r for r in self.requires if not (ROOT / r).exists()]
        if miss:
            return False, "eksik dosya: " + ", ".join(miss)
        if any(p.kind == "pre" for p in self.params) and not find_pre_files():
            return False, "ön-eğitimli popülasyon dosyası yok (önce 'Hızlı demo popülasyonu' ya da bir ön-eğitim işi)"
        if self.prereg:
            h = git_tracked_commit(self.prereg)
            if not (ROOT / self.prereg).exists() or not h:
                return False, f"ön-kayıt belgesi commit edilmemiş ({self.prereg}) — R-1"
        return True, ""

    def build_params(self, given: dict | None) -> dict:
        given = given or {}
        unknown = set(given) - {p.name for p in self.params}
        if unknown:
            raise ParamError(f"bilinmeyen parametre: {sorted(unknown)}")
        return {p.name: p.coerce(given.get(p.name)) for p in self.params}

    def argv(self, vals: dict) -> list[str]:
        return self.base(vals)

    def is_done(self, vals: dict) -> bool:
        return bool(self.done_when and self.done_when(vals))

    def public(self) -> dict:
        ok, why = self.runnable()
        return {"id": self.id, "title": self.title, "summary": self.summary, "group": self.group, "prereg": self.prereg,
                "validator": self.validator, "resumable": self.resumable, "gpu": self.gpu, "gpu_note": self.gpu_note, "cost": self.cost,
                "runnable": ok, "blocked_reason": why, "after": list(self.after), "why": self.why,
                "params": [{"name": p.name, "label": p.label, "kind": p.kind, "default": p.default, "lo": p.lo, "hi": p.hi,
                            "choices": list(p.choices) if p.kind != "pre" else find_pre_files(), "help": p.help} for p in self.params]}


PY = [sys.executable, "-X", "utf8", "-I", "-m"]      # -X utf8: Windows'ta varsayılan kodlama UTF-8 değildir (Türkçe/→/≥ yazdıran betikler çökmesin; -I ortam değişkenlerini yok sayar)


def _exists(*rel):
    return all((ROOT / r).exists() for r in rel)


# --------------------------------------------------------------------------- O5c (ön-kayıtlı doğrulayıcı)
O5C_SEEDS = (("274", "206"), ("275", "207"), ("276", "208"), ("277", "209"))
O5C_ARMS = ("plastic_t", "plastic", "frozen")
O5C_CHUNKS = 8


def o5c_progress(_vals) -> tuple[int, int, str]:
    pre = sum(_exists(f"results/odor_val/pre_s{p}.npz") for _, p in O5C_SEEDS)
    part = 0
    for s, _ in O5C_SEEDS:
        d = ROOT / "results" / "o5_val" / f"c_s{s}" / "partial"
        part += len(glob.glob(str(d / "*.npz")))
    fin = sum(_exists(f"results/o5_val/c_s{s}/results.json") for s, _ in O5C_SEEDS)
    total = 4 + 4 * (len(O5C_ARMS) * O5C_CHUNKS + 1) + 4
    done = pre + part + fin
    return min(done, total), total, f"ön-eğitim {pre}/4 · kol×parça dosyası {part}/{4 * (len(O5C_ARMS) * O5C_CHUNKS + 1)} · değerlendirme {fin}/4"


def o5c_done(_vals) -> bool:
    return all(_exists(f"results/o5_val/c_s{s}/results.json") for s, _ in O5C_SEEDS)


def _reg() -> dict[str, TestDef]:
    T: list[TestDef] = []
    T.append(TestDef(
        "demo_pre", "Hızlı demo popülasyonu (canlı izleme için)",
        "Küçük bir ön-eğitimli canlı kümesi üretir (4 canlı, kısa). Canlı oyun izlemesi için ön koşul; KANIT DEĞİLDİR.",
        "arac", lambda v: PY + ["sinek.experiments.odor_pretrain", "--seed", str(v["seed"]), "--agents", str(v["agents"]), "--episodes", str(v["episodes"]),
                                "--episode-seconds", str(v["episode_seconds"]), "--threads", str(v["threads"]), "--device", v["device"], "--out", "results/ops/pre_demo.npz"],
        params=(Param("seed", "Tohum (geliştirme 100-149)", "int", 150, 100, 199, flag="--seed"), Param("agents", "Canlı sayısı (çift)", "int", 4, 2, 24),
                Param("episodes", "Ön-eğitim bölümü", "int", 2, 1, 12), Param("episode_seconds", "Bölüm süresi (sn)", "float", 20.0, 5, 60),
                Param("threads", "CPU iş parçacığı", "int", 2, 1, 32), Param("device", "Cihaz", "choice", "cpu", choices=("cpu", "cuda"))),
        done_when=lambda v: _exists("results/ops/pre_demo.npz"), priority=10, cost="dakikalar (CPU)", gpu="var",
        gpu_note="--device cuda desteklenir (yalnız bu araç ve canlı izleme; doğrulayıcılar CPU'da kalır, K-059)", resumable=False,
        why="Canlı izleme için ilk gereksinim."))
    T.append(TestDef(
        "pytest", "Birim testleri", "Depodaki tüm testler (`pytest -q tests`). Kurulumun doğru çalıştığını gösterir.", "test",
        lambda v: PY + ["pytest", "-q", "tests", "-x"], priority=5, cost="birkaç dk", gpu="yok",
        why="Yeni makinede kurulumun sağlam olduğunu doğrular."))
    T.append(TestDef(
        "gv0", "G-V0 — görsel ayrılabilirlik kapısı", "O6 görsel ön ucunun iki deseni KC düzeyinde ayırıp ayırmadığını ölçer (tekrarlı ölçüm, K-050).", "kapi",
        lambda v: PY + ["sinek.experiments.gv0_ayrilabilirlik", "--n", str(v["n"]), "--reps", str(v["reps"]), "--out", "results/ops/gv0_son.md"],
        params=(Param("n", "Ağ sayısı", "int", 32, 4, 128), Param("reps", "Tekrar", "int", 6, 1, 20)),
        report_files=("results/ops/gv0_son.md",), priority=40, cost="dakikalar", gpu="yok", why="Görsel ön ucun tabanını yeniden doğrular."))
    T.append(TestDef(
        "gv2", "G-V2 — zorunlu temasta öğrenme kapasitesi", "Görsel ve koku kanalının zorunlu temasta ne kadar öğrenebildiğini ölçer (K-053).", "kapi",
        lambda v: PY + ["sinek.experiments.gv2_ogrenme_kapasitesi"], requires=("results/odor_games/pre_s102.npz",),
        priority=45, cost="dakikalar", gpu="yok", why="O6b tanısında kullanılan kapı; geliştirme popülasyonu (tohum 102) gerekir."))
    T.append(TestDef(
        "o6_pilot", "O6 geliştirme pilotu (kanıt değildir)", "O6a/O6b/O6c oyununda saf ve kör kolların blok blok net tercih tablosu. Geliştirme tohumları 100-149.", "gelistirme",
        lambda v: PY + ["sinek.experiments.o6_dev", "--pre", v["pre"], "--game", v["game"], "--seed", str(v["seed"]), "--agents", str(v["agents"]),
                        "--copies", str(v["copies"]), "--episodes", str(v["episodes"]), "--seconds", str(v["seconds"]), "--n-vis", "6", "--threads", str(v["threads"]),
                        "--vis-taxis", str(v["vis_taxis"]), "--out", f"results/ops/o6_{v['game']}_s{v['seed']}.md"]
        + (["--reward-target", str(v["reward_target"])] if v["reward_target"] > 0 else []),
        params=(Param("pre", "Popülasyon dosyası", "pre", None), Param("game", "Oyun", "choice", "O6b", choices=("O6a", "O6b", "O6c")),
                Param("seed", "Oyun tohumu (100-149)", "int", 140, 100, DEV_SEED_MAX), Param("agents", "Canlı", "int", 12, 2, 48), Param("copies", "Kopya", "int", 2, 2, 8),
                Param("episodes", "Bölüm", "int", 24, 4, 80), Param("seconds", "Bölüm süresi (sn)", "float", 30.0, 10, 60),
                Param("vis_taxis", "Görsel yaklaşma refleksi (0=kapalı)", "float", 0.0, 0, 20),
                Param("reward_target", "DAN hedefi T (0=varsayılan 0,6)", "float", 0.0, 0, 5), Param("threads", "CPU iş parçacığı", "int", 2, 1, 32)),
        report_files=("results/ops/o6_*.md",), priority=60, cost="10-60 dk", gpu="yok",
        why="O6b çözülmedi (K-058); seçilen yol için tek önceden yazılmış değerle deneme."))
    T.append(TestDef(
        "o5c_pretrain_validator", "O5c — ön-kayıtlı doğrulayıcı (T=2,5; 4 popülasyon)",
        "docs/odor_o5c_plani.md'ye göre: ön-eğitim 206-209, plastic_t/plastic/frozen kolları, değerlendirme. Kesinleşmiş ölçütler DEĞİŞMEZ; yalnız CPU (K-059). Windows/Linux/Mac: bash gerekmez (K-062).", "dogrulayici",
        lambda v: PY + ["sinek.ops.o5c_kuyruk", "--workers", str(v["workers"])],
        params=(Param("workers", "Paralel işçi", "int", 4, 1, 32, help="CPU çekirdek sayısına göre"),),
        prereg="docs/odor_o5c_plani.md", done_when=o5c_done, progress=o5c_progress, resumable=True, validator=True, priority=20,
        cost="saatler (CPU, 4 işçi ≈ 10-20 sa tahmin)", gpu="yok",
        gpu_note="Doğrulayıcı CPU'da koşar: GPU'da rastgele sayı akışları farklı olur, ön-kayıtlı CRN eşlemesi/sonuçlar karşılaştırılamaz (K-059)",
        report_files=("results/o5c_ozet.md",), why="Bekleyen en önemli doğrulayıcı (K-057); kalıcı makine gerekiyordu."))
    T.append(TestDef(
        "o5c_ozet", "O5c — hüküm özeti", "Biten O5c sonuçlarından ön-kayıtlı hüküm kuralını uygular (yalnız okur).", "arac",
        lambda v: PY + ["sinek.experiments.o5c_ozet", "--out", "results/o5c_ozet.md"], requires=("results/o5_val/c_s274/results.json",),
        report_files=("results/o5c_ozet.md",), priority=21, after=("o5c_pretrain_validator",), cost="saniyeler", gpu="yok",
        why="Doğrulayıcı bitince hükmü yazar."))
    T.append(TestDef(
        "reg_t25", "T=2,5 gerileme denetimi (O1–O3)", "T=2,5 varsayılan olmadan önce O1–O3 oyunlarında gerileme olmadığını gösteren betik (henüz yazılmadı).", "planli",
        lambda v: [], disabled_reason="betik henüz yazılmadı (planlandı: K-048 sonrası)", priority=30, after=("o5c_pretrain_validator",),
        why="T'yi varsayılan yapmanın ön koşulu."))
    T.append(TestDef(
        "o6b_audit", "O6b — öğrenme zamanı/işareti denetimi", "Temas anında öğrenme zamanlamasını ve işaretini denetleyen tanı (henüz yazılmadı).", "planli",
        lambda v: [], disabled_reason="betik henüz yazılmadı (planlandı: K-058 devamı)", priority=35,
        why="O6b'nin açık hipotezlerinden biri."))
    return {t.id: t for t in T}


REGISTRY: dict[str, TestDef] = _reg()


def suggest(done_ids: set[str], queued_ids: set[str], n: int = 5) -> list[dict]:
    """Akıllı öneri: çalıştırılabilir, bitmemiş, kuyrukta olmayan işler; ön koşulu (after) bitenler önce, sonra öncelik sırası.
    Her satır gerekçesini taşır (gerçek duruma göre)."""
    rows = []
    for t in REGISTRY.values():
        ok, why_not = t.runnable()
        if t.id in queued_ids:
            continue
        vals = None
        try:
            vals = t.build_params({p.name: (find_pre_files()[0] if p.kind == "pre" and find_pre_files() else None) for p in t.params if p.kind == "pre"} or None)
        except ParamError:
            pass
        finished = bool(vals is not None and t.is_done(vals)) if t.done_when else (t.id in done_ids and t.group != "dogrulayici")
        waiting = [a for a in t.after if a not in done_ids and not (REGISTRY[a].done_when and REGISTRY[a].is_done({}))]
        rows.append({"id": t.id, "title": t.title, "runnable": ok, "blocked_reason": why_not, "finished": finished, "waiting_for": waiting,
                     "priority": t.priority, "why": t.why, "group": t.group})
    rows = [r for r in rows if not r["finished"]]
    rows.sort(key=lambda r: (not r["runnable"], bool(r["waiting_for"]), r["priority"]))
    return rows[:n]
