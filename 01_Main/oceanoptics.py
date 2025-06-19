#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同期誤差測定 ― シンプル表示版

● なにをする？
    2 台の Ocean Insight 分光器で *ほぼ同時* に 100 回スペクトルを取得し、
    積算開始時刻差 |Δ| (ms) を測って "どの程度ずれているか" を一目で示します。

● 出力は 3 つだけ
    1. 進捗バー (#####...)
    2. 統計まとめ (平均・中央値・95%タイル・最大)
    3. 絶対誤差のヒストグラム (自動表示)

※ 積算時間: 4 ms  (両機共通)
※ 開始時刻差 = 終了時刻差 なので終了時刻を利用
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import matplotlib.pyplot as plt
import seabreeze
from seabreeze.spectrometers import list_devices, Spectrometer

# ------------------ 設定 ------------------
BACKENDS = ["cseabreeze", "pyseabreeze"]
NEEDED   = 2      # 必要台数
INT_MS   = 100    # 積算時間 [ms]
ITER     = 20    # 測定回数


# -------------- バックエンド選択 --------------

def pick_backend(required=NEEDED):
    best, best_be = [], None


    for be in BACKENDS:
        try:
            seabreeze.use(be)
        except Exception:
            continue
        devs = list_devices()
        if len(devs) >= required:
            return be, devs
        if len(devs) > len(best):
            best, best_be = devs, be
    return best_be, best

# ---------------- 測定関数 ----------------

def acquire(spec: Spectrometer):
    t_cmd = time.perf_counter()
    _ = spec.spectrum()
    t_fin = time.perf_counter()
    return t_cmd, t_fin

# ----------------- メイン -----------------

def main():
    be, devs = pick_backend()
    if not be or len(devs) < NEEDED:
        print("[ERROR] 分光器を 2 台検出できません")
        sys.exit(1)

    specs = [Spectrometer(devs[i]) for i in range(NEEDED)]
    for s in specs:
        s.integration_time_micros(INT_MS * 1000)
        s.spectrum()  # ウォームアップ

    abs_errors = []
    bar_unit = ITER // 50 or 1  # 進捗バー更新間隔
    print("計測中:", end=" ")

    with ThreadPoolExecutor(max_workers=NEEDED) as ex:
        for n in range(1, ITER + 1):
            times = list(ex.map(acquire, specs))
            # シリアル順で固定 (list_devices 順序)
            c0, f0 = times[0]
            c1, f1 = times[1]
            delta_ms = abs(f1 - f0) * 1000  # 絶対誤差(ms)
            abs_errors.append(delta_ms)
            if n % bar_unit == 0 or n == ITER:
                print("#", end="", flush=True)
    print(" 完了")

    # ---------- 統計 ----------
    a = np.array(abs_errors)
    mean = a.mean()
    median = np.median(a)
    p95 = np.percentile(a, 95)
    max_v = a.max()

    print("\n=== 誤差統計 (ms) ===")
    print(f"平均   : {mean:.3f}")
    print(f"中央値 : {median:.3f}")
    print(f"95%タイル: {p95:.3f}")
    print(f"最大   : {max_v:.3f}")

    # ---------- ヒストグラム ----------
    plt.figure(figsize=(8, 4))
    plt.hist(a, bins='auto')
    plt.axvline(mean, linestyle="--", label=f"平均 {mean:.2f} ms")
    plt.xlabel("|Δ| (ms)")
    plt.ylabel("Count")
    plt.title(f"Start 時刻差の分布  N={ITER}, int={INT_MS} ms")
    plt.legend()
    plt.tight_layout()
    plt.show()

    for s in specs:
        s.close()

if __name__ == "__main__":
    main()
