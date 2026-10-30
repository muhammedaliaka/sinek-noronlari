"""Oyun tanımları (docs/dort_koku_oyunu_plani.md §3). Sayılar PİLOT ÖNCESİ adaydır; ön-kayıtta dondurulur."""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class SlotSpec:
    """Bir kaynak yuvası. Yuva 0 = gerçek hedef, yuva 1 = decoy (sahte hedef)."""
    active: bool = True
    profile: str = "none"        # none | gauss | bump | trail
    odor: str = "rewarded"       # rewarded (canlının ödüllü kokusu) | A | B (sabit koku dizini 0/1; O5) | none (kokusuz)
    reward: float = 1.0          # temasta ödül
    amp: float = 1.0
    sigma: float = 8.0           # gauss
    radius: float = 5.0          # bump
    width: float = 4.0           # trail yanal yarı genişlik
    lam: float = 12.0            # trail boylamsal uzunluk ölçeği
    contact_level: float = 0.0   # temasa-bağlı koku düzeyi (tüketim süresince, her iki antene); 0 = yok
    visual: str = "none"         # O6: none | X | Y (kaynağın sabit görsel deseni; canlıya göre rol dengelemesi `vis_swap` ile). reward < 0: ısı cezası (acı kanalı)


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
    bandit: bool = False         # O5: temasta olasılıklı ödül (dünyadaki reward_p), herhangi bir kaynağın tüketimi bölümü bitirir
    end_any: bool = False        # O6: herhangi bir kaynağın (ödül ya da ısı tuzağı) tüketimi bölümü bitirir

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
    # O5 (geliştirme): iki kaynak, kokular A (yuva 0) ve B (yuva 1); ödül olasılıkları bölümden bölüme `GameWorld.reward_p` ile değişir
    # O6 (görsel + koku, ısı tuzağı; docs/gorsel_koku_oyunu_plani.md): yuva 0 = güvenli (ödül +1), yuva 1 = ısı tuzağı (−1); herhangi bir temas bölümü bitirir.
    # O6a: yalnız koku (güvenli=A, tuzak=B, görsel yok). O6b: iki yuvada AYNI koku, güvenli=desen X, tuzak=desen Y. O6c: kokusuz güvenli(X) vs ödüllü kokuyu ×2 yayan tuzak(Y).
    "O6a": GameSpec("O6a", target=SlotSpec(profile="gauss", odor="A", sigma=8.0, reward=1.0),
                    decoy=SlotSpec(active=True, profile="gauss", odor="B", sigma=8.0, reward=-1.0), end_any=True),
    "O6b": GameSpec("O6b", target=SlotSpec(profile="gauss", odor="A", sigma=8.0, reward=1.0, visual="X"),
                    decoy=SlotSpec(active=True, profile="gauss", odor="A", sigma=8.0, reward=-1.0, visual="Y"), end_any=True),
    "O6c": GameSpec("O6c", target=SlotSpec(profile="none", odor="none", reward=1.0, visual="X"),
                    decoy=SlotSpec(active=True, profile="gauss", odor="A", sigma=8.0, amp=2.0, reward=-1.0, visual="Y"), end_any=True),
    "O5": GameSpec("O5", target=SlotSpec(profile="gauss", odor="A", sigma=8.0), decoy=SlotSpec(active=True, profile="gauss", odor="B", sigma=8.0, reward=1.0),
                   bandit=True),
}
