"""Evre 1 yapılandırması: dünya, beyin ve hareket parametreleri.

Tüm sayılar bir model varsayımıdır; ölçülmüş biyolojik değerler değildir.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass
class WorldConfig:
    arena: float = 40.0              # kare alan kenarı (birim)
    n_odors: int = 2                 # A ve B kokusu
    n_glom: int = 8                  # koku kanalı (glomerül) sayısı
    glom_per_odor: int = 4           # bir kokunun açtığı glomerül sayısı
    odor_overlap: int = 1            # A ve B arasında ortak glomerül sayısı
    odor_sigma: float = 8.0          # koku bulutunun yayılımı (Gauss sigma)
    odor_gain: float = 4.0           # derişimden glomerül aktivasyonuna doygunluk
    antenna_side: float = 1.2        # anten yanal ofseti
    antenna_fwd: float = 0.6         # anten ileri ofseti
    contact_radius: float = 1.5      # yiyeceğe temas yarıçapı
    n_sources_per_odor: int = 3      # gezinme arenasında her koku için kaynak
    choice_distance: float = 12.0    # seçim testinde merkezden kaynak uzaklığı
    respawn_min_dist: float = 8.0    # tüketilen kaynağın yeniden doğuş uzaklığı
    wall_margin: float = 3.0         # kaynakların duvardan uzaklığı
    dt: float = 0.02                 # dünya adımı (saniye)
    feed_time: float = 0.4           # temas sonrası yeme süresi (saniye)
    energy_per_reward: float = 1.0   # ödül başına enerji kazancı
    metabolism: float = 0.01         # saniye başına enerji harcaması


@dataclass
class BrainConfig:
    n_glom: int = 8
    pn_per_glom: int = 5
    n_kc: int = 1000                 # yarımküre başına Kenyon hücresi
    kc_in: int = 6                   # her KC'nin aldığı PN sayısı
    n_mbon: int = 32                 # yarımküre, tür (yaklaş/kaçın) başına MBON
    n_grn: int = 8                   # tat/temas nöronu (tür başına)
    snn_dt_ms: float = 2.0

    # duyu (PN) Poisson hızları
    pn_base_rate: float = 3.0
    pn_max_rate: float = 120.0

    # Kenyon hücreleri
    tau_kc_ms: float = 10.0
    j_pn_kc: float = 0.25
    kc_thresh: float = 1.0
    apl_tau_ms: float = 25.0
    apl_gain: float = 6.0            # KC etkinliğinin APL ile geri baskılanması

    # MBON'lar
    tau_mb_ms: float = 15.0
    mb_bias: float = 0.55            # eşik altı tonik sürüş
    j_kc_mb: float = 0.02

    # plastik KC->MBON ağırlıkları
    w0: float = 0.5
    w_max: float = 1.0
    w_jitter: float = 0.02

    # öğrenme (üç etkenli: KC izi x dopamin x MBON türü)
    eta: float = 5.0                 # öğrenme hızı (1/saniye cinsinden)
    tau_elig: float = 0.3            # uygunluk izi (saniye)
    elig_ref_rate: float = 50.0
    reward_target: float = 0.6       # ödülün V birimindeki karşılığı (ulaşılabilir doygunluk altında)

    # MBON -> değer okuması
    tau_valence: float = 0.15
    valence_gain: float = 40.0       # Hz farkı -> V birimi
    grn_max_rate: float = 150.0
    tau_taste: float = 0.06


@dataclass
class ConnectomeBrainConfig:
    """Evre 2: gerçek bağlantıdan (MaleCNS v1.0) çıkarılmış mantar cismi alt ağı.

    Sayılar model varsayımıdır; bağlantı sayıları (sinaps) veriden gelir.
    """
    data_dir: str = "data/processed/malecns_v1.0_R"
    n_grn: int = 8                   # tat/temas nöronu (tür başına)
    snn_dt_ms: float = 2.0

    # duyu (PN) Poisson hızları
    pn_base_rate: float = 3.0
    pn_max_rate: float = 120.0

    # görsel ön uç (O6, docs/gorsel_koku_oyunu_plani.md §3). n_vis_feat=0: KAPALI → koku yolu bit-bit aynı kalır.
    # VPN->KC sinaps sayıları veriden (vpn_kc.feather), PN ile AYNI ölçekle ve j_pn_kc ile; VPN ayarı (özellik->VPN) elle yazılmış, sabit-rastgeledir (R-11).
    n_vis_feat: int = 0
    vis_gain: float = 4.0            # özellik etkinliğinden VPN etkinliğine doygunluk (odor_gain gibi)
    vis_tuning_seed: int = 0         # ayar matrisinin tohumu (popülasyon sabiti; canlı tohumundan bağımsız)
    vis_tuning_density: float = 0.10  # (K-053; ilk tasarım 0,4) VPN başına özellik kanalına bağlanma olasılığı
    vis_kc_gain: float = 8.0         # VPN->KC ağırlık çarpanı (K-053; 47 VPN, yüzlerce PN'e karşı; görsel KC kodu koku koduna kıyasla ≈6× dardı); 1 = PN ile aynı ölçek
    vis_avoid_scale: float = 1.0     # görsel KC (VPN girdili) -> 'kaçın' sınıfı MBON sinapslarının çarpanı; eğitimsiz ağın görsel girdiye nötr olması için `games.vis_calibration.neutral_scale` ile kalibre edilir (E-17, K-051); 1 = kalibrasyonsuz

    # Kenyon hücreleri ve APL (gerçek PN->KC, KC->APL, APL->KC sinaps sayılarıyla)
    tau_kc_ms: float = 10.0
    j_pn_kc: float = 0.25            # ortalama PN->KC bağlantısı için sıçrama (sinaps sayısı ortalamaya bölünür)
    kc_thresh: float = 1.0
    apl_tau_ms: float = 25.0
    apl_gain: float = 6.0

    # MBON'lar (gerçek KC->MBON sinaps sayılarıyla)
    tau_mb_ms: float = 15.0
    mb_bias: float = 0.55
    j_kc_mb: float = 0.02
    w0: float = 0.5                  # MBON başına ortalama KC->MBON ağırlığı (kc_mbon_norm="mbon" iken)
    kc_mbon_norm: str = "mbon"       # "mbon": her MBON'un toplam KC girdisi eşitlenir; "global": tek ölçek
    class_shuffle_seed: int = -1     # >=0: KONTROL — MBON yaklaş/kaçın sınıfları karıştırılır (bölme eşlemesi aynı kalır)

    # öğrenme: DAN'a bağlı, bölmeye özgü baskılanma (W <- W exp(-eta dt iz D)) ve
    # karşı sınıf dopaminiyle geri yükleme (W <- W + (W0 - W) (1 - exp(-eta dt iz R)))
    eta: float = 5.0
    restore: bool = True             # False: yalnız baskılanma (kontrol)
    tau_elig: float = 0.3
    elig_ref_rate: float = 50.0
    reward_target: float = 0.6
    recovery_rate: float = 0.0       # 1/sn; W'nin gerçek (başlangıç) değerine yavaş dönüşü (0 = kapalı)

    # MBON -> değer okuması: V = (class_balance * yaklaş hızı - kaçın hızı) / valence_gain
    tau_valence: float = 0.15
    valence_gain: float = 10.0
    class_balance: float = 1.0       # sınıf dengesi; eğitimsiz ağdan ölçülür (evre2.calibrate_balance)
    grn_max_rate: float = 150.0
    tau_taste: float = 0.06


@dataclass
class MotorConfig:
    speed: float = 8.0               # birim/saniye (yeme sırasında 0)
    turn_gain: float = 10.0          # rad/saniye (öğrenilmiş kontrast x kazanç)
    wander_sigma: float = 1.0        # rad/sqrt(saniye) rastgele gezinme
    contrast_eps: float = 0.05       # kontrast paydasındaki koruma (V birimi)


@dataclass
class Config:
    world: WorldConfig = field(default_factory=WorldConfig)
    brain: BrainConfig = field(default_factory=BrainConfig)
    cbrain: ConnectomeBrainConfig = field(default_factory=ConnectomeBrainConfig)
    motor: MotorConfig = field(default_factory=MotorConfig)
    brain_kind: str = "synthetic"    # "synthetic" (Evre 1) | "connectome" (Evre 2)

    def __post_init__(self) -> None:
        if self.brain_kind not in ("synthetic", "connectome"):
            raise ValueError(f"bilinmeyen brain_kind: {self.brain_kind}")
        if self.brain_kind == "synthetic" and self.brain.n_glom != self.world.n_glom:
            raise ValueError("brain.n_glom ile world.n_glom eşit olmalı")
        steps = self.world.dt * 1000.0 / self.snn_dt_ms
        if abs(steps - round(steps)) > 1e-6 or round(steps) < 1:
            raise ValueError("world.dt, snn_dt_ms'nin tam katı olmalı")

    @property
    def snn_dt_ms(self) -> float:
        return self.cbrain.snn_dt_ms if self.brain_kind == "connectome" else self.brain.snn_dt_ms

    @property
    def substeps(self) -> int:
        return int(round(self.world.dt * 1000.0 / self.snn_dt_ms))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Config":
        def build(klass, values):
            names = {f.name for f in fields(klass)}
            return klass(**{k: v for k, v in values.items() if k in names})

        return cls(
            world=build(WorldConfig, d.get("world", {})),
            brain=build(BrainConfig, d.get("brain", {})),
            cbrain=build(ConnectomeBrainConfig, d.get("cbrain", {})),
            motor=build(MotorConfig, d.get("motor", {})),
            brain_kind=d.get("brain_kind", "synthetic"),
        )
