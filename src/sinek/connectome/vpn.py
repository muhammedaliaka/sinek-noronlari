"""Görsel projeksiyon nöronlarının (VPN) KC'lere bağlantısının çıkarılması (O6 planı §3; yalnız duyu ön ucu).

    python3 -I -m sinek.connectome.vpn           # ham veri: data/raw/malecns_v1.0 ; çıktı: data/processed/malecns_v1.0_R/{vpn_neurons,vpn_kc}.feather

Seçim kuralı `malecns.extract_mushroom_body` içindeki PN kuralının aynısıdır: üst sınıf `visual_projection` olan ve işlenmiş alt ağdaki KC'lere (KC listesi
`neurons.feather`'dan okunur, yeniden türetilmez) toplam en az `min_syn` sinaps veren nöronlar. Mevcut `neurons.feather` / `edges.feather` DEĞİŞMEZ
(eski sonuçların ve kontrol noktalarının özeti aynı kalır); görsel nöronlar ayrı dosyalardadır.
Model varsayımı (veri değil): nörotransmitter işareti PN ile aynı kuralla (yalnız GABA eksi).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as pf

from .malecns import ANNOT, NT, WEIGHTS

SUPERCLASS = "visual_projection"


def extract_vpn(raw: Path, proc: Path, min_syn: int = 20) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    kc = pd.read_feather(proc / "neurons.feather").query("pop == 'KC'")
    kc_ids = kc["bodyId"].to_numpy()
    ann = pf.read_table(raw / ANNOT, columns=["bodyId", "superclass", "type", "somaSide", "statusLabel"]).to_pandas()
    nt = pf.read_table(raw / NT, columns=["body", "consensus_nt", "predicted_nt_confidence"]).to_pandas()
    nt = nt.rename(columns={"body": "bodyId", "consensus_nt": "nt", "predicted_nt_confidence": "nt_conf"})
    w = pf.read_table(raw / WEIGHTS, memory_map=True)
    cand = ann.loc[ann["superclass"] == SUPERCLASS, "bodyId"].to_numpy()
    m = pc.and_(pc.is_in(w["body_post"], value_set=pa.array(kc_ids)), pc.is_in(w["body_pre"], value_set=pa.array(cand)))
    e = w.filter(m).to_pandas()
    tot = e.groupby("body_pre").weight.sum()
    keep = tot[tot >= min_syn].index.to_numpy()
    e = e[e.body_pre.isin(keep)].reset_index(drop=True)
    n = ann[ann.bodyId.isin(keep)].merge(nt, on="bodyId", how="left").sort_values(["type", "bodyId"]).reset_index(drop=True)
    meta = {"superclass": SUPERCLASS, "min_syn": min_syn, "n_vpn": int(len(n)), "n_edges": int(len(e)), "n_synapses": int(e.weight.sum()),
            "n_kc_targeted": int(e.body_post.nunique()), "n_kc": int(len(kc_ids)),
            "kc_types_targeted": kc.set_index("bodyId").loc[e.body_post.unique(), "type"].value_counts().to_dict()}
    return n, e, meta


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", default="data/raw/malecns_v1.0")
    ap.add_argument("--proc", default="data/processed/malecns_v1.0_R")
    ap.add_argument("--min-syn", type=int, default=20)
    a = ap.parse_args(argv)
    proc = Path(a.proc)
    n, e, meta = extract_vpn(Path(a.raw), proc, a.min_syn)
    n.to_feather(proc / "vpn_neurons.feather")
    e.to_feather(proc / "vpn_kc.feather")
    (proc / "vpn_meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta, indent=1, ensure_ascii=False))
    print(n["type"].value_counts().head(15).to_dict())


if __name__ == "__main__":
    main()
