import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QWidget, QTextEdit

class JsonToDataFrameApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Extract ΔAbs and Wavelength to DataFrame")
        self.resize(800, 600)

        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # JSONファイルを読み込むボタン
        load_button = QPushButton("Load JSON File and Extract ΔAbs")
        load_button.clicked.connect(self.load_json_file)
        main_layout.addWidget(load_button)

        # データフレームを表示するテキストエディット
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        main_layout.addWidget(self.data_display)

        self.setCentralWidget(main_widget)

    def load_json_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "JSONファイルを読み込む", "", "JSON Files (*.json);;All Files (*)", options=options)

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # データを格納するための辞書
                all_data = {}
                wavelengths = None

                for pulse_name, pulse_data in data.items():
                    # 各データセットの波長とΔAbsを取得
                    x_dark_ref, y_dark_ref = self.parse_data(pulse_data['DARK_ref'])
                    _, y_dark_sig = self.parse_data(pulse_data['DARK_sig'])
                    _, y_ref = self.parse_data(pulse_data['ref'])
                    _, y_ref_p = self.parse_data(pulse_data['ref_p'])
                    _, y_sig = self.parse_data(pulse_data['sig'])
                    _, y_sig_p = self.parse_data(pulse_data['sig_p'])

                    # ΔAbsの計算
                    log_values = self.calculate_delta_abs(y_ref, y_ref_p, y_dark_ref, y_dark_sig, y_sig, y_sig_p)

                    # 波長を保持
                    if wavelengths is None:
                        wavelengths = x_dark_ref
                    # データセット名が数値だけの場合、6.666を掛ける
                    if pulse_name.isdigit():
                        pulse_name = str(float(pulse_name) * 6.666)
                        #有効数字小数点以下四捨五入
                        pulse_name = str(round(float(pulse_name), 2))
                    all_data[pulse_name] = log_values

                # データフレームに変換
                df = pd.DataFrame(all_data, index=wavelengths)
                df.index.name = 'Wavelength'
                self.display_dataframe(df)

                # ΔAbsデータをimshowで表示
                self.plot_delta_abs(df)

            except Exception as e:
                QMessageBox.warning(self, "エラー", f"ファイルの読み込み中にエラーが発生しました: {e}")

    def parse_data(self, data):
        """テキストデータを波長と強度のリストに変換します。"""
        x_values, y_values = [], []
        for line in data.splitlines():
            if line.strip():
                parts = line.split()
                try:
                    x_values.append(float(parts[0]))
                    y_values.append(float(parts[1]))
                except (ValueError, IndexError):
                    continue
        return x_values, y_values

    def calculate_delta_abs(self, y_ref, y_ref_p, y_dark_ref, y_dark_sig, y_sig, y_sig_p):
        """ΔAbsを計算する関数"""
        log_values = []
        for ref_p_real, sig_real, sig_p_real, ref_real in zip(y_ref_p, y_sig, y_sig_p, y_ref):
            if ref_real != 0 and sig_p_real != 0:
                log_value = np.log((ref_p_real * sig_real) / (sig_p_real * ref_real))
                log_values.append(log_value)
            else:
                log_values.append(np.nan)
        return log_values

    def display_dataframe(self, df):
        """データフレームをテキストエディットに表示"""
        self.data_display.clear()
        self.data_display.append(str(df))

    def plot_delta_abs(self, df):
        """ΔAbsデータをimshowで表示"""
        plt.figure(figsize=(10, 6))
        plt.imshow(df.T, aspect='auto', cmap='nipy_spectral', origin='lower', extent=[df.index.min(), df.index.max(), 0, df.shape[1]])
        plt.colorbar(label='ΔAbs')
        plt.xlabel('Wavelength')
        plt.ylabel('Time / fs')  # y軸ラベルを"Time / fs"に設定
        plt.title('ΔAbs Heatmap')
        plt.yticks(np.arange(df.shape[1]), df.columns)  # データセット名をy軸に表示
        plt.show()

# アプリケーションの起動
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JsonToDataFrameApp()
    window.show()
    sys.exit(app.exec_())
