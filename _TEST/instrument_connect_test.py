import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QPushButton

def get_usb_devices():
    # macOSのsystem_profilerでUSB情報取得
    result = subprocess.run(
        ["system_profiler", "SPUSBDataType"],
        stdout=subprocess.PIPE,
        text=True
    )
    lines = result.stdout.splitlines()
    devices = []
    # 代表的なデバイス名（例：Product ID行やDevice行）だけ抽出
    for line in lines:
        if ":" in line and ("Product ID" in line or "Manufacturer" in line or "Serial Number" in line or "Location ID" in line or "Device" in line):
            devices.append(line.strip())
    return devices

class USBDeviceViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USBデバイス一覧")
        self.layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        self.refresh_btn = QPushButton("更新")
        self.refresh_btn.clicked.connect(self.update_list)
        
        self.layout.addWidget(self.refresh_btn)
        self.layout.addWidget(self.list_widget)
        self.setLayout(self.layout)
        
        self.update_list()
    
    def update_list(self):
        self.list_widget.clear()
        devices = get_usb_devices()
        if devices:
            for dev in devices:
                self.list_widget.addItem(dev)
        else:
            self.list_widget.addItem("USBデバイスが見つかりませんでした")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = USBDeviceViewer()
    viewer.show()
    sys.exit(app.exec_())