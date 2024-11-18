import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QWidget, QTextEdit, QListWidget, QListWidgetItem, QHBoxLayout, QLabel
)
from PyQt5.QtCore import Qt  # Qtをインポート

class JsonToDataFrameApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ΔAbs Data Extractor")
        self.resize(600, 400)

        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # JSONファイルを読み込むボタン
        load_button = QPushButton("Load JSON")
        load_button.clicked.connect(self.load_json_file)
        main_layout.addWidget(load_button)

        # 波長選択セクション
        wavelength_layout = QVBoxLayout()
        wavelength_label = QLabel("Wavelengths:")
        self.wavelength_list = QListWidget()
        self.wavelength_list.setSelectionMode(QListWidget.MultiSelection)

        wavelength_buttons_layout = QHBoxLayout()
        plot_wavelength_button = QPushButton("Plot")
        plot_wavelength_button.clicked.connect(self.update_plot_by_wavelength)
        wavelength_buttons_layout.addWidget(plot_wavelength_button)

        save_wavelength_button = QPushButton("Save")
        save_wavelength_button.clicked.connect(self.save_wavelength_dataframe)
        wavelength_buttons_layout.addWidget(save_wavelength_button)

        wavelength_layout.addWidget(wavelength_label)
        wavelength_layout.addWidget(self.wavelength_list)
        wavelength_layout.addLayout(wavelength_buttons_layout)

        main_layout.addLayout(wavelength_layout)

        # データセット名選択セクション
        dataset_layout = QVBoxLayout()
        dataset_label = QLabel("Datasets:")
        self.dataset_list = QListWidget()
        self.dataset_list.setSelectionMode(QListWidget.MultiSelection)

        dataset_buttons_layout = QHBoxLayout()
        plot_dataset_button = QPushButton("Plot")
        plot_dataset_button.clicked.connect(self.update_plot_by_dataset)
        dataset_buttons_layout.addWidget(plot_dataset_button)

        save_dataset_button = QPushButton("Save")
        save_dataset_button.clicked.connect(self.save_dataset_dataframe)
        dataset_buttons_layout.addWidget(save_dataset_button)

        dataset_layout.addWidget(dataset_label)
        dataset_layout.addWidget(self.dataset_list)
        dataset_layout.addLayout(dataset_buttons_layout)

        main_layout.addLayout(dataset_layout)

        # データフレームを表示するテキストエディット
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        main_layout.addWidget(self.data_display)

        self.setCentralWidget(main_widget)

        self.df = None  # データフレームを保持するための変数

    def load_json_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                all_data = {}
                wavelengths = None

                for pulse_name, pulse_data in data.items():
                    x_dark_ref, y_dark_ref = self.parse_data(pulse_data['DARK_ref'])
                    _, y_dark_sig = self.parse_data(pulse_data['DARK_sig'])
                    _, y_ref = self.parse_data(pulse_data['ref'])
                    _, y_ref_p = self.parse_data(pulse_data['ref_p'])
                    _, y_sig = self.parse_data(pulse_data['sig'])
                    _, y_sig_p = self.parse_data(pulse_data['sig_p'])

                    log_values = self.calculate_delta_abs(y_ref, y_ref_p, y_dark_ref, y_dark_sig, y_sig, y_sig_p)

                    if wavelengths is None:
                        wavelengths = x_dark_ref
                    all_data[pulse_name] = log_values

                self.df = pd.DataFrame(all_data, index=wavelengths)
                self.df.index.name = 'Wavelength'
                self.display_dataframe(self.df)

                self.wavelength_list.clear()
                for wavelength in wavelengths:
                    item = QListWidgetItem(str(wavelength))
                    self.wavelength_list.addItem(item)

                self.dataset_list.clear()
                for dataset_name in all_data.keys():
                    item = QListWidgetItem(dataset_name)
                    self.dataset_list.addItem(item)

                self.plot_delta_abs(self.df)

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error loading file: {e}")

    def parse_data(self, data):
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
        log_values = []
        for ref_p_real, sig_real, sig_p_real, ref_real in zip(y_ref_p, y_sig, y_sig_p, y_ref):
            if ref_real != 0 and sig_p_real != 0:
                log_value = np.log((ref_p_real * sig_real) / (sig_p_real * ref_real))
                log_values.append(log_value)
            else:
                log_values.append(np.nan)
        return log_values

    def display_dataframe(self, df):
        self.data_display.clear()
        self.data_display.append(str(df))

    def plot_delta_abs(self, df):
        plt.figure(figsize=(10, 6))
        plt.imshow(df.T, aspect='auto', cmap='nipy_spectral', origin='lower', extent=[df.index.min(), df.index.max(), 0, df.shape[1]])
        plt.colorbar(label='ΔAbs')
        plt.xlabel('Wavelength / nm')
        plt.ylabel('Pulse Position')
        plt.title('ΔAbs Heatmap')
        plt.yticks(np.arange(df.shape[1]), df.columns)
        plt.show()

    def update_plot_by_wavelength(self):
        selected_wavelengths = [float(item.text()) for item in self.wavelength_list.selectedItems()]
        if selected_wavelengths and self.df is not None:
            plt.figure(figsize=(10, 6))
            for selected_wavelength in selected_wavelengths:
                if selected_wavelength in self.df.index:
                    values = self.df.loc[selected_wavelength]
                    plt.plot(self.df.columns, values, marker='o', label=f'Wavelength {selected_wavelength} nm')
            plt.title('ΔAbs at Selected Wavelengths')
            plt.xlabel('Dataset')
            plt.ylabel('ΔAbs')
            plt.grid()
            plt.legend()
            plt.show()

    def update_plot_by_dataset(self):
        selected_datasets = [item.text() for item in self.dataset_list.selectedItems()]
        if selected_datasets and self.df is not None:
            plt.figure(figsize=(10, 6))
            for selected_dataset in selected_datasets:
                if selected_dataset in self.df.columns:
                    values = self.df[selected_dataset]
                    plt.plot(self.df.index, values, marker='o', label=f'Dataset: {selected_dataset}')
            plt.title('ΔAbs for Selected Datasets')
            plt.xlabel('Wavelength / nm')
            plt.ylabel('ΔAbs')
            plt.grid()
            plt.legend()
            plt.show()

    def save_wavelength_dataframe(self):
        selected_wavelengths = [float(item.text()) for item in self.wavelength_list.selectedItems()]
        if selected_wavelengths and self.df is not None:
            filtered_df = self.df.loc[selected_wavelengths]
            options = QFileDialog.Options()
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Wavelength DataFrame", "", "CSV Files (*.csv);;All Files (*)", options=options)
            if save_path:
                filtered_df.to_csv(save_path)
                QMessageBox.information(self, "Success", "Wavelength DataFrame saved.")

    def save_dataset_dataframe(self):
        selected_datasets = [item.text() for item in self.dataset_list.selectedItems()]
        if selected_datasets and self.df is not None:
            filtered_df = self.df[selected_datasets]
            options = QFileDialog.Options()
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Dataset DataFrame", "", "CSV Files (*.csv);;All Files (*)", options=options)
            if save_path:
                filtered_df.to_csv(save_path)
                QMessageBox.information(self, "Success", "Dataset DataFrame saved.")

# アプリケーションの起動
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JsonToDataFrameApp()
    window.show()
    sys.exit(app.exec_())
