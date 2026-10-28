"""Evre 1 deney hattı: A (koku/ödül öğrenme) -> C (bellek kalıcılığı) -> B (ödül tersine çevirme).

    python -m sinek.experiments.evre1 --out results/evre1

Üç koşul aynı batch içinde koşar: plastic (öğrenen), frozen (aynı deneyim,
öğrenme kapalı), random (yalnızca rastgele gezinme). Başarı ölçütleri README'de
önceden yazılıdır; bu betik onları otomatik hesaplayıp PASS/FAIL raporlar.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..config import Config
from . import protocol as P


def build_parser(description: str | None = None, default_out: str = "results/evre1") -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=description or __doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agents", type=int, default=20, help="koşul başına canlı sayısı")
    ap.add_argument("--episodes", type=int, default=8, help="A eğitimi bölüm sayısı")
    ap.add_argument("--reversal-episodes", type=int, default=8)
    ap.add_argument("--episode-seconds", type=float, default=60.0)
    ap.add_argument("--trials", type=int, default=4, help="canlı başına seçim denemesi")
    ap.add_argument("--test-seconds", type=float, default=40.0)
    ap.add_argument("--test-every", type=int, default=2, help="kaç bölümde bir seçim testi")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=default_out)
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--quick", action="store_true", help="hızlı duman testi (anlamlı istatistik vermez)")
    ap.add_argument("--swap-roles", action=argparse.BooleanOptionalAction, default=False,
                    help="koşul başına canlıların ikinci yarısında A rolü koku 1 olur (koku kimliği dengelemesi, Evre 2b)")
    return ap


def parse_args(argv=None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def log(msg: str, t0: float) -> None:
    print(f"[{time.time() - t0:7.0f}s] {msg}", flush=True)


def fmt_pref(d: dict) -> str:
    lo, hi = d["pref_A_ci95"]
    return f"{d['pref_A_mean']:.2f} [{lo:.2f}, {hi:.2f}]"


def main(argv=None) -> dict:
    return run(parse_args(argv), Config())


def run(a: argparse.Namespace, cfg: Config, patterns=None, title: str = "Evre 1", extra: dict | None = None,
        evaluator=None, renderer=None, curve_key: str = "pref_A") -> dict:
    """A -> C -> B hattı. `patterns`: koku desenleri (None: seed'ten); `extra`: sonuç dosyasına eklenir.

    `evaluator(stages, a, conds, persisted)` ve `renderer(result)` Evre 2b için değiştirilebilir (varsayılan: Evre 1 ölçütleri).
    """
    evaluator = evaluator or evaluate
    renderer = renderer or render_summary
    if a.quick:
        a.agents, a.episodes, a.reversal_episodes = 4, 2, 2   # çift: rol dengelemesiyle de çalışır
        a.episode_seconds, a.trials, a.test_seconds, a.test_every = 15.0, 2, 15.0, 1
    t0 = time.time()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    conds = ["plastic"] * a.agents + ["frozen"] * a.agents + ["random"] * a.agents
    creature = P.build(cfg, conds, seed=a.seed, device=a.device, patterns=patterns)
    swap = _swap_mask(a.agents, 3, a.swap_roles)
    if a.swap_roles:
        creature.world.set_swap(torch.as_tensor(swap))
    test_seed = 12345 + a.seed
    n_neurons = creature.brain.n_neurons()
    log(f"canlı başına {n_neurons} nöron; {len(conds)} canlı ({a.agents} x 3 koşul), cihaz={a.device}", t0)

    stages: list[dict] = []
    contacts_by_cond: dict[str, list] = {c: [] for c in P.CONDITIONS}
    cond_arr = np.array(conds)

    def run_test(name: str, episode: int, phase: str) -> P.ChoiceResult:
        res = P.choice_test(creature, a.trials, a.test_seconds, seed=test_seed)
        summ = P.summarize(res, conds)
        stages.append({"name": name, "episode": episode, "phase": phase, "summary": summ,
                       "n_a": res.n_a.tolist(), "n_b": res.n_b.tolist()})
        log(f"{name:<22} A-tercih  plastic {fmt_pref(summ['plastic'])} | frozen {fmt_pref(summ['frozen'])}"
            f" | random {fmt_pref(summ['random'])} | seçim oranı plastic {summ['plastic']['choice_rate']:.2f}", t0)
        return res

    def train_block(first_ep: int, n_eps: int, rewards, phase: str) -> None:
        creature.world.set_rewards(*rewards)
        for k in range(1, n_eps + 1):
            tl = P.train(creature, 1, a.episode_seconds, rewards)
            c = tl.contact_array()[0]
            assert c.shape[-1] == 2, "rol eşlemesi iki koku varsayar"
            c = np.where(swap[:, None], c[:, ::-1], c)    # koku -> rol (A/B)
            for cond in P.CONDITIONS:
                contacts_by_cond[cond].append(c[cond_arr == cond].mean(0))
            ep = first_ep + k
            log(f"{phase} bölüm {ep}: plastic temas A={contacts_by_cond['plastic'][-1][0]:.1f} "
                f"B={contacts_by_cond['plastic'][-1][1]:.1f}", t0)
            if k % a.test_every == 0 or k == n_eps:
                run_test(f"{phase} sonrası bölüm {ep}", ep, phase)

    # ---- 0. naif --------------------------------------------------------------
    naive = run_test("naif (eğitimsiz)", 0, "naive")

    # ---- A. koku/ödül öğrenme -----------------------------------------------
    train_block(0, a.episodes, (1.0, 0.0), "A")
    after_a_stage = stages[-1]
    after_a_res = P.ChoiceResult(
        np.array(after_a_stage["n_a"]), np.array(after_a_stage["n_b"]), a.trials, np.zeros(len(conds))
    )
    traj_after_a = P.record_trajectories(creature, [i for i in _pick(conds, "plastic", 6) if not swap[i]], a.test_seconds)

    # ---- C. bellek kalıcılığı ---------------------------------------------------
    ck = checkpoint.save(creature, out / "after_A.npz", extra={"phase": "after_A"})
    reloaded = checkpoint.load(ck, device=a.device)
    res_loaded = P.choice_test(reloaded, a.trials, a.test_seconds, seed=test_seed)
    identical = bool(
        np.array_equal(res_loaded.n_a, after_a_res.n_a) and np.array_equal(res_loaded.n_b, after_a_res.n_b)
    )
    w_equal = bool(np.array_equal(
        reloaded.brain.W.cpu().numpy(), creature.brain.W.cpu().numpy()))
    log(f"C kalıcılık: ağırlıklar birebir={w_equal}, test sonuçları birebir={identical}", t0)

    # ---- B. ödül tersine çevirme ---------------------------------------------
    rev_start = a.episodes
    train_block(rev_start, a.reversal_episodes, (0.0, 1.0), "B")
    traj_after_b = P.record_trajectories(creature, [i for i in _pick(conds, "plastic", 6) if not swap[i]], a.test_seconds)

    # ---- ölçütler -------------------------------------------------------------
    verdict = evaluator(stages, a, conds, identical and w_equal)
    result = {
        "args": vars(a), "config": cfg.to_dict(), "neurons_per_creature": n_neurons,
        "stages": stages, "verdict": verdict,
        "contacts": {k: np.array(v).tolist() for k, v in contacts_by_cond.items()},
        "persistence": {"weights_identical": w_equal, "test_identical": identical},
        "swap": swap.astype(int).tolist(),
        "wall_seconds": time.time() - t0,
        "title": title, **(extra or {}),
    }
    (out / "results.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    (out / "summary.md").write_text(renderer(result))
    if not a.no_plots:
        try:
            from . import plots

            curve = [{"episode": s["episode"], "summary": s["summary"]} for s in stages]
            plots.learning_curve(curve, rev_start, out / "ogrenme_egrisi.png", key=curve_key)
            plots.contacts_curve({k: np.array(v) for k, v in contacts_by_cond.items()}, rev_start, out / "temaslar.png")
            plots.trajectories({"A eğitiminden sonra": traj_after_a, "ödül tersine çevrildikten sonra": traj_after_b},
                               out / "yollar.png")
        except ImportError:
            log("matplotlib yok; grafikler atlandı (pip install matplotlib)", t0)
    log(f"bitti. Özet: {out / 'summary.md'}", t0)
    for k, v in verdict.items():
        log(f"  {'PASS' if v['pass'] else 'FAIL'}  {k}: {v['detail']}", t0)
    return result


def _swap_mask(n_agents: int, n_cond: int, swap_roles: bool) -> np.ndarray:
    """Koşul başına canlıların ilk yarısı normal, ikinci yarısı A rolü = koku 1 (rol-dengeli tasarım)."""
    m = np.zeros(n_agents * n_cond, dtype=bool)
    if swap_roles:
        if n_agents % 2:
            raise ValueError("--swap-roles için canlı sayısı (--agents) çift olmalı, yoksa rol dengelemesi bozulur")
        for c in range(n_cond):
            m[c * n_agents + n_agents // 2:(c + 1) * n_agents] = True
    return m


def _pick(conds, name, n):
    return [i for i, c in enumerate(conds) if c == name][:n]


def _pref(stage, cond):
    return np.array([np.nan if v is None else v for v in stage["summary"][cond]["pref_A_per_agent"]])


def evaluate(stages, a, conds, persisted: bool) -> dict:
    """README'deki önceden yazılmış başarı ölçütlerini hesaplar."""
    last_a = next(s for s in reversed(stages) if s["phase"] == "A")
    last_b = next(s for s in reversed(stages) if s["phase"] == "B")
    naive = stages[0]
    v = {}

    pl = last_a["summary"]["plastic"]
    p_fr = P.permutation_p(_pref(last_a, "plastic"), _pref(last_a, "frozen"))
    p_rn = P.permutation_p(_pref(last_a, "plastic"), _pref(last_a, "random"))
    v["A1 öğrenme: eğitilmiş A-tercihi > 0.5 (GA alt sınırı)"] = {
        "pass": bool(pl["pref_A_ci95"][0] > 0.5),
        "detail": f"plastic {fmt_pref(pl)}"}
    v["A2 öğrenme: plastic > frozen ve > random (p<0.01)"] = {
        "pass": bool(p_fr < 0.01 and p_rn < 0.01 and pl["pref_A_mean"] > last_a["summary"]["frozen"]["pref_A_mean"]
                     and pl["pref_A_mean"] > last_a["summary"]["random"]["pref_A_mean"]),
        "detail": f"p(frozen)={p_fr:.4f}, p(random)={p_rn:.4f}"}
    nv = naive["summary"]["plastic"]
    v["A3 naif canlının tercihi yok (GA 0.5'i kapsar)"] = {
        "pass": bool(nv["pref_A_ci95"][0] <= 0.5 <= nv["pref_A_ci95"][1]),
        "detail": f"naif plastic {fmt_pref(nv)}"}
    v["C bellek: yeniden yüklenen canlı birebir aynı davranır"] = {
        "pass": bool(persisted), "detail": "ağırlıklar ve test sonuçları birebir eşit" if persisted else "FARK VAR"}
    pb = last_b["summary"]["plastic"]
    p_rev = P.permutation_p(_pref(last_a, "plastic"), _pref(last_b, "plastic"))
    v["B1 tersine çevirme: A-tercihi anlamlı düştü (p<0.01)"] = {
        "pass": bool(p_rev < 0.01 and pb["pref_A_mean"] < pl["pref_A_mean"]),
        "detail": f"{pl['pref_A_mean']:.2f} -> {pb['pref_A_mean']:.2f}, p={p_rev:.4f}"}
    v["B2 tersine çevirme: B artık tercih edilir (A-tercihi GA üst sınırı < 0.5)"] = {
        "pass": bool(pb["pref_A_ci95"][1] < 0.5), "detail": f"plastic {fmt_pref(pb)}"}
    return v


def render_summary(r: dict) -> str:
    a = r["args"]
    L = [f"# {r.get('title', 'Evre 1')} sonuç özeti", ""]
    L.append(f"- Canlı başına nöron: **{r['neurons_per_creature']}** (spiking nöronlar + tat/temas nöronları)")
    L.append(f"- Canlı sayısı: koşul başına **{a['agents']}** (plastic / frozen / random), seçim denemesi canlı başına **{a['trials']}**")
    L.append(f"- Eğitim: A için {a['episodes']} bölüm, tersine çevirmede {a['reversal_episodes']} bölüm, bölüm = {a['episode_seconds']:.0f} sanal sn")
    L.append(f"- Toplam çalışma süresi: {r['wall_seconds'] / 60:.1f} dk, tohum: {a['seed']}")
    L += ["", "## Ölçütler", ""]
    for k, v in r["verdict"].items():
        L.append(f"- **{'PASS' if v['pass'] else 'FAIL'}** — {k}: {v['detail']}")
    L += ["", "## Seçim testi: A tercih oranı A/(A+B)", "",
          "Ortalama [%95 bootstrap GA]; 0.5 = tercih yok. Seçim oranı = bir kaynağa ulaşan deneme oranı.", "",
          "| Aşama | Bölüm | plastic | frozen | random | seçim oranı (plastic) |", "|---|---:|---|---|---|---:|"]
    for s in r["stages"]:
        sm = s["summary"]
        L.append(f"| {s['name']} | {s['episode']} | {fmt_pref(sm['plastic'])} | {fmt_pref(sm['frozen'])} | "
                 f"{fmt_pref(sm['random'])} | {sm['plastic']['choice_rate']:.2f} |")
    L += ["", "## Notlar", "",
          "- `frozen`: aynı deneyimi yaşar ama sinapslar değişmez; `random`: dönüş kazancı 0.",
          "- Seçim testlerinde tüm aşamalar aynı rastgele düzenleri kullanır (ortak rastgele sayılar); aşamalar arası farklar bu yüzden daha az gürültülüdür, ama aşamalar birbirinden bağımsız örneklem değildir.",
          "- Bu sonuçlar sanal ortam ve bu model için geçerlidir; gerçek sinek davranışı hakkında iddia taşımaz."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
