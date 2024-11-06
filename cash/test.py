import serial
import time

# シリアルポートの設定
port = 'COM4'  # 使用するポートに合わせて変更してください
baudrate = 9600

# シリアル接続の初期化
ser = serial.Serial(port, baudrate, timeout=1)
time.sleep(2)  # 接続の安定化のために少し待つ

def send_command(steps, delay_time, direction):
    command = f"{steps},{delay_time},{direction}\n"  # コマンド形式
    ser.write(command.encode())  # コマンドを送信
    print(f"Sent command: {command.strip()}")

try:
    while True:
        # ユーザーからの入力を受け取る
        steps = int(input("ステップ数を入力してください（0で終了）: "))
        if steps == 0:
            break
        delay_time = int(input("遅延時間（ミリ秒）を入力してください: "))
        direction = int(input("方向を入力してください（1: 時計回り, -1: 反時計回り）: "))

        send_command(steps, delay_time, direction)

except KeyboardInterrupt:
    print("プログラムを終了します。")

finally:
    ser.close()  # シリアル接続を閉じる
