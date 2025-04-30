#接続されている装置を調べて名前を表示するプログラム

import serial.tools.list_ports
import time
import serial
import sys

def main():
    # 接続されているポートを調べる
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        print(p.device)

    # 接続されているポートが1つもない場合COM1
    if len(ports) == 0:
        print("No ports found")
        sys.exit()

    # ポート名を入力
    port_name = input("Enter port name: ")

    # シリアル通信の設定
    ser = serial.Serial(port_name, 9600, timeout=1)

    # 接続されている装置の名前を調べる
    ser.write(b'IDN\n')
    time.sleep(1)
    print(ser.readline().decode('utf-8'))
        
    ser.close()

if __name__ == "__main__":
    main()
