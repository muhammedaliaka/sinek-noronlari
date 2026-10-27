"""Çıkarılan alt ağın denetimi: Markdown raporu üretir.

    python -m sinek.connectome.audit --raw data/raw/malecns_v1.0 --out docs/evre2_veri_denetimi.md

Raporun amacı varsayımları görünür kılmaktır: hangi nöronlar neye göre seçildi, soma tarafı ile
bağlantıya dayalı yarımküre ataması nerede ayrışıyor, eşik değerlerine duyarlılık, bölme eşlemesi ne kadar keskin.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import malecns, mbmodel
from .graph import Connectome
from .sources import MALE_CNS


def _md(df: pd.DataFrame) -> str:
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    L = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for idx, row in df.iterrows():
        L.append("| " + " | ".join([str(idx)] + [("%g" % v if isinstance(v, (float, np.floating)) else str(v)) for v in row]) + " |")
    return "\n".join(L)


def audit(raw_dir: str, c: Connectome, thresholds=(10, 20, 50)) -> str:
    n = c.neurons
    d = mbmodel.from_connectome(c)
    out = ["# Evre 2 — veri denetimi (MaleCNS v1.0, sağ yarımküre mantar cismi)", "",
           f"Kaynak: {MALE_CNS.title}, `{MALE_CNS.version}`, lisans {MALE_CNS.license}. {MALE_CNS.citation_note}", "",
           "Bu rapor `python -m sinek.connectome.audit` ile üretilir; sayılar çıkarılan alt ağdan hesaplanır.", ""]

    out += ["## 1. Popülasyonlar", ""]
    t = pd.DataFrame({
        "nöron": n.groupby("pop").size(),
        "tip": n.groupby("pop")["type"].nunique(),
        "soma R": n[n.somaSide == "R"].groupby("pop").size(),
        "soma L": n[n.somaSide == "L"].groupby("pop").size(),
    }).fillna(0).astype(int).reindex(malecns.POP_ORDER)
    t.index.name = "popülasyon"
    out += [_md(t), "",
            f"Kenar: {c.meta['n_edges']}, toplam sinaps: {c.meta['n_synapses']}. "
            "Soma tarafı L olan nöronlar bağlantıya göre sağ yarımküreye atanmıştır (aşağıda ayrıntı).", ""]

    out += ["## 2. Nörotransmitter (sınıflandırıcı tahmini; ölçüm değil)", ""]
    nt = pd.crosstab(n["pop"], n["nt"]).reindex(malecns.POP_ORDER)
    nt.index.name = "popülasyon"
    out += [_md(nt), "",
            "Beklenti: KC = asetilkolin, APL = GABA, DAN = dopamin, MBON karışık. DPM için gerçekte serotonin / GABA beklenir; "
            "'dopamin' tahmini yanlıştır ve DPM bu nedenle simülasyona alınmaz. 3 PN'nin GABA tahmini inhibitör PN'lerle uyumludur ve işareti simülasyonda korunur.", ""]

    out += ["## 3. PN → KC bağlantısı", ""]
    W = c.block("PN", "KC")
    per_kc = (W > 0).sum(0)
    kc = n[n["pop"] == "KC"].reset_index(drop=True)
    out += [f"- KC başına PN (benzersiz): ortalama {per_kc.mean():.2f}, medyan {np.median(per_kc):.0f}, "
            f"yüzdelikler 5/95: {np.percentile(per_kc, 5):.0f}/{np.percentile(per_kc, 95):.0f}",
            f"- Bağlantı başına ortalama sinaps: {W[W > 0].mean():.1f} (maks {W.max():.0f})",
            f"- PN girdisi olmayan KC: {int((per_kc == 0).sum())}/{len(per_kc)} — tipleri: "
            f"{kc[per_kc == 0].type.value_counts().to_dict()} (görsel girdili KC alt tipleri beklenir)",
            f"- Glomerül (PN grubu) sayısı: {d.n_glom}; glomerül başına PN: "
            f"{pd.Series(d.pn_glom).value_counts().value_counts().sort_index().to_dict()} (PN sayısı: glomerül sayısı)", ""]

    out += ["## 4. Yarımküre ataması: soma tarafı ↔ bağlantı", "",
            "MBON ve DAN'larda soma tarafı ile bağlantıya dayalı atama farklıdır; bağlantı esas alınmıştır:", ""]
    lr = n[(n.somaSide != "R") & n["pop"].isin(["PN", "MBON", "DAN"])]
    out += [_md(lr.groupby(["pop", "type"]).size().rename("soma L").to_frame()), ""]

    out += [f"### Eşik duyarlılığı (`min_syn`)", "", "| min_syn | " + " | ".join(malecns.POP_ORDER) + " |",
            "|---|" + "|".join(["---:"] * len(malecns.POP_ORDER)) + "|"]
    for ms in thresholds:
        cc = c if ms == c.meta["min_syn"] else malecns.extract_mushroom_body(raw_dir, side=c.meta["side"], min_syn=ms)
        out.append(f"| {ms} | " + " | ".join(str(cc.meta["counts"][p]) for p in malecns.POP_ORDER) + " |")
    out.append("")

    out += ["## 5. Bölme eşlemesi: MBON tipi ↔ DAN sınıfı", "",
            "Her MBON'un aldığı DAN sinapslarının PPL1 payı. `u` = PPL1 payı − PAM payı "
            "(u→+1: PPL1 bölmesi, **yaklaş** sınıfı; u→−1: PAM bölmesi, **kaçın** sınıfı). Bu eşleme bir **model varsayımıdır**.", ""]
    mb = pd.DataFrame({"tip": d.mbon_types, "nt": n.set_index("bodyId").loc[d.ids["MBON"], "nt"].to_numpy(), "u": d.mbon_u})
    g = mb.groupby("tip").agg(nöron=("u", "size"), nt=("nt", lambda s: "/".join(sorted(set(s)))), u=("u", "mean")).round(2)
    g["sınıf"] = np.where(g.u > 0.5, "yaklaş", np.where(g.u < -0.5, "kaçın", "karışık"))
    g.index.name = "MBON tipi"
    out += [_md(g), "",
            f"Keskin eşleme (|u| > 0.8): {int((np.abs(d.mbon_u) > 0.8).sum())}/{d.n_mbon} MBON. "
            f"Sınıf sayıları: yaklaş {d.summary['mbon_approach']}, kaçın {d.summary['mbon_avoid']}.",
            "", "Sınıf × nörotransmitter (MBON sayısı):", ""]
    ct = pd.crosstab(np.where(d.mbon_u > 0, "yaklaş (PPL1)", "kaçın (PAM)"), mb.nt)
    ct.index.name = "sınıf"
    out += [_md(ct), "",
            "Nörotransmitter ile sınıf tam örtüşmez (ör. PAM bölmelerinde asetilkolinli ve GABA'lı MBON'lar da vardır); "
            "bu yüzden sınıf, nörotransmitter işaretinden değil DAN bölme payından türetilmiştir ve sonuçlar bu varsayıma bağlıdır "
            "(karıştırma kontrolü: `docs/evre2_sonuclar.md`).", ""]

    out += ["## 6. Kapsam dışı bırakılanlar (bilinçli)", "",
            "- KC → KC (586 648 sinaps), MBON → MBON, MBON → DAN, DAN → KC: simülasyonda yok (DAN → KC bölme bilgisi taşımaz; "
            "bölme DAN → MBON'dan çıkarılır).",
            "- PPL2 / PPM3 gibi diğer dopamin nöronları, MB-C1 gibi MB ilişkili diğer tipler, DPM.",
            "- Açıklanmamış nöron parçaları (KC girdisinin ~%4'ü).", ""]
    return "\n".join(out)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=f"data/raw/{MALE_CNS.key}")
    ap.add_argument("--processed", default=mbmodel.DEFAULT_DIR)
    ap.add_argument("--out", default="docs/evre2_veri_denetimi.md")
    a = ap.parse_args(argv)
    c = Connectome.load(mbmodel.resolve_dir(a.processed))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(audit(a.raw, c))
    print(f"yazıldı: {a.out}")


if __name__ == "__main__":
    main()
