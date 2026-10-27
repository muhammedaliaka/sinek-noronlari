"""Bağlantı verisi kabı: nöron tablosu + sinaps ağırlıklı kenar listesi + kaynak bilgisi."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class Connectome:
    """`neurons`: bodyId, pop (popülasyon), type, group, somaSide, nt, ...
    `edges`: body_pre, body_post, weight (sinaps sayısı). `meta`: kaynak, sürüm, lisans, çıkarım ayarları."""

    neurons: pd.DataFrame
    edges: pd.DataFrame
    meta: dict = field(default_factory=dict)

    def ids(self, pop: str) -> np.ndarray:
        return self.neurons.loc[self.neurons["pop"] == pop, "bodyId"].to_numpy()

    def pops(self) -> dict[str, int]:
        return self.neurons["pop"].value_counts().to_dict()

    def block(self, pre: str, post: str, pre_ids=None, post_ids=None) -> np.ndarray:
        """Yoğun (n_pre, n_post) sinaps sayısı matrisi; sıra `pre_ids` / `post_ids`.

        Verilmezse popülasyonun nöron tablosundaki sırası kullanılır."""
        pre_ids = self.ids(pre) if pre_ids is None else np.asarray(pre_ids)
        post_ids = self.ids(post) if post_ids is None else np.asarray(post_ids)
        pi = pd.Series(np.arange(len(pre_ids)), index=pre_ids)
        qi = pd.Series(np.arange(len(post_ids)), index=post_ids)
        e = self.edges[self.edges.body_pre.isin(pre_ids) & self.edges.body_post.isin(post_ids)]
        out = np.zeros((len(pre_ids), len(post_ids)), dtype=np.float32)
        np.add.at(out, (pi.reindex(e.body_pre).to_numpy(), qi.reindex(e.body_post).to_numpy()),
                  e.weight.to_numpy(dtype=np.float32))
        return out

    # ------------------------------------------------------------------ disk
    def save(self, directory: str | Path) -> Path:
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        self.neurons.reset_index(drop=True).to_feather(d / "neurons.feather")
        self.edges.reset_index(drop=True).to_feather(d / "edges.feather")
        (d / "meta.json").write_text(json.dumps(self.meta, indent=1, ensure_ascii=False, default=str))
        return d

    @classmethod
    def load(cls, directory: str | Path) -> "Connectome":
        d = Path(directory)
        return cls(
            neurons=pd.read_feather(d / "neurons.feather"),
            edges=pd.read_feather(d / "edges.feather"),
            meta=json.loads((d / "meta.json").read_text()),
        )
