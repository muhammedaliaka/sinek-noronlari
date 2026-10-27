"""Evre 2: gerçek bağlantıdan (MaleCNS v1.0) çıkarılmış mantar cismi ile çalışan beyin.

Devre (her yarımküre için; ikisi de AYNI sağ-yarımküre bağlantısını kullanır):

    PN (Poisson, glomerül başına) --[gerçek sinaps sayıları]--> KC (LIF)  <==> APL (hız birimi)
    KC --[gerçek sinaps sayıları x plastik çarpan]--> MBON (LIF)
    DAN (hız birimi): bölme dopamini D_m = DAN->MBON sinaps payıyla ağırlıklı PAM/PPL1 etkinliği

Öğrenme: W_km, [0, gerçek başlangıç değeri W0_km] aralığında kalır; bölmenin DAN'ı etkinken baskılanır
  (W <- W exp(-eta dt iz_k D_m)), karşı sınıf DAN etkinken W0'a doğru geri yüklenir (bkz. `_plasticity`).
  PAM etkinliği = max(delta, 0) (ödül hatası), PPL1 etkinliği = max(-delta, 0) (ceza / ödül yokluğu).
Değer: V = (class_balance * yaklaş sınıfı MBON hızı - kaçın sınıfı MBON hızı) / kazanç.

Bağlantıdan gelen: sinaps sayıları (PN->KC, KC->APL, APL->KC, KC->MBON), PN glomerül ataması,
nörotransmitter işareti (PN), bölme eşlemesi (DAN->MBON payı).
Model varsayımları (docs/evre2_*.md'de ayrıntılı): MBON'un yaklaş/kaçın sınıfı DAN sınıfından türetilir;
tüm PAM = ödül, tüm PPL1 = ceza işareti; sinaps sayıları göreli ağırlığa çevrilir; KC->KC, MBON->MBON,
MBON->DAN, DPM yok; DAN'ların duyusal girdisi (tat) bağlantıdan değil modelden gelir.
"""
from __future__ import annotations

import math

import numpy as np
import torch

from .config import ConnectomeBrainConfig
from .connectome import mbmodel
from .connectome.mbmodel import MBData

H = 2  # yarımküre sayısı (sol, sağ)


class ConnectomeBrain:
    def __init__(
        self,
        cfg: ConnectomeBrainConfig,
        batch: int,
        seed: int,
        device: str = "cpu",
        dt_world: float = 0.02,
        substeps: int = 10,
        data: MBData | None = None,
    ):
        self.cfg, self.B, self.R = cfg, batch, batch * H
        self.seed = seed
        self.device = torch.device(device)
        self.dt_world, self.substeps = dt_world, substeps
        self.dt_s = cfg.snn_dt_ms / 1000.0
        self.gen = torch.Generator(device=self.device).manual_seed(seed + 7)
        self.data = d = data if data is not None else mbmodel.load(cfg.data_dir)
        self.n_glom, self.n_pn, self.n_kc, self.n_mbon, self.n_dan = d.n_glom, d.n_pn, d.n_kc, d.n_mbon, d.n_dan

        t = lambda a: torch.as_tensor(a, device=self.device)
        self.pn_glom = t(d.pn_glom)
        self.w_pn_kc = t(d.w_pn_kc) * cfg.j_pn_kc                  # (n_pn, n_kc)
        self.kc_apl = t(d.kc_apl) / d.n_kc                         # APL girdisi = ağırlıklı KC oranı
        self.apl_kc = t(d.apl_kc)                                  # (n_kc,)

        C = d.kc_mbon
        if cfg.kc_mbon_norm == "mbon":
            Cn = C / C.mean(0, keepdims=True)
        elif cfg.kc_mbon_norm == "global":
            Cn = C / C.mean()
        else:
            raise ValueError(f"kc_mbon_norm: {cfg.kc_mbon_norm}")
        self.W0 = t(Cn * cfg.w0).float()                           # (n_kc, n_mbon) gerçek başlangıç ağırlığı
        self.W = self.W0.expand(self.R, -1, -1).clone()            # plastik, yarımküre başına

        self.dan_mbon = t(d.dan_mbon)                              # (n_dan, n_mbon), sütun toplamı 1
        self.dan_is_ppl = t(d.dan_is_ppl)
        u_np = d.mbon_u
        if cfg.class_shuffle_seed >= 0:        # kontrol: sınıf etiketleri MBON'lar arasında karıştırılır
            u_np = u_np[np.random.default_rng(cfg.class_shuffle_seed).permutation(len(u_np))]
        u = t(u_np)
        app, avo = u.clamp(min=0), (-u).clamp(min=0)
        self.cls_w = torch.stack([app / app.sum(), avo / avo.sum()], dim=1)   # (n_mbon, 2)
        self.eta_scale = torch.ones(batch, device=self.device)

        self.a_kc = math.exp(-cfg.snn_dt_ms / cfg.tau_kc_ms)
        self.a_apl = math.exp(-cfg.snn_dt_ms / cfg.apl_tau_ms)
        self.a_mb = math.exp(-cfg.snn_dt_ms / cfg.tau_mb_ms)
        self.a_elig = math.exp(-self.dt_s / cfg.tau_elig)
        self.reset_state()

    # ------------------------------------------------------------------ durum
    def reset_state(self) -> None:
        R, dev = self.R, self.device
        self.v_kc = torch.zeros(R, self.n_kc, device=dev)
        self.apl = torch.zeros(R, device=dev)
        self.v_mb = torch.zeros(R, self.n_mbon, device=dev)
        self.elig = torch.zeros(R, self.n_kc, device=dev)
        self.rate_mb = torch.zeros(R, self.n_mbon, device=dev)   # EMA MBON hızı (Hz)
        self.rate = torch.zeros(R, 2, device=dev)                # sınıf hızları: yaklaş, kaçın
        self.taste = torch.zeros(self.B, 3, device=dev)
        self.valence = torch.zeros(R, device=dev)
        self.last_delta = torch.zeros(R, device=dev)
        self.kc_frac = torch.zeros(R, device=dev)

    # ------------------------------------------------------------------ adım
    @torch.no_grad()
    def step(
        self,
        glom: torch.Tensor,      # (B, 2, n_glom)  [0,1]
        taste: torch.Tensor,     # (B,)  +tatlı / -acı
        touch: torch.Tensor,     # (B,)  0/1
        learn: bool = True,
    ) -> torch.Tensor:
        """Bir dünya adımı kadar ağı çalıştırır, (B, 2) değer (valence) döndürür."""
        c, R, dt_s, dev = self.cfg, self.R, self.dt_s, self.device
        n_sub = self.substeps
        pn_p = (c.pn_base_rate + c.pn_max_rate * glom.reshape(R, self.n_glom)[:, self.pn_glom]) * dt_s
        grn_p = torch.stack(
            [taste.clamp(min=0), (-taste).clamp(min=0), touch], dim=-1
        ) * c.grn_max_rate * dt_s                                              # (B, 3)
        rand = lambda *s: torch.rand(*s, generator=self.gen, device=dev)

        spikes = torch.empty(R, n_sub, self.n_kc, device=dev)
        kc_spikes = torch.zeros(R, device=dev)
        cnt_grn = torch.zeros(self.B, 3, device=dev)
        for k in range(n_sub):
            pn = (rand(R, self.n_pn) < pn_p).float()
            self.v_kc = (self.v_kc * self.a_kc + pn @ self.w_pn_kc
                         - c.apl_gain * self.apl.unsqueeze(1) * self.apl_kc)
            spk = self.v_kc >= c.kc_thresh
            self.v_kc = torch.where(spk, torch.zeros_like(self.v_kc), self.v_kc).clamp_(min=-1.0)
            s = spk.float()
            spikes[:, k] = s
            kc_spikes += s.mean(1)
            self.apl = self.apl * self.a_apl + s @ self.kc_apl
            self.elig = self.elig * self.a_elig + s * ((1 - self.a_elig) / (dt_s * c.elig_ref_rate))
            cnt_grn += (rand(self.B, 3, c.n_grn) < grn_p.unsqueeze(-1)).float().sum(-1)

        # KC dinamiği W'ye bağlı değildir: tüm alt adımların MBON sürüşü tek matris çarpımıyla
        drive = torch.bmm(spikes, self.W)                                      # (R, n_sub, n_mbon)
        cnt_mb = torch.zeros(R, self.n_mbon, device=dev)
        for k in range(n_sub):
            self.v_mb = (self.v_mb * self.a_mb + (1 - self.a_mb) * c.mb_bias + c.j_kc_mb * drive[:, k]
                         + 0.08 * torch.randn(R, self.n_mbon, generator=self.gen, device=dev))
            fire = self.v_mb >= 1.0
            self.v_mb = torch.where(fire, torch.zeros_like(self.v_mb), self.v_mb)
            cnt_mb += fire.float()

        win = n_sub * dt_s
        a_v = min(1.0, self.dt_world / c.tau_valence)
        a_t = min(1.0, self.dt_world / c.tau_taste)
        self.rate_mb += a_v * (cnt_mb / win - self.rate_mb)
        self.rate = self.rate_mb @ self.cls_w
        self.taste += a_t * (cnt_grn / (c.n_grn * win) - self.taste)
        self.kc_frac = kc_spikes / n_sub

        self.valence = (c.class_balance * self.rate[:, 0] - self.rate[:, 1]) / c.valence_gain
        reward = ((self.taste[:, 0] - self.taste[:, 1]) / c.grn_max_rate).repeat_interleave(H)
        gate = (self.taste[:, 2] / c.grn_max_rate).repeat_interleave(H)
        self.last_delta = gate * (c.reward_target * reward - self.valence)

        if learn:
            self._plasticity()
        return self.valence.view(self.B, H)

    def _plasticity(self) -> None:
        """Bölmeye özgü iki yönlü kural (W, 0 ile gerçek başlangıç değeri W0 arasında kalır).

        PAM etkinliği = max(delta, 0), PPL1 etkinliği = max(-delta, 0). Bir MBON'un aldığı DAN payı
        (dan_mbon) bölmesini belirler:
          baskılanma  D_m = kendi bölmesinin DAN'ı etkinken      (PAM bölmesinde ödül, PPL1 bölmesinde ceza/ödül yokluğu)
          geri yükleme R_m = karşı sınıf DAN etkinken            (PAM bölmesinde ceza/yokluk, PPL1 bölmesinde ödül)
        Böylece delta > 0 kaçın sınıfını baskılayıp yaklaş sınıfını eski haline getirir ve tersi (Rescorla-Wagner'in
        sınırlı, iki yönlü karşılığı); tek yönlü sürüklenme ile bellek kapasitesi tükenmez.
        """
        c = self.cfg
        eta = (c.eta * self.eta_scale).repeat_interleave(H)                    # (R,)
        pos, neg = self.last_delta.clamp(min=0), (-self.last_delta).clamp(min=0)
        own = torch.where(self.dan_is_ppl, neg.unsqueeze(1), pos.unsqueeze(1))  # (R, n_dan)
        D = own @ self.dan_mbon                                                # (R, n_mbon) baskılanma
        R_ = (torch.where(self.dan_is_ppl, pos.unsqueeze(1), neg.unsqueeze(1)) @ self.dan_mbon) if c.restore else None
        active = (D.sum(1) > 0) if R_ is None else ((D.sum(1) + R_.sum(1)) > 0)
        rows = ((eta > 0) & active).nonzero().squeeze(1)
        if rows.numel():
            k = (eta[rows] * self.dt_world).view(-1, 1, 1) * self.elig[rows].unsqueeze(2)    # (r, n_kc, 1)
            W = self.W[rows] * torch.exp(-k * D[rows].unsqueeze(1))
            if R_ is not None:
                W = W + (self.W0 - W) * (1 - torch.exp(-k * R_[rows].unsqueeze(1)))
            self.W[rows] = W
        if c.recovery_rate > 0:
            r = (c.recovery_rate * self.dt_world * (self.eta_scale > 0).float()).repeat_interleave(H)
            self.W += r.view(-1, 1, 1) * (self.W0 - self.W)

    # --------------------------------------------------------- kayıt / çoğaltma
    def state_dict(self) -> dict:
        d = self.data.ids
        return {
            "W": self.W.view(self.B, H, self.n_kc, self.n_mbon).cpu().clone(),
            "kc_ids": torch.from_numpy(d["KC"].copy()), "mbon_ids": torch.from_numpy(d["MBON"].copy()),
            "seed": self.seed,
        }

    def load_state_dict(self, state: dict) -> None:
        d = self.data.ids
        for key, ids in (("kc_ids", d["KC"]), ("mbon_ids", d["MBON"])):
            if not torch.equal(torch.as_tensor(state[key]), torch.from_numpy(ids.copy())):
                raise ValueError(f"Checkpoint {key} bu bağlantı verisiyle uyuşmuyor")
        W = state["W"]
        if W.shape[0] != self.B:
            raise ValueError(f"Checkpoint batch={W.shape[0]}, beyin batch={self.B}")
        self.W = W.reshape(self.R, self.n_kc, self.n_mbon).to(self.device).clone()

    def select(self, idx) -> "ConnectomeBrain":
        """Seçilen canlıların (aynı bağlantı, aynı ağırlıklar) bağımsız kopyası."""
        idx = torch.as_tensor(idx, dtype=torch.long).to(self.device)
        out = ConnectomeBrain(self.cfg, len(idx), self.seed, str(self.device), self.dt_world,
                              self.substeps, data=self.data)
        W = self.W.view(self.B, H, self.n_kc, self.n_mbon)[idx]
        out.W = W.reshape(out.R, self.n_kc, self.n_mbon).clone()
        out.eta_scale = self.eta_scale[idx].clone()
        return out

    def expand(self, m: int) -> "ConnectomeBrain":
        return self.select(torch.arange(self.B).repeat_interleave(m))

    def n_neurons(self) -> int:
        return H * (self.n_pn + self.n_kc + 1 + self.n_mbon + self.n_dan) + 3 * self.cfg.n_grn
