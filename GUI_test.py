import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QFileDialog, QSizePolicy, QToolBar
import json

class DataGraphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("データグラフ作成")

        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QHBoxLayout()  # 横に並べるレイアウト
        main_widget.setLayout(main_layout)

        # ツールバーの設定
        self.toolbar = QToolBar("ツールバー")
        self.addToolBar(self.toolbar)

        # ツールバーにボタンを追加
        plot_button = QPushButton("グラフを描く")
        plot_button.clicked.connect(self.plot_graph)
        self.toolbar.addWidget(plot_button)

        save_button = QPushButton("データを保存")
        save_button.clicked.connect(self.save_data)
        self.toolbar.addWidget(save_button)

        load_button = QPushButton("データを読み込む")
        load_button.clicked.connect(self.load_data)
        self.toolbar.addWidget(load_button)

        # 左側のレイアウト (ダークデータ)
        dark_layout = QVBoxLayout()
        self.text_boxes = {}
        self.text_boxes['DARK_ref'] = self.create_text_box('DARK_ref', dark_layout)
        self.text_boxes['DARK_sig'] = self.create_text_box('DARK_sig', dark_layout)

        # 右側のレイアウト (残りのデータ)
        remaining_layout = QVBoxLayout()
        self.text_boxes['ref'] = self.create_text_box('ref', remaining_layout)
        self.text_boxes['sig'] = self.create_text_box('sig', remaining_layout)
        self.text_boxes['ref_p'] = self.create_text_box('ref_p', remaining_layout)
        self.text_boxes['sig_p'] = self.create_text_box('sig_p', remaining_layout)

        # 左側と右側のレイアウトをメインレイアウトに追加
        main_layout.addLayout(dark_layout, 1)  # 左側を柔軟に
        main_layout.addLayout(remaining_layout, 1)  # 右側を柔軟に

        self.setCentralWidget(main_widget)

    def create_text_box(self, label, layout):
        h_layout = QHBoxLayout()
        lbl = QLabel(f'データ {label}:')
        h_layout.addWidget(lbl)
        text_box = QPlainTextEdit()
        text_box.setFixedSize(150, 80)  # テキストボックスのサイズを設定
        text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 柔軟にサイズを調整
        h_layout.addWidget(text_box)
        layout.addLayout(h_layout)
        return text_box

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

        # LOG計算結果グラフを別ウィンドウで表示
        log_fig = plt.figure(figsize=(6, 4))  # 小さめのウィンドウサイズ
        plt.plot(x_dark_ref, log_values, color='black', linestyle='-',
                 label='LOG((ref_p - DARK_ref) * (sig - DARK_sig) / (sig_p - DARK_sig) / (ref - DARK_ref))')
        plt.axhline(0.01, color='red', linestyle='--')  # y=0.01の赤い横線
        plt.axhline(-0.01, color='red', linestyle='--')  # y=-0.01の赤い横線
        plt.title('LOG計算結果グラフ')
        plt.xlabel('DARK_ref 1列目 (X軸)')
        plt.ylabel('LOG値')
        plt.legend()
        plt.grid()
        plt.get_current_fig_manager().window.setGeometry(100, 100, 600, 400)  # ウィンドウの位置とサイズを設定
        plt.show()

        # ref と ref_p のグラフと sig と sig_p のグラフを同じウィンドウで表示
        combined_fig = plt.figure(figsize=(6, 8))  # 縦長のウィンドウサイズ

        # 上部 (ref と ref_p のグラフ)
        plt.subplot(2, 1, 1)
        plt.plot(x_dark_ref, results['ref - DARK_ref'], color='black', linestyle='-', label='ref - DARK_ref')
        plt.plot(x_dark_ref, results['ref_p - DARK_ref'], color='gray', linestyle='--', label='ref_p - DARK_ref')
        plt.title('ref と ref_p の計算結果グラフ')
        plt.xlabel('DARK_ref 1列目 (X軸)')
        plt.ylabel('値の差')
        plt.legend()
        plt.grid()

        # 下部 (sig と sig_p のグラフ)
        plt.subplot(2, 1, 2)
        plt.plot(x_dark_ref, results['sig - DARK_sig'], color='black', linestyle='-', label='sig - DARK_sig')
        plt.plot(x_dark_ref, results['sig_p - DARK_sig'], color='gray', linestyle='--', label='sig_p - DARK_sig')
        plt.title('sig と sig_p の計算結果グラフ')
        plt.xlabel('DARK_ref 1列目 (X軸)')
        plt.ylabel('値の差')
        plt.legend()
        plt.grid()

        plt.tight_layout()
        plt.get_current_fig_manager().window.setGeometry(800, 100, 600, 800)  # ウィンドウの位置とサイズを設定
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
