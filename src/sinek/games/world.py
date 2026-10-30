"""Oyun dünyası: sonlu destekli koku alanları, temas sırası sözleşmesi, ortak rastgele sayı (CRN) için ayrı RNG akışları.

`World` (Evre 1/2) alt sınıfıdır: anten geometrisi, duvar, hareket ve `taste_touch()` aynen kullanılır; `sense()` ve temas yeniden
yazılmıştır. Beyin API'si değişmez: `brain.step(glom, taste, touch, learn)`.

Bilgi sınırı: beyne yalnız `sense()` (anten glomerül aktivasyonu), `taste_touch()` gider. Konum, hedef, yerleşim, zaman beyne verilmez.
Nedensel sıra (Creature.step): sense → beyin → hareket → temas; temasın etkisi (tat, dokunma, temasa-bağlı koku) bir sonraki adımda görünür.
"""
from __future__ import annotations

import math

import torch

from ..config import WorldConfig
from ..world import World
from . import fields
from .layout import make_layout
from .spec import GameSpec

REARM_MARGIN = 1.0   # temastan sonra kaynak, canlı temas yarıçapı+bu kadar uzaklaşınca yeniden etkinleşir

# O6 görsel ön uç (ELLE YAZILMIŞ sabitler, R-11; pilotta kuram kontrolüyle ayarlanır): göz ekseni ±45°, açısal pencere, uzaklığa bağlı görünürlük
EYE_AXIS = math.pi / 4
EYE_SIGMA = 0.9          # rad
VIS_D0 = 12.0            # görünürlük yarıya düşen uzaklık ölçeği (arena kenarı 40; koku σ=8'den uzun menzil)


def vis_patterns(n_feat: int, seed: int = 0) -> torch.Tensor:
    """İki sabit görsel desen X, Y: (2, n_feat) [0,1]; özellik kümeleri çakışmaz (keyfî ama sabit; keyfî-kod ilkesi koku desenleriyle aynı)."""
    g = torch.Generator().manual_seed(7_000 + seed)
    perm = torch.randperm(n_feat, generator=g)
    out = torch.zeros(2, n_feat)
    half = n_feat // 2
    out[0, perm[:half]] = 0.6 + 0.4 * torch.rand(half, generator=g)
    out[1, perm[half:half * 2]] = 0.6 + 0.4 * torch.rand(half, generator=g)
    return out


class GameWorld(World):
    def __init__(self, cfg: WorldConfig, spec: GameSpec, batch: int, seed: int, device: str = "cpu",
                 patterns: torch.Tensor | None = None, swap: torch.Tensor | None = None, n_vis: int = 0, vis_swap: torch.Tensor | None = None):
        """`swap`: eleman başına rol dengelemesi (True: ödüllü koku = koku 1); ilk yerleşimden önce uygulanır.
        `n_vis` > 0: görsel kanal açık (O6); `vis_swap`: görsel rol dengelemesi (True: X↔Y); verilmezse `swap` kullanılır."""
        if batch % 2:
            raise ValueError("ayna çiftleri için batch çift olmalı")
        super().__init__(cfg, batch, seed, device, patterns)
        if swap is not None:
            self.set_swap(swap)
        self.spec = spec
        # ayrı RNG akışları (Z-09). Her bölümün başında ikisi de (tohum, bölüm numarası) işlevi olarak yeniden tohumlanır:
        # erken bitiş (stop_when_done) gibi sonuca bağlı tüketim farkları kollar arasındaki ortak rastgele sayıları (CRN) bozamaz.
        self._seed, self.episode = seed, 0
        self.layout_gen = torch.Generator(device=self.device)
        self.noise_gen = torch.Generator(device=self.device)
        self.reward_gen = torch.Generator(device=self.device)           # O5: temasta ödül çekimleri (bölüm başında önceden, CRN)
        self.reward_p = torch.ones(batch, 2, device=self.device)         # (B,2) yuva başına ödül olasılığı (yalnız bandit oyunlarında kullanılır)
        z = torch.zeros(1, cfg.n_glom, device=self.device)
        self.pattern_ext = torch.cat([self.patterns, z])             # son satır: kokusuz (−1 dizini)
        self.anosmic = torch.zeros(batch, dtype=torch.bool, device=self.device)
        self.n_vis = n_vis
        self.vis_pat = vis_patterns(n_vis).to(self.device) if n_vis > 0 else None
        self.vis_swap = (self.swap if vis_swap is None else torch.as_tensor(vis_swap, dtype=torch.bool, device=self.device)).clone()
        self.blind = torch.zeros(batch, dtype=torch.bool, device=self.device)
        self.arm_reward = torch.ones(batch, dtype=torch.bool, device=self.device)
        self.arm_odor = torch.ones(batch, dtype=torch.bool, device=self.device)
        self.test_mode = True
        self.mode = "game"
        self.reset_game()

    # ------------------------------------------------------------------ kurulum
    def odor_rewarded(self) -> torch.Tensor:
        """(B,) canlının ödüllü kokusunun dizini (A fazı: rol dengelemesi `swap` ile)."""
        return self.swap.long()

    def reward_mask(self) -> torch.Tensor:
        """(B, n_glom) ödüllü kokunun glomerül maskesi (yalnız referans karşılaştırıcı kullanır)."""
        return self.patterns[self.odor_rewarded()]

    def set_blind(self, mask) -> None:
        """Görsel kapalı kol (VPN girdisi sıfır; beyin ve RNG tüketimi aynı kalır → CRN bozulmaz)."""
        self.blind = torch.as_tensor(mask, dtype=torch.bool, device=self.device).clone()

    def set_vis_swap(self, mask) -> None:
        self.vis_swap = torch.as_tensor(mask, dtype=torch.bool, device=self.device).clone()

    def set_anosmic(self, mask) -> None:
        self.anosmic = torch.as_tensor(mask, dtype=torch.bool, device=self.device).clone()

    def set_arms(self, reward_on, odor_on) -> None:
        """O3 çarpanlı kolları: hedef temasında ödül var/yok ve temasa-bağlı koku var/yok (eleman başına)."""
        self.arm_reward = torch.as_tensor(reward_on, dtype=torch.bool, device=self.device).clone()
        self.arm_odor = torch.as_tensor(odor_on, dtype=torch.bool, device=self.device).clone()

    def reset_game(self, test: bool | None = None) -> None:
        """Yeni deneme: yerleşim `layout_gen`'den; sayaçlar sıfırlanır. `test`: ilk temas denemeyi bitirir (öğrenme kapalı testler)."""
        if test is not None:
            self.test_mode = bool(test)
        B, dev, sp = self.B, self.device, self.spec
        self.layout_gen.manual_seed(self._seed + 101 + 7919 * self.episode)
        self.noise_gen.manual_seed(self._seed + 202 + 7919 * self.episode)
        self.reward_gen.manual_seed(self._seed + 303 + 7919 * self.episode)
        self.episode += 1
        self.reward_u = torch.rand(B, 2, generator=self.reward_gen, device=dev)
        lay = make_layout(sp, self.cfg, B, self.layout_gen, dev)
        self._alloc(n_src=2)
        self.pos = lay["start"].clone()
        self.heading = lay["heading"].clone()
        self.src_pos = lay["src_pos"].clone()
        self.poly = lay["poly"].clone()
        self.src_active = torch.tensor([[s.active for s in sp.slots()]], device=dev).expand(B, -1).clone()
        rewarded = self.odor_rewarded()
        odor = torch.full((B, 2), -1, dtype=torch.long, device=dev)
        for k, s in enumerate(sp.slots()):
            if s.active and s.odor == "rewarded":
                odor[:, k] = rewarded
            elif s.active and s.odor in ("A", "B"):
                odor[:, k] = 0 if s.odor == "A" else 1
        self.src_odor = odor                                           # (B,2) −1 = kokusuz
        self.src_reward = torch.tensor([[s.reward for s in sp.slots()]], device=dev).expand(B, -1).clone()
        vis = torch.full((B, 2), -1, dtype=torch.long, device=dev)           # (B,2) görsel desen dizini; −1 = görünmez
        for k, s_ in enumerate(sp.slots()):
            if s_.active and s_.visual in ("X", "Y"):
                base = 0 if s_.visual == "X" else 1
                vis[:, k] = torch.where(self.vis_swap, torch.full_like(vis[:, k], 1 - base), torch.full_like(vis[:, k], base))
        self.src_vis = vis
        self.armed = torch.ones(B, 2, dtype=torch.bool, device=dev)
        self.contact_count = torch.zeros(B, 2, dtype=torch.long, device=dev)
        self.first_contact_slot = torch.full((B,), -1, dtype=torch.long, device=dev)
        self.first_contact_step = torch.full((B,), -1, dtype=torch.long, device=dev)
        self.first_odor_step = torch.full((B,), -1, dtype=torch.long, device=dev)   # alandan gelen ilk koku (temasa-bağlı değil)
        self.path_len = torch.zeros(B, device=dev)
        self.wall_steps = torch.zeros(B, dtype=torch.long, device=dev)
        self.finish_pending = torch.zeros(B, dtype=torch.bool, device=dev)
        self.contact_level_b = torch.zeros(B, device=dev)
        self.contact_pat = torch.zeros(B, self.cfg.n_glom, device=dev)

    # --------------------------------------------------------------- algılama
    def odor_field(self, ant: torch.Tensor) -> torch.Tensor:
        """(B,2,2) anten konumları -> (B,2,S) kaynak başına derişim; destek dışı TAM 0.0."""
        out = []
        for k, s in enumerate(self.spec.slots()):
            if not s.active or s.profile == "none":
                out.append(torch.zeros(self.B, 2, device=self.device))
                continue
            if s.profile == "trail":
                f = fields.trail(ant, self.poly, s.width, s.lam, s.amp)
            else:
                d = (ant - self.src_pos[:, k].unsqueeze(1)).norm(dim=-1)
                f = fields.bump(d, s.radius, s.amp) if s.profile == "bump" else fields.gauss(d, s.sigma, s.amp)
            out.append(f * self.src_active[:, k].unsqueeze(1).float())
        return torch.stack(out, -1)

    def sense(self) -> torch.Tensor:
        """(B,2,n_glom) [0,1). Koku yokken (alan 0, temasa-bağlı koku yok) çıktı TAM 0.0'dır; anosmik elemanda her zaman 0."""
        c = self.cfg
        field = self.odor_field(self._antennae())                       # (B,2,S)
        seen = (field > 0).flatten(1).any(-1)
        newly = seen & (self.first_odor_step < 0)
        self.first_odor_step[newly] = self.steps
        idx = torch.where(self.src_odor < 0, torch.full_like(self.src_odor, self.pattern_ext.shape[0] - 1), self.src_odor)
        drive = torch.einsum("bns,bsg->bng", field, self.pattern_ext[idx])
        eating = (self.feed_timer > 0).float() * self.contact_level_b
        drive = drive + eating.view(-1, 1, 1) * self.contact_pat.unsqueeze(1)
        glom = 1.0 - torch.exp(-c.odor_gain * drive)
        return torch.where(self.anosmic.view(-1, 1, 1), torch.zeros_like(glom), glom)

    def sense_vis(self) -> torch.Tensor | None:
        """(B,2 göz,n_vis) [0,1]: göz başına görsel özellik etkinliği (sol göz = sol anten tarafı). Görsel kanal kapalıysa ya da oyunda görsel kaynak yoksa None
        (eski oyunlarda `Creature.step` eski yola düşer). Kör elemanda sıfır. Bilgi sınırı: yalnız kaynağın görünen deseni; ödül/ısı bilgisi YOK."""
        if self.n_vis == 0 or not any(s.active and s.visual != "none" for s in self.spec.slots()):
            return None
        rel = self.src_pos - self.pos.unsqueeze(1)                                      # (B,S,2)
        d = rel.norm(dim=-1)                                                            # (B,S)
        bearing = torch.atan2(rel[..., 1], rel[..., 0]) - self.heading.unsqueeze(1)     # (B,S) başın önüne göre
        axes = torch.tensor([EYE_AXIS, -EYE_AXIS], device=self.device)                  # sol, sağ
        dlt = torch.remainder(bearing.unsqueeze(1) - axes.view(1, 2, 1) + math.pi, 2 * math.pi) - math.pi     # (B,2,S)
        gain = (torch.exp(-dlt ** 2 / (2 * EYE_SIGMA ** 2)) / (1.0 + (d / VIS_D0) ** 2).unsqueeze(1)) * self.src_active.unsqueeze(1).float()
        pat = self.vis_pat[self.src_vis.clamp(min=0)] * (self.src_vis >= 0).unsqueeze(-1).float()       # (B,S,F)
        out = torch.einsum("bes,bsf->bef", gain, pat).clamp(max=1.0)
        return torch.where(self.blind.view(-1, 1, 1), torch.zeros_like(out), out)

    # ------------------------------------------------------------------- adım
    def step(self, turn_rate: torch.Tensor, speed: float) -> None:
        before, alive = self.pos.clone(), ~self.done
        super().step(turn_rate, speed)
        self.path_len += (self.pos - before).norm(dim=-1) * alive.float()
        L = self.cfg.arena
        self.wall_steps += (((self.pos <= 0) | (self.pos >= L)).any(-1) & alive).long()
        self.done |= self.finish_pending & (self.feed_timer <= 0) & ~self.done

    def _contacts(self, could_touch: torch.Tensor) -> None:
        c = self.cfg
        dist = (self.pos.unsqueeze(1) - self.src_pos).norm(dim=-1)      # (B,S)
        self.armed |= dist > c.contact_radius + REARM_MARGIN
        hit = (dist < c.contact_radius) & self.src_active & self.armed & could_touch.unsqueeze(-1)
        any_hit = hit.any(-1)
        if not bool(any_hit.any()):
            return
        rows = torch.nonzero(any_hit).squeeze(-1)
        slot = torch.where(hit, dist, torch.full_like(dist, 1e9)).argmin(-1)[rows]
        self.contact_count[rows, slot] += 1
        first = self.first_contact_slot[rows] < 0
        r1 = rows[first]
        self.first_contact_slot[r1] = slot[first]
        self.first_contact_step[r1] = self.steps
        self.armed[rows, slot] = False
        if self.test_mode:
            self.done[rows] = True                                      # test: ilk temas seçimdir, tüketim yok
            return
        reward = self.src_reward[rows, slot] * torch.where(slot == 0, self.arm_reward[rows].float(), torch.ones_like(slot, dtype=torch.float))
        if self.spec.bandit:                                            # ödül bu bölümde önceden çekilmiş u'ya bağlı: reward = [u < p]
            reward = reward * (self.reward_u[rows, slot] < self.reward_p[rows, slot]).float()
        self.feed_timer[rows] = c.feed_time
        self.feed_reward[rows] = reward
        lvl = torch.tensor([s.contact_level for s in self.spec.slots()], device=self.device)[slot]
        odor = self.src_odor[rows, slot]
        on = (lvl > 0) & (odor >= 0) & torch.where(slot == 0, self.arm_odor[rows], torch.ones_like(slot, dtype=torch.bool))
        self.contact_level_b[rows] = torch.where(on, lvl, torch.zeros_like(lvl))
        pat = self.pattern_ext[torch.where(odor < 0, torch.full_like(odor, self.pattern_ext.shape[0] - 1), odor)]
        self.contact_pat[rows] = pat
        self.finish_pending[rows] |= (slot >= 0) if (self.spec.bandit or self.spec.end_any) else (slot == 0)   # gerçek hedef (bandit/end_any: herhangi bir kaynak) tüketilince deneme biter

    # ----------------------------------------------------------------- çıktılar
    def outcome(self) -> dict[str, torch.Tensor]:
        """Deneme sonu özeti (araştırmacıya; beyne gitmez). Süreler saniye; yoksa nan."""
        dt = self.cfg.dt
        t = torch.where(self.first_contact_step >= 0, (self.first_contact_step.float() + 1) * dt, torch.full_like(self.path_len, float("nan")))
        zone = torch.where(self.first_odor_step >= 0, self.first_odor_step.float() * dt, torch.full_like(self.path_len, float("nan")))
        return {"slot": self.first_contact_slot.clone(), "time": t, "odor_time": zone, "path_len": self.path_len.clone(),
                "contacts": self.contact_count.clone(), "wall_steps": self.wall_steps.clone()}
