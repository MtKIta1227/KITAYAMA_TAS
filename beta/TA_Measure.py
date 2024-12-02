import os
import time
import logging
import pyvisa as visa
import serial
import serial.tools.list_ports
import subprocess
import json

# コンフィグ設定
def setup_config():
    # ログファイルの設定
    log_dir = os.path.join(os.path.dirname(__file__), 'TA_LOG')
    os.makedirs(log_dir, exist_ok=True)
    log_filename = time.strftime('TAlog_%Y%m%d_%H%M%S') + '.log'
    log_file = os.path.join(log_dir, log_filename)
    logging.basicConfig(level=logging.INFO, filename=log_file, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('Start TA Measurement Program')

    # データの保存先フォルダの設定
    global output_folder_path
    script_dir = os.path.dirname(os.path.realpath(__file__)) # スクリプトのディレクトリを取得
    output_folder_path = os.path.join(script_dir, 'TA_DATA') # データの保存先フォルダをスクリプトのディレクトリに設定
    print('データの保存先フォルダ:', output_folder_path)
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
        logging.info('Create output folder: %s' % output_folder_path)


# 座標の設定
def set_coordinates():
    global start_button_coordinates, profile0_coordinates, profile0_coordinates2, profile0_coordinates3, profile1_coordinates, profile1_coordinates2, profile1_coordinates3


# 接続されている機器のリストを取得
def get_connected_devices():
    global devices, rm
    rm = visa.ResourceManager()
    devices = rm.list_resources()
    print('接続されている機器:', devices)
    logging.info('Connected devices: %s' % devices)



# 遅延ステージの初期化
def init_stage():
    global ser, sta, config, FSpeed
    print('\n>> 遅延ステージへの接続テストを行います')
    if 'GPIB1::7::INSTR' not in devices:
        print('SURUGA D220が接続されていません')
        logging.error('SURUGA D220 is not connected')
        while True:
            user_input = input('>> 再接続テストを行いますか？ (Enter: 再接続, p: スキップ): ')
            if user_input == '':
                if 'GPIB1::7::INSTR' in devices:
                    print('SURUGA D220が接続されました')
                    logging.info('SURUGA D220 is connected')
                    break
                else:
                    print('再接続に失敗しました。もう一度試してください。')
                    logging.error('Failed to reconnect SURUGA D220')
            elif user_input.lower() == 'p':
                print('D220への接続テストをスキップします')
                logging.info('Skipped connection test for SURUGA D220')
                break
            else:
                print('無効な入力です。再度入力してください。')
    else:
        print('SURUGA D220が接続されました')
        logging.info('Connected to SURUGA D220')


# coordinates_configの設定
def load_coordinates_config_from_json():
    global coordinates_config
    coordinates_config = {}
    json_file_path = os.path.join(os.path.dirname(__file__), 'ini', 'coordinates_config.json')

    print('JSONファイルが存在するか確認します')
    if os.path.exists(json_file_path):
        print('JSONファイルが見つかりました')
        with open(json_file_path, 'r') as f:
            coordinates_config = json.load(f)
            logging.info('Loaded coordinates_config from coordinates_config.json')
    else:
        print('JSONファイルが見つかりません')
        with open(json_file_path, 'w') as f:
            json.dump(coordinates_config, f, indent=4)
            logging.info('Created coordinates_config.json')

    try:
        start_button_coordinates = tuple(coordinates_config['start_button_coordinates'])
        profile0_coordinates = tuple(coordinates_config['profile0_coordinates'])
        profile1_coordinates = tuple(coordinates_config['profile1_coordinates'])

        print('\n>> 登録されている座標を表示します')
        print('-----------------------------------------------------')
        print('start_button_coordinates:', start_button_coordinates)
        print('profile0_coordinates:', profile0_coordinates)
        print('profile1_coordinates:', profile1_coordinates)
        print('-----------------------------------------------------')

        start_button_coordinates = confirm_change('start_button_coordinates', start_button_coordinates)
        profile0_coordinates = confirm_change('profile0_coordinates', profile0_coordinates)
        profile1_coordinates = confirm_change('profile1_coordinates', profile1_coordinates)

        profile0_coordinates2 = (profile0_coordinates[0], profile0_coordinates[1] + 30)
        profile0_coordinates3 = (profile0_coordinates[0], profile0_coordinates[1] + 45)
        profile1_coordinates2 = (profile1_coordinates[0], profile1_coordinates[1] + 30)
        profile1_coordinates3 = (profile1_coordinates[0], profile1_coordinates[1] + 45)
        print('\n >> 最終的な座標を表示は以下の通りです。')
        print('-----------------------------------------------------')
        print('start_button_coordinates:', start_button_coordinates)
        print('profile0_coordinates:', profile0_coordinates)
        print('profile1_coordinates:', profile1_coordinates)
        print('-----------------------------------------------------')
        return (start_button_coordinates,
                profile0_coordinates, profile0_coordinates2, profile0_coordinates3,
                profile1_coordinates, profile1_coordinates2, profile1_coordinates3)

    except KeyError as e:
        logging.error(f'JSONファイルが見つかりません: {e}')
        set_coordinates_manually(json_file_path)


# 座標の変更を確認
def confirm_change(name, current_value):
    while True:
        change = input(f'\n>> {name}の値を変更しますか？ (y/n): ')
        if change.lower() == 'y':
            new_value = input(f'>> 新しい{name}を入力してください (例: 100,200): ')
            try:
                new_tuple = tuple(map(int, new_value.split(',')))
                print(f'{name}の値を({new_value})に変更しました')
                return new_tuple
            except ValueError:
                print('無効な形式です。整数のペアで入力してください。')
        elif change.lower() == 'n':
            return current_value
        else:
            print('無効な入力です。再度入力してください。')


# 座標を任意入力
def set_coordinates_manually(json_file_path):
    global coordinates_config
    print('座標を設定してください。')

    while True:
        try:
            start_button_coordinates = input('start_button_coordinatesを入力してください (例: 100,200): ')
            profile0_coordinates = input('profile0_coordinatesを入力してください (例: 100,150): ')
            profile1_coordinates = input('profile1_coordinatesを入力してください (例: 100,300): ')

            coordinates_config['start_button_coordinates'] = list(map(int, start_button_coordinates.split(',')))
            coordinates_config['profile0_coordinates'] = list(map(int, profile0_coordinates.split(',')))
            coordinates_config['profile1_coordinates'] = list(map(int, profile1_coordinates.split(',')))

            with open(json_file_path, 'w') as f:
                json.dump(coordinates_config, f, indent=4)
                logging.info('Updated coordinates_config.json with new values')

            print('座標が更新されました。')
            print('-----------------------------------------------------')
            print('start_button_coordinates:', start_button_coordinates)
            print('profile0_coordinates:', profile0_coordinates)
            print('profile1_coordinates:', profile1_coordinates)
            print('-----------------------------------------------------')
            break

        except ValueError:
            print('無効な形式です。整数のペアで入力してください。')

    start_button_coordinates = confirm_change('start_button_coordinates', tuple(coordinates_config['start_button_coordinates']))
    profile0_coordinates = confirm_change('profile0_coordinates', tuple(coordinates_config['profile0_coordinates']))
    profile1_coordinates = confirm_change('profile1_coordinates', tuple(coordinates_config['profile1_coordinates']))

    print('\n>> 最終的な座標を表示は以下の通りです。')
    print('-----------------------------------------------------')
    print('start_button_coordinates:', start_button_coordinates)
    print('profile0_coordinates:', profile0_coordinates)
    print('profile1_coordinates:', profile1_coordinates)
    print('-----------------------------------------------------')
    print('priofile0_coordinates2:', profile0_coordinates2)
    print('priofile0_coordinates3:', profile0_coordinates3)
    print('priofile1_coordinates2:', profile1_coordinates2)
    print('priofile1_coordinates3:', profile1_coordinates3)
    print('-----------------------------------------------------')


# 測定条件の設定(露光時間と積算回数)
def set_measurement_conditions():
    global exposure_time,integration, accumulation_count
    while True:
        try:
            exposure_time = float(input('Exposure time (msec)を入力してください: '))
            integration = float(input('Integrationを入力してください: '))
            accumulation_count = float(exposure_time * integration/1000) #sec換算
            print(f"exposure_time: {exposure_time} ms, Integration: {integration}, 測定時間: {accumulation_count} sec")
            confirm = input('値を確認してください。変更しますか？ (y/n): ').strip().lower()
            if confirm == 'n':
                break  
        # 数値以外の入力があった場合のエラー処理
        except ValueError:
            print("無効な入力です。数値を入力してください。")
    print('\n>> 測定条件を設定しました')
    print('-----------------------------------------------------')
    print(f"露光時間: {exposure_time} msec")
    print(f"積算回数: {integration}")
    print(f"測定時間: {accumulation_count} sec")
    print('-----------------------------------------------------')
    return exposure_time, integration, accumulation_count
        
        
# シャッターの初期化
def init_shutter():
    print('シャッターへの接続テストを行います')
    logging.info('シャッターの初期化を開始します')
    
    global arduino
    com_port = 'COM4'
    
    while True:
        available_ports = [com.device for com in serial.tools.list_ports.comports()]
        
        if com_port not in available_ports:
            print(f'{com_port}でシャッターに接続できませんでした')
            logging.error(f'{com_port}への接続に失敗しました')

            user_input = input('>> 再接続テストを行いますか？ (Enter: 再接続, p: スキップ): ').strip().lower()

            if user_input == '':
                continue
            elif user_input == 'p':
                print('接続テストをスキップします')
                logging.info('シャッターの接続テストをスキップしました')
                break
            else:
                print('無効な入力です。再度入力してください。')
        else:
            try:
                arduino = serial.Serial(com_port, 9600, timeout=1)
                time.sleep(2)

                if arduino.is_open:
                    print(f'{com_port}でシャッターに接続しました')
                    logging.info(f'{com_port}にシャッターが接続されました')
                break
            except Exception as e:
                print(f'接続中にエラーが発生しました: {e}')
                logging.error(f'接続中にエラーが発生しました: {e}')


import os
import json
import logging

# パルス設定の読み込み
def load_pulse_config_from_json():
    global pulse_config
    pulse_config = {}
    # JSONファイルのパスはpythonファイルがある同じ階層にあるiniフォルダ内
    json_file_path = os.path.join(os.path.dirname(__file__), 'ini_test', 'pulse_config.json')

    print('JSONファイルが存在するか確認します')
    
    if os.path.exists(json_file_path):
        print('JSONファイルが見つかりました。既存の設定を使用しますか？ (y/n)')
        use_existing = input().lower()
        if use_existing == 'y':
            with open(json_file_path, 'r') as f:
                pulse_config = json.load(f)
                logging.info('Loaded pulse_config from pulse_config.json')
            print('既存の設定を使用します。')
            # 既存の設定を変更するためのプロセスに入る
            update_existing_config()
        else:
            print('新しい設定を作成します。')
            create_empty_pulse_config(json_file_path)
            set_pulse_config()
    else:
        print('JSONファイルが見つかりません。新しく作成します。')
        create_empty_pulse_config(json_file_path)
        set_pulse_config()

def create_empty_pulse_config(json_file_path):
    # 空のJSONファイルを作成
    with open(json_file_path, 'w') as f:
        json.dump(pulse_config, f, indent=4)
        logging.info('Created pulse_config.json')

def set_pulse_config():
    print('各ループごとのステップサイズを設定します。')
    
    while True:
        try:
            loop = int(input('>> ループ番号を入力してください (整数): '))
            stepsize = int(input('>> ステップサイズを入力してください (整数): '))
            
            pulse_config[loop] = stepsize
            print(f'ループ {loop} にステップサイズ {stepsize} を追加しました。')

            cont = input('\n>> Enterで続けてループを追加 (okと入力で終了): ')
            if cont.lower() == 'ok':
                break

        except ValueError:
            print('無効な入力です。整数を入力してください。')

    # 設定内容の確認
    confirm_pulse_config()

def update_existing_config():
    print('既存の設定を変更します。')
    confirm_pulse_config()

def confirm_pulse_config():
    print('最終的なパルス設定を確認します:')
    print('-----------------------------------------------------')
    for loop, stepsize in pulse_config.items():
        print(f'ループ {loop}: ステップサイズ {stepsize}')
    print('-----------------------------------------------------')

    while True:
        change = input('変更が必要な場合はループ番号を入力してください (終了する場合は"ok"と入力): ')
        if change.lower() == 'ok':
            break
        try:
            loop = int(change)
            if loop in pulse_config:
                new_stepsize = int(input(f'新しいステップサイズを入力してください (ループ {loop}): '))
                pulse_config[loop] = new_stepsize
                print(f'ループ {loop} のステップサイズを {new_stepsize} に変更しました。')
            else:
                print('そのループ番号は存在しません。')
        except ValueError:
            print('無効な入力です。整数を入力してください。')

    # 最終設定をJSONに書き込む
    save_pulse_config()

def save_pulse_config():
    json_file_path = os.path.join(os.path.dirname(__file__), 'ini', 'pulse_config.json')
    with open(json_file_path, 'w') as f:
        json.dump(pulse_config, f, indent=4)
        logging.info('Updated pulse_config.json with new values')
    print('設定が保存されました。')

# 関数のテスト
if __name__ == "__main__":
    load_pulse_config_from_json()

def main():
    print("╔════════════════════════════════════════════╗")
    print("║     ~ TA Measurement Program ~  20240913   ║")
    print("╚════════════════════════════════════════════╝")

    # コンフィグ設定
    setup_config()

    # 装置の初期化
    print('\n>> 各装置への接続テストを行います')
    get_connected_devices() # 接続されている機器のリストを取得
    init_stage() # 遅延ステージの初期化
    init_shutter() # シャッターの初期化

    # パスを指定してWindowSpy.ahkを実行
    windowspy_path = "C:\\Program Files\\AutoHotkey\\WindowSpy.ahk"
    subprocess.Popen([windowspy_path], shell=True)

    # JSONファイルの読み込み（保存しておいた初期値の読み込み）
    print('\n>> JSONファイルから座標を読み込みます')
    load_coordinates_config_from_json()

    # 座標の設定
    set_coordinates()

    # 測定条件の設定(露光時間と積算回数)
    print('\n>> 測定条件を設定します')
    set_measurement_conditions()\
    
    #各ループにおけるステップサイズを設定
    load_pulse_config_from_json()
    
    # 測定

if __name__ == '__main__':
    main()