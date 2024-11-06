import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QFileDialog, QSizePolicy, QToolBar, QListWidget
from PyQt5.QtGui import QPixmap
import json
import os
import pandas as pd

class DataGraphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("データグラフ作成")
        self.resize(400, 600)

        # パルスを保存する辞書
        self.pulse_data = {}

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

        save_excel_button = QPushButton("Output Excel")
        save_excel_button.clicked.connect(self.save_data_to_excel)
        self.toolbar.addWidget(save_excel_button)

        # パルス入力用のレイアウト
        pulse_layout = QHBoxLayout()
        self.pulse_input = QPlainTextEdit()
        self.pulse_input.setFixedSize(100, 30)
        pulse_button = QPushButton("Save Pulse Data")
        pulse_button.clicked.connect(self.save_pulse_data)

        pulse_layout.addWidget(QLabel("Pulse:"))
        pulse_layout.addWidget(self.pulse_input)
        pulse_layout.addWidget(pulse_button)
        main_layout.addLayout(pulse_layout)

        # パルスリストの表示
        self.pulse_list = QListWidget()
        main_layout.addWidget(QLabel("Saved Pulses:"))
        main_layout.addWidget(self.pulse_list)

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

        # パルス選択用のボタン
        select_pulse_button = QPushButton("Load Selected Pulse Data")
        select_pulse_button.clicked.connect(self.load_selected_pulse_data)
        main_layout.addWidget(select_pulse_button)

        # 重ね書きボタンの追加
        overlay_button = QPushButton("Overlay Pulses")
        overlay_button.clicked.connect(self.overlay_pulses)
        main_layout.addWidget(overlay_button)

        self.setCentralWidget(main_widget)

        # テキストボックスの内容が変更されたときにプレビューを更新する
        for text_box in self.text_boxes.values():
            text_box.textChanged.connect(self.update_graphs)

    def create_text_box_with_graph(self, label, layout):
        h_layout = QHBoxLayout()
        
        lbl = QLabel(f'{label}:')
        lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lbl.setFixedWidth(70)
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

        # ref - DARK_refとref_p - DARK_refの差を計算
        results['Difference_ref'] = [ref_p - ref for ref_p, ref in zip(results['ref_p - DARK_ref'], results['ref - DARK_ref'])]
        # 絶対値を取る
        results['Difference_ref'] = [abs(value) for value in results['Difference_ref']]
        # 最大値で正規化
        results['Difference_ref'] = [value / max(results['Difference_ref']) for value in results['Difference_ref']]

        # sig - DARK_sigとsig_p - DARK_sigの差を計算
        results['Difference_sig'] = [sig_p - sig for sig_p, sig in zip(results['sig_p - DARK_sig'], results['sig - DARK_sig'])]
        # 絶対値を取る
        results['Difference_sig'] = [abs(value) for value in results['Difference_sig']]
        # 最大値で正規化
        results['Difference_sig'] = [value / max(results['Difference_sig']) for value in results['Difference_sig']]        

        # 差を計算
        results['Difference'] = [ref - sig for ref, sig in zip(results['Difference_ref'], results['Difference_sig'])]
        # 絶対値を取る
        results['Difference'] = [abs(value) for value in results['Difference']]
        # 最大値で正規化
        results['Difference'] = [value / max(results['Difference']) for value in results['Difference']]
    
        # LOG計算 (ΔAbsの計算)
        log_values = []
        for ref_p_real, sig_real, sig_p_real, ref_real in zip(
                y_ref_p, y_sig, y_sig_p, y_ref):
            if ref_real != 0 and sig_p_real != 0:
                log_value = np.log((ref_p_real * sig_real) / (sig_p_real * ref_real))
                log_values.append(log_value)
            else:
                log_values.append(np.nan)

        # LOG計算結果グラフを別ウィンドウで表示
        log_fig = plt.figure(figsize=(6, 4))
        plt.plot(x_dark_ref, log_values, color='black', alpha=0.7, linestyle='-',
                 label='LOG = log((ref_p * sig) / (sig_p * ref))')
        plt.axhspan(-0.01, 0.01, color='green', alpha=0.2)
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
        plt.plot(x_dark_ref, results['ref_p - DARK_ref'], color='black', linestyle='--', label='ref_p - DARK_ref')
        plt.xlabel('Wavelength / nm')
        plt.ylabel('Counts')
        plt.legend()
        plt.tight_layout()
        plt.grid()

        # 中部 (sig と DARK_sig および sig_p と DARK_sig のグラフ)
        plt.subplot(3, 1, 2)  # 3行1列の配置の2つ目
        plt.plot(x_dark_ref, results['sig - DARK_sig'], color='black', alpha=0.7, linestyle='-', label='sig - DARK_sig')
        plt.plot(x_dark_ref, results['sig_p - DARK_sig'], color='black', linestyle='--', label='sig_p - DARK_sig')
        plt.xlabel('Wavelength / nm')
        plt.ylabel('Counts')
        plt.legend()
        plt.tight_layout()
        plt.grid()

        # 下部
        plt.subplot(3, 1, 3)  # 3行1列の配置の3つ目
        plt.plot(x_dark_ref, results['Difference_ref'], color='r', alpha=0.6, linestyle='-', label='Difference_ref')
        plt.plot(x_dark_ref, results['Difference_sig'], color='b', alpha=0.6, linestyle='-', label='Difference_sig')
        plt.plot(x_dark_ref, results['Difference'], color='k', alpha=0.9, linestyle='-', label='Difference')

        plt.xlabel('Wavelength / nm')
        plt.ylabel('Difference')
        plt.legend()
        plt.grid()

        plt.tight_layout()
        plt.show()

    def overlay_pulses(self):
        # 重ね書き用のグラフを描画
        plt.figure(figsize=(6, 4))

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

        # 重ね書きのプロット
        for pulse in self.pulse_data.keys():
            pulse_data = self.pulse_data[pulse]
            # log計算
            x_dark_ref, y_dark_ref = self.parse_data(pulse_data['DARK_ref'])
            _, y_dark_sig = self.parse_data(pulse_data['DARK_sig'])
            _, y_ref = self.parse_data(pulse_data['ref'])
            _, y_sig = self.parse_data(pulse_data['sig'])
            _, y_ref_p = self.parse_data(pulse_data['ref_p'])
            _, y_sig_p = self.parse_data(pulse_data['sig_p'])

            # LOG計算 (ΔAbsの計算)  
            log_values = []
            for ref_p_real, sig_real, sig_p_real, ref_real in zip(
                    y_ref_p, y_sig, y_sig_p, y_ref):
                if ref_real != 0 and sig_p_real != 0:
                    log_value = np.log((ref_p_real * sig_real) / (sig_p_real * ref_real))
                    log_values.append(log_value)
                else:
                    log_values.append(np.nan)
            plt.plot(x_dark_ref, log_values, label=f'Pulse {pulse}')
            plt.xlabel('Wavelength / nm')
            plt.ylabel('ΔAbs')
            plt.legend()
            plt.grid()
            plt.title('Transient Absorption Spectrum')
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
        # エクセルファイルの保存先を選択
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "エクセルファイルを保存", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        
        if file_path:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for pulse, data in self.pulse_data.items():
                    # データを抽出
                    x_dark_ref, y_dark_ref = self.parse_data(data['DARK_ref'])
                    _, y_dark_sig = self.parse_data(data['DARK_sig'])
                    _, y_ref = self.parse_data(data['ref'])
                    _, y_sig = self.parse_data(data['sig'])
                    _, y_ref_p = self.parse_data(data['ref_p'])
                    _, y_sig_p = self.parse_data(data['sig_p'])
    
                    # DataFrameを作成
                    df = pd.DataFrame({
                        'Wavelength': x_dark_ref,
                        'DARK_ref': y_dark_ref,
                        'DARK_sig': y_dark_sig,
                        'ref': y_ref,
                        'sig': y_sig,
                        'ref_p': y_ref_p,
                        'sig_p': y_sig_p
                    })
                    #log計算したデータを追加
                    log_values = []
                    for ref_p_real, sig_real, sig_p_real, ref_real in zip(
                            y_ref_p, y_sig, y_sig_p, y_ref):
                        if ref_real != 0 and sig_p_real != 0:
                            log_value = np.log((ref_p_real * sig_real) / (sig_p_real * ref_real))
                            log_values.append(log_value)
                        else:
                            log_values.append(np.nan)
                    df['ΔAbs'] = log_values
                    # パルス名でシートを作成
                    df.to_excel(writer, sheet_name=pulse, index=False)
            
            print("データがエクセルファイルに保存されました:", file_path)

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

    def save_pulse_data(self):
        pulse_value = self.pulse_input.toPlainText().strip()
        if pulse_value:
            # 各テキストボックスの内容を保存
            data = {label: text_box.toPlainText() for label, text_box in self.text_boxes.items()}
            self.pulse_data[pulse_value] = data
            self.update_pulse_list()
            print(f"Pulse {pulse_value}のデータが保存されました。")

    def load_selected_pulse_data(self):
        selected_item = self.pulse_list.currentItem()
        if selected_item:
            pulse_value = selected_item.text()
            if pulse_value in self.pulse_data:
                data = self.pulse_data[pulse_value]
                for label, content in data.items():
                    if label in self.text_boxes:
                        self.text_boxes[label].setPlainText(content)
                print(f"Pulse {pulse_value}のデータが読み込まれました。")
            else:
                print(f"Pulse {pulse_value}のデータは見つかりません。")

    def update_pulse_list(self):
        self.pulse_list.clear()
        for pulse in self.pulse_data.keys():
            self.pulse_list.addItem(pulse)

# アプリケーションの起動
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataGraphApp()
    window.show()
    sys.exit(app.exec_())
