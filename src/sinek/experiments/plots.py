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
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, fontsize=8, frameon=False)
    fig.text(0.01, 0.01, "Not: 'öğrenme kapalı' ve 'rastgele' koşulları değişmez, aynı düzenlerle test edildikleri için çizgileri düzdür.",
             fontsize=6.5, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
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


def _normalize(rec: dict, i: int):
    """Denemeyi merkezde sıfırla ve döndür: A kaynağı (+d, 0), B kaynağı (-d, 0)."""
    a, b = rec["src_pos"][i, 0], rec["src_pos"][i, 1]
    c = (a + b) / 2
    u = a - c
    ang = np.arctan2(u[1], u[0])
    rot = np.array([[np.cos(-ang), -np.sin(-ang)], [np.sin(-ang), np.cos(-ang)]])
    path = (rec["path"][:, i] - c) @ rot.T
    return path, np.linalg.norm(u)


def trajectories(panels: dict[str, dict], out: Path, n_show: int = 8) -> Path:
    """Her deneme döndürülmüştür: A kaynağı (yeşil) sağda, B kaynağı (turuncu) solda."""
    plt = _plt()
    fig, axes = plt.subplots(1, len(panels), figsize=(4.4 * len(panels), 4.0), squeeze=False)
    for ax, (title, rec) in zip(axes[0], panels.items()):
        n = min(n_show, rec["path"].shape[1])
        for i in range(n):
            path, d = _normalize(rec, i)
            ax.plot(path[:, 0], path[:, 1], lw=0.9, alpha=0.75)
            ax.plot(path[-1, 0], path[-1, 1], "k.", ms=4)
        ax.add_patch(plt.Circle((d, 0), rec["contact_radius"], color="#2ca02c", alpha=0.6))
        ax.add_patch(plt.Circle((-d, 0), rec["contact_radius"], color="#ff7f0e", alpha=0.6))
        ax.text(d, 2.4, "A", ha="center", color="#2ca02c", weight="bold")
        ax.text(-d, 2.4, "B", ha="center", color="#ff7f0e", weight="bold")
        ax.plot(0, 0, "k+", ms=8)
        lim = rec["arena"] / 2
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Seçim testi yolları (merkezden başlar, siyah nokta = ilk temas)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out
