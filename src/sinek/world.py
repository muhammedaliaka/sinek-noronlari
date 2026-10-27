"""Toplu (batch) 2B dünya: koku kaynakları, yiyecek teması, enerji.

Her batch elemanı bağımsız bir canlı + dünyadır. Ödül kuralı her eleman için
ayrı tutulur (`reward_by_odor`); böylece aynı anda farklı koşullar çalıştırılabilir.
"""
from __future__ import annotations

import math

import torch

from .config import WorldConfig


def odor_patterns(cfg: WorldConfig, seed: int) -> torch.Tensor:
    """(n_odors, n_glom) koku desenleri. A ve B belirli sayıda glomerülü paylaşır."""
    g = torch.Generator().manual_seed(1000 + seed)
    k, ov = cfg.glom_per_odor, cfg.odor_overlap
    if cfg.n_odors != 2:
        raise NotImplementedError("Evre 1 iki koku (A/B) ile çalışır")
    if 2 * k - ov > cfg.n_glom:
        raise ValueError("n_glom, iki kokunun glomerülleri için yetersiz")
    perm = torch.randperm(cfg.n_glom, generator=g)
    a = perm[:k]
    b = torch.cat([a[:ov], perm[k : 2 * k - ov]])
    pat = torch.zeros(2, cfg.n_glom)
    pat[0, a] = 1.0
    pat[1, b] = 1.0
    return pat


class World:
    def __init__(
        self,
        cfg: WorldConfig,
        batch: int,
        seed: int,
        device: str = "cpu",
        patterns: torch.Tensor | None = None,
    ):
        """`patterns`: koku desenleri (n_odors, n_glom). Verilmezse `seed`ten üretilir.

        Test dünyaları, eğitim dünyasının desenlerini burada geçirmelidir; aksi halde
        "A" ve "B" canlının öğrendiği kokular olmaz.
        """
        self.cfg = cfg
        self.B = batch
        self.device = torch.device(device)
        self.gen = torch.Generator(device=self.device).manual_seed(seed + 1)
        self.patterns = (odor_patterns(cfg, seed) if patterns is None else patterns).to(self.device)
        # (B, n_odors): A ödüllü, B ödülsüz varsayılan
        self.reward_by_odor = torch.zeros(batch, cfg.n_odors, device=self.device)
        self.reward_by_odor[:, 0] = 1.0
        # rol dengelemesi (Evre 2b): swap olan canlıda "A rolü" koku 1'dir (A = önce ödüllenen koku). Varsayılan: hiçbiri.
        self.swap = torch.zeros(batch, dtype=torch.bool, device=self.device)
        self._rewards = (1.0, 0.0)
        self.consumable = True
        self.mode = "forage"
        self._alloc(n_src=cfg.n_odors * cfg.n_sources_per_odor)
        self.reset_forage()

    # ------------------------------------------------------------------ kurulum
    def _alloc(self, n_src: int) -> None:
        B, dev = self.B, self.device
        self.pos = torch.zeros(B, 2, device=dev)
        self.heading = torch.zeros(B, device=dev)
        self.feed_timer = torch.zeros(B, device=dev)
        self.feed_reward = torch.zeros(B, device=dev)
        self.energy = torch.ones(B, device=dev)
        self.n_contacts = torch.zeros(B, 2, device=dev)  # koku türüne göre temas sayısı
        self.src_pos = torch.zeros(B, n_src, 2, device=dev)
        self.src_kind = torch.zeros(B, n_src, dtype=torch.long, device=dev)
        self.done = torch.zeros(B, dtype=torch.bool, device=dev)
        self.choice = torch.full((B,), -1, dtype=torch.long, device=dev)
        self.choice_step = torch.full((B,), -1, dtype=torch.long, device=dev)
        self.steps = 0

    def _rand(self, *shape: int) -> torch.Tensor:
        return torch.rand(*shape, generator=self.gen, device=self.device)

    def _uniform_pos(self, *lead: int) -> torch.Tensor:
        m, L = self.cfg.wall_margin, self.cfg.arena
        return m + (L - 2 * m) * self._rand(*lead, 2)

    def reset_forage(self) -> None:
        """Gezinme arenası: rastgele başlangıç, her kokudan n kaynak."""
        c = self.cfg
        n = c.n_sources_per_odor
        self.mode, self.consumable = "forage", True
        self._alloc(n_src=c.n_odors * n)
        self.pos = self._uniform_pos(self.B)
        self.heading = self._rand(self.B) * 2 * math.pi
        kinds = torch.arange(c.n_odors, device=self.device).repeat_interleave(n)
        self.src_kind = kinds.expand(self.B, -1).clone()
        self.src_pos = self._uniform_pos(self.B, c.n_odors * n)

    def reset_choice(self) -> None:
        """İki seçenekli test: merkezde başlangıç, A ve B karşılıklı, taraf rastgele."""
        c = self.cfg
        self.mode, self.consumable = "choice", False
        self._alloc(n_src=2)
        centre = torch.full((self.B, 2), c.arena / 2, device=self.device)
        ang = self._rand(self.B) * 2 * math.pi
        u = torch.stack([torch.cos(ang), torch.sin(ang)], dim=-1)
        flip = (self._rand(self.B) < 0.5)
        sign = torch.where(flip, -1.0, 1.0).unsqueeze(-1)
        self.src_pos[:, 0] = centre + sign * c.choice_distance * u
        self.src_pos[:, 1] = centre - sign * c.choice_distance * u
        self.src_kind[:, 0], self.src_kind[:, 1] = 0, 1
        self.pos = centre.clone()
        self.heading = self._rand(self.B) * 2 * math.pi

    # --------------------------------------------------------------- algılama
    def _antennae(self) -> torch.Tensor:
        c = self.cfg
        d = torch.stack([torch.cos(self.heading), torch.sin(self.heading)], dim=-1)
        perp = torch.stack([-d[:, 1], d[:, 0]], dim=-1)
        base = self.pos + c.antenna_fwd * d
        left = base + c.antenna_side * perp
        right = base - c.antenna_side * perp
        return torch.stack([left, right], dim=1)  # (B, 2, 2)

    def sense(self) -> torch.Tensor:
        """Sol/sağ antende glomerül aktivasyonu, (B, 2, n_glom), [0,1]."""
        c = self.cfg
        ant = self._antennae()                                          # (B,2,2)
        d2 = ((ant.unsqueeze(2) - self.src_pos.unsqueeze(1)) ** 2).sum(-1)  # (B,2,S)
        conc = torch.exp(-d2 / (2 * c.odor_sigma**2))
        pat = self.patterns[self.src_kind]                              # (B,S,G)
        drive = torch.einsum("bns,bsg->bng", conc, pat)
        return 1.0 - torch.exp(-c.odor_gain * drive)

    def taste_touch(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Yeme sırasında işaretli tat sinyali (+tatlı, -acı) ve temas (0/1)."""
        eating = (self.feed_timer > 0).float()
        return self.feed_reward * eating, eating

    # ------------------------------------------------------------------- adım
    def step(self, turn_rate: torch.Tensor, speed: float) -> None:
        """turn_rate (B,) rad/saniye. Yemekte olan veya işi biten canlı hareket etmez."""
        c = self.cfg
        moving = (self.feed_timer <= 0) & ~self.done
        self.heading = self.heading + turn_rate * c.dt * moving
        step_len = speed * c.dt * moving.float()
        self.pos = self.pos + step_len.unsqueeze(-1) * torch.stack(
            [torch.cos(self.heading), torch.sin(self.heading)], dim=-1
        )
        self._walls()
        self.feed_timer = (self.feed_timer - c.dt).clamp(min=0.0)
        self.energy = self.energy - c.metabolism * c.dt * (~self.done).float()
        self._contacts(moving)
        self.steps += 1

    def _walls(self) -> None:
        L = self.cfg.arena
        x, y = self.pos[:, 0], self.pos[:, 1]
        hit_x = (x < 0) | (x > L)
        hit_y = (y < 0) | (y > L)
        self.heading = torch.where(hit_x, math.pi - self.heading, self.heading)
        self.heading = torch.where(hit_y, -self.heading, self.heading)
        self.pos = self.pos.clamp(0.0, L)

    def _contacts(self, could_touch: torch.Tensor) -> None:
        c = self.cfg
        dist = (self.pos.unsqueeze(1) - self.src_pos).norm(dim=-1)      # (B,S)
        hit = (dist < c.contact_radius) & could_touch.unsqueeze(-1)
        any_hit = hit.any(-1)
        if not bool(any_hit.any()):
            return
        nearest = torch.where(hit, dist, torch.full_like(dist, 1e9)).argmin(-1)  # (B,)
        rows = torch.nonzero(any_hit).squeeze(-1)
        kinds = self.src_kind[rows, nearest[rows]]
        reward = self.reward_by_odor[rows, kinds]
        self.n_contacts[rows, kinds] += 1
        if self.consumable:
            self.feed_timer[rows] = c.feed_time
            self.feed_reward[rows] = reward
            self.energy[rows] += c.energy_per_reward * reward
            self._respawn(rows, nearest[rows])
        else:
            first = self.choice[rows] < 0
            r_first = rows[first]
            self.choice[r_first] = kinds[first]
            self.choice_step[r_first] = self.steps
            self.done[rows] = True

    def _respawn(self, rows: torch.Tensor, which: torch.Tensor) -> None:
        """Tüketilen kaynağı, canlıdan yeterince uzak rastgele bir yere taşı."""
        c = self.cfg
        n_try = 8
        cand = self._uniform_pos(len(rows), n_try)                      # (R,n,2)
        d = (cand - self.pos[rows].unsqueeze(1)).norm(dim=-1)           # (R,n)
        ok = d >= c.respawn_min_dist
        # yeterince uzak ilk aday; yoksa en uzak aday
        pick = torch.where(ok.any(-1), ok.float().argmax(-1), d.argmax(-1))
        self.src_pos[rows, which] = cand[torch.arange(len(rows), device=self.device), pick]

    # ---------------------------------------------------------------- yardımcı
    def set_rewards(self, reward_a: float, reward_b: float) -> None:
        """Ödüller ROL başınadır (A, B). `swap` olan canlılarda A rolü koku 1, B rolü koku 0'dır."""
        self._rewards = (float(reward_a), float(reward_b))
        ra = torch.full((self.B,), float(reward_a), device=self.device)
        rb = torch.full((self.B,), float(reward_b), device=self.device)
        self.reward_by_odor[:, 0] = torch.where(self.swap, rb, ra)
        self.reward_by_odor[:, 1] = torch.where(self.swap, ra, rb)

    def set_swap(self, swap: torch.Tensor) -> None:
        """Rol dengelemesini ayarla ve mevcut ödülleri yeni eşlemeyle yeniden uygula."""
        self.swap = torch.as_tensor(swap, dtype=torch.bool, device=self.device).clone()
        self.set_rewards(*self._rewards)
