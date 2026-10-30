"""Görsel girdi fizibilite denetimi (O6 planı §1): sağ yarımküredeki KC'lerin sinaptik girdisi presinaptik üst sınıfa (superclass) göre nereden geliyor?

    python3 -I -m sinek.connectome.visual_audit --out docs/gorsel_girdi_denetimi.md

Çıktı: KC alt tipi başına (a) girdi ağırlığının üst sınıf payları, (b) görsel projeksiyon (visual_projection) nöronlarının tipleri ve ağırlıkları.
Ham veri `data/raw/malecns_v1.0` (≈1 GB; `python -m sinek.connectome.fetch`) gerekir; işlenmiş alt ağ yetmez (görsel PN'ler orada yok).
Bu bir DENETİM'dir: görsel girdinin bağlantı verisinde var olup olmadığını söyler; "görsel öğrenme çalışır" demek değildir.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather

RAW = Path("data/raw/malecns_v1.0")
PROC = Path("data/processed/malecns_v1.0_R")
VISUAL = ("visual_projection", "visual_centrifugal")


def audit(raw: Path = RAW, proc: Path = PROC) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    kc = pd.read_feather(proc / "neurons.feather").query("pop == 'KC'")
    ann = feather.read_table(raw / "body-annotations-male-cns-v1.0-minconf-0.5.feather",
                             columns=["bodyId", "superclass", "type"]).to_pandas()
    w = feather.read_table(raw / "connectome-weights-male-cns-v1.0-minconf-0.5.feather")
    e = w.filter(pc.is_in(w["body_post"], value_set=pa.array(kc["bodyId"].values))).to_pandas()
    e = (e.merge(ann.rename(columns={"bodyId": "body_pre"}), on="body_pre", how="left")
          .merge(kc[["bodyId", "type"]].rename(columns={"bodyId": "body_post", "type": "kctype"}), on="body_post"))
    e["superclass"] = e["superclass"].fillna("(açıklamasız)")
    share = e.pivot_table(index="kctype", columns="superclass", values="weight", aggfunc="sum", fill_value=0)
    share = share.div(share.sum(axis=1), axis=0)
    vis = e[e["superclass"].isin(VISUAL)]
    n_vis_pre = vis.groupby("kctype")["body_pre"].nunique().rename("benzersiz görsel presinaptik nöron")
    n_kc = kc.groupby("type").size().rename("KC sayısı")
    summary = pd.concat([n_kc, share.get("visual_projection", 0).rename("görsel proj. ağırlık payı"), n_vis_pre], axis=1).fillna(0)
    top = (vis.groupby(["kctype", "type"])["weight"].sum().rename("toplam ağırlık").reset_index()
              .sort_values("toplam ağırlık", ascending=False))
    return summary, share, top


def main(argv=None) -> str:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if not (RAW / "connectome-weights-male-cns-v1.0-minconf-0.5.feather").exists():
        raise SystemExit("ham veri yok: python -m sinek.connectome.fetch")
    summary, share, top = audit()
    L = ["# Görsel girdi denetimi — MaleCNS v1.0 sağ yarımküre KC'leri (otomatik üretilir: `sinek.connectome.visual_audit`)", "",
         "## KC alt tipine göre görsel projeksiyon girdisi", "", "| KC alt tipi | KC sayısı | görsel proj. ağırlık payı | benzersiz görsel presinaptik nöron |", "|---|---|---|---|"]
    for t, r in summary.sort_values("görsel proj. ağırlık payı", ascending=False).iterrows():
        L.append(f"| {t} | {int(r['KC sayısı'])} | {r['görsel proj. ağırlık payı']:.3f} | {int(r['benzersiz görsel presinaptik nöron'])} |")
    L += ["", "## Üst sınıf payları (satır: KC alt tipi; yalnız ≥%1 olan sütunlar)", ""]
    cols = [c for c in share.columns if share[c].max() >= 0.01]
    L += ["| KC alt tipi | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for t, r in share[cols].iterrows():
        L.append(f"| {t} | " + " | ".join(f"{r[c]:.3f}" for c in cols) + " |")
    L += ["", "## En ağırlıklı görsel presinaptik tipler (KC alt tipi × tip; toplam sinaps ağırlığı)", "", "| KC alt tipi | görsel nöron tipi | ağırlık |", "|---|---|---|"]
    L += [f"| {r.kctype} | {r.type} | {int(r['toplam ağırlık'])} |" for _, r in top.head(25).iterrows()]
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return text


if __name__ == "__main__":
    main()
