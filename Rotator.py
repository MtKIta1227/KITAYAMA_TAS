import pyvisa

#接続されているデバイスのリストを取得
rm = pyvisa.ResourceManager()
devices = rm.list_resources()

#デバイスのリストを表示
print(devices)
