"""Mantar cismi (mushroom body) esinli spiking beyin.

Devre (her yarımküre için, sol ve sağ anten ayrı işlenir):

    ORN/PN (Poisson) -> KC (seyrek LIF, APL geri baskılaması) -> MBON-yaklaş / MBON-kaçın
                                       ^ plastik KC->MBON ağırlıkları
    Tat/temas nöronları (Poisson) -> DAN (hız birimi) -> dopamin sinyali

Öğrenme kuralı (üç etkenli): KC uygunluk izi x dopamin x MBON türü işareti.
Dopamin, ödül ile MBON'ların kendi değer tahmini arasındaki farktır
(delta = temas * (ödül - V)); tahmin ödüle yaklaşınca öğrenme durur, ödül
kalkınca tahmin söner (silinme / ödül tersine çevirme).

Basitleştirmeler (kasıtlı, Evre 1):
- MBON'lar tür başına ortak bir KC->MBON ağırlık vektörünü paylaşır; nöronlar
  bağımsız membran gürültüsü ve farklı tonik sürüş ile ayrışır.
- DAN ve APL spiking değildir (hız/gradyan birimi; APL zaten gerçekte spike atmaz).
- Sol ve sağ yarımküre aynı KC kablolamasını kullanır, ağırlıkları ayrı öğrenir.
"""
from __future__ import annotations

import math

import torch

from .config import BrainConfig

H = 2  # yarımküre sayısı (sol, sağ)


class MushroomBodyBrain:
    def __init__(
        self,
        cfg: BrainConfig,
        batch: int,
        seed: int,
        device: str = "cpu",
        dt_world: float = 0.02,
        substeps: int = 10,
    ):
        self.cfg, self.B, self.R = cfg, batch, batch * H
        self.seed = seed
        self.device = torch.device(device)
        self.dt_world, self.substeps = dt_world, substeps
        self.dt_s = cfg.snn_dt_ms / 1000.0
        self.gen = torch.Generator(device=self.device).manual_seed(seed + 7)
        self.n_pn = cfg.n_glom * cfg.pn_per_glom

        # --- sabit kablolama: CPU'da üretilir, cihazdan bağımsız tekrar üretilebilir
        wg = torch.Generator().manual_seed(seed + 13)
        scores = torch.rand(cfg.n_kc, self.n_pn, generator=wg)
        self.kc_inputs = scores.topk(cfg.kc_in, dim=1).indices            # (n_kc, kc_in)
        w_pk = torch.zeros(self.n_pn, cfg.n_kc)
        w_pk.scatter_(0, self.kc_inputs.t(), cfg.j_pn_kc)
        self.w_pn_kc = w_pk.to(self.device)
        # yaklaş/kaçın aynı tonik sürüş dağılımını paylaşır (başlangıçta sistematik tercih yok)
        bias = cfg.mb_bias * (1.0 + 0.1 * torch.randn(1, cfg.n_mbon, generator=wg))
        self.mb_bias = bias.expand(2, -1).contiguous().to(self.device)     # (2, n_mbon)

        # --- plastik KC->MBON (tür başına): [:, :, 0] yaklaş, [:, :, 1] kaçın
        jit = cfg.w_jitter * torch.randn(self.R, cfg.n_kc, 2, generator=wg)
        self.W = (cfg.w0 + jit).clamp(0.0, cfg.w_max).to(self.device)
        self.eta_scale = torch.ones(batch, device=self.device)             # eleman başına

        self.a_kc = math.exp(-cfg.snn_dt_ms / cfg.tau_kc_ms)
        self.a_apl = math.exp(-cfg.snn_dt_ms / cfg.apl_tau_ms)
        self.a_mb = math.exp(-cfg.snn_dt_ms / cfg.tau_mb_ms)
        self.a_elig = math.exp(-self.dt_s / cfg.tau_elig)
        self.reset_state()

    # ------------------------------------------------------------------ durum
    def reset_state(self) -> None:
        c, R, dev = self.cfg, self.R, self.device
        self.v_kc = torch.zeros(R, c.n_kc, device=dev)
        self.apl = torch.zeros(R, device=dev)
        self.v_mb = torch.zeros(R, 2, c.n_mbon, device=dev)
        self.elig = torch.zeros(R, c.n_kc, device=dev)
        self.rate = torch.zeros(R, 2, device=dev)           # EMA MBON hızı (Hz): yaklaş, kaçın
        self.taste = torch.zeros(self.B, 3, device=dev)      # EMA GRN hızı: tatlı, acı, temas
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
        c, R, dt_s = self.cfg, self.R, self.dt_s
        pn_p = (c.pn_base_rate + c.pn_max_rate * glom.reshape(R, c.n_glom)
                .repeat_interleave(c.pn_per_glom, dim=1)) * dt_s              # (R, n_pn)
        grn_p = torch.stack(
            [taste.clamp(min=0), (-taste).clamp(min=0), touch], dim=-1
        ) * c.grn_max_rate * dt_s                                              # (B, 3)

        cnt_mb = torch.zeros(R, 2, device=self.device)
        cnt_grn = torch.zeros(self.B, 3, device=self.device)
        kc_spikes = torch.zeros(R, device=self.device)
        rand = lambda *s: torch.rand(*s, generator=self.gen, device=self.device)

        for _ in range(self.substeps):
            pn = (rand(R, self.n_pn) < pn_p).float()
            self.v_kc = self.v_kc * self.a_kc + pn @ self.w_pn_kc - c.apl_gain * self.apl.unsqueeze(1)
            spk = self.v_kc >= c.kc_thresh
            self.v_kc = torch.where(spk, torch.zeros_like(self.v_kc), self.v_kc).clamp_(min=-1.0)
            s = spk.float()
            frac = s.mean(1)
            self.apl = self.apl * self.a_apl + frac
            kc_spikes += frac
            self.elig = self.elig * self.a_elig + s * ((1 - self.a_elig) / (dt_s * c.elig_ref_rate))

            drive = torch.bmm(s.unsqueeze(1), self.W).squeeze(1)               # (R, 2)
            self.v_mb = (
                self.v_mb * self.a_mb
                + (1 - self.a_mb) * self.mb_bias
                + c.j_kc_mb * drive.unsqueeze(-1)
                + 0.08 * torch.randn(R, 2, c.n_mbon, generator=self.gen, device=self.device)
            )
            fire = self.v_mb >= 1.0
            self.v_mb = torch.where(fire, torch.zeros_like(self.v_mb), self.v_mb)
            cnt_mb += fire.float().sum(-1)
            cnt_grn += (rand(self.B, 3, c.n_grn) < grn_p.unsqueeze(-1)).float().sum(-1)

        win = self.substeps * dt_s
        a_v = min(1.0, self.dt_world / c.tau_valence)
        a_t = min(1.0, self.dt_world / c.tau_taste)
        self.rate += a_v * (cnt_mb / (c.n_mbon * win) - self.rate)
        self.taste += a_t * (cnt_grn / (c.n_grn * win) - self.taste)
        self.kc_frac = kc_spikes / self.substeps

        self.valence = (self.rate[:, 0] - self.rate[:, 1]) / c.valence_gain   # (R,)
        reward = ((self.taste[:, 0] - self.taste[:, 1]) / c.grn_max_rate).repeat_interleave(H)
        gate = (self.taste[:, 2] / c.grn_max_rate).repeat_interleave(H)
        self.last_delta = gate * (c.reward_target * reward - self.valence)

        if learn:
            eta = (c.eta * self.eta_scale).repeat_interleave(H)               # (R,)
            dw = (eta * self.dt_world * self.last_delta).unsqueeze(1) * self.elig  # (R, n_kc)
            self.W[:, :, 0] += dw
            self.W[:, :, 1] -= dw
            self.W.clamp_(0.0, c.w_max)
        return self.valence.view(self.B, H)

    # --------------------------------------------------------- kayıt / çoğaltma
    def state_dict(self) -> dict:
        return {
            "W": self.W.view(self.B, H, self.cfg.n_kc, 2).cpu().clone(),
            "kc_inputs": self.kc_inputs.clone(),
            "seed": self.seed,
        }

    def load_state_dict(self, state: dict) -> None:
        if not torch.equal(state["kc_inputs"], self.kc_inputs):
            raise ValueError("Checkpoint kablolaması bu beyinle uyuşmuyor (seed/ayar farklı)")
        W = state["W"]
        if W.shape[0] != self.B:
            raise ValueError(f"Checkpoint batch={W.shape[0]}, beyin batch={self.B}")
        self.W = W.reshape(self.R, self.cfg.n_kc, 2).to(self.device).clone()

    def select(self, idx) -> "MushroomBodyBrain":
        """Seçilen canlıların (aynı kablolama, aynı ağırlıklar) bağımsız kopyası."""
        idx = torch.as_tensor(idx, dtype=torch.long)
        out = MushroomBodyBrain(
            self.cfg, len(idx), self.seed, str(self.device), self.dt_world, self.substeps
        )
        W = self.W.view(self.B, H, self.cfg.n_kc, 2)[idx.to(self.device)]
        out.W = W.reshape(out.R, self.cfg.n_kc, 2).clone()
        out.eta_scale = self.eta_scale[idx.to(self.device)].clone()
        return out

    def expand(self, m: int) -> "MushroomBodyBrain":
        """Her canlıyı m kez kopyala (aynı ağırlıklar); test denemelerini paralel koşmak için."""
        return self.select(torch.arange(self.B).repeat_interleave(m))

    def n_neurons(self) -> int:
        c = self.cfg
        per_hemi = self.n_pn + c.n_kc + 2 * c.n_mbon
        return H * per_hemi + 3 * c.n_grn
