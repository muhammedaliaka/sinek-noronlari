"""R-8 veri kontrolü (yol haritası adım 3.3): DAN girdileri nereden geliyor, MBON→DAN geri bildirimi ne kadar ve hangi işaretle?

    python3 -I -m sinek.experiments.dan_girdi_analizi --out docs/dan_girdi_analizi.md

Betimseldir; bir başarı/karar ölçütü değildir (yalnız modül tasarımına veri sağlar). Ham dosyalar (`data/raw/malecns_v1.0`) gerekir.
Bölümler: A) DAN girdi bileşimi (tam bağlantı grafı); B) doğrudan MBON→DAN sınıf matrisi (işaretli; glutamat işareti belirsiz → iki varsayım);
C) MBON↔DAN karşılıklılığı, DAN-etiketi karıştırma boş modeliyle; D) iki adımlı MBON→X→DAN yol payı (X: aracı nöron).
Nörotransmitter işaretleri sınıflandırıcı TAHMİNLERİDİR (ölçüm değil) [doğrulanmadı: glutamatın işareti reseptöre bağlıdır].
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.feather as pf

from ..connectome import mbmodel
from ..connectome.graph import Connectome

RAW = "data/raw/malecns_v1.0"
W_FILE = f"{RAW}/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
A_FILE = f"{RAW}/body-annotations-male-cns-v1.0-minconf-0.5.feather"
NT_FILE = f"{RAW}/body-neurotransmitters-male-cns-v1.0.feather"
DEFAULT_DIR = mbmodel.DEFAULT_DIR


def _category(typ: np.ndarray, cls: np.ndarray, sup: np.ndarray) -> np.ndarray:
    out = np.empty(len(typ), dtype=object)
    for i, (t, c, s) in enumerate(zip(typ, cls, sup)):
        t, c, s = str(t), str(c), str(s)
        if c == "Kenyon_Cell" or t.startswith("KC"):
            out[i] = "KC"
        elif t.startswith("MBON"):
            out[i] = "MBON"
        elif t.startswith(("PAM", "PPL1", "PPL2", "PPM")):
            out[i] = "DAN (hepsi)"
        elif t in ("APL", "DPM"):
            out[i] = t
        elif s in ("nan", "None"):
            out[i] = "açıklamasız"
        else:
            out[i] = "diğer: " + s
    return out


def _load_raw():
    t = pf.read_table(W_FILE, memory_map=True)
    return t["body_pre"].to_numpy(), t["body_post"].to_numpy(), t["weight"].to_numpy()


def section_a(pre, post, w, d, n) -> list[str]:
    dan_ids = d.ids["DAN"]
    ppl_ids = dan_ids[d.dan_is_ppl]
    m = np.isin(post, dan_ids)
    p, q, ww = pre[m], post[m], w[m]
    ann = pd.read_feather(A_FILE, columns=["bodyId", "superclass", "class", "type"]).drop_duplicates("bodyId").set_index("bodyId")
    a = ann.reindex(p)
    cat = _category(a["type"].to_numpy(), a["class"].to_numpy(), a["superclass"].to_numpy())
    df = pd.DataFrame({"cat": cat, "w": ww, "ppl": np.isin(q, ppl_ids)})
    tot = df.groupby("cat").w.sum().sort_values(ascending=False)
    L = ["## A. DAN girdi bileşimi (tam bağlantı grafı; alt ağdaki 161 sağ-yarımküre DAN'ın aldığı sinapslar)", "",
         f"Toplam {int(df.w.sum()):,} sinaps. Sütunlar: tüm DAN / PAM / PPL1 (sinaps payı).", "",
         "| öncül sınıfı | tüm DAN | PAM | PPL1 |", "|---|---|---|---|"]
    g = df.groupby(["cat", "ppl"]).w.sum().unstack(fill_value=0)
    for cname in tot.index[:12]:
        row = g.loc[cname]
        L.append(f"| {cname} | {tot[cname] / tot.sum():.3f} | {row.get(False, 0) / g[False].sum():.3f} | {row.get(True, 0) / g[True].sum():.3f} |")
    L += ["", "KC = Kenyon hücresi (tüm yarımküreler), MBON/DAN (hepsi) = ad önekine göre. `diğer: cb_intrinsic` = mantar cismi dışında kalan merkez-beyin içi nöronlar (aracılar).", ""]
    return L


def _signed(nt: np.ndarray, glu: float) -> np.ndarray:
    return np.where(nt == "gaba", -1.0, np.where(nt == "glutamate", glu, 1.0))


def section_b_c(c: Connectome, d, n, n_null: int, seed: int) -> list[str]:
    ids = d.ids
    md = c.block("MBON", "DAN", ids["MBON"], ids["DAN"])          # (mbon, dan) sinaps
    dm = c.block("DAN", "MBON", ids["DAN"], ids["MBON"])          # (dan, mbon)
    nt = n.loc[ids["MBON"], "nt"].to_numpy()
    ppl, u = d.dan_is_ppl, d.mbon_u
    app, avo = u > 0.5, u < -0.5
    kc_dan = c.block("KC", "DAN", ids["KC"], ids["DAN"]).sum()
    L = ["## B. Doğrudan MBON→DAN (alt ağ; sağ yarımküre)", "",
         f"MBON→DAN: {int(md.sum()):,} sinaps, {int((md > 0).sum())} kenar. Karşılaştırma: KC→DAN {int(kc_dan):,} sinaps (modelde yok), DAN→MBON {int(dm.sum()):,}.",
         f"MBON sınıfı (modelin u değeri): yaklaş {int(app.sum())}, kaçın {int(avo.sum())}, karışık {int((~app & ~avo).sum())}. DAN: PAM {int((~ppl).sum())}, PPL1 {int(ppl.sum())}.", "",
         "İşaretli sinaps toplamı (satır MBON sınıfı → sütun DAN sınıfı; mutlak toplam parantezde). Glutamat işareti belirsiz olduğundan iki varsayım:", "",
         "| glutamat | yaklaş→PAM | yaklaş→PPL1 | kaçın→PAM | kaçın→PPL1 |", "|---|---|---|---|---|"]
    for glu in (-1.0, +1.0):
        S = md * _signed(nt, glu)[:, None]
        cells = [f"{S[m][:, sel].sum():+.0f} ({md[m][:, sel].sum():.0f})" for m in (app, avo) for sel in (~ppl, ppl)]
        L.append(f"| {'inhibitör (−1)' if glu < 0 else 'eksitatör (+1)'} | " + " | ".join(cells) + " |")
    L += ["", "Çıkarım için tek başına okuma: çıkarıcı hata devresi (yaklaş→PAM <0 ve kaçın→PPL1 <0) yalnız kısmen görülür; sonuç glutamat varsayımına bağlıdır.", ""]
    A, B = (md > 0).astype(float), (dm.T > 0).astype(float)
    rng = np.random.default_rng(seed)
    obs = (A * B).sum()
    nul = np.array([(A * B[:, rng.permutation(B.shape[1])]).sum() for _ in range(n_null)])
    r = np.corrcoef(np.log1p(md).ravel(), np.log1p(dm.T).ravel())[0, 1]
    L += ["## C. MBON↔DAN karşılıklılığı", "",
          f"Karşılıklı (j→i ve i→j) MBON-DAN çifti: **{int(obs)}** (MBON→DAN {int(A.sum())} kenar, DAN→MBON {int(B.sum())} kenar). "
          f"Boş model (DAN etiketi karıştırma, her iki yönün derecesi korunur, {n_null} tekrar): {nul.mean():.1f} ± {nul.std():.1f}; "
          f"gözlenenden büyük ya da eşit boş değer oranı {(nul >= obs).mean():.4f} (alt sınır 1/{n_null}). "
          f"Log-sinaps korelasyonu r={r:.2f}.",
          "Not: boş model bölme (compartment) yapısını da bozar; bu yüzden 'karşılıklılık var' demenin ötesinde bir şey (ör. bölme-içi döngü) söylemez.", ""]
    return L


def section_d(pre, post, w, d, n) -> list[str]:
    """İki adımlı MBON→X→DAN. Ölçü ("atfedilebilir DAN girdisi"): Σ_{j,x} (w_jx / girdi_x) · w_xi / (DAN toplam girdisi), yani
    X'in girdisinin MBON'dan gelen payı kadarının X'in DAN çıktısına yansıdığı varsayılır. Doğrudan MBON→DAN payı ile aynı paydada."""
    mbon, dan = d.ids["MBON"], d.ids["DAN"]
    u = d.mbon_u
    cls_j = pd.Series(np.where(u > 0.5, "yaklaş", np.where(u < -0.5, "kaçın", "karışık")), index=mbon)
    nt_j = n.loc[mbon, "nt"]
    nt_tab = pf.read_table(NT_FILE, memory_map=True, columns=["body", "consensus_nt"]).to_pandas().drop_duplicates("body").set_index("body")["consensus_nt"]
    ann = pd.read_feather(A_FILE, columns=["bodyId", "superclass", "class", "type"]).drop_duplicates("bodyId").set_index("bodyId")
    m1 = np.isin(pre, mbon)
    e1 = pd.DataFrame({"j": pre[m1], "x": post[m1], "w": w[m1]}).groupby(["j", "x"]).w.sum().reset_index()
    m2 = np.isin(post, dan)
    dan_in = float(w[m2].sum())
    e2 = pd.DataFrame({"x": pre[m2], "i": post[m2], "w": w[m2]}).groupby(["x", "i"]).w.sum().reset_index()
    e2["ppl"] = np.isin(e2.i.to_numpy(), dan[d.dan_is_ppl])
    direct = float(e1[e1.x.isin(dan)].w.sum())
    xs = np.intersect1d(e1.x.unique(), e2.x.unique())
    xs = xs[~np.isin(xs, dan)]
    mx = np.isin(post, xs)
    in_tot = pd.Series(w[mx]).groupby(post[mx]).sum()
    a_x = ann.reindex(xs)
    cat = pd.Series(_category(a_x["type"].to_numpy(), a_x["class"].to_numpy(), a_x["superclass"].to_numpy()), index=xs)
    cat = cat.where(~cat.str.startswith("diğer: ") | (cat == "diğer: cb_intrinsic"), "diğer sınıflar")
    nt_x = nt_tab.reindex(xs)
    e1x = e1[e1.x.isin(xs)].copy()
    e1x["coef"] = e1x.w / e1x.x.map(in_tot)
    t_x = e2[e2.x.isin(xs)].groupby(["x", "ppl"]).w.sum().unstack(fill_value=0).reindex(xs, fill_value=0)
    e1x["cat"] = e1x.x.map(cat)
    e1x["att_pam"] = e1x.coef * e1x.x.map(t_x.get(False, pd.Series(0, index=xs)))
    e1x["att_ppl"] = e1x.coef * e1x.x.map(t_x.get(True, pd.Series(0, index=xs)))
    e1x["att"] = e1x.att_pam + e1x.att_ppl
    L = ["## D. İki adımlı MBON→X→DAN (X: DAN dışı aracı nöron)", "",
         f"Toplam DAN girdisi {int(dan_in):,} sinaps. Doğrudan MBON→DAN (48 sağ MBON): {int(direct):,} sinaps = **{direct / dan_in:.4f}** pay.",
         f"MBON'dan girdi alıp DAN'a çıktı veren aracı nöron: {len(xs):,}. 'Atfedilebilir DAN girdisi' = Σ (w_jx / X'in toplam girdisi) · (X→DAN sinapsı) / DAN toplam girdisi:", "",
         "| aracı sınıfı | aracı sayısı | atfedilebilir DAN girdisi payı |", "|---|---|---|"]
    for k, g in e1x.groupby("cat"):
        L.append(f"| {k} | {g.x.nunique():,} | {g.att.sum() / dan_in:.4f} |")
    L += ["", "Karşılaştırma için doğrudan yol payı yukarıdadır. KC aracılığı (MBON→KC→DAN) mantar cismi içi bir döngüdür; cb_intrinsic aracılar dış yapılara açılır.", ""]
    L += ["### İşaretli iki adımlı sınıf matrisi (yalnız cb_intrinsic aracılar; payda DAN toplam girdisi; ×10⁴)", "",
          "Aracı işareti nt tahminiyle (asetilkolin +, GABA −, glutamat ±); dopamin/oktopamin/serotonin/belirsiz aracılar işaretsiz sayılır ve hariç tutulur.", "",
          "| glutamat | yaklaş→PAM | yaklaş→PPL1 | kaçın→PAM | kaçın→PPL1 |", "|---|---|---|---|---|"]
    ci = e1x[e1x.cat == "diğer: cb_intrinsic"].copy()
    ci["cls"] = ci.j.map(cls_j)
    for glu in (-1.0, +1.0):
        sj = pd.Series(_signed(nt_j.to_numpy(), glu), index=mbon)
        nx = nt_x.reindex(ci.x).to_numpy()
        sx = np.where(nx == "acetylcholine", 1.0, np.where(nx == "gaba", -1.0, np.where(nx == "glutamate", glu, 0.0)))
        sgn = ci.j.map(sj).to_numpy() * sx
        cells = []
        for c in ("yaklaş", "kaçın"):
            mm = (ci.cls == c).to_numpy()
            for col in ("att_pam", "att_ppl"):
                cells.append(f"{(sgn[mm] * ci[col].to_numpy()[mm]).sum() / dan_in * 1e4:+.2f}")
        L.append(f"| {'inhibitör (−1)' if glu < 0 else 'eksitatör (+1)'} | " + " | ".join(cells) + " |")
    uns = ci.assign(nx=nt_x.reindex(ci.x).to_numpy())
    uns = uns[~uns.nx.isin(["acetylcholine", "gaba", "glutamate"])].att.sum() / max(ci.att.sum(), 1e-9)
    L += ["", f"İşaretsiz (dopamin/oktopamin/serotonin/belirsiz) aracıların cb_intrinsic yol kütlesindeki payı: {uns:.3f}.",
          "Yorum sınırı: yol payı sinaps sayısı üzerinden yapısal ölçüdür; işlevsel etki (işaret, nonlineerlik, bölme) içermez.", ""]
    return L


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=DEFAULT_DIR)
    ap.add_argument("--null", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    c = Connectome.load(str(mbmodel.resolve_dir(a.data_dir)))
    d = mbmodel.load(a.data_dir)
    n = c.neurons.set_index("bodyId")
    pre, post, w = _load_raw()
    L = ["# DAN girdi ve MBON→DAN geri bildirim analizi (R-8 veri kontrolü)", "",
         "Betimsel veri kontrolü (`python3 -I -m sinek.experiments.dan_girdi_analizi`); karar ölçütü değildir. Kaynak: MaleCNS v1.0 (CC BY 4.0). "
         "Nörotransmitter işaretleri **tahmindir** [doğrulanmadı].", ""]
    L += section_a(pre, post, w, d, n)
    L += section_b_c(c, d, n, a.null, a.seed)
    L += section_d(pre, post, w, d, n)
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
