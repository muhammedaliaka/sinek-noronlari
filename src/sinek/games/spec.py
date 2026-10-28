"""Oyun tanımları (docs/dort_koku_oyunu_plani.md §3). Sayılar PİLOT ÖNCESİ adaydır; ön-kayıtta dondurulur."""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class SlotSpec:
    """Bir kaynak yuvası. Yuva 0 = gerçek hedef, yuva 1 = decoy (sahte hedef)."""
    active: bool = True
    profile: str = "none"        # none | gauss | bump | trail
    odor: str = "rewarded"       # rewarded (canlının ödüllü kokusu) | none (kokusuz)
    reward: float = 1.0          # temasta ödül
    amp: float = 1.0
    sigma: float = 8.0           # gauss
    radius: float = 5.0          # bump
    width: float = 4.0           # trail yanal yarı genişlik
    lam: float = 12.0            # trail boylamsal uzunluk ölçeği
    contact_level: float = 0.0   # temasa-bağlı koku düzeyi (tüketim süresince, her iki antene); 0 = yok


@dataclass(frozen=True)
class GameSpec:
    name: str
    target: SlotSpec = field(default_factory=lambda: SlotSpec(active=False))
    decoy: SlotSpec = field(default_factory=lambda: SlotSpec(active=False))
    bend: float | None = None    # iz: None=iz yok, 0.0=düz, h=tek dönüş sapması
    start: str = "uniform"       # uniform | ring (hedef bölgesinin R+ring_gap halkası)
    ring_gap: float = 2.0
    dmin: float = 14.0           # başlangıç–kaynak ve kaynak–kaynak en küçük uzaklık
    start_margin: float = 3.0
    src_margin: float = 6.0

    def slots(self):
        return (self.target, self.decoy)

    def with_slot(self, which: str, **kw) -> "GameSpec":
        return replace(self, **{which: replace(getattr(self, which), **kw)})


_TRAIL = SlotSpec(profile="trail", width=4.0, lam=12.0)
_ZONE = SlotSpec(profile="bump", radius=5.0)
_DECOY = SlotSpec(profile="gauss", sigma=8.0, reward=0.0)

GAMES: dict[str, GameSpec] = {
    # çapa: tek Gauss kaynak (doğrulayıcı değil)
    "O1R": GameSpec("O1R", target=SlotSpec(profile="gauss", sigma=8.0)),
    "O1a": GameSpec("O1a", target=_TRAIL, bend=0.0),
    "O1b": GameSpec("O1b", target=_TRAIL, bend=8.0),
    "O2full": GameSpec("O2full", target=_ZONE),
    "O2near": GameSpec("O2near", target=_ZONE, start="ring"),
    # O3: alan yok; kimlik temas anında, tüketim süresince sunulur (kollar `set_arms` ile)
    "O3": GameSpec("O3", target=SlotSpec(profile="none", contact_level=1.0)),
    # O4a: yalnız decoy (ödüllü kokulu, ödülsüz)
    "O4a": GameSpec("O4a", decoy=replace(_DECOY, active=True)),
    # O4c: decoy + kokusuz gerçek hedef
    "O4c": GameSpec("O4c", target=SlotSpec(profile="none", odor="none"), decoy=replace(_DECOY, active=True)),
}
