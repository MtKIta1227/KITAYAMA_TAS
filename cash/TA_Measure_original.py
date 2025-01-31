import os, io, time, configparser, logging, serial, datetime
import pyautogui, clipboard, subprocess, json
import pyvisa as visa 
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 装置の初期化
def instrument_initialized():
    global ser, sta, config, FSpeed

    #シャッターの初期化
    print(">>   Connecting to SIGMA MARK-202...")
    logging.info("Connecting to SIGMA MARK-202...")
    time.sleep(1)
    port, baudrate, timeout, parity, bytesize, stopbits, xonxoff, rtscts, dsrdtr = "COM1", 9600, 3, serial.PARITY_NONE, serial.EIGHTBITS, serial.STOPBITS_ONE, False, False, False
    ser = serial.Serial(port, baudrate, timeout=timeout, parity=parity, bytesize=bytesize, stopbits=stopbits, xonxoff=xonxoff, rtscts=rtscts, dsrdtr=dsrdtr)
    logging.info(f"port:{port}, baudrate{baudrate}, timeout={timeout}, parity={parity}, bytesize={bytesize}, stopbits={stopbits}, xonxoff={xonxoff}, rtscts={rtscts}, dsrdtr={dsrdtr}")
    time.sleep(1)
    print(">>   Successful connection to SIGMA MARK-202.")
    logging.info("Successful connection to SIGMA MARK-202.")
    print("open: {0}".format(ser.portstr))
    logging.info(f"open: {ser.portstr}")
    ser.write(b'D:1S5000F5000R1000\r\n')  
    logging.info('S5000F5000R1000')
    time.sleep(1)

    #ステージの初期化
    print(">>   Connecting to SURUGA D220...")
    logging.info("Connecting to SURUGA D220...")
    rm = visa.ResourceManager()
    sta=rm.open_resource('GPIB1::7::INSTR')
    time.sleep(1)
    print(">>   Successful connection to SURUGA D220.")
    logging.info("Successful connection to SURUGA D220.")
    time.sleep(1)
    print(u"Driver ID: ", sta.query("*IDN?"))
    logging.info(f"Driver ID: {sta.query('*IDN?')}")
    time.sleep(0.5)
    print("Initialising...")
    sta.write("AXIs1:DRiverDIVision 1")
    sta.write("AXIs1:Fspeed0 5000")#駆動速度
    FSpeed=sta.query('AXIs1:Fspeed0?')
    time.sleep(0.5)

    print('-------------------- ステージパラメータ--------------------')
    print(f"1パルス移動量(um): {sta.query('AXis1:RESOLUTion?')}")
    logging.info(f"1-pulse travel distance (um): {sta.query('AXis1:RESOLUTion?')}")
    #print(f"定パルス移動量(um): {sta.query('AXis1:PULSe?')}")
    logging.info(f"Constant pulse travel distance (um): {sta.query('AXis1:PULSe?')}")    
    print(f"ドライバ分割数(FULL:0, HALF1):  {sta.query('AXis1:DRiverDIVision?')}")
    logging.info(f"Number of driver divisions (FULL:0, HALF1):  {sta.query('AXis1:DRiverDIVision?')}")
    print(f"分解能(pulse): {sta.query('AXis1:RESOLUTion?')}")
    logging.info(f"Resolution (pulse): {sta.query('AXis1:RESOLUTion?')}")
    print(f"駆動速度(pps): {sta.query('AXIs1:Fspeed0?')}")
    logging.info(f"Drive speed (pps): {sta.query('AXIs1:Fspeed0?')}")
    print('-----------------------------------------------------------')
    time.sleep(1)
    script_directory = os.path.dirname(os.path.abspath(__file__))    # スクリプトのディレクトリの絶対パスを取得
    config_file_path = os.path.join(script_directory, 'config.ini') # config.ini ファイルへの完全なパスを構築
    config = configparser.ConfigParser() # iniファイルの読み込み
    config.read(config_file_path)

    #!!!!!!!!!!!!!!!!!!!!!!!!後で消去!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #原点復帰
    sta.write("AXIs1:Fspeed0 1000")#駆動速度を1000pps設定
    FSpeed=sta.query('AXIs1:Fspeed0?')
    position=sta.query('AXIs1:POSition?') #現在位置を取得
    print(f"現在位置(pulse): {position}")
    print(">>原点復帰中...")
    time_to_zero=int(int(position)/int(FSpeed)+1)
    sta.write('AXIs1:Go ORG') #原点復帰
    time.sleep(time_to_zero)
    position=sta.query('AXIs1:POSition?') #現在位置を取得
    print(f"現在位置(pulse): {position}")

    print("+1000 pulse")
    sta.write("AXIs1:Fspeed0 5000")#駆動速度を設定
    FSpeed=sta.query('AXIs1:Fspeed0?')
    sta.write('AXIs1:PULS 1000:GO 0')#ステージを+1000pulseに移動
    time.sleep(int(1000/int(FSpeed))+1)
    position=sta.query('AXIs1:POSition?') #現在位置を取得
    print(f">>現在位置(pulse): {position}")

    sta.write('AXIS1:POSition -150')    
    position=sta.query('AXIs1:POSition?') #現在位置を取得
    print(f">>現在位置(pulse): {position}")
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    #測定シーケンス
    #print("\n次のパルス間隔で測定予定です:")
    #for section in config.sections():
    #    print(f"\n[{section}]")
    #    for key, value in config.items(section):
    #        print(f"{key}: {value}")
    print("初期化完了\n")
    #time.sleep(1)

# LOGファイルと測定結果ファイルの出力先設定
def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), 'TA_LOG')
    os.makedirs(log_dir, exist_ok=True)
    log_filename = time.strftime("log_%Y%m%d_%H%M%S.log")
    log_file = os.path.join(log_dir, log_filename)
    logging.basicConfig(level=logging.INFO,
                        filename=log_file,
                        filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Start Log")


    # データ保存先のフォルダの設定
    global output_folder_path
    script_directory = os.path.dirname(os.path.realpath(__file__))    # 現在のスクリプトのディレクトリを取得
    output_folder_path = os.path.join(script_directory, 'Raw_TAData')# Raw_TADataフォルダのパスを作成

    # Raw_TADataフォルダが存在しない場合は作成
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

# JSONファイルから変数の値を読み込む
def load_config_from_json():
    # JSONファイルの保存先ディレクトリを指定
    save_dir = os.path.join(os.path.dirname(__file__), 'int')
    json_file_path = os.path.join(save_dir, "config.json")
    
    # JSONファイルから変数の値を読み込む
    logging.info("Get the value of a variable from a JSON file.")
    global start_button_coordinates, profile0_coordinates, profile0_coordinates2, profile0_coordinates3, profile1_coordinates, profile1_coordinates2, profile1_coordinates3
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)
            start_button_coordinates = tuple(data["start_button_coordinates"])
            print(start_button_coordinates)
            profile0_coordinates = tuple(data["profile0_coordinates"])
            print(profile0_coordinates)
            profile1_coordinates = tuple(data["profile1_coordinates"])
            print(profile1_coordinates)
            # Calculate the other coordinates based on the loaded values
            x, y = profile0_coordinates
            profile0_coordinates2 = (x, y + 30)
            profile0_coordinates3 = (x, y + 45)

            x, y = profile1_coordinates
            profile1_coordinates2 = (x, y + 30)
            profile1_coordinates3 = (x, y + 45)
        return start_button_coordinates, profile0_coordinates, profile1_coordinates

# 各座標の登録
def set_coordinates(target):
    logging.info("Coordinate registration")
    global start_button_coordinates, profile0_coordinates, profile0_coordinates2, profile0_coordinates3, profile1_coordinates, profile1_coordinates2, profile1_coordinates3

    x = int(input(f"Enter X coordinate for {target}: "))
    y = int(input(f"Enter Y coordinate for {target}: "))

    if target == 'start':
        global start_button_coordinates
        start_button_coordinates = (x, y)
        logging.info(f"start_button_coordinates: {str(start_button_coordinates)}")   
    
    elif target == 'profile0':
        global profile0_coordinates, profile0_coordinates2, profile0_coordinates3
        profile0_coordinates = (x, y)
        profile0_coordinates2 = (x, y + 30)
        profile0_coordinates3 = (x, y + 45)
        logging.info(f"profile0_coordinates: {str(profile0_coordinates)}")
        logging.info(f"profile0_coordinates2: {str(profile0_coordinates2)}")
        logging.info(f"profile0_coordinates3: {str(profile0_coordinates3)}")

    elif target == 'profile1':
        global profile1_coordinates, profile1_coordinates2, profile1_coordinates3
        profile1_coordinates = (x, y)
        profile1_coordinates2 = (x, y + 30)
        profile1_coordinates3 = (x, y + 45)
        logging.info(f"profile1_coordinates: {str(profile1_coordinates)}")
        logging.info(f"profile1_coordinates2: {str(profile1_coordinates2)}")
        logging.info(f"profile1_coordinates3: {str(profile1_coordinates3)}")

#シャッター
def shutter_rotation(ser, angle):
    global time_rotation
    direction = '+' if angle > 0 else '-'
    rotation_command = f'M:1{direction}P{abs(angle)}\r\n'
    
    ser.write(rotation_command.encode())
    ser.write(b'G:\r\n')
    
    print(f"Shutter switching...")
    logging.info(f"Shutter switching ...")
    time_rotation = int(abs(angle) / 5000) + 0.5
    time.sleep(time_rotation)

#測定
def start_measurement(loop_count, acquisitiontime):
    global excel_data, delta_Abs_data

    # 現在の日時を取得
    current_datetime = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    logging.info(f"Measurement start time: {current_datetime}")

    # excel_dataとdelta_Abs_dataの初期化

    delta_Abs_data = pd.DataFrame()
    
    #ここから測定時間の計測開始
    start = time.time()
    with pd.ExcelWriter(os.path.join(output_folder_path, f'{current_datetime}_TA.xlsx'), engine='xlsxwriter') as writer:
        for i in range(loop_count):

            excel_data = pd.DataFrame([])  # データフレームを空にする
            position = sta.query('AXIs1:POSition?')
            position_to_time = round(int(position) / 15 * 0.1, 2)
            print("----------------------------------------")
            print(f">>POSITION:{str(position)} Pulse")
            print(f">>TIME:{str(position_to_time)} ps")
            logging.info(f"loop count: {i+1}")
            logging.info(f"Measurement position(pulse): {position}")
            pyautogui.click(*start_button_coordinates)

            # ----------------------ポンプ光ありの測定----------------------------
            print("Measuring with pumping ...")
            #logging.info("Measuring with pumping ..")
            clipboard.copy("")
            time.sleep(acquisitiontime / 1000 + 0.2)
            # --------------INTERVAL = DataGet + ShutterCLOSE -------------------
            pyautogui.click(*profile0_coordinates)
            time.sleep(0.1)
            pyautogui.click(*profile0_coordinates2)
            time.sleep(0.1)
            pyautogui.click(*profile0_coordinates3)
            time.sleep(0.1)
            Data_Profile0_excited = clipboard.paste()
            print("Get Data_Profile0_excited")
            #print(f"-----Profile0[Loop {i+1}]-----\n{Data_Profile0_excited}")

            clipboard.copy("")
            pyautogui.click(*profile1_coordinates)
            time.sleep(0.1)
            pyautogui.click(*profile1_coordinates2)
            time.sleep(0.1)
            pyautogui.click(*profile1_coordinates3)
            time.sleep(0.1)
            Data_Profile1_excited = clipboard.paste()
            print("GET Data_Profile1_excited")
            #print(f"-----Profile1[Loop {i+1}]-----\n{Data_Profile1_excited}")
            #logging.info("Measured with pumping!")

            shutter_rotation(ser, 18000)  # Shutterを閉じる
            print("Shutter CLOSED.")
            #logging.info("Shutters closed.")
            # ----------------------ポンプ光なしの測定---------------------------
            pyautogui.click(*start_button_coordinates)
            print("Measuring withOUT pumping ...")
            #logging.info("Measuring withOUT pumping ...")
            clipboard.copy("")
            time.sleep(acquisitiontime / 1000 + 0.2)
            # --------------INTERVAL = DataGet + ShutterOPEN ----------------
            pyautogui.click(*profile0_coordinates)
            time.sleep(0.1)
            pyautogui.click(*profile0_coordinates2)
            time.sleep(0.1)
            pyautogui.click(*profile0_coordinates3)
            time.sleep(0.1)
            Data_Profile0 = clipboard.paste()
            print("GER Data_Profile0")
            #print(f"-----Profile0[Loop {i+1}]-----\n{Data_Profile0}")

            clipboard.copy("")
            pyautogui.click(*profile1_coordinates)
            time.sleep(0.1)
            pyautogui.click(*profile1_coordinates2)
            time.sleep(0.1)
            pyautogui.click(*profile1_coordinates3)
            time.sleep(0.1)
            Data_Profile1 = clipboard.paste()
            print("GET Data_Profile1")
            #logging.info("Measured withOUT pumping ...")

            #print(f"-----Profile1[Loop {i+1}]-----\n{Data_Profile1}")

            shutter_rotation(ser, -18000)  # Shutterを開ける
            print("Shutters  OPENED.")
            #logging.info("Shutters  opened.")

            # ---------------INTERVAL= STAGE移動-------------------------------------------

            # ポンプ光ありのデータをデータフレームに追加
            df_excited = pd.read_csv(io.StringIO(Data_Profile0_excited), sep='\t', header=None,
                                     names=['Wavelength/nm', f'I_Sam_Ex_{position}'])
            excel_data = pd.concat([excel_data, df_excited.set_index('Wavelength/nm')], axis=1, sort=False)

            df_excited = pd.read_csv(io.StringIO(Data_Profile1_excited), sep='\t', header=None,
                                     names=['Wavelength/nm', f'I_Ref_Ex_{position}'])
            excel_data = pd.concat([excel_data, df_excited.set_index('Wavelength/nm')], axis=1, sort=False)

            # ポンプ光なしのデータをデータフレームに追加
            df_normal = pd.read_csv(io.StringIO(Data_Profile0), sep='\t', header=None,
                                    names=['Wavelength/nm', f'I_Sam_{position}'])
            excel_data = pd.concat([excel_data, df_normal.set_index('Wavelength/nm')], axis=1, sort=False)

            df_normal = pd.read_csv(io.StringIO(Data_Profile1), sep='\t', header=None,
                                    names=['Wavelength/nm', f'I_Ref_{position}'])
            excel_data = pd.concat([excel_data, df_normal.set_index('Wavelength/nm')], axis=1, sort=False)

            # delta_Absの計算
            profile1 = np.loadtxt(io.StringIO(Data_Profile1), delimiter='\t')
            profile1_excited = np.loadtxt(io.StringIO(Data_Profile1_excited), delimiter='\t')
            profile0 = np.loadtxt(io.StringIO(Data_Profile0), delimiter='\t')
            profile0_excited = np.loadtxt(io.StringIO(Data_Profile0_excited), delimiter='\t')   
            delta_Abs = np.log(profile0[:, 1] * profile1_excited[:, 1] / (profile1[:, 1] * profile0_excited[:, 1]))

            # delta_Absを新しいデータフレームに追加
            delta_Abs_df = pd.DataFrame({'Wavelength/nm': profile1[:, 0], f'{position_to_time}': delta_Abs})
            delta_Abs_data = pd.concat([delta_Abs_data, delta_Abs_df.set_index('Wavelength/nm')], axis=1, sort=False)


            # エクセルファイルに保存
            print("Save to Excel file")
            print(f"Stage Moving...")
            #logging.info("Save to Excel file\n")
            delta_Abs_data.reset_index().to_excel(writer, sheet_name='delta ABS', index=False)
            excel_data.reset_index().to_excel(writer, sheet_name=f'{position}_{position_to_time}ps', index=False)
            
            # グラフの作成(OPTIONAL)
            graph_timing=int(i+1)
            # ループ数が1５の倍数の場合にグラフ化
            if (graph_timing % 15 == 0) and (graph_timing >= 80):
                # 最新の５つのデータを取得
                recent_data = delta_Abs_data.iloc[:, -15:]

                # グラフの作成
                plt.figure(figsize=(10, 6))
                for col in recent_data.columns:
                    plt.plot(recent_data.index, recent_data[col], label=col)

                plt.xlabel('Wavelength/nm')
                plt.ylabel('Delta Abs')
                plt.title('Recent Delta Abs Data')
                plt.legend()
                plt.grid(True)
                plt.show()

            #ステージ移動
            stepsize = int(config.get('PulseSettings', f'Loop_{i+1}_stepsize'))
            sta.write(f'AXIs1:PULS {stepsize}:GO 0')
            #logging.info(f"STAGE in operation...")
            time.sleep(stepsize/int(FSpeed)+1)

    
    #測定時間の計測終了
    elapsed_time = time.time() - start

    #測定時間をhmsに変換
    m, s = divmod(elapsed_time, 60)
    h, m = divmod(m, 60)
    logging.info(f"Measurement time:{h:.0f}h {m:.0f} min {s:.0f} sec")
    logging.info(f"Normal Termination")# main関数とプログラムの実行部分
    print("\n")
    print("----------------------------------------")
    print("Measurement completed!!")
    print(f"Measurement time:{h:.0f}h {m:.0f} min {s:.0f} sec")
    print("----------------------------------------")
    logging.info("Measurement completed!!")
    ser.close()

#main
def main():
    print("╔════════════════════════════════════════════╗")
    print("║     ~ TA Measurement Program ~  ver 2.1    ║")
    print("╚════════════════════════════════════════════╝")

    # ログの設定
    setup_logging()

    # 装置の初期化
    #instrument_initialized()
    #input("装置の設定がよければ'Enter'を押してください。")

    # WindowSpyの起動
    #file_path = r'C:\Users\USER\Desktop\Laser_Program\03_TA\Measurement\operation_test\WindowSpy.ahk'
    #subprocess.Popen(file_path, shell=True)

    # jsonファイルの読み込み
    load_config_from_json()

    # ターゲットの座標を設定
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

    data = {                                                   
        "start_button_coordinates": start_button_coordinates,
        "profile0_coordinates": profile0_coordinates,
        "profile1_coordinates": profile1_coordinates
        }
    save_dir = os.path.join(os.path.dirname(__file__), 'int') # dataをJSONファイルに保存
    json_file_path = os.path.join(save_dir, "config.json")
    os.makedirs(save_dir, exist_ok=True)
    with open(json_file_path, "w") as json_file:
        json.dump(data, json_file)

    #測定条件の設定（露光時間と積算回数）
    while True:
        expoduretime = float(input("Enter Expodure time (in milliseconds): "))
        integration = float(input("Enter integration: "))
        acquisitiontime = expoduretime * integration
        user_input = input("ループ回数(): ").strip()
        try:
            loop_count = int(user_input)
            if loop_count > 0:
                break
            else:
                print("０以上の値を入力してください")
        except ValueError:
            print("０以上の値を入力してください")

    #測定開始
    while True:
        user_input = input("測定の準備ができたら'start'と入力してください: ").strip().lower()
        if user_input == "start":
            start_measurement(loop_count, acquisitiontime)
            break
        else:
            print("有効な文字列を入力してください (start).")
    
    input("終了するには'Enter'を押してください。")
            
if __name__ == "__main__":
    main()