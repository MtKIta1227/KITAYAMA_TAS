#GPIB1::7::INSTRの装置と接続
# 2021/06/01

import pyvisa
import time

# GPIBのアドレス
address = "GPIB1::7::INSTR"

# GPIBのアドレスに接続
rm = pyvisa.ResourceManager()
inst = rm.open_resource(address)

#IDNコマンドを送信して、装置のIDを取得
inst.write("*IDN?")
print(inst.read())


#現在の遅延ステージの位置を取得
inst.write(