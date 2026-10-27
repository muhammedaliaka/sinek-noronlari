"""MaleCNS v1.0'dan mantar cismi (mushroom body) alt ağının çıkarılması.

Seçim kuralları tamamen verideki açıklamalardan ve bağlantılardan türetilir:

  KC    : class == Kenyon_Cell ve soma tarafı `side`
  PN    : tip adı "PN" ile biter ve seçilen KC'lere en az `min_syn` sinaps verir (glomerül = "_" öncesi)
  MBON  : tip "MBON..." ve KC girdisinin >= %50'si seçilen KC'lerden (yarımküre bağlantıdan bulunur)
  DAN   : tip PAM.. veya PPL1.. ve (seçilen KC + MBON)'lara en az `min_syn` sinaps, oranın >= %50'si bu yarımküreye
  APL/DPM: tip adı APL / DPM, KC'lerle sinaps oranı >= %50 bu yarımküreye

Soma tarafı yerine bağlantı kullanılır, çünkü bazı MBON'ların hücre gövdesi karşı taraftadır.
Kapsam dışı bırakılanlar (bilinçli): PPL2/PPM12 DAN'ları, MB-C1 gibi diğer MB-ilişkili tipler,
ve açıklanmamış nöron parçaları (KC girdisinin ~%4'ü).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as pf

from .graph import Connectome
from .sources import MALE_CNS

ANNOT = "body-annotations-male-cns-v1.0-minconf-0.5.feather"
NT = "body-neurotransmitters-male-cns-v1.0.feather"
WEIGHTS = "connectome-weights-male-cns-v1.0-minconf-0.5.feather"

POP_ORDER = ["PN", "KC", "APL", "DPM", "MBON", "DAN"]


def load_neurons(raw: Path) -> pd.DataFrame:
    a = pf.read_table(raw / ANNOT).to_pandas()
    nt = pf.read_table(raw / NT, columns=["body", "consensus_nt", "predicted_nt_confidence"]).to_pandas()
    nt = nt.rename(columns={"body": "bodyId", "consensus_nt": "nt", "predicted_nt_confidence": "nt_conf"})
    return a.merge(nt, on="bodyId", how="left")


def _edges_touching(table: pa.Table, ids: np.ndarray, *, pre: bool, post: bool) -> pd.DataFrame:
    vs = pa.array(ids)
    mask = None
    if post:
        mask = pc.is_in(table["body_post"], value_set=vs)
    if pre:
        m2 = pc.is_in(table["body_pre"], value_set=vs)
        mask = m2 if mask is None else pc.or_(mask, m2)
    return table.filter(mask).to_pandas()


def extract_mushroom_body(raw_dir: str | Path, side: str = "R", min_syn: int = 20) -> Connectome:
    raw = Path(raw_dir)
    ann = load_neurons(raw)
    ty = ann["type"].fillna("")
    w = pf.read_table(raw / WEIGHTS, memory_map=True)

    kc = ann[(ann["class"] == "Kenyon_Cell") & (ann["somaSide"] == side)]
    kc_ids = kc["bodyId"].to_numpy()
    kc_all = ann.loc[ann["class"] == "Kenyon_Cell", "bodyId"].to_numpy()

    kc_in = _edges_touching(w, kc_ids, pre=False, post=True)     # X -> KC(side)
    kc_out = _edges_touching(w, kc_ids, pre=True, post=False)    # KC(side) -> X
    t_of = ann.set_index("bodyId")["type"].fillna("")

    # ---- PN
    pre_t = t_of.reindex(kc_in.body_pre).to_numpy()
    pn_syn = kc_in[pd.Series(pre_t).str.endswith("PN").to_numpy()].groupby("body_pre").weight.sum()
    pn_ids = pn_syn[pn_syn >= min_syn].index.to_numpy()

    # ---- MBON: KC girdisinin yarımküre oranı
    all_kc_to = _edges_touching(w, np.array(kc_all), pre=True, post=False)
    mb_syn_all = all_kc_to[t_of.reindex(all_kc_to.body_post).str.startswith("MBON").to_numpy()]
    tot = mb_syn_all.groupby("body_post").weight.sum()
    side_syn = kc_out[kc_out.body_post.isin(tot.index)].groupby("body_post").weight.sum()
    frac = (side_syn / tot).dropna()
    mbon_ids = frac[(frac >= 0.5) & (side_syn.reindex(frac.index) >= min_syn)].index.to_numpy()

    # ---- DAN: PAM/PPL1; (KC + MBON) hedeflerine sinaps oranı
    dan_pool = ann.loc[ty.str.match(r"^(PAM|PPL1)\d"), "bodyId"].to_numpy()
    d_out = _edges_touching(w, dan_pool, pre=True, post=False)
    in_side = d_out.body_post.isin(np.concatenate([kc_ids, mbon_ids]))
    in_any = d_out.body_post.isin(np.concatenate([kc_all, mbon_ids]))   # karşı yarımküre KC'leri dahil
    dan_side = d_out[in_side].groupby("body_pre").weight.sum()
    dan_any = d_out[in_any].groupby("body_pre").weight.sum()
    dfrac = (dan_side / dan_any).dropna()
    dan_ids = dfrac[(dfrac >= 0.5) & (dan_side.reindex(dfrac.index) >= min_syn)].index.to_numpy()

    # ---- APL / DPM
    def _local(name: str) -> np.ndarray:
        pool = ann.loc[ty == name, "bodyId"].to_numpy()
        e = _edges_touching(w, pool, pre=True, post=True)
        kc_set = set(kc_ids.tolist()); kc_other = set(kc_all.tolist()) - kc_set
        to_side = e[e.body_pre.isin(pool) & e.body_post.isin(kc_set)].groupby("body_pre").weight.sum()
        from_side = e[e.body_post.isin(pool) & e.body_pre.isin(kc_set)].groupby("body_post").weight.sum()
        side_tot = to_side.add(from_side, fill_value=0)
        oth_to = e[e.body_pre.isin(pool) & e.body_post.isin(kc_other)].groupby("body_pre").weight.sum()
        oth_from = e[e.body_post.isin(pool) & e.body_pre.isin(kc_other)].groupby("body_post").weight.sum()
        oth_tot = oth_to.add(oth_from, fill_value=0)
        f = side_tot / side_tot.add(oth_tot, fill_value=0)
        return f[f >= 0.5].index.to_numpy()

    apl_ids, dpm_ids = _local("APL"), _local("DPM")

    pops = {"PN": pn_ids, "KC": kc_ids, "APL": apl_ids, "DPM": dpm_ids, "MBON": mbon_ids, "DAN": dan_ids}
    rows = []
    for p in POP_ORDER:
        sub = ann[ann.bodyId.isin(pops[p])].copy()
        sub["pop"] = p
        sub["group"] = sub["type"].fillna("").str.replace(r"_.*$", "", regex=True) if p == "PN" else sub["type"]
        rows.append(sub)
    neurons = pd.concat(rows, ignore_index=True)
    neurons = neurons[["bodyId", "pop", "type", "group", "somaSide", "superclass", "nt", "nt_conf", "statusLabel"]]
    order = pd.CategoricalDtype(POP_ORDER, ordered=True)
    neurons = neurons.assign(pop=neurons["pop"].astype(order)).sort_values(["pop", "type", "bodyId"])
    neurons = neurons.assign(pop=neurons["pop"].astype(str)).reset_index(drop=True)

    sel = neurons["bodyId"].to_numpy()
    edges = _edges_touching(w, sel, pre=True, post=False)
    edges = edges[edges.body_post.isin(sel)].reset_index(drop=True)

    meta = {
        "source": MALE_CNS.key, "version": MALE_CNS.version, "license": MALE_CNS.license,
        "home": MALE_CNS.home, "citation_note": MALE_CNS.citation_note,
        "files_md5": {f.name: f.md5_hex for f in MALE_CNS.files},
        "side": side, "min_syn": min_syn,
        "counts": {p: int(len(pops[p])) for p in POP_ORDER},
        "n_edges": int(len(edges)), "n_synapses": int(edges.weight.sum()),
    }
    return Connectome(neurons=neurons, edges=edges, meta=meta)


def describe(c: Connectome) -> str:
    """Çıkarılan alt ağın kısa, doğrulanabilir özeti (sayılar, soma tarafı, nörotransmitter)."""
    n = c.neurons
    L = [f"{c.meta['source']}  taraf={c.meta['side']}  min_syn={c.meta['min_syn']}",
         f"kenar={c.meta['n_edges']}  sinaps={c.meta['n_synapses']}", ""]
    L.append("popülasyon  nöron  tip  somaSide  nörotransmitter")
    for p in POP_ORDER:
        s = n[n["pop"] == p]
        L.append(f"{p:<10} {len(s):>6} {s['type'].nunique():>4}  "
                 f"{s['somaSide'].value_counts().to_dict()}  {s['nt'].value_counts().to_dict()}")
    return "\n".join(L)


def main(argv=None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description="MaleCNS ham dosyalarından mantar cismi alt ağını çıkarır")
    ap.add_argument("--raw", default=f"data/raw/{MALE_CNS.key}")
    ap.add_argument("--out", default=f"data/processed/{MALE_CNS.key}_R")
    ap.add_argument("--side", default="R", choices=["R", "L"])
    ap.add_argument("--min-syn", type=int, default=20)
    a = ap.parse_args(argv)
    c = extract_mushroom_body(a.raw, side=a.side, min_syn=a.min_syn)
    c.save(a.out)
    print(describe(c))
    print(f"\nkaydedildi: {a.out}")


if __name__ == "__main__":
    main()
