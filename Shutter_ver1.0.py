import serial
import serial.tools.list_ports
import time
import tkinter as tk
from tkinter import messagebox, StringVar, ttk

def list_serial_ports():
    """接続されているシリアルポートのリストを取得します。"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def send_command(arduino, steps, delay_time, direction):
    command = f"{steps},{delay_time},{direction}\n"
    arduino.write(command.encode())
    time.sleep(delay_time)

def operate_motor(arduino, steps, direction):
    try:
        send_command(arduino, steps, 2, direction)
    except Exception as e:
        messagebox.showerror("エラー", f"モーターの操作中にエラーが発生しました: {str(e)}")

def connect_serial_port(port):
    """Arduinoに接続します。"""
    return serial.Serial(port, 9600, timeout=1)

def on_run_motor():
    try:
        steps = int(steps_entry.get())  # ステップ数を整数として取得
        direction = direction_var.get()
        operate_motor(arduino, steps, direction)
    except ValueError:
        messagebox.showerror("エラー", "モーターのステップ数は整数で入力してください。")

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

# モーターの入力フィールド
tk.Label(root, text="モーター ステップ数:").grid(row=1, column=0)
steps_entry = tk.Entry(root)  # ステップ数入力用エントリ
steps_entry.grid(row=1, column=1)

direction_var = StringVar(value="1")  # 初期値をCWに設定
tk.Label(root, text="モーター 方向:").grid(row=2, column=0)
tk.Radiobutton(root, text="CW", variable=direction_var, value="1").grid(row=2, column=1)
tk.Radiobutton(root, text="CCW", variable=direction_var, value="-1").grid(row=2, column=2)

run_button = tk.Button(root, text="Run", command=on_run_motor)
run_button.grid(row=1, column=2)

root.mainloop()

# プログラム終了時にシリアルポートを閉じる
if 'arduino' in globals():
    arduino.close()
