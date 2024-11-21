import pyvisa
import tkinter as tk
from tkinter import messagebox


class DeviceControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("装置接続")
        self.root.geometry("300x400")

        # VISAリソースマネージャー
        self.rm = pyvisa.ResourceManager()
        self.instrument = None

        # UIの初期化
        self._initialize_ui()

    def _initialize_ui(self):
        # 状態表示ラベル
        self.lbl_state = tk.Label(self.root, text="未接続", font=("Arial", 12))
        self.lbl_state.pack(pady=5)

        # 接続・切断ボタン
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        self.btn_connect = tk.Button(button_frame, text="接続", command=self.connect_device, width=10)
        self.btn_connect.pack(side=tk.LEFT, padx=5)

        self.btn_disconnect = tk.Button(button_frame, text="切断", command=self.disconnect_device, width=10, state=tk.DISABLED)
        self.btn_disconnect.pack(side=tk.LEFT, padx=5)

        # 駆動速度設定
        tk.Label(self.root, text="速度 (pps)：").pack(pady=3)
        self.txt_speed = tk.Entry(self.root, width=10, state=tk.DISABLED)
        self.txt_speed.pack(pady=3)
        self.txt_speed.bind("<KeyRelease>", self.validate_inputs)

        # 現在位置
        tk.Label(self.root, text="現在位置：").pack(pady=3)
        self.txt_current_position = tk.Entry(self.root, width=10, state=tk.DISABLED)
        self.txt_current_position.pack(pady=3)

        self.btn_set_position = tk.Button(self.root, text="位置設定", command=self.set_position, width=10, state=tk.DISABLED)
        self.btn_set_position.pack(pady=3)

        # ステップ駆動設定
        tk.Label(self.root, text="パルス数：").pack(pady=3)
        self.txt_step = tk.Entry(self.root, width=10, state=tk.DISABLED)
        self.txt_step.pack(pady=3)
        self.txt_step.bind("<KeyRelease>", self.validate_inputs)

        self.btn_step_drive = tk.Button(self.root, text="ステップ駆動", command=self.step_drive, width=10, state=tk.DISABLED)
        self.btn_step_drive.pack(pady=3)

        # 駆動方向
        direction_frame = tk.Frame(self.root)
        direction_frame.pack(pady=5)

        self.direction = tk.StringVar(value="CCW")
        tk.Radiobutton(direction_frame, text="CCW", variable=self.direction, value="CCW", command=self.update_direction).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(direction_frame, text="CW", variable=self.direction, value="CW", command=self.update_direction).pack(side=tk.LEFT, padx=5)

    def connect_device(self):
        """デバイスに接続します。"""
        try:
            self.instrument = self.rm.open_resource("GPIB1::7::INSTR")
            self.instrument.timeout = 2000
            r_data = self.instrument.query("*IDN?")
            self.lbl_state["text"] = f"接続成功: {r_data.strip()}"
            self._enable_controls()
            self.update_position()
        except Exception as e:
            self.lbl_state["text"] = "接続エラー"
            messagebox.showerror("エラー", f"デバイス接続エラー:\n{str(e)}")

    def disconnect_device(self):
        """デバイスから切断します。"""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        self.lbl_state["text"] = "未接続"
        self._disable_controls()

    def update_position(self):
        """現在位置を更新します。"""
        if not self.instrument:
            return
        try:
            r_data = self.instrument.query("AXI1:POS?")
            self.txt_current_position.delete(0, tk.END)
            self.txt_current_position.insert(tk.END, r_data.strip())
        except Exception as e:
            self.lbl_state["text"] = "位置取得エラー"
            messagebox.showerror("エラー", f"位置取得エラー:\n{str(e)}")

    def step_drive(self):
        """ステップ駆動を行います。"""
        if not self.instrument:
            return
        try:
            speed = float(self.txt_speed.get())
            pulses = int(self.txt_step.get())
            direction_value = self.direction.get()
            command = f"AXI1:L0 {speed}:PULS {pulses}:GO {direction_value}"
            self.instrument.write(command)
            self.update_position()
        except ValueError:
            messagebox.showerror("エラー", "速度とパルス数は有効な数値でなければなりません")
        except Exception as e:
            messagebox.showerror("エラー", f"ステップ駆動エラー:\n{str(e)}")

    def set_position(self):
        """現在位置を設定します。"""
        if not self.instrument:
            return
        try:
            new_position = float(self.txt_current_position.get())
            self.instrument.write(f"AXI1:POS {new_position}")
        except ValueError:
            messagebox.showerror("エラー", "位置は有効な数値でなければなりません")
        except Exception as e:
            messagebox.showerror("エラー", f"位置設定エラー:\n{str(e)}")

    def validate_inputs(self, event=None):
        """入力値を検証します。"""
        try:
            float(self.txt_speed.get())
            int(self.txt_step.get())
            self.lbl_state["text"] = "入力値は正常です"
        except ValueError:
            self.lbl_state["text"] = "入力値が無効です"

    def update_direction(self):
        """方向の変更時に状態を更新します。"""
        self.lbl_state["text"] = f"方向変更: {self.direction.get()}"

    def _enable_controls(self):
        """テキストボックスやボタンを有効化します。"""
        for widget in [self.txt_speed, self.txt_step, self.txt_current_position, self.btn_set_position, self.btn_step_drive]:
            widget.config(state="normal")
        self.btn_disconnect.config(state="normal")

    def _disable_controls(self):
        """テキストボックスやボタンを無効化します。"""
        for widget in [self.txt_speed, self.txt_step, self.txt_current_position, self.btn_set_position, self.btn_step_drive]:
            widget.config(state="disabled")
        self.btn_disconnect.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceControllerApp(root)
    root.mainloop()
