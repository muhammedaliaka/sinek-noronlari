"""Gerçek bağlantı verisi kaynakları: sürüm, lisans, bütünlük bilgisi.

Boyut ve md5 değerleri indirme öncesinde sunucunun bildirdiği değerlerdir
(Google Cloud Storage `content-length` ve `x-goog-hash: md5`, 2026-10-27'de okundu).
Veri değişirse indirme doğrulaması başarısız olur; sessizce başka sürüm kullanılmaz.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteFile:
    name: str
    url: str
    size: int
    md5_b64: str          # GCS'nin bildirdiği base64 md5
    about: str

    @property
    def md5_hex(self) -> str:
        return base64.b64decode(self.md5_b64).hex()


@dataclass(frozen=True)
class Dataset:
    key: str
    title: str
    version: str
    license: str
    home: str
    citation_note: str
    files: tuple[RemoteFile, ...]

    def file(self, name: str) -> RemoteFile:
        for f in self.files:
            if f.name == name:
                return f
        raise KeyError(name)


_BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome"

MALE_CNS = Dataset(
    key="malecns_v1.0",
    title="MaleCNS connectome (erkek Drosophila beyin + ventral sinir kordonu)",
    version="male-cns:v1.0 (yayın: 2026-06-08)",
    license="CC-BY (atıf zorunlu)",
    home="https://male-cns.janelia.org/",
    citation_note=(
        "FlyEM (HHMI Janelia), Cambridge Zoology, MRC LMB ve Google Research işbirliği; CC BY 4.0. "
        "Makale: https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6 (Cell, 2026); "
        "ön baskı: doi:10.1101/2025.10.09.680999. Yazar listesi için makale sayfasına bakın; "
        "veriyi kullanan her yayın bu çalışmaya atıf vermelidir."
    ),
    files=(
        RemoteFile(
            "body-annotations-male-cns-v1.0-minconf-0.5.feather",
            f"{_BASE}/body-annotations-male-cns-v1.0-minconf-0.5.feather",
            14483314, "UKdxh3DFciDxYLpPQxq4ng==",
            "Nöron açıklamaları (sınıf, tür, taraf, ...); nörotransmitter hariç",
        ),
        RemoteFile(
            "body-neurotransmitters-male-cns-v1.0.feather",
            f"{_BASE}/body-neurotransmitters-male-cns-v1.0.feather",
            43282834, "PYQrEv5cSe763lKNfdJKHw==",
            "Nöron başına toplu nörotransmitter tahminleri",
        ),
        RemoteFile(
            "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
            f"{_BASE}/connectome-weights-male-cns-v1.0-minconf-0.5.feather",
            1051241946, "8w6dzKJc/QIb8eez2XVZng==",
            "Nöron-nöron bağlantı ağırlıkları (tam bağlantı grafı)",
        ),
    ),
)

DATASETS = {MALE_CNS.key: MALE_CNS}
