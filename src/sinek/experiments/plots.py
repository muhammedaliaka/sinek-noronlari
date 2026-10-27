"""Evre 1 grafikleri (matplotlib isteğe bağlı)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

COLORS = {"plastic": "#1f77b4", "frozen": "#7f7f7f", "random": "#d62728"}
LABELS = {
    "plastic": "Öğrenen (plastik)",
    "frozen": "Öğrenme kapalı",
    "random": "Rastgele politika",
}


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def learning_curve(stages: list[dict], reversal_start: int | None, out: Path) -> Path:
    """stages: [{'episode': int, 'summary': {cond: {...}}}] zaman sırasıyla."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 4))
    x = [s["episode"] for s in stages]
    for cond in ("plastic", "frozen", "random"):
        ys, lo, hi = [], [], []
        for s in stages:
            d = s["summary"][cond]
            ys.append(d["pref_A_mean"])
            lo.append(d["pref_A_ci95"][0])
            hi.append(d["pref_A_ci95"][1])
        ys, lo, hi = map(np.array, (ys, lo, hi))
        ax.plot(x, ys, "-o", color=COLORS[cond], label=LABELS[cond], ms=4)
        ax.fill_between(x, lo, hi, color=COLORS[cond], alpha=0.15)
    ax.axhline(0.5, color="k", lw=0.8, ls=":")
    if reversal_start is not None:
        ax.axvline(reversal_start, color="k", lw=0.8, ls="--")
        ax.text(reversal_start + 0.1, 0.03, "ödül tersine çevrildi\n(A ödülsüz, B ödüllü)", fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Eğitim bölümü")
    ax.set_ylabel("A tercih oranı  A/(A+B)")
    ax.set_title("Seçim testinde A tercihi (ortalama ve %95 GA)")
    ax.legend(loc="center left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def contacts_curve(contacts: dict[str, np.ndarray], reversal_start: int | None, out: Path) -> Path:
    """contacts[cond]: (episodes, 2) ortalama A/B temas sayısı (gezinme arenası)."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 4))
    for cond, c in contacts.items():
        x = np.arange(1, len(c) + 1)
        ax.plot(x, c[:, 0], "-", color=COLORS[cond], label=f"{LABELS[cond]} - A")
        ax.plot(x, c[:, 1], "--", color=COLORS[cond], label=f"{LABELS[cond]} - B")
    if reversal_start is not None:
        ax.axvline(reversal_start + 0.5, color="k", lw=0.8, ls="--")
    ax.set_xlabel("Eğitim bölümü")
    ax.set_ylabel("Bölüm başına temas")
    ax.set_title("Gezinme arenasında A ve B temas sayıları")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def trajectories(panels: dict[str, dict], out: Path, n_show: int = 6) -> Path:
    """panels: {başlık: record_trajectories çıktısı}. A=yeşil, B=turuncu."""
    plt = _plt()
    fig, axes = plt.subplots(1, len(panels), figsize=(4.2 * len(panels), 4.4), squeeze=False)
    for ax, (title, rec) in zip(axes[0], panels.items()):
        L = rec["arena"]
        n = min(n_show, rec["path"].shape[1])
        for i in range(n):
            p = rec["path"][:, i]
            ax.plot(p[:, 0], p[:, 1], lw=0.9, alpha=0.8)
            ax.plot(p[-1, 0], p[-1, 1], "k.", ms=4)
            a, b = rec["src_pos"][i, 0], rec["src_pos"][i, 1]
            ax.add_patch(plt.Circle(a, rec["contact_radius"], color="#2ca02c", alpha=0.35))
            ax.add_patch(plt.Circle(b, rec["contact_radius"], color="#ff7f0e", alpha=0.35))
        ax.set_xlim(0, L)
        ax.set_ylim(0, L)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Seçim testi yolları (yeşil=A kaynağı, turuncu=B kaynağı; her yol ayrı deneme)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out
