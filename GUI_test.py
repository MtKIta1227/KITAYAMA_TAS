import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QFileDialog, QSizePolicy
import json

class DataGraphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("データグラフ作成")

        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # 各テキストボックスとラベルを作成
        self.text_boxes = {}
        for label in ['DARK_ref', 'DARK_sig', 'ref', 'sig', 'ref_p', 'sig_p']:
            h_layout = QHBoxLayout()
            lbl = QLabel(f'データ {label}:')
            h_layout.addWidget(lbl)
            text_box = QPlainTextEdit()
            text_box.setFixedSize(150, 80)  # テキストボックスのサイズを設定
            text_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            h_layout.addWidget(text_box)
            main_layout.addLayout(h_layout)
            self.text_boxes[label] = text_box

        # プロットボタン
        plot_button = QPushButton("グラフを描く")
        plot_button.clicked.connect(self.plot_graph)
        main_layout.addWidget(plot_button)

        # 保存ボタン
        save_button = QPushButton("データを保存")
        save_button.clicked.connect(self.save_data)
        main_layout.addWidget(save_button)

        # 読み込みボタン
        load_button = QPushButton("データを読み込む")
        load_button.clicked.connect(self.load_data)
        main_layout.addWidget(load_button)

        self.setCentralWidget(main_widget)

    def parse_data(self, data):
        x_values, y_values = [], []
        for line in data.splitlines():
            if line.strip():
                parts = line.split()
                x_values.append(float(parts[0]))  # 1列目の値を取得
                y_values.append(float(parts[1]))  # 2列目の値を取得
        return x_values, y_values

    def plot_graph(self):
        # 各テキストボックスからデータを取得
        x_dark_ref, y_dark_ref = self.parse_data(self.text_boxes['DARK_ref'].toPlainText())
        _, y_dark_sig = self.parse_data(self.text_boxes['DARK_sig'].toPlainText())
        _, y_ref = self.parse_data(self.text_boxes['ref'].toPlainText())
        _, y_sig = self.parse_data(self.text_boxes['sig'].toPlainText())
        _, y_ref_p = self.parse_data(self.text_boxes['ref_p'].toPlainText())
        _, y_sig_p = self.parse_data(self.text_boxes['sig_p'].toPlainText())

        # 計算
        results = {
            'ref - DARK_ref': [ref - dark_ref for dark_ref, ref in zip(y_dark_ref, y_ref)],
            'sig - DARK_sig': [sig - dark_sig for dark_sig, sig in zip(y_dark_sig, y_sig)],
            'ref_p - DARK_ref': [ref_p - dark_ref for dark_ref, ref_p in zip(y_dark_ref, y_ref_p)],
            'sig_p - DARK_sig': [sig_p - dark_sig for dark_sig, sig_p in zip(y_dark_sig, y_sig_p)],
        }

        # 新しい計算式 LOG((ref_p - DARK_ref) * (sig - DARK_sig) / (sig_p - DARK_sig) / (ref - DARK_ref))
        log_values = []
        for ref_p_dark, sig_dark, sig_p_dark, ref_dark in zip(
                results['ref_p - DARK_ref'], results['sig - DARK_sig'], results['sig_p - DARK_sig'], results['ref - DARK_ref']):
            if ref_dark != 0 and sig_p_dark != 0:  # ゼロ除算を避ける
                log_value = np.log((ref_p_dark * sig_dark) / (sig_p_dark * ref_dark))
                log_values.append(log_value)
            else:
                log_values.append(np.nan)  # ゼロ除算が発生した場合はNaNを追加

        # グラフの描画
        fig, axs = plt.subplots(3, 1, figsize=(10, 15))

        # ref と ref_p のグラフ
        axs[0].plot(x_dark_ref, results['ref - DARK_ref'], color='black', linestyle='-', label='ref - DARK_ref')
        axs[0].plot(x_dark_ref, results['ref_p - DARK_ref'], color='gray', linestyle='--', label='ref_p - DARK_ref')
        axs[0].set_title('ref と ref_p の計算結果グラフ')
        axs[0].set_xlabel('DARK_ref 1列目 (X軸)')
        axs[0].set_ylabel('値の差')
        axs[0].legend()
        axs[0].grid()

        # sig と sig_p のグラフ
        axs[1].plot(x_dark_ref, results['sig - DARK_sig'], color='black', linestyle='-', label='sig - DARK_sig')
        axs[1].plot(x_dark_ref, results['sig_p - DARK_sig'], color='gray', linestyle='--', label='sig_p - DARK_sig')
        axs[1].set_title('sig と sig_p の計算結果グラフ')
        axs[1].set_xlabel('DARK_ref 1列目 (X軸)')
        axs[1].set_ylabel('値の差')
        axs[1].legend()
        axs[1].grid()

        # LOG計算結果グラフ
        axs[2].plot(x_dark_ref, log_values, color='black', linestyle='-', marker='x', label='LOG((ref_p - DARK_ref) * (sig - DARK_sig) / (sig_p - DARK_sig) / (ref - DARK_ref))')
        axs[2].set_title('LOG計算結果グラフ')
        axs[2].set_xlabel('DARK_ref 1列目 (X軸)')
        axs[2].set_ylabel('LOG値')
        axs[2].legend()
        axs[2].grid()

        plt.tight_layout()
        plt.show()

    def save_data(self):
        # 保存用の辞書を作成
        data = {label: self.text_boxes[label].toPlainText() for label in self.text_boxes}
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "データを保存", "", "JSON Files (*.json);;All Files (*)", options=options)
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(data, f)
            print("データが保存されました:", file_path)

    def load_data(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "データを読み込む", "", "JSON Files (*.json);;All Files (*)", options=options)
        
        if file_path:
            with open(file_path, 'r') as f:
                data = json.load(f)
            for label, content in data.items():
                if label in self.text_boxes:
                    self.text_boxes[label].setPlainText(content)
            print("データが読み込まれました:", file_path)

# アプリケーションの起動
app = QApplication(sys.argv)
window = DataGraphApp()
window.show()
sys.exit(app.exec_())
