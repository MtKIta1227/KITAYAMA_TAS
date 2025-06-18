#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同期誤差測定（開始・終了）

2 台の Ocean Insight 分光器を *ほぼ同時* に駆動し、

- コマンド発行時刻差        (command-Δ)
- 積算終了時刻差            (finish-Δ)
- 積算開始時刻差            (start-Δ = finish-Δ)

を 100 回測定してグラフ化します。

> **注意**  
> 積算時間が両機同じなら **開始差 = 終了差** なので、
> `start-Δ` は `finish-Δ` をそのまま採用します。
> 以前バージョンで積算時間を差し引いていたのは誤りでした。
"""

import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import matplotlib.pyplot as plt
import seabreeze
from seabreeze.spectrometers import list_devices, Spectrometer

# --- 設定 ---
BACKENDS = ["cseabreeze", "pyseabreeze"]  # 使用候補バックエンド
NEEDED    = 2                               # 必要台数
INT_MS    = 100                               # 積算時間 [ms]
ITER      = 100                             # 測定回数

# --- Util ---

def pick_backend(required=NEEDED):
    """利用可能なバックエンドを探す"""
    best, best_be = [], None
    for be in BACKENDS:
        try:
            seabreeze.use(be)
        except Exception as e:
            print(f"[WARN] {be} load fail: {e}")
            continue
        devs = list_devices()
        print(f"[{be}] detect {len(devs)}")
        if len(devs) >= required:
            return be, devs
        if len(devs) > len(best):
            best, best_be = devs, be
    return best_be, best


def acquire(spec: Spectrometer):
    """コマンド発行直前・戻り直後の時刻を返す"""
    t_cmd = time.perf_counter()
    _ = spec.spectrum()
    t_fin = time.perf_counter()
    return spec.serial_number, t_cmd, t_fin

# --- main ---

def main():
    be, devs = pick_backend(NEEDED)
    if not be or len(devs) < NEEDED:
        print("[ERROR] 2 台検出できません")
        sys.exit(1)

    print(f"\n[INFO] backend = {be}")
    for i, d in enumerate(devs):
        print(f"  dev[{i}] serial={d.serial_number}")

    # 分光器オープン & 積算時間設定
    specs = [Spectrometer(devs[i]) for i in range(NEEDED)]
    for s in specs:
        s.integration_time_micros(INT_MS * 1000)

    # ウォームアップ 1 枚
    for s in specs:
        s.spectrum()

    cmd_diffs, fin_diffs, start_diffs = [], [], []
    with ThreadPoolExecutor(max_workers=NEEDED) as ex:
        for n in range(1, ITER + 1):
            res = list(ex.map(acquire, specs))
            res.sort(key=lambda x: x[0])  # serial 順
            _, c0, f0 = res[0]
            _, c1, f1 = res[1]
            cmd = abs(c1 - c0) * 1000
            fin = abs(f1 - f0) * 1000
            start = fin  # 同積算時間なら開始差＝終了差
            cmd_diffs.append(cmd)
            fin_diffs.append(fin)
            start_diffs.append(start)
            print(f"#{n:3d} cmd-Δ={cmd:.3f}  fin-Δ={fin:.3f}  start-Δ={start:.3f} ms")

    # 統計
    cmd_mean, fin_mean, start_mean = map(np.mean, (cmd_diffs, fin_diffs, start_diffs))

    print("\n[SUMMARY]")
    print(f"平均 cmd-Δ   : {cmd_mean:.3f} ms")
    print(f"平均 finish-Δ: {fin_mean:.3f} ms")
    print(f"平均 start-Δ : {start_mean:.3f} ms")

    # --- plot ---
    x = np.arange(1, ITER + 1)
    plt.figure(figsize=(10, 4))
    plt.plot(x, start_diffs, label="start-Δ", marker="o", ms=3)
    plt.hlines(start_mean, 1, ITER, linestyles="--", label=f"mean {start_mean:.2f} ms")
    plt.title(f"Start-Δ | N={ITER}, int={INT_MS} ms")
    plt.xlabel("Shot #")
    plt.ylabel("Error (ms)")
    plt.legend()
    plt.tight_layout()
    plt.show()

    for s in specs:
        s.close()

if __name__ == "__main__":
    main()
