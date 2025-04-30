"""delay_controller_gui_suruga_v3.py
Delay controller GUI laid out to match the reference screenshot (axis buttons row, four option panes, and close button).

Author: ChatGPT, 2025‑04‑30 (rev‑1)
"""

import pyvisa
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

rm = pyvisa.ResourceManager()
instrument = None


class DelayControllerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Delay Controller – Suruga DS102")
        self.root.geometry("660x400")
        self.root.minsize(640, 380)

        # ──────────────── State variables *before* building frames ──────────────── #
        # （build メソッド内で参照するため，先に定義しておく）
        self.direction = tk.StringVar(value="CCW")
        self.drive_mode = tk.StringVar(value="cont")

        # ───────────────────────── Frame Layout ────────────────────────── #
        #   row‑0  : axis buttons + DS102 label + close button
        #   row‑1  : parameter frames (drive‑speed, drive‑mode | comm, drive)
        #
        #   column‑0 ← left half              | column‑1 ← right half
        #
        self.root.columnconfigure(0, weight=1, minsize=320)
        self.root.columnconfigure(1, weight=1, minsize=320)

        # Build UI blocks – order no longer matters for variable availability
        self._build_axis_header()          # row‑0
        self._build_drive_speed_frame()    # row‑1 / col‑0 (top)
        self._build_drive_mode_frame()     # row‑2 / col‑0 (bottom)
        self._build_comm_frame()           # row‑1 / col‑1 (top)
        self._build_drive_frame()          # row‑2 / col‑1 (bottom)

        # Disable controls until connection is established
        self._set_drive_state("disabled")

    # ───────────────────────── Axis Header Row ────────────────────────── #
    def _build_axis_header(self):
        header = tk.Frame(self.root)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(4, 2), padx=5)
        header.columnconfigure(tuple(range(10)), weight=1)

        # axis buttons – square 25px wide
        for i, axis in enumerate(["X", "Y", "Z", "U", "V", "W"]):
            tk.Button(header, text=axis, width=3).grid(row=0, column=i, padx=1)

        # DS102 label
        tk.Label(header, text="DS102", font=("Arial", 10, "bold")).grid(row=0, column=6, padx=10)

        # spacer column (7)
        header.columnconfigure(7, weight=3)

        # close button
        tk.Button(header, text="閉じる", command=self.root.destroy, width=8).grid(row=0, column=9, padx=(0, 4))

    # ───────────────────────── Drive Speed Settings ────────────────────── #
    def _build_drive_speed_frame(self):
        self.frame_speed = tk.LabelFrame(self.root, text="駆動速度設定")
        self.frame_speed.grid(row=1, column=0, sticky="nsew", padx=5, pady=4)
        self.frame_speed.columnconfigure(1, weight=1)

        labels = [
            ("初速度(L)：", "100", "pps"),
            ("加減速レート(R)：", "100", "ms"),
            ("S字レート(S)：", "100", "%"),
            ("駆動速度(F)：", "1000", "pps"),
        ]
        self.ent_init_speed, self.ent_acc_rate, self.ent_s_rate, self.ent_drive_speed = (None,)*4
        entries = []
        for r, (lbl, default, unit) in enumerate(labels):
            tk.Label(self.frame_speed, text=lbl, anchor="w", width=14).grid(row=r, column=0, sticky="w", padx=3, pady=1)
            ent = tk.Entry(self.frame_speed, width=12)
            ent.insert(tk.END, default)
            ent.grid(row=r, column=1, sticky="w", padx=3, pady=1)
            tk.Label(self.frame_speed, text=unit).grid(row=r, column=2, sticky="w", padx=3)
            entries.append(ent)
        (self.ent_init_speed, self.ent_acc_rate, self.ent_s_rate, self.ent_drive_speed) = entries

    # ───────────────────────── Drive Mode Selection ────────────────────── #
    def _build_drive_mode_frame(self):
        self.frame_mode = tk.LabelFrame(self.root, text="駆動方法選択")
        self.frame_mode.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 4))
        self.frame_mode.columnconfigure(1, weight=1)

        # continuous drive radio
        tk.Radiobutton(
            self.frame_mode, text="連続駆動", variable=self.drive_mode, value="cont"
        ).grid(row=0, column=0, sticky="w", padx=6, pady=2)

        # step drive radio + entry
        tk.Radiobutton(
            self.frame_mode, text="ステップ駆動", variable=self.drive_mode, value="step"
        ).grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self.ent_step_pulses = tk.Entry(self.frame_mode, width=8)
        self.ent_step_pulses.insert(tk.END, "1000")
        self.ent_step_pulses.grid(row=1, column=1, sticky="w", padx=2)
        tk.Label(self.frame_mode, text="Pulse").grid(row=1, column=2, sticky="w")

        # home (origin return)
        tk.Radiobutton(
            self.frame_mode, text="原点復帰", variable=self.drive_mode, value="home"
        ).grid(row=2, column=0, sticky="w", padx=6, pady=2)
        self.cmb_home = ttk.Combobox(
            self.frame_mode,
            values=["ORG 0", "ORG 1", "ORG 2"],
            width=7,
            state="readonly",
        )
        self.cmb_home.current(0)
        self.cmb_home.grid(row=2, column=1, sticky="w", padx=2)

    # ───────────────────────── Communication Frame ─────────────────────── #
    def _build_comm_frame(self):
        self.frame_comm = tk.LabelFrame(self.root, text="通信設定")
        self.frame_comm.grid(row=1, column=1, sticky="nsew", padx=5, pady=4)
        self.frame_comm.columnconfigure(1, weight=1)

        # port
        tk.Label(self.frame_comm, text="通信ポート：").grid(row=0, column=0, sticky="e", padx=3, pady=2)
        self.cmb_res = ttk.Combobox(self.frame_comm, values=self._list_resources(), width=12, state="readonly")
        if self.cmb_res["values"]:
            self.cmb_res.current(0)
        self.cmb_res.grid(row=0, column=1, sticky="w", padx=3)
        tk.Button(self.frame_comm, text="接続", command=self.connect, width=8).grid(row=0, column=2, padx=4)

        # baud rate
        tk.Label(self.frame_comm, text="ボーレート：").grid(row=1, column=0, sticky="e", padx=3, pady=2)
        self.cmb_baud = ttk.Combobox(self.frame_comm, values=["9600", "19200", "38400", "57600", "115200"], width=12, state="readonly")
        self.cmb_baud.set("38400")
        self.cmb_baud.grid(row=1, column=1, sticky="w", padx=3)
        tk.Button(self.frame_comm, text="切断", command=self.disconnect, width=8).grid(row=1, column=2, padx=4)

    # ───────────────────────── Drive / Jog Frame ──────────────────────── #
    def _build_drive_frame(self):
        self.frame_drive = tk.LabelFrame(self.root, text="駆動")
        self.frame_drive.grid(row=2, column=1, sticky="nsew", padx=5, pady=(0, 4))
        self.frame_drive.columnconfigure((0, 1, 2), weight=1)

        # position row
        tk.Label(self.frame_drive, text="ポジション：").grid(row=0, column=0, sticky="e", padx=3, pady=2)
        self.ent_position = tk.Entry(self.frame_drive, width=10)
        self.ent_position.insert(tk.END, "0")
        self.ent_position.grid(row=0, column=1, sticky="w", padx=3)
        tk.Button(self.frame_drive, text="ポジション設定", command=self.set_position, width=12).grid(row=0, column=2, padx=3)

        # status row
        tk.Label(self.frame_drive, text="ステータス：").grid(row=1, column=0, sticky="e", padx=3, pady=2)
        self.lbl_state = tk.Label(self.frame_drive, text="未接続")
        self.lbl_state.grid(row=1, column=1, columnspan=2, sticky="w", padx=3)

        # jog buttons
        self.btn_ccw = tk.Button(self.frame_drive, text="- (CCW)", width=10, command=lambda: self.jog("CCW"))
        self.btn_ccw.grid(row=2, column=0, padx=4, pady=4)
        self.btn_stop = tk.Button(self.frame_drive, text="停止", width=10, command=self.stop)
        self.btn_stop.grid(row=2, column=1, padx=4, pady=4)
        self.btn_cw = tk.Button(self.frame_drive, text="+ (CW)", width=10, command=lambda: self.jog("CW"))
        self.btn_cw.grid(row=2, column=2, padx=4, pady=4)

    # ───────────────────────── Helper Methods ──────────────────────────── #
    def _list_resources(self):
        try:
            return rm.list_resources()
        except Exception:
            return ()

    def _set_drive_state(self, state):
        widgets = [
            self.ent_init_speed,
            self.ent_acc_rate,
            self.ent_s_rate,
            self.ent_drive_speed,
            self.ent_step_pulses,
            self.ent_position,
            self.btn_ccw,
            self.btn_cw,
            self.btn_stop,
        ]
        for w in widgets:
            w.config(state=state)

    # ───────────────────────── VISA Connection ─────────────────────────── #
    def connect(self):
        global instrument
        if instrument:
            self.disconnect()
        res_name = self.cmb_res.get()
        if not res_name:
            messagebox.showwarning("Warning", "通信ポートが選択されていません")
            return
        try:
            instrument = rm.open_resource(res_name)
            # Note: DS102 uses fixed baud 38400; ensure timeout
            instrument.baud_rate = int(self.cmb_baud.get())
            instrument.timeout = 2000
            idn = instrument.query("*IDN?").strip()
            self.lbl_state["text"] = idn if idn else "接続成功"
            self._set_drive_state("normal")
            self.update_position()
        except Exception as e:
            instrument = None
            self.lbl_state["text"] = "接続エラー"
            messagebox.showerror("接続エラー", str(e))

    def disconnect(self):
        global instrument
        if instrument:
            try:
                instrument.close()
            except Exception:
                pass
        instrument = None
        self.lbl_state["text"] = "未接続"
        self._set_drive_state("disabled")

    # ───────────────────────── Motion Commands ────────────────────────── #
    def _build_speed_command(self):
        """Create the command segment containing L / R / S / F parameters."""
        try:
            l = float(self.ent_init_speed.get())
            r = float(self.ent_acc_rate.get())
            s = float(self.ent_s_rate.get())
            f = float(self.ent_drive_speed.get())
        except ValueError:
            raise ValueError("速度パラメータは数値で入力してください")
        return f"L{l} R{r} S{s} F{f}"

    def execute_drive(self):
        if instrument is None:
            return
        try:
            speed_cmd = self._build_speed_command()
        except ValueError as err:
            messagebox.showerror("入力エラー", str(err))
            return

        mode = self.drive_mode.get()
        if mode == "cont":
            cmd = f"AXI1:{speed_cmd}:GO {self.direction.get()}"  # continuous
        elif mode == "step":
            try:
                pulses = int(self.ent_step_pulses.get())
            except ValueError:
                messagebox.showerror("入力エラー", "Pulse 数は整数で入力してください")
                return
            cmd = f"AXI1:{speed_cmd}:PULS {pulses}:GO {self.direction.get()}"
        else:  # home
            origin = self.cmb_home.get().split()[1]
            cmd = f"AXI1:ORG {origin}"
        try:
            instrument.write(cmd)
            self.lbl_state["text"] = "動作中"
            self.update_position()
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def jog(self, dir_):
        self.direction.set(dir_)
        self.execute_drive()

    def stop(self):
        if instrument is None:
            return
        try:
            instrument.write("STOP 0")
            self.lbl_state["text"] = "停止"
            self.update_position()
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    # ───────────────────────── Position Helpers ───────────────────────── #
    def update_position(self):
        if instrument is None:
            return
        try:
            pos = instrument.query("AXI1:POS?").strip()
            self.ent_position.delete(0, tk.END)
            self.ent_position.insert(0, pos)
        except Exception as e:
            self.lbl_state["text"] = "位置取得エラー"
            messagebox.showerror("エラー", str(e))

    def set_position(self):
        if instrument is None:
            return
        new_pos = self.ent_position.get()
        try:
            float(new_pos)
        except ValueError:
            messagebox.showerror("入力エラー", "位置は数値で入力してください")
            return
        try:
            instrument.write(f"AXI1:POS {new_pos}")
        except Exception as e:
            messagebox.showerror("エラー", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = DelayControllerGUI(root)
    root.mainloop()
