import pyvisa
import tkinter as tk
from tkinter import messagebox

# グローバル変数
rm = pyvisa.ResourceManager()
instrument = None

# 接続ボタンを押した時の処理
def connect_button_click():
    global instrument
    try:
        instrument = rm.open_resource('GPIB1::7::INSTR')
        instrument.timeout = 2000
        r_data = instrument.query('*IDN?')
        lblState['text'] = f'接続成功: {r_data}'
        enable_controls()
        update_position()
    except Exception as e:
        lblState['text'] = '接続エラー'
        messagebox.showerror('エラー', str(e))

# 切断ボタンを押した時の処理
def disconnect_button_click():
    global instrument
    if instrument:
        instrument.close()
        lblState['text'] = '未接続'
        disable_controls()

# 現在位置を更新する
def update_position():
    if instrument is None:
        return
    try:
        r_data = instrument.query('AXI1:POS?')
        txtCurrentPosition.delete(0, tk.END)
        txtCurrentPosition.insert(tk.END, r_data)
    except Exception as e:
        lblState['text'] = '位置取得エラー'
        messagebox.showerror('エラー', f'位置取得エラー: {str(e)}')

# 駆動する
def move_stage(direction):
    speed = txtSpeed.get()
    command = f'AXI1:L0 {speed}:GO {direction.get()}J'
    instrument.write(command)
    update_position()

# ステップ駆動
def step_drive():
    speed = txtSpeed.get()
    pulses = txtStep.get()
    command = f'AXI1:L0 {speed}:PULS {pulses}:GO {direction.get()}'
    instrument.write(command)
    update_position()

# ポジションを設定
def set_position():
    new_position = txtCurrentPosition.get()
    try:
        float(new_position)  # 数値チェック
        instrument.write(f'AXI1:POS {new_position}')
    except ValueError:
        messagebox.showerror('エラー', '位置は数値でなければなりません')

# 入力値が変更されたときの処理
def on_value_change(event):
    try:
        # 速度とパルス数のバリデーション
        speed = float(txtSpeed.get())
        pulses = int(txtStep.get())
        lblState['text'] = '値が正常です'
    except ValueError:
        lblState['text'] = '速度とパルス数は数値である必要があります'

# テキストボックスやボタンを有効化
def enable_controls():
    txtSpeed.config(state='normal')
    txtStep.config(state='normal')
    txtCurrentPosition.config(state='normal')
    btnSetPosition.config(state='normal')

# テキストボックスやボタンを無効化
def disable_controls():
    txtSpeed.config(state='disabled')
    txtStep.config(state='disabled')
    txtCurrentPosition.config(state='disabled')
    btnSetPosition.config(state='disabled')

# メインウィンドウの設定
root = tk.Tk()
root.title('装置接続')
root.geometry('300x300')

# 状態表示ラベル
lblState = tk.Label(root, text='未接続', font=('Arial', 10))
lblState.pack(pady=5)

# 接続・切断ボタン
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

btnConnect = tk.Button(button_frame, text='接続', command=connect_button_click, width=10)
btnConnect.pack(side=tk.LEFT, padx=5)

btnDisconnect = tk.Button(button_frame, text='切断', command=disconnect_button_click, width=10)
btnDisconnect.pack(side=tk.LEFT, padx=5)

# 駆動速度設定
tk.Label(root, text='速度 (pps)：').pack(pady=3)
txtSpeed = tk.Entry(root, width=10)
txtSpeed.pack(pady=3)
txtSpeed.bind("<KeyRelease>", on_value_change)  # 値が変更されたときの処理をバインド

# 現在位置表示
tk.Label(root, text='現在位置：').pack(pady=3)
txtCurrentPosition = tk.Entry(root, width=10)
txtCurrentPosition.pack(pady=3)
btnSetPosition = tk.Button(root, text='位置設定', command=set_position, width=10)
btnSetPosition.pack(pady=3)

# ステップ駆動設定
tk.Label(root, text='パルス数：').pack(pady=3)
txtStep = tk.Entry(root, width=10)
txtStep.pack(pady=3)
txtStep.bind("<KeyRelease>", on_value_change)  # 値が変更されたときの処理をバインド
btnStepDrive = tk.Button(root, text='ステップ駆動', command=step_drive, width=10)
btnStepDrive.pack(pady=3)

# 駆動方向ボタン
direction_frame = tk.Frame(root)
direction_frame.pack(pady=5)

direction = tk.StringVar(value='CCW')
tk.Radiobutton(direction_frame, text='CCW', variable=direction, value='CCW').pack(side=tk.LEFT, padx=5)
tk.Radiobutton(direction_frame, text='CW', variable=direction, value='CW').pack(side=tk.LEFT, padx=5)

# メインループ
root.mainloop()
