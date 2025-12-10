#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.adb_utils import ADBUtils

def test_install_apk():
    print("测试APK安装功能...")
    
    # 这里需要提供一个有效的设备ID和APK路径进行测试
    # 由于我们没有真实的设备和APK，我们将演示诊断功能
    
    # 模拟一个不存在的APK文件测试
    print("\n1. 测试不存在的APK文件:")
    result = ADBUtils.install_apk("emulator-5554", "nonexistent.apk")
    print(f"成功: {result['success']}")
    print(f"错误: {result['error']}")
    
    # 测试诊断功能
    print("\n2. 测试诊断功能:")
    diagnosis = ADBUtils.diagnose_install_issue("emulator-5554", "nonexistent.apk")
    for item in diagnosis:
        print(item)
    
    # 测试ADB版本
    print("\n3. 测试ADB版本:")
    version_result = ADBUtils.run_adb_command("version")
    if version_result["success"]:
        print(f"ADB版本: {version_result['output']}")
    else:
        print(f"ADB错误: {version_result['error']}")

if __name__ == "__main__":
    test_install_apk()