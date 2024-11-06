import serial
import serial.tools.list_ports
import time
import tkinter as tk
from tkinter import messagebox, StringVar, ttk

# 1ステップあたりの角度（360°/512 step）
STEP_ANGLE = 360 / 512

def angle_to_steps(angle):
    return int(angle / STEP_ANGLE)

def list_serial_ports():
    """接続されているシリアルポートのリストを取得します。"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def send_command(arduino, motor_id, angle, delay_time, direction):
    steps = angle_to_steps(angle)
    command = f"{motor_id},{steps},{delay_time},{direction}\n"
    arduino.write(command.encode())
    time.sleep(delay_time)

def operate_motor(arduino, motor_id, angle, direction):
    try:
        send_command(arduino, motor_id, angle, 2, direction)
    except Exception as e:
        messagebox.showerror("エラー", f"モーター{motor_id}の操作中にエラーが発生しました: {str(e)}")

def connect_serial_port(port):
    """Arduinoに接続します。"""
    return serial.Serial(port, 9600, timeout=1)

def on_run_motor1():
    try:
        angle = float(angle1_entry.get())
        direction = direction1_var.get()
        operate_motor(arduino, 1, angle, direction)
    except ValueError:
        messagebox.showerror("エラー", "モーター1の角度は数値で入力してください。")

def on_run_motor2():
    try:
        angle = float(angle2_entry.get())
        direction = direction2_var.get()
        operate_motor(arduino, 2, angle, direction)
    except ValueError:
        messagebox.showerror("エラー", "モーター2の角度は数値で入力してください。")

def connect_to_selected_port():
    global arduino
    try:
        if 'arduino' in globals():
            arduino.close()  # 以前の接続を閉じる
        selected_port = port_var.get()  # ドロップダウンからポートを取得
        arduino = connect_serial_port(selected_port)
    except Exception as e:
        messagebox.showerror("接続エラー", str(e))

# GUIの設定
root = tk.Tk()
root.title("Shutter Control")

# シリアルポートのリストを取得
ports = list_serial_ports()
selected_port = ports[0] if ports else None

# シリアルポートの選択
port_var = StringVar(value=selected_port)
port_label = tk.Label(root, text="シリアルポートを選択:")
port_label.grid(row=0, column=0)

port_dropdown = ttk.Combobox(root, textvariable=port_var, values=ports)
port_dropdown.grid(row=0, column=1)

connect_button = tk.Button(root, text="接続", command=connect_to_selected_port)
connect_button.grid(row=0, column=2)

# モーター1の入力フィールド
tk.Label(root, text="モーター1 角度:").grid(row=1, column=0)
angle1_entry = tk.Entry(root)
angle1_entry.grid(row=1, column=1)

direction1_var = StringVar(value="0")  # 初期値を0に変更
tk.Label(root, text="モーター1 方向:").grid(row=2, column=0)
tk.Radiobutton(root, text="CW", variable=direction1_var, value="1").grid(row=2, column=1)
tk.Radiobutton(root, text="CCW", variable=direction1_var, value="0").grid(row=2, column=2)

run_button1 = tk.Button(root, text="Run", command=on_run_motor1)
run_button1.grid(row=1, column=2)  # Runボタンを角度入力欄の右側に配置

# モーター2の入力フィールド
tk.Label(root, text="モーター2 角度:").grid(row=3, column=0)
angle2_entry = tk.Entry(root)
angle2_entry.grid(row=3, column=1)

direction2_var = StringVar(value="0")  # 初期値を0に変更
tk.Label(root, text="モーター2 方向:").grid(row=4, column=0)
tk.Radiobutton(root, text="CW", variable=direction2_var, value="1").grid(row=4, column=1)
tk.Radiobutton(root, text="CCW", variable=direction2_var, value="0").grid(row=4, column=2)

run_button2 = tk.Button(root, text="Run", command=on_run_motor2)
run_button2.grid(row=3, column=2)  # Runボタンを角度入力欄の右側に配置

root.mainloop()

# プログラム終了時にシリアルポートを閉じる
if 'arduino' in globals():
    arduino.close()
