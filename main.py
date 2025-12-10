#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
adb助手 v1.0
程序入口文件
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow
import os

def main():
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用图标
    if getattr(sys, "frozen", False):
        icon_path = os.path.join(sys._MEIPASS, "ui", "icons", "android.ico")
    else:
        icon_path = "ui/icons/android.ico"
    app.setWindowIcon(QIcon(icon_path))
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()