import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QSpinBox, QFileDialog, QMessageBox
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.setCentralWidget(self.widget)

        self.textEdit1 = QTextEdit()
        self.textEdit2 = QTextEdit()

        self.layout.addWidget(self.textEdit1)
        self.layout.addWidget(self.textEdit2)

        self.plotButton = QPushButton('Plot')
        self.movingAvgButton = QPushButton('Moving Average Plot')
        self.saveButton = QPushButton('Save Data')
        self.layout.addWidget(self.plotButton)
        self.layout.addWidget(self.movingAvgButton)
        self.layout.addWidget(self.saveButton)

        self.windowSizeLabel = QLabel('Moving Average Window Size:')
        self.layout.addWidget(self.windowSizeLabel)

        self.windowSizeSpinBox = QSpinBox()
        self.windowSizeSpinBox.setMinimum(1)
        self.windowSizeSpinBox.setValue(5)  # Default window size
        self.layout.addWidget(self.windowSizeSpinBox)

        self.setGeometry(100, 100, 200, 200)
        self.setWindowTitle('Text Editor')
        self.show()

        self.plotButton.clicked.connect(self.plotGraph)
        self.movingAvgButton.clicked.connect(self.plotMovingAverage)
        self.saveButton.clicked.connect(self.saveData)
        self.windowSizeSpinBox.valueChanged.connect(self.updateWindowSize)

        self.window_size = self.windowSizeSpinBox.value()  # Initial window size

    def plotGraph(self):
        text1 = self.textEdit1.toPlainText()
        text2 = self.textEdit2.toPlainText()

        x1, y1 = self.processText(text1)
        x2, y2 = self.processText(text2)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

        if x1 and y1:
            ax1.plot(x1, y1, label='Graph 1')

        if x2 and y2:
            ax1.plot(x2, y2, label='Graph 2')

        if x1 or x2:
            ax1.set_xlabel('X')
            ax1.set_ylabel('Y')
            ax1.set_title('Combined Graph')
            ax1.grid(True)
            ax1.legend()

        rmse = self.calculateRMSE(y1, y2)
        ax2.bar(np.arange(len(rmse)), rmse)
        ax2.set_xlabel('Data Point')
        ax2.set_ylabel('RMSE')
        ax2.set_title('Root Mean Squared Error (RMSE)')
        ax2.grid(True)


        plt.tight_layout()
        plt.show()

    def plotMovingAverage(self):
        text1 = self.textEdit1.toPlainText()
        text2 = self.textEdit2.toPlainText()

        x1, y1 = self.processText(text1)
        x2, y2 = self.processText(text2)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

        if y1 and y2:
            moving_avg1 = self.calculateMovingAverage(y1, self.window_size)  # Use the current window size
            moving_avg2 = self.calculateMovingAverage(y2, self.window_size)  # Use the current window size
            #ax1.plot(x1, y1, label='Graph 1')
            ax1.plot(x1, moving_avg1, label='Moving Average 1')
           # ax1.plot(x2, y2, label='Graph 2')
            ax1.plot(x2, moving_avg2, label='Moving Average 2')
            ax1.set_xlabel('X')
            ax1.set_ylabel('Y')
            ax1.set_title('Moving Average Plot')
            ax1.grid(True)
            ax1.legend()

            rmse = self.calculateRMSE(moving_avg1, moving_avg2)
            ax2.bar(np.arange(len(rmse)), rmse)
            ax2.set_xlabel('Data Point')
            ax2.set_ylabel('RMSE')
            ax2.set_title('Root Mean Squared Error (RMSE)')
            ax2.grid(True)

        plt.tight_layout()
        plt.show()

    def processText(self, text):
        lines = text.split('\n')
        x = []
        y = []

        for line in lines:
            if line:
                values = line.split('\t')
                if len(values) == 2:
                    try:
                        x.append(float(values[0]))
                        y.append(float(values[1]))
                    except ValueError:
                        pass

        return x, y

    def calculateRMSE(self, y1, y2):
        rmse = []
        min_len = min(len(y1), len(y2))

        for i in range(min_len):
            rmse.append(np.sqrt((y1[i] - y2[i]) ** 2))

        return rmse

    def calculateMovingAverage(self, y, window_size):
        moving_avg = np.convolve(y, np.ones(window_size) / window_size, mode='same')
        return moving_avg

    def updateWindowSize(self):
        self.window_size = self.windowSizeSpinBox.value()  # Update the window size when the spinbox value changes

    def saveData(self):
        text1 = self.textEdit1.toPlainText()
        text2 = self.textEdit2.toPlainText()

        x1, y1 = self.processText(text1)
        x2, y2 = self.processText(text2)

        moving_avg1 = self.calculateMovingAverage(y1, self.window_size)
        moving_avg2 = self.calculateMovingAverage(y2, self.window_size)

        data = {
            'Wavelength': x1,  # Use x1 as the wavelength axis
            'Graph 1': y1,
            'Moving Average 1': moving_avg1,
            'Graph 2': y2,
            'Moving Average 2': moving_avg2
        }

        df = pd.DataFrame(data)
        save_path, _ = QFileDialog.getSaveFileName(self, 'Save Data', '', 'Text Files (*.txt)')

        if save_path:
            df.to_csv(save_path, sep='\t', index=False)

            msg = f"Data saved to {save_path}"
            QMessageBox.information(self, "Save Data", msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = TextEditor()
    sys.exit(app.exec_())
