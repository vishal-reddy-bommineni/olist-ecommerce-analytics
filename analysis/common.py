"""Shared helpers: read-only DuckDB access and chart styling."""
import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import DB_PATH

BLUE, GREY, RED, DARK = "#2b6cb0", "#a0aec0", "#c53030", "#1a365d"


def connect():
    return duckdb.connect(str(DB_PATH), read_only=True)


def df(sql, con=None):
    own = con is None
    con = con or connect()
    try:
        return con.execute(sql).df()
    finally:
        if own:
            con.close()


def style(ax, title=None, xlabel=None, ylabel=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if title:
        ax.set_title(title, fontsize=10, loc="left")
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
