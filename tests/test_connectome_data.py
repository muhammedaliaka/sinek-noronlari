"""Bağlantı verisi hattı: indirme doğrulaması, alt ağ çıkarımı, yoğun matrislere çevirme.

Çevrimdışı çalışır: küçük sahte MaleCNS dosyaları üretir. Gerçek veriye yalnızca
depodaki hazır çıktıyı (data/processed) okuyan testler dokunur.
"""
import base64
import hashlib

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather as pf
import pytest

from sinek.connectome import fetch as F
from sinek.connectome import malecns, mbmodel
from sinek.connectome.graph import Connectome
from sinek.connectome.sources import RemoteFile


# ------------------------------------------------------------------ indirme
def _remote(tmp_path, payload: bytes, md5_ok: bool = True) -> RemoteFile:
    src = tmp_path / "src.bin"
    src.write_bytes(payload)
    md5 = base64.b64encode(hashlib.md5(payload if md5_ok else payload + b"x").digest()).decode()
    return RemoteFile("x.bin", src.as_uri(), len(payload), md5, "test")


def test_fetch_downloads_and_verifies(tmp_path):
    f = _remote(tmp_path, b"abc" * 1000)
    out = F.fetch_file(f, tmp_path / "dst", log=lambda *_: None)
    assert out.read_bytes() == b"abc" * 1000 and F.is_valid(f, out)
    assert not (tmp_path / "dst" / "x.bin.part").exists()
    # geçerli dosya yeniden indirilmez
    mtime = out.stat().st_mtime_ns
    F.fetch_file(f, tmp_path / "dst", log=lambda *_: None)
    assert out.stat().st_mtime_ns == mtime


def test_fetch_rejects_corrupt_download(tmp_path):
    f = _remote(tmp_path, b"abc" * 1000, md5_ok=False)
    with pytest.raises(RuntimeError, match="doğrulaması BAŞARISIZ"):
        F.fetch_file(f, tmp_path / "dst", log=lambda *_: None)
    assert not (tmp_path / "dst" / "x.bin").exists()      # bozuk dosya kabul edilmez


def test_pinned_sources_are_wellformed():
    from sinek.connectome.sources import MALE_CNS

    assert MALE_CNS.license.startswith("CC-BY")
    for f in MALE_CNS.files:
        assert f.url.startswith("https://") and f.size > 0 and len(f.md5_hex) == 32


# ------------------------------------------------------------- sahte MaleCNS
def _write_fake_malecns(raw):
    ann = pd.DataFrame([
        # bodyId, class, somaSide, type
        (1, "Kenyon_Cell", "R", "KCg-m"), (2, "Kenyon_Cell", "R", "KCg-m"), (3, "Kenyon_Cell", "R", "KCab-s"),
        (4, "Kenyon_Cell", "R", "KCab-s"), (5, "Kenyon_Cell", "R", "KCab-s"), (6, "Kenyon_Cell", "R", "KCab-s"),
        (7, "Kenyon_Cell", "L", "KCg-m"), (8, "Kenyon_Cell", "L", "KCg-m"),
        (20, "ALPN", "R", "DA1_lPN"), (21, "ALPN", "R", "DA1_vPN"), (22, "ALPN", "R", "DM2_lPN"),
        (23, "ALPN", "L", "VA1v_adPN"), (24, "LHN", "R", "LH_x"),
        (30, "MBON", "R", "MBON01"), (31, "MBON", "R", "MBON02"), (32, "MBON", "L", "MBON03"),
        (40, "DAN", "R", "PAM01"), (41, "DAN", "R", "PPL101"), (42, "DAN", "R", "PAM02"), (43, "DAN", "R", "PPL102"),
        (44, "DAN", "R", "PPL2ab"),
        (50, "APL", "R", "APL"), (51, "APL", "L", "APL"), (52, "DPM", "R", "DPM"),
    ], columns=["bodyId", "class", "somaSide", "type"])
    ann["superclass"], ann["statusLabel"] = "x", "Traced"
    nt = pd.DataFrame({"body": ann.bodyId,
                       "consensus_nt": ["gaba" if t in ("APL",) else "dopamine" if t.startswith(("PAM", "PPL", "DPM")) else "acetylcholine"
                                        for t in ann.type],
                       "predicted_nt_confidence": 0.9})
    E = []
    def e(pre, post, w): E.append((pre, post, w))
    for kc in range(1, 7):
        e(20, kc, 3); e(21, kc, 2)                    # PN -> sağ KC (>= min_syn toplam)
        e(kc, 50, 2); e(50, kc, 2)                    # APL <-> sağ KC
        e(52, kc, 1)
    e(22, 1, 1)                                       # çok zayıf PN: dışarıda kalmalı
    e(23, 7, 9); e(23, 8, 9)                          # sadece sol KC'lere: dışarıda
    e(24, 1, 9)                                       # PN değil
    e(1, 30, 6); e(2, 30, 6); e(7, 30, 2)             # MBON01: sağ KC payı 12/14
    e(1, 31, 2); e(7, 31, 6); e(8, 31, 6)             # MBON02: sağ payı 2/14 -> dışarıda
    e(3, 32, 8); e(4, 32, 8)                          # MBON03 gövdesi solda ama KC girdisi sağdan
    e(40, 30, 10); e(40, 1, 4); e(40, 2, 4)           # PAM01 -> sağ MBON + sağ KC
    e(41, 31, 10); e(41, 7, 10)                       # PPL101 -> dışarıdaki MBON + sol KC
    e(42, 7, 10); e(42, 8, 10); e(42, 1, 3); e(42, 2, 3)   # PAM02: çoğunlukla sol -> dışarıda
    e(43, 32, 12)                                     # PPL102 -> sağ'dan beslenen MBON03
    e(44, 30, 50)                                     # PPL2ab: kapsam dışı tip
    e(30, 40, 5)                                      # MBON -> DAN (alt ağ kenarı, korunur)
    e(51, 7, 10); e(7, 51, 10)                        # sol APL
    w = pd.DataFrame(E, columns=["body_pre", "body_post", "weight"])
    pf.write_feather(pa.Table.from_pandas(ann), raw / malecns.ANNOT)
    pf.write_feather(pa.Table.from_pandas(nt), raw / malecns.NT)
    pf.write_feather(pa.Table.from_pandas(w), raw / malecns.WEIGHTS)


@pytest.fixture()
def fake_cns(tmp_path):
    _write_fake_malecns(tmp_path)
    return malecns.extract_mushroom_body(tmp_path, side="R", min_syn=5)


def test_extraction_selects_by_connectivity_rules(fake_cns):
    c = fake_cns
    assert set(c.ids("KC")) == {1, 2, 3, 4, 5, 6}                  # soma tarafı R
    assert set(c.ids("PN")) == {20, 21}                            # zayıf / sol / PN-olmayan elendi
    assert set(c.ids("MBON")) == {30, 32}                          # bağlantıya göre; soma tarafına göre değil
    assert set(c.ids("DAN")) == {40, 43}                           # PPL2ab, sol-ağırlıklı ve dışarıdaki hedefler elendi
    assert set(c.ids("APL")) == {50} and set(c.ids("DPM")) == {52}
    assert c.meta["counts"] == {"PN": 2, "KC": 6, "APL": 1, "DPM": 1, "MBON": 2, "DAN": 2}


def test_extraction_edges_stay_inside_subnetwork_and_record_provenance(fake_cns):
    c = fake_cns
    sel = set(c.neurons.bodyId)
    assert set(c.edges.body_pre) <= sel and set(c.edges.body_post) <= sel
    assert c.meta["license"].startswith("CC-BY") and c.meta["version"] and "annotations" in "".join(c.meta["files_md5"])
    assert c.meta["n_synapses"] == int(c.edges.weight.sum())


def test_connectome_save_load_roundtrip(fake_cns, tmp_path):
    fake_cns.save(tmp_path / "out")
    r = Connectome.load(tmp_path / "out")
    assert r.neurons.equals(fake_cns.neurons.reset_index(drop=True))
    assert r.edges.equals(fake_cns.edges.reset_index(drop=True)) and r.meta == fake_cns.meta


def test_block_returns_synapse_counts_in_requested_order(fake_cns):
    pn, kc = fake_cns.ids("PN"), fake_cns.ids("KC")
    b = fake_cns.block("PN", "KC")
    assert b.shape == (2, 6) and (b[list(pn).index(20)] == 3).all() and (b[list(pn).index(21)] == 2).all()
    rev = fake_cns.block("PN", "KC", pn[::-1], kc[::-1])
    assert np.array_equal(rev, b[::-1, ::-1])


def test_mbdata_from_fake_connectome(fake_cns):
    d = mbmodel.from_connectome(fake_cns)
    assert d.glom_names == ["DA1"] and (d.pn_glom == 0).all()      # iki PN aynı glomerül
    assert d.w_pn_kc.shape == (2, 6) and np.isclose(np.abs(d.w_pn_kc[d.w_pn_kc != 0]).mean(), 1.0)
    assert np.isclose(d.kc_apl.mean(), 1.0) and np.isclose(d.apl_kc.mean(), 1.0)
    assert np.allclose(d.dan_mbon.sum(0), 1.0)                     # sütun = DAN payı
    # PAM01 -> MBON01 (u=-1: kaçın), PPL102 -> MBON03 (u=+1: yaklaş)
    by = dict(zip(d.ids["MBON"], d.mbon_u))
    assert by[30] == -1.0 and by[32] == 1.0


def test_mbdata_rejects_mbon_without_dan_input(fake_cns):
    c = fake_cns
    c.edges = c.edges[~((c.edges.body_post == 30) & c.edges.body_pre.isin([40]))]
    with pytest.raises(ValueError, match="DAN girdisi"):
        mbmodel.from_connectome(c)


# ------------------------------------------------------ depodaki gerçek çıktı
@pytest.fixture(scope="module")
def real():
    try:
        return Connectome.load(mbmodel.resolve_dir(mbmodel.DEFAULT_DIR))
    except FileNotFoundError:
        pytest.skip("data/processed bulunamadı")


def test_committed_subnetwork_matches_documented_counts(real):
    assert real.meta["counts"] == {"PN": 123, "KC": 2045, "APL": 1, "DPM": 1, "MBON": 48, "DAN": 161}
    assert real.meta["license"].startswith("CC-BY") and real.meta["version"].startswith("male-cns:v1.0")
    assert real.meta["n_synapses"] == 1485307
    assert set(real.neurons[real.neurons["pop"] == "KC"].nt) == {"acetylcholine"}
    assert set(real.neurons[real.neurons["pop"] == "APL"].nt) == {"gaba"}


def test_real_mbdata_properties(real):
    d = mbmodel.from_connectome(real)
    assert (d.n_pn, d.n_kc, d.n_mbon, d.n_dan, d.n_glom) == (123, 2045, 48, 161, 58)
    assert np.allclose(d.dan_mbon.sum(0), 1.0, atol=1e-5)
    # bölme eşlemesi keskin: MBON'ların çoğunluğu PAM ya da PPL1 bölmesine ait (|u| > 0.8)
    assert (np.abs(d.mbon_u) > 0.8).sum() >= 40
    assert d.summary["mbon_approach"] > 0 and d.summary["mbon_avoid"] > 0
