#!/usr/bin/env python
"""
usb4000_easyconf.py  – 交互測定フレームワーク（変更容易版）
------------------------------------------------------------
◎ 変更したい値は Config クラスか外部 JSON/YAML だけ
◎ tqdm で進捗表示、PyQt5 + Matplotlib + Toolbar で可視化
◎ Python 3.9+  /  pip install seabreeze pyqt5 matplotlib tqdm pyyaml
"""

# ─────────────────────────
# 0. 標準 / サードパーティ
# ─────────────────────────
import sys, time, threading, collections, argparse, json, pathlib
from dataclasses import dataclass, asdict
import numpy as np
from seabreeze.spectrometers import Spectrometer
from tqdm import tqdm

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout

try:               # YAML は任意
    import yaml
except ImportError:
    yaml = None

# ─────────────────────────
# 1. ここを書き換えれば即反映 ─ Config
# ─────────────────────────
@dataclass
class Config:
    freq_hz:   float = 70     # TTL 周波数 [Hz]
    pair_n:    int   = 1000       # ON/OFF ペア数
    integ_ms:  float = None      # 露光時間 [ms] (None→周期×0.4)
    ring_len:  int   = 512       # リングバッファ長 (frames)
    cmap:      str   = "viridis" # ヒートマップ用カラーマップ
    title:     str   = "USB4000 Viewer"

# ─────────────────────────
# 2. 外部設定ファイル読み込み
# ─────────────────────────
def load_config_from_file(path: pathlib.Path) -> Config:
    data = {}
    if path.suffix in (".yaml", ".yml") and yaml:
        data = yaml.safe_load(path.read_text())
    elif path.suffix == ".json":
        data = json.loads(path.read_text())
    return Config(**{**asdict(Config()), **(data or {})})

# ─────────────────────────
# 3. データ取得スレッド
# ─────────────────────────
def start_grabber(cfg: Config,
                  ring: collections.deque,
                  stop_evt: threading.Event):
    """USB4000 を edge-trigger で連続取得し deque に push"""
    def _worker():
        try:
            dev = Spectrometer.from_first_available()
        except Exception as e:
            print("[ERROR] open spectrometer:", e)
            stop_evt.set(); return

        integ = cfg.integ_ms or (1 / cfg.freq_hz * 1e3 * 0.4)  # 周期×0.4
        dev.trigger_mode(2)  # External-edge
        dev.integration_time_micros(int(integ * 1000))

        try:
            for _ in tqdm(range(cfg.pair_n * 2),
                          desc="Acquiring", ncols=80, colour="cyan"):
                if stop_evt.is_set():
                    break
                wl, intens = dev.spectrum(correct_dark_counts=True)
                ring.append((time.perf_counter(), intens))
        finally:
            dev.close()
            stop_evt.set()

    threading.Thread(target=_worker, daemon=True).start()

# ─────────────────────────
# 4. PyQt5 GUI
# ─────────────────────────
class PlotWin(QWidget):
    def __init__(self, cfg: Config, wl, dA, heat, deltas):
        super().__init__()
        self.setWindowTitle(cfg.title)

        fig = Figure(figsize=(8, 9), tight_layout=True)
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)

        layout = QVBoxLayout(self)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        # (1) 平均 ΔA
        ax1 = fig.add_subplot(3, 1, 1)
        ax1.plot(wl, dA, lw=1.2)
        ax1.set(xlabel="Wavelength / nm", ylabel="ΔA",
                title="Averaged ΔA (ON / OFF)")
        ax1.grid(ls="--", alpha=.5)

        # (2) ヒートマップ
        ax2 = fig.add_subplot(3, 1, 2)
        im = ax2.imshow(
            heat, aspect="auto", origin="lower",
            extent=[wl.min(), wl.max(), 0, heat.shape[0]-1],
            cmap=cfg.cmap
        )
        fig.colorbar(im, ax=ax2, label="Intensity (arb. u.)")
        ax2.set(
            xlabel="Wavelength / nm",
            ylabel=f"Shot index\n(0–{cfg.pair_n-1}: OFF, {cfg.pair_n}–{cfg.pair_n*2-1}: ON)",
            title="Raw intensity map"
        )

        # (3) 取り込み間隔ヒスト
        T_target = 1 / cfg.freq_hz * 1e3
        ax3 = fig.add_subplot(3, 1, 3)
        ax3.hist(deltas, bins=40, range=(0, T_target * 1.6), color="teal")
        ax3.axvline(T_target, color="crimson", ls="--",
                    label=f"{T_target:.0f} ms target")
        mean, std = deltas.mean(), deltas.std()
        ax3.set(
            xlabel="Acquisition interval / ms",
            ylabel="Frequency",
            title=f"Interval  |  Mean {mean:.2f} ms  Std {std:.2f} ms"
        )
        ax3.legend()
        ax3.grid(ls="--", alpha=.5)

# ─────────────────────────
# 5. Main
# ─────────────────────────
def main():
    # -- CLI
    argp = argparse.ArgumentParser(add_help=False)
    argp.add_argument("--cfg", type=str, help="JSON or YAML config file")
    cli_args, _ = argp.parse_known_args()

    cfg = load_config_from_file(pathlib.Path(cli_args.cfg)) if cli_args.cfg else Config()

    # -- Ring & Grabber
    ring = collections.deque(maxlen=cfg.ring_len)
    stop_evt = threading.Event()
    start_grabber(cfg, ring, stop_evt)

    # -- 待機
    while not stop_evt.is_set():
        time.sleep(0.1)
    if not ring:
        print("[ERROR] no frames captured"); return

    # -- データ整形
    ts, frames = zip(*ring)
    ts = np.asarray(ts)
    frames = np.asarray(frames)

    wl_axis = Spectrometer.from_first_available().wavelengths()
    on, off = frames[0::2], frames[1::2]
    dA = -np.log10(on.mean(0) / off.mean(0))
    dA[~np.isfinite(dA)] = 0
    heat = np.vstack((off, on))
    intervals = np.diff(ts) * 1e3  # ms

    # -- GUI
    app = QApplication(sys.argv)
    win = PlotWin(cfg, wl_axis, dA, heat, intervals)
    win.resize(820, 920)   # ← resize は戻り値 None
    win.show()
    sys.exit(app.exec_())

# ─────────────────────────
if __name__ == "__main__":
    main()
