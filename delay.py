import pyvisa
import time
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

# PyVISAリソースと初期設定
axisNo = '1'  # 初期軸番号
direction = 'CCW'
mode = 0  # 初期駆動方法
rm = pyvisa.ResourceManager()
instrument = None

# 状態を更新する関数
def update_status():
    if instrument:
        try:
            status = serial_write_read(f'AXI{axisNo}:SB1?')
            lblState.config(text="動作中" if int(status) & 0x40 else "停止")
            position = serial_write_read(f'AXI{axisNo}:POS?')
            txtPosition.delete(0, tk.END)
            txtPosition.insert(tk.END, position)
        except Exception:
            lblState.config(text="エラー")
    else:
        lblState.config(text="未接続")
    root.after(500, update_status)  # 状態を定期的に更新

# コントローラへの接続処理
def comm_port_open():
    global instrument
    try:
        instrument = rm.open_resource('GPIB1::7::INSTR')
        instrument.timeout = 2000
        messagebox.showinfo("接続完了", "コントローラに接続しました。")
        lblState.config(text="接続済み")
    except Exception as e:
        messagebox.showerror("接続エラー", f"接続失敗: {e}")

# 通信を閉じる処理
def comm_port_close():
    global instrument
    if instrument:
        instrument.close()
        instrument = None
    lblState.config(text="未接続")
    messagebox.showinfo("切断完了", "コントローラとの接続を切断しました。")

# 軸選択時の処理
def select_axis(axis):
    global axisNo
    axisNo = axis
    for btn in axis_buttons.values():
        btn.config(bg="SystemButtonFace")
    axis_buttons[axis].config(bg="LightBlue")

# ステージの駆動
def move_stage(direction):
    global axisNo, mode
    try:
        if mode == 0:  # 連続駆動
            cmd = f'AXI{axisNo}:GO {direction}J'
        elif mode == 1:  # ステップ駆動
            steps = txtStep.get()
            cmd = f'AXI{axisNo}:PULS {steps}:GO {direction}'
        elif mode == 2:  # 原点復帰
            cmd = f'AXI{axisNo}:GO ORG'
        serial_write(cmd)
    except Exception as e:
        messagebox.showerror("エラー", f"駆動失敗: {e}")

# コマンド送信処理
def serial_write(command):
    if instrument:
        instrument.write(command)

# コマンド送受信処理
def serial_write_read(command):
    if instrument:
        serial_write(command)
        time.sleep(0.1)
        return instrument.read()

# GUIの構築
root = tk.Tk()
root.title("ステージコントローラ")
root.geometry("600x400")

# 通信設定フレーム
frame_connection = ttk.LabelFrame(root, text="通信設定")
frame_connection.pack(fill="x", padx=10, pady=5)

btnConnect = ttk.Button(frame_connection, text="接続", command=comm_port_open)
btnConnect.pack(side="left", padx=5, pady=5)

btnDisconnect = ttk.Button(frame_connection, text="切断", command=comm_port_close)
btnDisconnect.pack(side="left", padx=5, pady=5)

lblState = ttk.Label(frame_connection, text="未接続", width=20, anchor="center", relief="sunken")
lblState.pack(side="right", padx=5, pady=5)

# 駆動軸フレーム
frame_axes = ttk.LabelFrame(root, text="駆動軸選択")
frame_axes.pack(fill="x", padx=10, pady=5)

axis_buttons = {}
for i, axis in enumerate(["1", "2", "3", "4", "5", "6"], start=1):
    btn = ttk.Button(frame_axes, text=f"軸 {axis}", width=10, command=lambda a=axis: select_axis(a))
    btn.pack(side="left", padx=5, pady=5)
    axis_buttons[axis] = btn

# 駆動設定フレーム
frame_drive = ttk.LabelFrame(root, text="駆動設定")
frame_drive.pack(fill="x", padx=10, pady=5)

lblSpeed = ttk.Label(frame_drive, text="速度:")
lblSpeed.pack(side="left", padx=5, pady=5)

txtSpeed = ttk.Entry(frame_drive, width=10)
txtSpeed.insert(0, "1000")
txtSpeed.pack(side="left", padx=5, pady=5)

lblStep = ttk.Label(frame_drive, text="ステップ:")
lblStep.pack(side="left", padx=5, pady=5)

txtStep = ttk.Entry(frame_drive, width=10)
txtStep.insert(0, "100")
txtStep.pack(side="left", padx=5, pady=5)

# 駆動操作フレーム
frame_controls = ttk.LabelFrame(root, text="操作")
frame_controls.pack(fill="x", padx=10, pady=5)

btnCCW = ttk.Button(frame_controls, text="CCW", command=lambda: move_stage("CCW"))
btnCCW.pack(side="left", padx=5, pady=5)

btnStop = ttk.Button(frame_controls, text="停止", command=lambda: serial_write("STOP 0"))
btnStop.pack(side="left", padx=5, pady=5)

btnCW = ttk.Button(frame_controls, text="CW", command=lambda: move_stage("CW"))
btnCW.pack(side="left", padx=5, pady=5)

# ステータス表示フレーム
frame_status = ttk.LabelFrame(root, text="ステータス")
frame_status.pack(fill="x", padx=10, pady=5)

lblPosition = ttk.Label(frame_status, text="ポジション:")
lblPosition.pack(side="left", padx=5, pady=5)

txtPosition = ttk.Entry(frame_status, width=15)
txtPosition.pack(side="left", padx=5, pady=5)

# 定期更新処理
update_status()

root.mainloop()
