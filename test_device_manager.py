#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.device_manager import DeviceManager

def test_device_manager():
    print("测试设备管理器...")
    
    # 创建设备管理器实例
    dm = DeviceManager()
    
    print(f"加载的MAC映射数量: {len(dm.mac_to_name)}")
    
    # 显示前几个MAC映射
    print("\n前5个MAC映射:")
    count = 0
    for mac, name in dm.mac_to_name.items():
        if count >= 5:
            break
        print(f"  {mac} = {name}")
        count += 1
    
    # 获取可使用设备
    print("\n正在获取可使用设备...")
    usable_devices = dm.get_usable_devices()
    
    print(f"\n可使用设备数量: {len(usable_devices)}")
    
    if usable_devices:
        print("\n可使用设备详情:")
        for device in usable_devices:
            print(f"  {device['name']} ({device['ip']}) [MAC: {device['mac']}]")
    else:
        print("未发现可使用设备")

if __name__ == "__main__":
    test_device_manager()