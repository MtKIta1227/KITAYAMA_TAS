import pyvisa
import tkinter as tk
from tkinter import messagebox

# グローバル変数
rm = pyvisa.ResourceManager()
instrument = None

class DeviceControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("装置接続")
        self.root.geometry("400x400")
        
        self._initialize_ui()
        self.disable_controls()

    def _initialize_ui(self):
        # 状態ラベル
        self.lbl_state = tk.Label(self.root, text="未接続", font=("Arial", 10))
        self.lbl_state.pack(pady=5)

        # 接続・切断ボタン
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        self.btn_connect = tk.Button(button_frame, text="接続", command=self.connect_button_click, width=10)
        self.btn_connect.pack(side=tk.LEFT, padx=5)
        self.btn_disconnect = tk.Button(button_frame, text="切断", command=self.disconnect_button_click, width=10)
        self.btn_disconnect.pack(side=tk.LEFT, padx=5)

        # 駆動速度
        tk.Label(self.root, text="速度 (pps)：").pack(pady=3)
        self.txt_speed = tk.Entry(self.root, width=10, state=tk.DISABLED)
        self.txt_speed.pack(pady=3)
        self.txt_speed.bind("<KeyRelease>", self.on_value_change)

        # 現在位置
        tk.Label(self.root, text="現在位置：").pack(pady=3)
        self.txt_current_position = tk.Entry(self.root, width=10, state=tk.DISABLED)
        self.txt_current_position.pack(pady=3)
        self.btn_set_position = tk.Button(self.root, text="位置設定", command=self.set_position, width=10, state=tk.DISABLED)
        self.btn_set_position.pack(pady=3)

        # パルス数
        tk.Label(self.root, text="パルス数：").pack(pady=3)
        self.txt_step = tk.Entry(self.root, width=10, state=tk.DISABLED)
        self.txt_step.pack(pady=3)
        self.txt_step.bind("<KeyRelease>", self.on_step_change)  # 入力変更時の検証

        # ステップ駆動
        self.btn_step_drive = tk.Button(self.root, text="ステップ駆動", command=self.step_drive, width=10, state=tk.DISABLED)
        self.btn_step_drive.pack(pady=3)

        # 駆動方向
        direction_frame = tk.Frame(self.root)
        direction_frame.pack(pady=5)
        self.direction = tk.StringVar(value="CCW")
        tk.Radiobutton(direction_frame, text="CCW", variable=self.direction, value="CCW", command=self.update_direction).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(direction_frame, text="CW", variable=self.direction, value="CW", command=self.update_direction).pack(side=tk.LEFT, padx=5)

    # 接続ボタン処理
    def connect_button_click(self):
        global instrument
        try:
            instrument = rm.open_resource("GPIB1::7::INSTR")
            instrument.timeout = 2000
            r_data = instrument.query("*IDN?")
            self.lbl_state["text"] = f"接続成功: {r_data}"
            self.enable_controls()
            self.update_position()
        except Exception as e:
            self.lbl_state["text"] = "接続エラー"
            messagebox.showerror("エラー", str(e))

    # 切断ボタン処理
    def disconnect_button_click(self):
        global instrument
        if instrument:
            instrument.close()
            instrument = None
            self.lbl_state["text"] = "未接続"
            self.disable_controls()

    # 現在位置の更新
    def update_position(self):
        if instrument is None:
            return
        try:
            r_data = instrument.query("AXI1:POS?")
            self.txt_current_position.delete(0, tk.END)
            self.txt_current_position.insert(tk.END, r_data)
        except Exception as e:
            self.lbl_state["text"] = "位置取得エラー"
            messagebox.showerror("エラー", f"位置取得エラー: {str(e)}")

    # ステップ駆動処理
    def step_drive(self):
        if instrument is None:
            return
        try:
            speed = float(self.txt_speed.get()) if self.txt_speed.get() else 1000  # デフォルト: 1000 pps
            pulses = int(self.txt_step.get()) if self.txt_step.get() else 10       # デフォルト: 10 パルス
            direction_value = self.direction.get()
            command = f"AXI1:L0 {speed}:PULS {pulses}:GO {direction_value}"
            instrument.write(command)
            self.update_position()
        except ValueError:
            messagebox.showerror("エラー", "速度とパルス数は有効な数値でなければなりません")
        except Exception as e:
            messagebox.showerror("エラー", f"ステップ駆動エラー:\n{str(e)}")

    # 位置設定処理
    def set_position(self):
        if instrument is None:
            return
        new_position = self.txt_current_position.get()
        try:
            float(new_position)
            instrument.write(f"AXI1:POS {new_position}")
        except ValueError:
            messagebox.showerror("エラー", "位置は数値でなければなりません")

    # 値変更時の処理
    def on_value_change(self, event=None):
        try:
            float(self.txt_speed.get())
            self.lbl_state["text"] = "速度が正常です"
        except ValueError:
            self.lbl_state["text"] = "速度は数値である必要があります"

    # パルス数変更時の処理
    def on_step_change(self, event=None):
        try:
            int(self.txt_step.get())
            self.lbl_state["text"] = f"パルス数更新: {self.txt_step.get()}"
        except ValueError:
            self.lbl_state["text"] = "パルス数は整数である必要があります"

    # 方向変更時の処理
    def update_direction(self):
        self.lbl_state["text"] = f"方向変更: {self.direction.get()}"

    # コントロールの有効化
    def enable_controls(self):
        self.txt_speed.config(state="normal")
        self.txt_step.config(state="normal")
        self.txt_current_position.config(state="normal")
        self.btn_set_position.config(state="normal")
        self.btn_step_drive.config(state="normal")

    # コントロールの無効化
    def disable_controls(self):
        self.txt_speed.config(state="disabled")
        self.txt_step.config(state="disabled")
        self.txt_current_position.config(state="disabled")
        self.btn_set_position.config(state="disabled")
        self.btn_step_drive.config(state="disabled")

# メイン処理
if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceControlApp(root)
    root.mainloop()
