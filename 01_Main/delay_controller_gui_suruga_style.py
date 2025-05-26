"""
DS102/DS112コントローラ制御用サンプルプログラム

Copyright 2023 SURUGA SEIKI Co.,Ltd. All rights reserved.
"""

import serial
import serial.tools.list_ports
import time
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

axisNo = '1'            # 軸番号
mode = 0                # 駆動方法(0:連続, 1:ステップ, 2:原点復帰)
ser = serial.Serial()

def connect_button_click(event):
    root.after(10, comm_port_open)

def comm_port_open():
    global ser
    if ser.is_open:
        ser.close()
    try:
        ser = serial.Serial(cmbCommPort.get(), cmbBaudrate.get(), timeout=2)
    except serial.SerialException:
        ser.close()
        lblState['text'] = '接続エラー発生'
        root.after(1, showerror('接続エラー発生'))
        return
    r_data = serial_write_read(('*IDN?' + '\r').encode('utf-8'))
    if 'SURUGA,DS1' in str(r_data):
        r_data = serial_write_read(('DS102VER?' + '\r').encode('utf-8'))
        lblFirmware['text'] = r_data
        r_data = serial_write_read(('CONTA?' + '\r').encode('utf-8'))
        # 軸数に応じてボタン有効化
        for btn in [btnAxisX, btnAxisY, btnAxisZ, btnAxisU, btnAxisV, btnAxisW]:
            btn['state'] = 'disabled'
        count = int(r_data)
        for i, btn in enumerate([btnAxisX, btnAxisY, btnAxisZ, btnAxisU, btnAxisV, btnAxisW], start=1):
            if i <= count:
                serial_write((f'AXI{i}:UNIT 0:SELSP 0' + '\r').encode('utf-8'))
                time.sleep(0.1)
                btn['state'] = 'normal'
        update_status()
    else:
        ser.close()
        lblState['text'] = '受信エラー発生'
        root.after(1, showerror(cmbCommPort.get() + 'にDS102/DS112コントローラが接続されていません'))

def disconnect_button_click(event):
    global ser
    if ser.is_open:
        ser.close()
    for btn in [btnAxisX, btnAxisY, btnAxisZ, btnAxisU, btnAxisV, btnAxisW]:
        btn['state'] = 'normal'
    lblState['text'] = '未接続'

def axis_select(ax, btn):
    global axisNo
    axisNo = str(ax)
    for b in [btnAxisX, btnAxisY, btnAxisZ, btnAxisU, btnAxisV, btnAxisW]:
        b.config(bg="SystemButtonFace")
    btn.config(bg="LightBlue")
    update_status()

def continue_mode():
    global mode
    mode = var.get()

def step_mode():
    global mode
    mode = var.get()

def org_mode():
    global mode
    mode = var.get()

def stop_button_click(event):
    serial_write(('STOP 0' + '\r').encode('utf-8'))

def ccw_button_press(event):
    global mode
    mode = var.get()
    move_stage('CCWJ')

def ccw_button_release(event):
    if mode == 0:
        serial_write(('STOP 0' + '\r').encode('utf-8'))

def cw_button_press(event):
    global mode
    mode = var.get()
    move_stage('CWJ')

def cw_button_release(event):
    if mode == 0:
        serial_write(('STOP 0' + '\r').encode('utf-8'))

def move_stage(jog_cmd=None):
    # 原点復帰を含む全駆動処理
    if mode == 2:
        # メモリスイッチ設定
        serial_write((f'AXI{axisNo}:MEMSW0 {cmbOrgMode.current()}' + '\r').encode('utf-8'))
        time.sleep(0.1)
        # 原点復帰コマンド
        serial_write((f'AXI{axisNo}:L0 {txtLSpeed.get()}:R0 {txtRate.get()}':S0 {txtSRate.get()}:F0 {txtSpeed.get()}:GO ORG' + '\r').encode('utf-8'))
    else:
        # CCWJ / CWJ / PULS 駆動
        base = f'AXI{axisNo}:L0 {txtLSpeed.get()}:R0 {txtRate.get()}:S0 {txtSRate.get()}:F0 {txtSpeed.get()}'
        if mode == 0 and jog_cmd:
            serial_write((base + f':GO {jog_cmd}' + '\r').encode('utf-8'))
        elif mode == 1:
            serial_write((base + f':PULS {txtStep.get()}:GO {mode == 1 and ("CCW" if jog_cmd is None else jog_cmd[:-1])}' + '\r').encode('utf-8'))
    threading.Timer(0.1, get_status).start()

def get_status():
    status = update_status()
    if status == 'run':
        threading.Timer(0.1, get_status).start()

def update_status():
    r_data = serial_write_read((f'AXI{axisNo}:SB3?' + '\r').encode('utf-8'))
    try:
        if not r_data or not int(r_data) & 0x01:
            lblState['text'] = '停止'
            return 'Stop'
    except ValueError:
        lblState['text'] = '停止'
        return 'Stop'
    r1 = int(serial_write_read((f'AXI{axisNo}:SB1?' + '\r').encode('utf-8')) or 0)
    if r1 & 0x40:
        lblState['text'] = '動作中'; status = 'run'
    elif r1 & 0x10:
        lblState['text'] = '原点検出'; status = 'Stop'
    else:
        lblState['text'] = '停止'; status = 'Stop'
    pos = serial_write_read((f'AXI{axisNo}:POS?' + '\r').encode('utf-8'))
    txtPosition.delete(0, tk.END); txtPosition.insert(tk.END, pos)
    return status

def serial_write(data):
    if ser.is_open:
        ser.write(data)

def serial_write_read(data):
    if ser.is_open:
        ser.write(data); time.sleep(0.1)
        return ser.read_until(b'\r')

def position_button_click(event):
    serial_write((f'AXI{axisNo}:POS {txtPosition.get()}' + '\r').encode('utf-8'))

def close_button_click(event):
    global ser
    if ser.is_open: ser.close()
    root.destroy()

def showerror(msg):
    messagebox.showerror('エラー', msg)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('DS102/DS112コントローラ・サンプルプログラム Ver.1.0.0')
    root.geometry('580x380')

    # ... (既存ウィジェット配置省略) ...

    # 駆動ボタン群
    frameRun = tk.Frame(frameDrive)
    frameRun.pack(fill=tk.BOTH, expand=True)
    btnCCW = tk.Button(frameRun, text='- (CCW)', width=10, height=2)
    btnCCW.bind('<ButtonPress-1>', ccw_button_press)
    btnCCW.bind('<ButtonRelease-1>', ccw_button_release)
    btnCCW.pack(side=tk.LEFT, padx=4, pady=0)
    btnStop = tk.Button(frameRun, text='停止', width=10, height=2)
    btnStop.bind('<Button-1>', stop_button_click)
    btnStop.pack(side=tk.LEFT, padx=4, pady=0)
    btnCW = tk.Button(frameRun, text='+ (CW)', width=10, height=2)
    btnCW.bind('<ButtonPress-1>', cw_button_press)
    btnCW.bind('<ButtonRelease-1>', cw_button_release)
    btnCW.pack(side=tk.LEFT, padx=4, pady=0)
    # ★ ホームボタン追加 ★
    btnHome = tk.Button(frameRun, text='ホーム', width=10, height=2)
    btnHome.bind('<Button-1>', home_button_click)
    btnHome.pack(side=tk.LEFT, padx=4, pady=0)

    root.mainloop()
