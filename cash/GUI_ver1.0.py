import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QFileDialog, QSizePolicy, QToolBar
from PyQt5.QtGui import QPixmap
import json
import os
import pandas as pd  # pandasのインポートを追加

class DataGraphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("データグラフ作成")
        self.resize(400, 600)

        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # ツールバーの設定
        self.toolbar = QToolBar("ツールバー")
        self.addToolBar(self.toolbar)

        # ツールバーにボタンを追加
        load_button = QPushButton("Load Data")
        load_button.clicked.connect(self.load_data)
        self.toolbar.addWidget(load_button)
        
        plot_button = QPushButton("Plot")
        plot_button.clicked.connect(self.plot_graph)
        self.toolbar.addWidget(plot_button)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_data)
        self.toolbar.addWidget(save_button)

        # Excel保存ボタンの追加
        save_excel_button = QPushButton("Output Excel")
        save_excel_button.clicked.connect(self.save_data_to_excel)
        self.toolbar.addWidget(save_excel_button)

        # 左側のレイアウト (ダークデータ)
        dark_layout = QVBoxLayout()
        self.text_boxes = {}
        self.graph_widgets = {}
        self.text_boxes['DARK_ref'], self.graph_widgets['DARK_ref'] = self.create_text_box_with_graph('DARK_ref', dark_layout)
        self.text_boxes['DARK_sig'], self.graph_widgets['DARK_sig'] = self.create_text_box_with_graph('DARK_sig', dark_layout)

        # 右側のレイアウト (残りのデータ)
        remaining_layout = QVBoxLayout()
        self.text_boxes['ref'], self.graph_widgets['ref'] = self.create_text_box_with_graph('ref', remaining_layout)
        self.text_boxes['sig'], self.graph_widgets['sig'] = self.create_text_box_with_graph('sig', remaining_layout)
        self.text_boxes['ref_p'], self.graph_widgets['ref_p'] = self.create_text_box_with_graph('ref_p', remaining_layout)
        self.text_boxes['sig_p'], self.graph_widgets['sig_p'] = self.create_text_box_with_graph('sig_p', remaining_layout)

        # 左側と右側のレイアウトをメインレイアウトに追加
        main_layout.addLayout(dark_layout)
        main_layout.addLayout(remaining_layout)

        self.setCentralWidget(main_widget)

        # テキストボックスの内容が変更されたときにプレビューを更新する
        for text_box in self.text_boxes.values():
            text_box.textChanged.connect(self.update_graphs)

    def create_text_box_with_graph(self, label, layout):
        h_layout = QHBoxLayout()
        
        lbl = QLabel(f'{label}:')
        lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 固定サイズに設定
        lbl.setFixedWidth(70)  # 幅を50に固定（必要に応じて調整）
        h_layout.addWidget(lbl)
        
        text_box = QPlainTextEdit()
        text_box.setFixedSize(150, 80)
        text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout.addWidget(text_box)

        graph_widget = QLabel()
        graph_widget.setFixedSize(100, 100)
        h_layout.addWidget(graph_widget)

        layout.addLayout(h_layout)
        return text_box, graph_widget

    def update_graphs(self):
        for label, text_box in self.text_boxes.items():
            data = text_box.toPlainText()
            self.update_graph(self.graph_widgets[label], data)

    # グラフを更新する関数
    def update_graph(self, graph_widget, data):
        plt.clf()
        if data.strip():
            x_values, y_values = self.parse_data(data)
            plt.figure(figsize=(1.5, 1))
            plt.plot(x_values, y_values, color='blue', alpha=0.7, linestyle='-', linewidth=1)
            plt.grid(graph_widget)
            plt.axis('off')
            plt.xlim(min(x_values), max(x_values) if x_values else 1)
            plt.ylim(min(y_values), max(y_values) if y_values else 1)

            temp_file_path = 'temp.png'
            plt.savefig(temp_file_path, bbox_inches='tight', pad_inches=0)
            plt.close()

            graph_widget.setPixmap(QPixmap(temp_file_path))
            os.remove(temp_file_path)

    # テキストボックスのデータを解析する関数
    def parse_data(self, data):
        x_values, y_values = [], []
        for line in data.splitlines():
            if line.strip():
                parts = line.split()
                x_values.append(float(parts[0]))
                y_values.append(float(parts[1]))
        return x_values, y_values

    def plot_graph(self):
        # 各テキストボックスからデータを取得
        x_dark_ref, y_dark_ref = self.parse_data(self.text_boxes['DARK_ref'].toPlainText())
        _, y_dark_sig = self.parse_data(self.text_boxes['DARK_sig'].toPlainText())
        _, y_ref = self.parse_data(self.text_boxes['ref'].toPlainText())
        _, y_sig = self.parse_data(self.text_boxes['sig'].toPlainText())
        _, y_ref_p = self.parse_data(self.text_boxes['ref_p'].toPlainText())
        _, y_sig_p = self.parse_data(self.text_boxes['sig_p'].toPlainText())

        # ダークデータを引いた値を計算
        results = {
            'ref - DARK_ref': [ref - dark_ref for dark_ref, ref in zip(y_dark_ref, y_ref)],
            'sig - DARK_sig': [sig - dark_sig for dark_sig, sig in zip(y_dark_sig, y_sig)],
            'ref_p - DARK_ref': [ref_p - dark_ref for dark_ref, ref_p in zip(y_dark_ref, y_ref_p)],
            'sig_p - DARK_sig': [sig_p - dark_sig for dark_sig, sig_p in zip(y_dark_sig, y_sig_p)],
        }


        #Sig ダークデータを引き、ポンプ有り無しの差を計算
        calc_deffer_sig = [
            sig_p_raw - dark_sig - (sig_dark_raw - dark_sig)
            for sig_p_raw, dark_sig, sig_dark_raw in zip(
                y_sig_p, y_dark_sig, y_sig)
        ]

        #絶対値を計算
        calc_deffer_sig = [abs(result) for result in calc_deffer_sig]

        #最大値で正規化
        max_value = max(calc_deffer_sig)
        calc_deffer_sig = [result / max_value for result in calc_deffer_sig]

        #Ref ダークデータを引き、ポンプ有り無しの差を計算
        calc_deffer_ref = [
            ref_p_raw - dark_ref - (ref_dark_raw - dark_ref)
            for ref_p_raw, dark_ref, ref_dark_raw in zip(
                y_ref_p, y_dark_ref, y_ref)
        ]
        #絶対値を計算
        calc_deffer_ref = [abs(result) for result in calc_deffer_ref]

        #最大値で正規化
        max_value = max(calc_deffer_ref)
        calc_deffer_ref = [result / max_value for result in calc_deffer_ref]

        #calc_deffer_sigとcalc_deffer_refの差を計算
        calc_deffer = [sig - ref for sig, ref in zip(calc_deffer_sig, calc_deffer_ref)]

        #絶対値を計算
        calc_deffer = [abs(result) for result in calc_deffer]

        #全体的に値が小さいか判断したいので、最大値で正規化
        max_value = max(calc_deffer)
        calc_deffer = [result / max_value for result in calc_deffer]

        # LOG計算 (ΔAbsの計算)
        log_values = []
        for ref_p_real, sig_real, sig_p_real, ref_real in zip(
                y_ref_p, y_sig, y_sig_p, y_ref):
            # 0での除算を避けるための処理
            if ref_real != 0 and sig_p_real != 0:
                log_value = np.log((ref_p_real * sig_real) / (sig_p_real * ref_real))
                log_values.append(log_value)
            else:
                # 0での除算の場合はnanを追加
                log_values.append(np.nan)



        # LOG計算結果グラフを別ウィンドウで表示
        log_fig = plt.figure(figsize=(6, 4))
        plt.plot(x_dark_ref, log_values, color='black', alpha=0.7, linestyle='-',
                 label='LOG = log((ref_p * sig) / (sig_p * ref))')
        
        #y軸の-0.01から0.01の範囲を緑色でハイライト
        plt.axhspan(-0.01, 0.01, color='green', alpha=0.2)
        #plt.axhline(0.01, color='red', alpha=0.8, linestyle='--')
        #plt.axhline(-0.01, color='red', alpha=0.8, linestyle='--')
        plt.title('Transient Absorption Spectrum')
        plt.xlabel('Wavelength / nm')
        plt.ylabel('ΔAbs')
        plt.legend()
        plt.grid()
        plt.get_current_fig_manager().window.setGeometry(100, 100, 800, 400)
        plt.tight_layout()
        plt.show()

        # ref と DARK_ref、sig と DARK_sig のグラフを同じウィンドウで表示
        combined_fig = plt.figure(figsize=(6, 10))  # 高さを調整

        # 上部 (ref と DARK_ref および ref_p と DARK_ref のグラフ)
        plt.subplot(3, 1, 1)  # 3行1列の配置の1つ目
        plt.plot(x_dark_ref, results['ref - DARK_ref'], color='black', alpha=0.7, linestyle='-', label='ref - DARK_ref')
        plt.plot(x_dark_ref, results['ref_p - DARK_ref'], color='black', alpha=0.7, linestyle='--', label='ref_p - DARK_ref')
        plt.xlabel('Wavelength / nm')
        plt.ylabel('Counts')
        plt.legend()
        plt.tight_layout()
        plt.grid()

        # 中部 (sig と DARK_sig および sig_p と DARK_sig のグラフ)
        plt.subplot(3, 1, 2)  # 3行1列の配置の2つ目
        plt.plot(x_dark_ref, results['sig - DARK_sig'], color='black', alpha=0.7, linestyle='-', label='sig - DARK_sig')
        plt.plot(x_dark_ref, results['sig_p - DARK_sig'], color='black', alpha=0.7, linestyle='--', label='sig_p - DARK_sig')
        plt.xlabel('Wavelength / nm')
        plt.ylabel('Counts')
        plt.legend()
        plt.tight_layout()
        plt.grid()

        # 下部
        plt.subplot(3, 1, 3)  # 3行1列の配置の3つ目
        plt.plot(x_dark_ref, calc_deffer, color='k', alpha=0.8, linestyle='-', label='a-b')
        plt.plot(x_dark_ref, calc_deffer_sig, color='b', alpha=0.6, linestyle='-', label='a = sig_p - DARK_sig - (sig - DARK_sig)')
        plt.plot(x_dark_ref, calc_deffer_ref, color='r', alpha=0.6, linestyle='-', label='b = ref_p - DARK_ref - (ref - DARK_ref)')
        plt.xlabel('Wavelength / nm')
        plt.ylabel('Difference')
        plt.legend()
        plt.grid()
        plt.get_current_fig_manager().window.setGeometry(900, 100, 400, 800)
        plt.tight_layout()
        plt.show()

    def save_data(self):
        data = {label: self.text_boxes[label].toPlainText() for label in self.text_boxes}
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "データを保存", "", "JSON Files (*.json);;All Files (*)", options=options)
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(data, f)
            print("データが保存されました:", file_path)

    def save_data_to_excel(self):
        data = {label: self.text_boxes[label].toPlainText() for label in self.text_boxes}
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Excelデータを保存", "", "Excel Files (*.xlsx);;All Files (*)", options=options)

        if file_path:
            # データをDataFrameに変換し、グラフデータも含める
            df = pd.DataFrame(dict([(k, pd.Series(v.splitlines())) for k, v in data.items()]))

            # グラフデータを追加
            x_dark_ref, y_dark_ref = self.parse_data(self.text_boxes['DARK_ref'].toPlainText())
            _, y_dark_sig = self.parse_data(self.text_boxes['DARK_sig'].toPlainText())
            _, y_ref = self.parse_data(self.text_boxes['ref'].toPlainText())
            _, y_sig = self.parse_data(self.text_boxes['sig'].toPlainText())
            _, y_ref_p = self.parse_data(self.text_boxes['ref_p'].toPlainText())
            _, y_sig_p = self.parse_data(self.text_boxes['sig_p'].toPlainText())

            # 各グラフデータをDataFrameに追加
            df_graph = pd.DataFrame({
                'Wavelength': x_dark_ref,
                'DARK_ref': y_dark_ref,
                'DARK_sig': y_dark_sig,
                'ref': y_ref,
                'sig': y_sig,
                'ref_p': y_ref_p,
                'sig_p': y_sig_p
            })

            # ΔAbsの計算結果を追加
            log_values = []
            for ref_p_real, sig_real, sig_p_real, ref_real in zip(
                    y_ref_p, y_sig, y_sig_p, y_ref):
                if ref_real != 0 and sig_p_real != 0:
                    log_value = np.log((ref_p_real * sig_real) / (sig_p_real * ref_real))
                    log_values.append(log_value)
                else:
                    log_values.append(np.nan)
            df_graph['ΔAbs'] = log_values
            

            # データをExcelに保存
            with pd.ExcelWriter(file_path) as writer:
                df_graph.to_excel(writer, sheet_name='Graph Data', index=False)

            print("データがExcelファイルとして保存されました:", file_path)

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
