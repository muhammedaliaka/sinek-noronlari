"""O5 DOĞRULAYICISI (docs/odor_o5_plani.md): olasılıklı iki-kollu koku oyunu, oturum içi tersine çevirme.

    python -m sinek.experiments.odor_validate_o5 --pre results/odor_val/pre_s200.npz --seed 260 --out results/o5_val/s260
    # kol işçileri (paralel; yalnız kontrol noktası yazar): ... --only-arms plastic    sonra kolsuz çağrı değerlendirir

Kollar (CRN eşli, her eleman bağımsız bir yaşam): plastic (öğrenmemiş beyin, öğrenme AÇIK), frozen (öğrenmemiş beyin, öğrenme kapalı), reference (elle kurulmuş izleyici; tersine çevirmede takip ettiği kokuyu değiştirir).
Canlılar `--chunks` parçaya bölünür (parça başına dünya tohumu seed + 1000·c, tüm kollarda aynı); kol × parça kontrol noktası (K-037 deseni).
GELİŞTİRME (yalnız --pilot): `--ens-k/--ens-tau` ile ek `plastic_ens` kolu (PlasticEnsembleBrain), `--only-chunks` ile parça paralelliği; kontrol noktası anahtarı yalnız bu kol için ayrışır.
Eşikler ve tasarım ön-kayıttadır; bu komut onları keşfetmez. `--pilot`: geliştirme tohumlarında (<200) deneme; doğrulayıcı tohumlar (≥200) `--pilot` olmadan.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from .. import checkpoint
from ..ensemble import PlasticEnsembleBrain
from ..games.protocol import ARMS, bandit_schedule, make_game_creature, play_sequence
from .odor_eval import EVALUATORS, O5_BLOCKS, Thr
from .odor_validate import _git_head, _sha
from .odor_validate_s import _part

CHUNK_STRIDE = 1000
O5B_ENS = (4, 0.04)         # docs/odor_o5b_plani.md: plastic_ens = K 4, τ_valence 0,04
KEYS = ("slot", "got", "better")
ARM_DEFS = {"plastic": ("naive_plastic", True), "frozen": ("naive", False), "reference": ("reference", False)}   # kol → (oyun kolu, öğrenme açık mı)


def _chunks(n: int, chunks: int) -> list[list[int]]:
    if chunks < 1 or n % chunks:
        raise ValueError("canlı sayısı parça sayısına bölünmeli")
    m = n // chunks
    return [list(range(c * m, (c + 1) * m)) for c in range(chunks)]


def run_arms(pre, seed: int, agents: int, copies: int, episodes: int, switch: int, seconds: float, p_hi: float, p_lo: float, chunks: int,
             plastic_scale: float = 1.0, only=None, verbose=True, part_dir=None, key: str = "", ens_k: int = 1, ens_tau=None, only_chunks=None,
             t_target: float | None = None) -> dict:
    """`ens_k > 1` (veya `ens_tau`): GELİŞTİRME kolu `plastic_ens` = plastic + `PlasticEnsembleBrain` (yalnız `--pilot`); varsayılan üç kol değişmez.
    `t_target` (K-048, yalnız `--pilot`): GELİŞTİRME kolu `plastic_t` = plastic + DAN hedefi `reward_target`=t_target (diğer kollar değişmez; CRN eşli).
    `only_chunks`: yalnız bu parçaları koş (paralel işçiler için; kontrol noktası yazar, birleştirme yapılmaz)."""
    parts = _chunks(min(agents, pre.world.B), chunks)
    arm_defs = dict(ARM_DEFS)
    if ens_k > 1 or ens_tau is not None:
        arm_defs["plastic_ens"] = ("naive_plastic", True)
    if t_target is not None:
        arm_defs["plastic_t"] = ("naive_plastic", True)
    suffix = lambda name: (f"|ens_k={ens_k}|ens_tau={ens_tau}" if name == "plastic_ens" else (f"|t_target={t_target}" if name == "plastic_t" else ""))
    res, t0 = {}, time.time()
    for name, (arm, _) in arm_defs.items():
        if only and name not in only:
            continue
        pieces = []
        for ci, ids in enumerate(parts):
            if only_chunks is not None and ci not in only_chunks:
                continue
            path, z = _part(part_dir, f"o5_{name}_c{ci}", key + suffix(name))
            if z is not None:
                pieces.append({k: z[k] for k in KEYS})
                if verbose:
                    print(f"[{time.time() - t0:6.0f}s] O5 {name:<9} parça {ci + 1}/{chunks} kontrol noktasından okundu", flush=True)
                continue
            c = make_game_creature(pre, "O5", arm, ids, copies, seed + CHUNK_STRIDE * ci, reward_target=t_target if name == "plastic_t" else None)
            if name in ("plastic", "plastic_ens", "plastic_t"):
                c.brain.eta_scale = torch.full((c.world.B,), float(plastic_scale))
            if name == "plastic_ens":
                c.brain = PlasticEnsembleBrain(c.brain, ens_k, ens_tau)
            sch = bandit_schedule(c.world.swap.cpu(), episodes, switch, p_hi, p_lo)
            r = play_sequence(c, sch, seconds, learn=ARMS[arm].eta > 0 and (name not in ("plastic", "plastic_ens", "plastic_t") or plastic_scale > 0),
                              flip_swap_at=switch if name == "reference" else None)
            r["better"] = np.stack([(p[:, 1] > p[:, 0]).numpy().astype(int) for p in sch])
            pieces.append({k: r[k] for k in KEYS})
            if path is not None:
                np.savez(path, key=key + suffix(name), **pieces[-1])
            if verbose:
                print(f"[{time.time() - t0:6.0f}s] O5 {name:<9} parça {ci + 1}/{chunks}: ödül oranı {pieces[-1]['got'].mean():.3f}", flush=True)
        if pieces:
            res[name] = {k: np.concatenate([p[k] for p in pieces], axis=1) for k in KEYS}      # (bölüm, yaşam)
    return res


def to_h(res: dict) -> dict:
    """(bölüm, yaşam) kayıtlarından değerlendirici girdisi: (yaşam, bölüm) ödül ve net tercih skoru."""
    h = {}
    for arm, r in res.items():
        h[arm] = r["got"].T.astype(int)
        h["net_" + arm] = np.where(r["slot"] < 0, 0, np.where(r["slot"] == r["better"], 1, -1)).T
    return h


def blocks_table(res: dict, size: int = 5) -> list[str]:
    nb = -(-res["frozen"]["slot"].shape[0] // size)
    L = ["| kol | " + " | ".join(f"b{i + 1}" for i in range(nb)) + " | ödül oranı | temas-yok |", "|---|" + "---|" * (nb + 2)]
    for arm, r in res.items():
        cells = []
        for s in range(0, r["slot"].shape[0], size):
            sl = slice(s, s + size)
            ch = r["slot"][sl] >= 0
            cells.append(f"{((r['slot'][sl] == r['better'][sl]) & ch).sum() / max(ch.sum(), 1):.2f}")
        L.append(f"| {arm} | " + " | ".join(cells) + f" | {r['got'].mean():.2f} | {(r['slot'] < 0).mean():.2f} |")
    return L


def blocks_for(episodes: int, switch: int) -> tuple:
    """Geç faz-1 = tersine çevirmeden önceki yarı, geç faz-2 = sonraki yarı. Varsayılan tasarımda (40 bölüm, 20'de tersine çevirme) = O5_BLOCKS."""
    return ((switch // 2, switch), (switch + (episodes - switch) // 2, episodes))


def ens_section(res: dict, thr: Thr, blocks=O5_BLOCKS) -> list[str]:
    """GELİŞTİRME (yalnız --pilot): plastic_ens betimsel değerlendirmesi ve plastic ile eşli fark (kanıt değildir)."""
    from .stats import paired_cluster_ci
    h = to_h(res)
    ev = EVALUATORS["O5"]({**h, "plastic": h["plastic_ens"], "net_plastic": h["net_plastic_ens"]}, thr, blocks=blocks)
    cols = np.r_[blocks[0][0]:blocks[0][1], blocks[1][0]:blocks[1][1]]
    L = ["", "## GELİŞTİRME: `plastic_ens` (PlasticEnsembleBrain) — kanıt değildir", "", "`plastic_ens − frozen` (ön-kayıtlı ölçüt kuralıyla, betimsel):", ""]
    for k, c in ev["criteria"].items():
        L.append(f"- {'✔' if c['passed'] else '✘'} {k}: fark {c['mean']:+.3f} [GA {c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}], p={c['p']:.4f}")
    L += ["", "`plastic_ens − plastic` (eşli, aynı dünyalar; yaşam birimli küme bootstrap %99 GA):", "", "| ölçü | fark [GA] |", "|---|---|"]
    r_e, r_p = res["plastic_ens"], res["plastic"]
    def late(r):
        slot, better, got = (r[k][cols].T for k in ("slot", "better", "got"))
        contact = slot >= 0
        good = contact & (slot == better)
        return {"ödül oranı": got.astype(float), "temas oranı": contact.astype(float), "net tercih": good.astype(float) - (contact & ~good).astype(float)}
    le, lp = late(r_e), late(r_p)
    for k in le:
        m, lo, hi = paired_cluster_ci(le[k].sum(1), lp[k].sum(1), le[k].shape[1], n=thr.n_boot, seed=11, alpha=thr.alpha)
        L.append(f"| {k} | {m:+.3f} [{lo:+.3f}; {hi:+.3f}] |")
    L += ["", "Mutlak (geç bloklar): " + "; ".join(f"{a}: ödül {late(res[a])['ödül oranı'].mean():.3f}, temas {late(res[a])['temas oranı'].mean():.3f}" for a in ("plastic_ens", "plastic", "frozen"))]
    return L


def evaluate(res: dict, thr: Thr, blocks=O5_BLOCKS, design: str = "O5") -> dict:
    return EVALUATORS[design](to_h(res), thr, blocks=blocks)


def report(seed: int, res: dict, ev: dict, thr: Thr, meta: dict, blocks=O5_BLOCKS) -> str:
    L = [f"# O5 doğrulayıcısı (oyun tohumu {seed})", "",
         f"{meta['stamp']} Ön-eğitim dosyası (yalnız rol dengelemesi/yapılandırma): `{meta['pre']}` (sha256[:16] {meta['pre_sha']}), kod commit `{meta['git']}`.", "",
         f"δ={thr.delta} (ödül/bölüm), α={thr.alpha}, referans kapısı ≥{thr.ref_min}; bloklar: geç faz-1 = bölüm {blocks[0][0] + 1}-{blocks[0][1]}, geç faz-2 = bölüm {blocks[1][0] + 1}-{blocks[1][1]}.", "",
         "## Betimsel: blok başına iyi kokuyu seçme oranı (temas olanlar arasında; blok = 5 bölüm; tersine çevirme bölüm " + str(meta["switch"] + 1) + "'de)", ""] + blocks_table(res)
    L += ["", "## Kapılar", ""] + [f"- {'✔' if v else '✘'} {k}" for k, v in ev["gates"].items()]
    L += ["", "## Ölçütler", ""]
    for k, c in ev["criteria"].items():
        L.append(f"- {'✔' if c['passed'] else '✘'} {k}: fark {c['mean']:+.3f} [GA {c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}], p={c['p']:.4f}")
    for k, c in ev.get("descriptive", {}).items():
        L.append(f"- (betimsel, karar vermez) {k}: fark {c['mean']:+.3f} [GA {c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}], p={c['p']:.4f}")
    L += ["", f"**Karar (bu tohum): {'BAŞARILI' if ev['passed'] else 'BAŞARISIZ'}** (kapılar {'tamam' if ev['gates_ok'] else 'EKSİK'}).",
          "Tüm doğrulayıcı tohumlarda geçmedikçe başarılı sayılmaz; başarısızlık olduğu gibi raporlanır."]
    return "\n".join(L) + "\n"


def main(argv=None) -> dict | None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=24)
    ap.add_argument("--copies", type=int, default=2)
    ap.add_argument("--episodes", type=int, default=40)
    ap.add_argument("--switch", type=int, default=20)
    ap.add_argument("--seconds", type=float, default=40.0)
    ap.add_argument("--p-hi", type=float, default=0.8)
    ap.add_argument("--p-lo", type=float, default=0.2)
    ap.add_argument("--chunks", type=int, default=None, help="varsayılan 4 (O5) / 8 (--o5b)")
    ap.add_argument("--o5b", action="store_true", help="O5b tasarımı (docs/odor_o5b_plani.md): plastic_ens (K=4, τ=0,04) kolu dahil, O5b değerlendirici; ön-kayıtlı doğrulayıcıda kullanılır")
    ap.add_argument("--plastic-scale", type=float, default=1.0)
    ap.add_argument("--delta", type=float, default=0.10)
    ap.add_argument("--ref-min", type=float, default=0.60)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--ens-k", type=int, default=1, help="GELİŞTİRME (--pilot): plastic_ens kolu için topluluk büyüklüğü")
    ap.add_argument("--ens-tau", type=float, default=None, help="GELİŞTİRME (--pilot): plastic_ens okuma entegrasyon süresi (sn)")
    ap.add_argument("--only-chunks", default=None, help="virgülle parça indeksleri: yalnız bu parçaları koş (kontrol noktası yazar), değerlendirme yok")
    ap.add_argument("--plastic-t", type=float, default=None, help="GELİŞTİRME (K-048; yalnız --pilot): ek kol plastic_t = plastic + DAN hedefi reward_target (varsayılan yapılandırma 0,6)")
    ap.add_argument("--only-arms", default=None, help="virgülle: yalnız bu kolları koş (kontrol noktası yaz), değerlendirme yok")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.seed >= 200 and a.pilot:
        raise SystemExit("--pilot yalnız geliştirme tohumlarıyla (<200)")
    if a.seed < 200 and not a.pilot:
        raise SystemExit("200 altı tohum doğrulayıcı olamaz: --pilot ekleyin (R-2)")
    if a.o5b:
        if a.ens_k != 1 or a.ens_tau is not None:
            raise SystemExit("--o5b ens ayarlarını sabitler (K=4, τ=0,04); --ens-k/--ens-tau ile birlikte verilemez")
        a.ens_k, a.ens_tau = O5B_ENS
    a.chunks = a.chunks or (8 if a.o5b else 4)
    ens = a.ens_k > 1 or a.ens_tau is not None
    if ens and not (a.pilot or a.o5b):
        raise SystemExit("--ens-k/--ens-tau geliştirme seçenekleridir: yalnız --pilot ile (ön-kayıtlı doğrulayıcıda yalnız --o5b)")
    if a.plastic_t is not None and not a.pilot:
        raise SystemExit("--plastic-t geliştirme seçeneğidir: yalnız --pilot ile (K-048; doğrulayıcı için ayrı ön-kayıt)")
    if a.threads:
        torch.set_num_threads(a.threads)
    thr = Thr(delta=a.delta, ref_min=a.ref_min, n_boot=a.boot, n_perm=a.boot)
    pre = checkpoint.load(a.pre)
    out = Path(a.out)
    (out / "partial").mkdir(parents=True, exist_ok=True)
    key = json.dumps({"seed": a.seed, "agents": a.agents, "copies": a.copies, "episodes": a.episodes, "switch": a.switch, "seconds": a.seconds, "p_hi": a.p_hi,
                      "p_lo": a.p_lo, "chunks": a.chunks, "plastic_scale": a.plastic_scale, "pre_sha": _sha(a.pre)}, sort_keys=True)
    t0 = time.time()
    only = set(a.only_arms.split(",")) if a.only_arms else None
    only_chunks = {int(x) for x in a.only_chunks.split(",")} if a.only_chunks else None
    res = run_arms(pre, a.seed, a.agents, a.copies, a.episodes, a.switch, a.seconds, a.p_hi, a.p_lo, a.chunks, a.plastic_scale, only, part_dir=out / "partial", key=key,
                   ens_k=a.ens_k, ens_tau=a.ens_tau, only_chunks=only_chunks, t_target=a.plastic_t)
    if only or only_chunks is not None:
        return None
    blocks = blocks_for(a.episodes, a.switch)
    ev = evaluate(res, thr, blocks, "O5b" if a.o5b else "O5")
    meta = {"stamp": "**PİLOT — kanıt değildir.**" if a.pilot else "Doğrulayıcı koşu.", "pre": a.pre, "pre_sha": _sha(a.pre), "git": _git_head(), "switch": a.switch, "blocks": blocks}
    text = report(a.seed, res, ev, thr, meta, blocks)
    if ens and not a.o5b:
        text += "\n".join(ens_section(res, thr, blocks)) + "\n"
    (out / "summary.md").write_text(text, encoding="utf-8")
    (out / "results.json").write_text(json.dumps({"args": vars(a), "meta": meta, "eval": ev,
                                                  "reward_rate": {k: float(v["got"].mean()) for k, v in res.items()},
                                                  "wall_seconds": time.time() - t0}, indent=1, default=float), encoding="utf-8")
    print(text)
    return ev


if __name__ == "__main__":
    main()
