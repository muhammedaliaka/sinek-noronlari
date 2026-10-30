"""Çıkarılmış mantar cismi alt ağından simülasyon dizileri (yoğun matrisler) üretir.

Veriden gelenler: PN->glomerül ataması, PN->KC / KC->APL / APL->KC / KC->MBON sinaps sayıları,
DAN->MBON sinaps sayıları (bölme eşlemesi), nörotransmitter tahminleri (işaret).

Model varsayımları (veri değildir):
  - MBON değer sınıfı: MBON'un aldığı DAN sinapslarındaki PPL1 payı - PAM payı  (u_m in [-1, 1]).
    u>0  => "yaklaş" MBON'u (cezalandırıcı PPL1 dopamini baskılar),
    u<0  => "kaçın" MBON'u (ödüllendirici PAM dopamini baskılar).
    Bu, Aso & Rubin (2016) çerçevesine dayanan bir varsayımdır; bağlantıdan doğrudan okunmaz.
  - Her sinaps sayısı, tek bir ortalama değere bölünerek göreli ağırlığa çevrilir;
    mutlak sinaps gücü (mV) bilinmediği için tek bir genel ölçek ayarlanır.
  - Kapsam dışı: KC->KC, MBON->MBON, MBON->DAN, DAN->KC (bölme eşlemesi DAN->MBON'dan çıkarılır), DPM.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .graph import Connectome

DEFAULT_DIR = "data/processed/malecns_v1.0_R"


def resolve_dir(data_dir: str | Path) -> Path:
    """Göreli yolu önce çalışma dizininde, sonra depo kökünde (src düzeni) arar."""
    p = Path(data_dir)
    if p.is_absolute() and p.exists():
        return p
    for base in (Path.cwd(), Path(__file__).resolve().parents[3]):
        if (base / p / "neurons.feather").exists():
            return base / p
    raise FileNotFoundError(
        f"{data_dir} bulunamadı. Depodaki hazır çıktı data/processed/ altındadır; "
        "ham veriden üretmek için: python -m sinek.connectome.fetch && python -m sinek.connectome.malecns"
    )


@dataclass
class MBData:
    ids: dict                  # {"PN","KC","MBON","DAN"} -> bodyId dizileri (sıra = matris sırası)
    glom_names: list           # glomerül adları (dünyadaki kanal sırası)
    pn_glom: np.ndarray        # (n_pn,) int  PN -> glomerül kanalı
    w_pn_kc: np.ndarray        # (n_pn, n_kc) işaretli, ortalama |bağlantı| = 1
    kc_apl: np.ndarray         # (n_kc,) ortalama = 1
    apl_kc: np.ndarray         # (n_kc,) ortalama = 1
    kc_mbon: np.ndarray        # (n_kc, n_mbon) ham sinaps sayısı
    dan_mbon: np.ndarray       # (n_dan, n_mbon) sütunlar toplamı 1 (DAN payı)
    dan_is_ppl: np.ndarray     # (n_dan,) bool
    mbon_u: np.ndarray         # (n_mbon,) PPL1 payı - PAM payı
    mbon_types: list
    summary: dict
    pn_kc_scale: float = 1.0                       # PN->KC ham |sinaps| ortalaması (VPN->KC aynı ölçeğe bölünür)
    vpn_ids: np.ndarray | None = None              # (n_vpn,) görsel projeksiyon nöronları (vpn_kc.feather yoksa None)
    vpn_types: list | None = None
    w_vpn_kc: np.ndarray | None = None             # (n_vpn, n_kc) işaretli, PN ile aynı ölçek

    @property
    def n_pn(self) -> int: return self.w_pn_kc.shape[0]
    @property
    def n_kc(self) -> int: return self.w_pn_kc.shape[1]
    @property
    def n_mbon(self) -> int: return self.kc_mbon.shape[1]
    @property
    def n_dan(self) -> int: return self.dan_mbon.shape[0]
    @property
    def n_glom(self) -> int: return len(self.glom_names)


def _nt_sign(nt) -> np.ndarray:
    return np.where(np.asarray(nt) == "gaba", -1.0, 1.0).astype(np.float32)


def from_connectome(c: Connectome) -> MBData:
    n = c.neurons.set_index("bodyId")
    ids = {p: c.ids(p) for p in ("PN", "KC", "MBON", "DAN")}

    # PN -> glomerül kanalı
    groups = n.loc[ids["PN"], "group"].astype(str).to_numpy()
    glom_names = sorted(set(groups))
    pn_glom = np.array([glom_names.index(g) for g in groups], dtype=np.int64)

    # PN -> KC (işaret: nörotransmitter), ortalama |bağlantı| = 1
    w = c.block("PN", "KC", ids["PN"], ids["KC"])
    w = w * _nt_sign(n.loc[ids["PN"], "nt"])[:, None]
    nz = np.abs(w[w != 0])
    pn_kc_scale = float(nz.mean())
    w_pn_kc = (w / pn_kc_scale).astype(np.float32)

    # KC <-> APL (tek APL); ortalama 1
    apl = c.ids("APL")
    if len(apl) != 1:
        raise ValueError(f"APL sayısı 1 olmalı, {len(apl)} bulundu")
    kc_apl = c.block("KC", "APL", ids["KC"], apl)[:, 0]
    apl_kc = c.block("APL", "KC", apl, ids["KC"])[0]
    kc_apl = (kc_apl / kc_apl.mean()).astype(np.float32)
    apl_kc = (apl_kc / apl_kc.mean()).astype(np.float32)

    # KC -> MBON
    kc_mbon = c.block("KC", "MBON", ids["KC"], ids["MBON"]).astype(np.float32)

    # DAN -> MBON bölme eşlemesi
    dm = c.block("DAN", "MBON", ids["DAN"], ids["MBON"])
    tot = dm.sum(0)
    if (tot <= 0).any():
        raise ValueError("DAN girdisi olmayan MBON var; bölme eşlemesi türetilemez")
    dan_mbon = (dm / tot).astype(np.float32)
    dan_type = n.loc[ids["DAN"], "type"].astype(str).to_numpy()
    dan_is_ppl = np.array([t.startswith("PPL1") for t in dan_type])
    ppl_frac = dan_mbon[dan_is_ppl].sum(0)
    mbon_u = (2.0 * ppl_frac - 1.0).astype(np.float32)          # = ppl - pam

    summary = {
        "n_pn": len(ids["PN"]), "n_kc": len(ids["KC"]), "n_mbon": len(ids["MBON"]), "n_dan": len(ids["DAN"]),
        "n_glom": len(glom_names),
        "kc_without_pn": int(((np.abs(w_pn_kc) > 0).sum(0) == 0).sum()),
        "mbon_approach": int((mbon_u > 0).sum()), "mbon_avoid": int((mbon_u < 0).sum()),
        "mbon_mixed(|u|<0.5)": int((np.abs(mbon_u) < 0.5).sum()),
    }
    return MBData(
        ids=ids, glom_names=glom_names, pn_glom=pn_glom, w_pn_kc=w_pn_kc, kc_apl=kc_apl, apl_kc=apl_kc,
        kc_mbon=kc_mbon, dan_mbon=dan_mbon, dan_is_ppl=dan_is_ppl, mbon_u=mbon_u,
        mbon_types=n.loc[ids["MBON"], "type"].astype(str).tolist(), summary=summary, pn_kc_scale=pn_kc_scale,
    )


def _attach_vpn(d: MBData, directory: Path) -> MBData:
    """O6 görsel ön ucu: `python -m sinek.connectome.vpn` çıktısı varsa VPN->KC sinapslarını ekler (yoksa alanlar None kalır; koku yolu etkilenmez)."""
    pn, pe = directory / "vpn_neurons.feather", directory / "vpn_kc.feather"
    if not (pn.exists() and pe.exists()):
        return d
    import pandas as pd

    vn, ve = pd.read_feather(pn), pd.read_feather(pe)
    vi = {b: i for i, b in enumerate(vn["bodyId"].to_numpy())}
    ki = {b: i for i, b in enumerate(d.ids["KC"].tolist())}
    w = np.zeros((len(vn), d.n_kc), np.float32)
    for pre, post, wt in zip(ve["body_pre"].to_numpy(), ve["body_post"].to_numpy(), ve["weight"].to_numpy()):
        w[vi[pre], ki[post]] = wt
    w = w * _nt_sign(vn["nt"])[:, None] / np.float32(d.pn_kc_scale)
    d.vpn_ids, d.vpn_types, d.w_vpn_kc = vn["bodyId"].to_numpy(), vn["type"].astype(str).tolist(), w
    return d


_CACHE: dict = {}


def load(data_dir: str | Path = DEFAULT_DIR) -> MBData:
    key = str(resolve_dir(data_dir))
    if key not in _CACHE:
        _CACHE[key] = _attach_vpn(from_connectome(Connectome.load(key)), Path(key))
    return _CACHE[key]


def connectome_config(data_dir: str | Path = DEFAULT_DIR, glom_per_odor: int = 8, odor_overlap: int = 2,
                      odor_sigma: float = 6.0, odor_gain: float = 2.0, turn_gain: float = 40.0, **world_over):
    """Evre 2 için `Config`: dünya kanal sayısı = verideki glomerül sayısı.

    Evre 1'den farkları (geliştirme tohumlarında seçildi, docs/evre2_plan.md): daha dar koku bulutu ve daha
    düşük doygunluk (iki koku arenada birbirine karışıp ayırt edilemez olmasın), daha yüksek dönüş kazancı
    (değer ölçeği farklı), valence_gain=10.
    """
    from ..config import Config, ConnectomeBrainConfig, MotorConfig, WorldConfig

    d = load(data_dir)
    world = WorldConfig(n_glom=d.n_glom, glom_per_odor=glom_per_odor, odor_overlap=odor_overlap,
                        odor_sigma=odor_sigma, odor_gain=odor_gain, **world_over)
    return Config(world=world, cbrain=ConnectomeBrainConfig(data_dir=str(data_dir)),
                  motor=MotorConfig(turn_gain=turn_gain), brain_kind="connectome")
