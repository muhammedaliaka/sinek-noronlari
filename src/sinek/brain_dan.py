"""Evre 3.3: DAN devresi varyantları (docs/evre3_dan_plani.md, K-026).

`DanBrain`, `ConnectomeBrain`'in alt sınıfıdır; KC/MBON dinamiği ve değer okuması aynıdır, yalnız plastisiteyi süren DAN etkinliği değişir.
Varyantlar (her biri bir öncekine bir bileşen ekler):
  V0  elle yazılmış δ (mevcut): PAM = max(δ,0), PPL1 = max(−δ,0), sınıf içinde tekdüze.
  V1  V0 · (1 + g_kc · a_i): a_i = KC→DAN bağlantı ağırlıklı KC etkinliği (eligibility izi) — öğretmen sinyalinin KC desenine özgü yükseltilmesi
      (Cervantes-Sandoval 2017: KC→DAN uyarıcı geri besleme öğrenmeyi güçlendirir; model burada çarpımsal bir soyutlamadır).
  V2  V1 + g_mbon · (MBON→DAN işaretli bağlantı · r_eff): r_eff = MBON hızı, MBON→MBON yanal etkiyle (g_lat) düzeltilmiş.
      MBON→MBON yanal etki yalnız DAN'a giden okumada uygulanır (KC→MBON dinamiğine geri beslenmez; basitleştirme).
  V3  V2, ancak elle δ'daki '− valence' (öngörü) terimi yok: yalnız dışsal ödül/ceza (tat) sürer.
Bağlantı ağırlıkları MaleCNS verisinden gelir; nörotransmitter işareti tahmindir (glutamat işareti `glu_sign` ile iki varsayım) [doğrulanmadı].
Kontrol: `wiring="shuffled"` yeni bağlantıların hedeflerini derece koruyarak karıştırır; tüm kazançlar 0 ise sonuç `ConnectomeBrain` ile birebir aynıdır.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .brain_connectome import H, ConnectomeBrain
from .config import ConnectomeBrainConfig
from .connectome import mbmodel
from .connectome.graph import Connectome


@dataclass(frozen=True)
class DanConfig:
    mode: str = "V0"             # V0 | V1 | V2 | V3
    g_kc: float = 0.0            # V1+: KC→DAN çarpımsal yükseltme kazancı
    g_mbon: float = 0.0          # V2+: MBON→DAN toplamsal geri besleme kazancı
    g_lat: float = 0.0           # V2+: MBON→MBON yanal etki kazancı (DAN okumasında)
    glu_sign: float = -1.0       # glutamaterjik MBON işareti varsayımı (−1 inhibitör, +1 eksitatör)
    wiring: str = "data"         # "data" | "shuffled" (derece-koruyan rastgele kontrol)
    wiring_seed: int = 0

    def __post_init__(self) -> None:
        if self.mode not in ("V0", "V1", "V2", "V3"):
            raise ValueError(f"bilinmeyen mod: {self.mode}")
        if self.wiring not in ("data", "shuffled"):
            raise ValueError(f"bilinmeyen wiring: {self.wiring}")


def degree_preserving(w: np.ndarray, rng: np.random.Generator, factor: int = 10) -> np.ndarray:
    """İkili çizge kenar değiş-tokuşu (a→b, c→d  ⇒  a→d, c→b): satır ve sütun dereceleri korunur, ağırlık kenarla birlikte taşınır."""
    rows, cols = np.nonzero(w)
    vals = w[rows, cols].copy()
    cols = cols.copy()
    exist = set(zip(rows.tolist(), cols.tolist()))
    n = len(rows)
    for _ in range(factor * n):
        i, j = rng.integers(n), rng.integers(n)
        a, b, c, d = rows[i], cols[i], rows[j], cols[j]
        if a == c or b == d or (a, d) in exist or (c, b) in exist:
            continue
        exist.remove((a, b)); exist.remove((c, d)); exist.add((a, d)); exist.add((c, b))
        cols[i], cols[j] = d, b
    out = np.zeros_like(w)
    out[rows, cols] = vals
    return out


_WIRING_CACHE: dict = {}


def build_wiring(data_dir: str, dcfg: DanConfig) -> dict:
    """KC→DAN (Kn), MBON→DAN (M), MBON→MBON (L) matrisleri. Kn: sütun toplamı 1; M ve L: işaretli, ortalama |sıfırdan farklı| = 1."""
    key = (str(mbmodel.resolve_dir(data_dir)), dcfg.glu_sign, dcfg.wiring, dcfg.wiring_seed)
    if key in _WIRING_CACHE:
        return _WIRING_CACHE[key]
    c = Connectome.load(key[0])
    d = mbmodel.load(data_dir)
    n = c.neurons.set_index("bodyId")
    ids = d.ids
    nt = n.loc[ids["MBON"], "nt"].to_numpy()
    sgn = np.where(nt == "gaba", -1.0, np.where(nt == "glutamate", dcfg.glu_sign, 1.0))
    kc_dan = c.block("KC", "DAN", ids["KC"], ids["DAN"]).astype(np.float64)
    m = c.block("MBON", "DAN", ids["MBON"], ids["DAN"]).astype(np.float64)
    lat = c.block("MBON", "MBON", ids["MBON"], ids["MBON"]).astype(np.float64)
    np.fill_diagonal(lat, 0.0)
    if dcfg.wiring == "shuffled":
        rng = np.random.default_rng(dcfg.wiring_seed)
        kc_dan, m, lat = (degree_preserving(x, rng) for x in (kc_dan, m, lat))
    tot = kc_dan.sum(0, keepdims=True)
    kn = np.divide(kc_dan, tot, out=np.zeros_like(kc_dan), where=tot > 0)
    M = (m * sgn[:, None])
    M = M / np.abs(M[M != 0]).mean()
    L = (lat * sgn[:, None])
    L = L / np.abs(L[L != 0]).mean()
    out = {"kn": kn.astype(np.float32), "M": M.astype(np.float32), "L": L.astype(np.float32)}
    _WIRING_CACHE[key] = out
    return out


class DanBrain(ConnectomeBrain):
    def __init__(self, cfg: ConnectomeBrainConfig, batch: int, seed: int, device: str = "cpu", dt_world: float = 0.02,
                 substeps: int = 10, data=None, dcfg: DanConfig | None = None):
        super().__init__(cfg, batch, seed, device, dt_world, substeps, data)
        self.dcfg = dcfg if dcfg is not None else DanConfig()
        w = build_wiring(cfg.data_dir, self.dcfg)
        t = lambda a: torch.as_tensor(a, device=self.device)
        self.kn, self.M, self.L = t(w["kn"]), t(w["M"]), t(w["L"])
        self._own = torch.zeros(self.R, self.n_dan, device=self.device)
        self._opp = torch.zeros(self.R, self.n_dan, device=self.device)
        self.dan_max = 0.0     # kararlılık izleme: görülen en büyük DAN etkinliği

    @torch.no_grad()
    def step(self, glom, taste, touch, learn: bool = True) -> torch.Tensor:
        v = super().step(glom, taste, touch, learn=False)
        self._dan_drive()
        if learn:
            self._plasticity()
        return v

    def _dan_drive(self) -> None:
        c, d = self.cfg, self.dcfg
        if d.mode == "V3":     # dışsal sürüş: yalnız ödül/ceza (öngörü terimi yok)
            reward = ((self.taste[:, 0] - self.taste[:, 1]) / c.grn_max_rate).repeat_interleave(H)
            gate = (self.taste[:, 2] / c.grn_max_rate).repeat_interleave(H)
            e = gate * c.reward_target * reward
            pos, neg = e.clamp(min=0), (-e).clamp(min=0)
        else:
            pos, neg = self.last_delta.clamp(min=0), (-self.last_delta).clamp(min=0)
        own = torch.where(self.dan_is_ppl, neg.unsqueeze(1), pos.unsqueeze(1))          # (R, n_dan)
        if d.mode in ("V1", "V2", "V3") and d.g_kc != 0.0:
            own = own * (1.0 + d.g_kc * (self.elig @ self.kn))
        if d.mode in ("V2", "V3") and d.g_mbon != 0.0:
            r = self.rate_mb / c.valence_gain
            if d.g_lat != 0.0:
                r = (r + d.g_lat * (r @ self.L)).clamp(min=0)
            own = (own + d.g_mbon * (r @ self.M)).clamp(min=0)
        self._own = own
        self._opp = torch.where(self.dan_is_ppl, pos.unsqueeze(1), neg.unsqueeze(1))
        self.dan_max = max(self.dan_max, float(own.max()))

    def _plasticity(self) -> None:
        """`ConnectomeBrain._plasticity` ile aynı kural; tek fark: baskılanma `own` (DAN başına), geri yükleme `opp` ile sürülür."""
        c = self.cfg
        eta = (c.eta * self.eta_scale).repeat_interleave(H)
        D = self._own @ self.dan_mbon
        R_ = (self._opp @ self.dan_mbon) if c.restore else None
        active = (D.sum(1) > 0) if R_ is None else ((D.sum(1) + R_.sum(1)) > 0)
        rows = ((eta > 0) & active).nonzero().squeeze(1)
        if rows.numel():
            k = (eta[rows] * self.dt_world).view(-1, 1, 1) * self.elig[rows].unsqueeze(2)
            W = self.W[rows] * torch.exp(-k * D[rows].unsqueeze(1))
            if R_ is not None:
                W = W + (self.W0 - W) * (1 - torch.exp(-k * R_[rows].unsqueeze(1)))
            self.W[rows] = W
        if c.recovery_rate > 0:
            r = (c.recovery_rate * self.dt_world * (self.eta_scale > 0).float()).repeat_interleave(H)
            self.W += r.view(-1, 1, 1) * (self.W0 - self.W)

    def select(self, idx) -> "DanBrain":
        base = super().select(idx)
        out = DanBrain(self.cfg, base.B, self.seed, str(self.device), self.dt_world, self.substeps, data=self.data, dcfg=self.dcfg)
        out.W, out.eta_scale = base.W, base.eta_scale
        return out
