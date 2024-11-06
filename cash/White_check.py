import os
import logging
import time
import pyautogui
import clipboard
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import json

# LOGファイルの設定
log_dir = os.path.join(os.path.dirname(__file__), 'LOG')
os.makedirs(log_dir, exist_ok=True)
log_filename = time.strftime("log_%Y%m%d_%H%M%S.log")
log_file = os.path.join(log_dir, log_filename)
logging.basicConfig(level=logging.INFO,
                    filename=log_file,
                    filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Start Log")

# JSONファイルの保存先ディレクトリを指定
save_dir = os.path.join(os.path.dirname(__file__), 'int')
json_file_path = os.path.join(save_dir, "config.json")

# 変数の初期値
start_button_coordinates = None
profile0_coordinates = None
profile1_coordinates = None
expoduretime = None
integration = None

# JSONファイルから変数の値を読み込む
#if os.path.exists(json_file_path):
#    with open(json_file_path, "r") as jr
#        data = json.load(json_file)
#        start_button_coordinates = tuplrrt_button_coordinates"])
#        profile0_coordinates = tuple(dar0_coordinates"])
#        profile1_coordinates = tuple(dar1_coordinates"])
#        expoduretime = data["expoduretir
#        integration = data["integration"]
#        
#        # Calculate the other coordinates based on the loaded values
#        x, y = profile0_coordinates
#        profile0_coordinates2 = (x, y + 30)
#        profile0_coordinates3 = (x, y + 45)
#        
#        x, y = profile1_coordinates
#        profile1_coordinates2 = (x, y + 30)
#        profile1_coordinates3 = (x, y + 45)
#
##### AutohotkeyのWindowSpyのパスを指定
file_path = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\AutoHotkey\Window Spy.lnk'
subprocess.Popen(file_path, shell=True)

# 各座標の登録関数
def set_coordinates(target):
    global start_button_coordinates, profile0_coordinates, profile0_coordinates2, profile0_coordinates3, profile1_coordinates, profile1_coordinates2, profile1_coordinates3

    x = int(input(f"Enter X coordinate for {target}: "))
    y = int(input(f"Enter Y coordinate for {target}: "))

    if target == 'start':
        start_button_coordinates = (x, y)
    elif target == 'profile0':
        profile0_coordinates = (x, y)
        profile0_coordinates2 = (x, y+30)
        profile0_coordinates3 = (x, y+45)
    elif target == 'profile1':
        profile1_coordinates = (x, y)
        profile1_coordinates2 = (x, y+30)
        profile1_coordinates3 = (x, y+45)

# aquisitiontimeを計算
def calculate_aquisitiontime(expoduretime, integration):
    return expoduretime * integration

while True:
    command = input("Enter a target (start, profile0, profile1), and then, command 'check'")
    if command == 'exit':
        break
    elif command == 'check':
        print(f"StartButton coordinates: {start_button_coordinates}")
        print(f"Profile0 coordinates: {profile0_coordinates}")
        print(f"Profile1 coordinates: {profile1_coordinates}")
        change_coords = input("Do you want to change the coordinates? (Yes/No): ")
        if change_coords.lower() == 'yes':
            target_to_change = input("Enter the target you want to change (Start, Profile0, Profile1): ")
            if target_to_change in ['start', 'profile0', 'profile1']:
                set_coordinates(target_to_change)
            else:
                print("Invalid target. Please enter 'Start', 'Profile0', or 'Profile1'.")
        else:
            break

    elif command in ['start', 'profile0', 'profile1']:
        set_coordinates(command)
    else:
        print("Invalid target. Please enter 'start', 'profile0', 'profile1', or 'check'.")

    
# 結果を表示
print("----------------------------------------------")
print(f"StartButton coordinates: {start_button_coordinates}")
print("----------------------------------------------")
print(f"Profile0 coordinstartates: {profile0_coordinates}")
print(f"Profile0 coordinates2: {profile0_coordinates2}")
print(f"Profile0 coordinates3: {profile0_coordinates3}")
print("----------------------------------------------")
print(f"Profile1 coordinates: {profile1_coordinates}")
print(f"Profile1 coordinates2: {profile1_coordinates2}")
print(f"Profile1 coordinates3: {profile1_coordinates3}")
print("----------------------------------------------")
print("Aquisitiontimeの設定に移ります.")
command = input("Press enter to continue...")

if command == '':
    expoduretime = float(input("Enter Expodure time (in milliseconds): "))
    integration = float(input("Enter integration: "))
    acquisitiontime = expoduretime * integration
    print(f"Calculated acquisitiontime: {acquisitiontime/1000} s")

    # 変数をJSONファイルに保存
    data = {
        "start_button_coordinates": start_button_coordinates,
        "profile0_coordinates": profile0_coordinates,
        "profile1_coordinates": profile1_coordinates,
        "expoduretime": expoduretime,
        "integration": integration
    }
    os.makedirs(save_dir, exist_ok=True)  # ディレクトリが存在しない場合は作成
    with open(json_file_path, "w") as json_file:
        json.dump(data, json_file)

print("----------------------------------------------")
print(f"Expodure time: {expoduretime}")
print(f"integration: {integration}")
print(f"[acquisition: {acquisitiontime/1000}s]")
logging.info("-----------------------------------------------------------")
# ログに座標を記録
logging.basicConfig(level=logging.INFO, filename='coordinates.log', filemode='a', format='%(asctime)s - %(message)s')
logging.info("--------------------COORDINATES SETTING--------------------")
logging.info(f"StartButton coordinates: {start_button_coordinates}")
logging.info(f"Profile0 coordinates: {profile0_coordinates}")
logging.info(f"Profile1 coordinates: {profile1_coordinates}")
logging.info(f"ExpodureTime: {expoduretime}")
logging.info(f"Integration: {integration}")
logging.info("-----------------------------------------------------------")

def start_measurement(loop_count):
    plt.ion()  # インタラクティブモードON
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.set_title("Profile0")
    ax2.set_title("Profile1")
    ax1.set_xlabel("Wavelength")
    ax1.set_ylabel("Intensity")
    ax2.set_xlabel("Wavelength")
    ax2.set_ylabel("Intensity")

    # Initialize legends for both plots
    legend_profile0 = []
    legend_profile1 = []

    # startbuttonのクリック
    pyautogui.click(*start_button_coordinates)
    # Loop回数を指定
    for i in range(loop_count):
        time.sleep(acquisitiontime / 1000 + 0.3)  # sec
        # Clipboardをクリア
        clipboard.copy("")

        # Profile0をクリップ
        pyautogui.click(*profile0_coordinates)
        time.sleep(0.1)  # sec
        pyautogui.click(*profile0_coordinates2)
        time.sleep(0.1)
        pyautogui.click(*profile0_coordinates3)

        # クリップボードの内容を取得
        Data_Profile0 = clipboard.paste()
        time.sleep(0.1)  # sec
        # クリップボードの内容を表示
        print(f"-----Profile0[Loop {i+1}]-----\n{Data_Profile0}")

        # Clipboardをクリア
        clipboard.copy("")

        # Profile1をクリップ
        pyautogui.click(*profile1_coordinates)
        time.sleep(0.1)  # sec
        pyautogui.click(*profile1_coordinates2)
        time.sleep(0.1)
        pyautogui.click(*profile1_coordinates3)

        # クリップボードの内容を取得
        Data_Profile1 = clipboard.paste()

        # クリップボードの内容を表示
        print(f"-----Profile1[Loop {i+1}]-----\n{Data_Profile1}")
        print(f"-----[Loop {i+2}] Processing...-----")
        logging.info(f"[Loop {i+1}]")
        # クリップボードの内容を基にグラフを描画
        def plot_graph(ax, data_str, legend):
            lines = data_str.split("\n")
            wavelengths, intensities = [], []
            for line in lines:
                if line:
                    w, i = map(float, line.split("\t"))
                    wavelengths.append(w)
                    intensities.append(i)
            ax.plot(wavelengths, intensities, label=legend)  # Add the legend to the plot
            plt.draw()

        # Profile0のデータをグラフに描画
        legend_profile0.append(f"Loop {i+1}")
        plot_graph(ax1, Data_Profile0, legend_profile0)
        ax1.legend(legend_profile0, loc='upper right')  # Add legend to ax1

        # Profile1のデータをグラフに描画
        legend_profile1.append(f"Loop {i+1}")
        plot_graph(ax2, Data_Profile1, legend_profile1)
        ax2.legend(legend_profile1, loc='upper right')  # Add legend to ax2

    plt.ioff()  # インタラクティブモードOFF
    plt.tight_layout
    plt.show()  # 最後にグラフを表示

    print("Finish!!")
    logging.info(f"Normal Termination")# main関数とプログラムの実行部分
def main():
    while True:
        user_input = input("ループ回数: ").strip()
        try:
            loop_count = int(user_input)
            if loop_count > 0:
                break
            else:
                print("０以上の値を入力してください")
        except ValueError:
            print("０以上の値を入力してください")

    while True:
        user_input = input("測定の準備ができたら'Start'と入力してください: ").strip().lower()

        if user_input == "start":
            start_measurement(loop_count)
            break
        else:
            print("有効な文字列を入力してください (start).")

if __name__ == "__main__":
    main()