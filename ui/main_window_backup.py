#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
adb助手 v1.0
主窗口UI模块
"""

import sys
import logging
import subprocess
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QListWidget, QLabel, QGroupBox, 
                               QProgressBar, QTextEdit, QSplitter, QApplication,
                               QDialog, QFileDialog, QLineEdit, QFormLayout, QMessageBox,
                               QInputDialog)
from PySide6.QtCore import Qt, QTimer, QProcess, QThread, Signal

# 导入设备管理器
from core.device_manager import DeviceManager

logger = logging.getLogger(__name__)

class InstallWorker(QThread):
    """安装应用的后台工作线程"""
    finished = Signal(dict)  # 发送结果信号
    
    def __init__(self, device_id, apk_path):
        super().__init__()
        self.device_id = device_id
        self.apk_path = apk_path
    
    def run(self):
        try:
            # 使用新的ADB工具类
            from core.adb_utils import ADBUtils
            result = ADBUtils.install_apk(self.device_id, self.apk_path)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class ConnectWorker(QThread):
    """连接设备的后台工作线程"""
    finished = Signal(dict)
    
    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
    
    def run(self):
        try:
            from core.adb_utils import ADBUtils
            result = ADBUtils.connect_device(self.ip_address)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class ClearCacheWorker(QThread):
    """清除缓存的后台工作线程"""
    finished = Signal(dict)
    
    def __init__(self, device_id, package_name):
        super().__init__()
        self.device_id = device_id
        self.package_name = package_name
    
    def run(self):
        try:
            from core.adb_utils import ADBUtils
            result = ADBUtils.clear_app_cache(self.device_id, self.package_name)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class KillProcessWorker(QThread):
    """杀掉进程的后台工作线程"""
    finished = Signal(dict)
    
    def __init__(self, device_id, package_name):
        super().__init__()
        self.device_id = device_id
        self.package_name = package_name
    
    def run(self):
        try:
            from core.adb_utils import ADBUtils
            result = ADBUtils.force_stop_app(self.device_id, self.package_name)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class UninstallWorker(QThread):
    """卸载应用的后台工作线程"""
    finished = Signal(dict)
    
    def __init__(self, device_id, package_name):
        super().__init__()
        self.device_id = device_id
        self.package_name = package_name
    
    def run(self):
        try:
            from core.adb_utils import ADBUtils
            result = ADBUtils.uninstall_app(self.device_id, self.package_name)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class DisconnectWorker(QThread):
    """断开连接的后台工作线程"""
    finished = Signal(dict)
    
    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id
    
    def run(self):
        try:
            from core.adb_utils import ADBUtils
            result = ADBUtils.disconnect_device(self.device_id)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_id = None
        self.device_manager = DeviceManager()
        self.current_worker = None  # 当前后台工作线程
        self.init_ui()
        
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("adb助手 v1.0")
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置窗口样式，移除可能的分隔线
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                padding: 5px 10px;
                margin: 2px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget, QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #ffffff;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)  # 减少控件间距
        main_layout.setContentsMargins(5, 5, 5, 5)  # 减少边距
        
        # 创建顶部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)  # 减少按钮间距
        
        self.refresh_btn = QPushButton("刷新设备")
        self.my_devices_btn = QPushButton("我的设备")
        self.connect_btn = QPushButton("连接IP")
        self.disconnect_btn = QPushButton("断开连接")
        self.install_btn = QPushButton("安装应用")
        self.kill_process_btn = QPushButton("杀掉进程")
        self.clear_cache_btn = QPushButton("清除缓存")
        self.uninstall_btn = QPushButton("卸载应用")
        self.screen_mirror_btn = QPushButton("设备画面")
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.my_devices_btn)
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.kill_process_btn)
        button_layout.addWidget(self.clear_cache_btn)
        button_layout.addWidget(self.uninstall_btn)
        button_layout.addWidget(self.screen_mirror_btn)
        button_layout.addStretch()
        
        # 创建包名显示区域
        package_group = QGroupBox("常用包名")
        package_layout = QVBoxLayout(package_group)
        package_layout.setContentsMargins(5, 15, 5, 5)  # 减少边距
        
        self.package_list = QTextEdit()
        self.package_list.setReadOnly(True)
        self.load_packages()
        package_layout.addWidget(self.package_list)
        
        # 创建设备列表区域
        device_group = QGroupBox("设备列表")
        device_layout = QVBoxLayout(device_group)
        device_layout.setContentsMargins(5, 15, 5, 5)  # 减少边距
        
        self.device_list = QListWidget()
        # 注意：移除了双击连接设备的功能，防止自动连接
        device_layout.addWidget(self.device_list)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 设置为不确定模式
        
        # 创建日志显示区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 15, 5, 5)  # 减少边距
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        
        # 添加所有组件到主布局
        main_layout.addLayout(button_layout)
        main_layout.addWidget(package_group)
        main_layout.addWidget(device_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(log_group)
        
        # 连接信号槽
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.my_devices_btn.clicked.connect(self.show_my_devices)
        self.connect_btn.clicked.connect(self.connect_ip)
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.install_btn.clicked.connect(self.install_app)
        self.kill_process_btn.clicked.connect(self.kill_process)
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.uninstall_btn.clicked.connect(self.uninstall_app)
        self.screen_mirror_btn.clicked.connect(self.screen_mirror)
        self.device_list.itemClicked.connect(self.select_device)
        
        # 初始化设备列表
        self.refresh_devices()
        
    def load_packages(self):
        """加载并显示包名列表"""
        packages_text = """商店包名:
com.tcl.appmarket2
com.changhong.appstore
com.huantv.appstore 
com.gxyx.appstore
com.gzgd.appstore
com.hbgd.appstore
com.yuedao.appstore
com.haier.tv.appstore
com.booslink.appstore 
com.jixin.appstore1
com.huantv.appstore
com.baseus.appstore
com.pandala.appstore
com.joydon.appstore

常用包名:
tv.huan.tvhelper
tv.huan.appdist_newsmy 
com.xiaodianshi.tv.yst
com.ktcp.csvideo
com.putao.PtSanguo
com.hongen.app.word.ott
fun.yecao.helper

流量监控包名:
infeed.advertisement.demo
es.infeed.advertisement.demo"""
        
        self.package_list.setText(packages_text)
        
    def refresh_devices(self):
        """刷新ADB连接的设备列表"""
        self.log("正在刷新ADB设备列表...")
        try:
            devices = self.device_manager.get_connected_devices()
            self.device_list.clear()
            
            if devices:
                self.log("ADB连接的设备:")
                for device in devices:
                    device_id = device['id']
                    status = device['status']
                    # 获取设备名称
                    device_name = self.device_manager.get_device_name(device_id)
                    # 添加设备到列表
                    self.device_list.addItem(f"{device_name} - {device_id} ({status})")
                self.log(f"共找到 {len(devices)} 个ADB设备")
            else:
                self.log("未发现ADB连接的设备")
                self.device_list.addItem("未发现ADB连接的设备")
        except Exception as e:
            self.log(f"刷新ADB设备列表时出错: {e}")
            
    def show_my_devices(self):
        """显示我的设备列表（在操作日志中展示可连接的设备IP）"""
        self.log("正在获取我的设备列表...")
        try:
            my_devices = self.device_manager.get_usable_devices()
            # 注意：这里不再清空或更新设备列表，只在操作日志中显示信息
            
            if my_devices:
                self.log("我的设备（局域网内发现，IP地址可直接复制）:")
                self.log("=" * 50)
                for i, device in enumerate(my_devices, 1):
                    self.log(f"{i}. {device['name']}")
                    # IP地址单独一行显示，方便复制
                    self.log(device['ip'])
                    self.log(f"MAC: {device['mac']}")
                    self.log("-" * 30)
                self.log(f"共找到 {len(my_devices)} 个设备")
                self.log("=" * 50)
                self.log("提示: 点击上方IP地址可直接复制，然后点击'连接IP'按钮进行连接")
            else:
                self.log("未发现我的设备")
        except Exception as e:
            self.log(f"获取我的设备时出错: {e}")
            
    def show_usable_devices(self):
        """显示可使用设备（保持向后兼容）"""
        self.show_my_devices()
        
    def connect_ip(self):
        """连接IP"""
        ip, ok = QInputDialog.getText(self, "连接设备", "请输入IP地址:")
        if ok and ip:
            # 格式化IP地址
            if not ":" in ip and not ip.startswith("192.168"):
                full_ip = f"192.168.{ip}:5555"
            elif not ":" in ip:
                full_ip = f"{ip}:5555"
            else:
                full_ip = ip
                
            self.log(f"准备连接 {full_ip}...")
            worker = ConnectWorker(full_ip)
            self.start_worker(worker, self.on_connect_finished)
            
    def select_device(self, item):
        """选择设备"""
        device_info = item.text()
        # 提取设备ID (在第二个破折号之后的部分)
        parts = device_info.split(' - ')
        if len(parts) > 1:
            id_and_status = parts[1]
            self.device_id = id_and_status.split(' ')[0]  # 提取设备ID
        else:
            self.device_id = device_info.split(' ')[0]  # 备用方案
            
        self.log(f"已选择设备: {self.device_id}")
        
    def start_worker(self, worker, callback):
        """启动后台工作线程"""
        self.current_worker = worker
        self.current_worker.finished.connect(callback)
        self.current_worker.finished.connect(self.on_worker_finished)
        self.progress_bar.setVisible(True)
        self.current_worker.start()
        
    def on_worker_finished(self):
        """工作线程完成后的处理"""
        self.progress_bar.setVisible(False)
        self.current_worker = None
        
    def install_app(self):
        """安装应用"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK Files (*.apk)")
        if file_path:
            self.log(f"准备安装 {file_path} 到设备 {self.device_id}...")
            worker = InstallWorker(self.device_id, file_path)
            self.start_worker(worker, self.on_install_finished)
            
    def on_install_finished(self, result):
        """安装完成的回调"""
        if result["success"]:
            self.log(f"安装成功: {result['output']}")
        else:
            self.log(f"安装失败: {result['error']}")
            # 如果错误信息包含诊断信息，单独显示
            if "诊断信息" in result['error']:
                self.log("=" * 50)
                self.log("安装问题诊断:")
                self.log("-" * 30)
                # 分行显示诊断信息
                lines = result['error'].split('\n')
                for line in lines:
                    if line.strip():
                        self.log(line)
                self.log("=" * 50)
            
    def connect_device_from_list(self, item):
        """从设备列表双击连接设备"""
        try:
            item_text = item.text()
            
            if item_text.startswith("[LAN]"):
                # LAN设备: [LAN] 设备名 - IP地址
                if " - " in item_text:
                    # 从列表项中提取IP地址
                    ip_address = item_text.split(" - ")[1]
                    self.log(f"准备连接设备: {ip_address}")
                    
                    # 使用工作线程连接设备
                    worker = ConnectWorker(f"{ip_address}:5555")
                    self.start_worker(worker, self.on_connect_finished)
                else:
                    self.log("无法从该项提取IP地址")
            elif item_text.startswith("[ADB]"):
                # ADB设备已经是连接状态，不需要再次连接
                self.log("该设备已经通过ADB连接")
            else:
                # 默认处理，假设是IP地址
                if " - " in item_text:
                    # 从列表项中提取IP地址
                    ip_address = item_text.split(" - ")[1].split(' ')[0]
                    self.log(f"准备连接设备: {ip_address}")
                    
                    # 使用工作线程连接设备
                    worker = ConnectWorker(f"{ip_address}:5555")
                    self.start_worker(worker, self.on_connect_finished)
                else:
                    self.log("无法从该项提取IP地址")
        except Exception as e:
            self.log(f"连接设备时出错: {e}")
            
    def on_connect_finished(self, result):
        """连接完成的回调"""
        if result["success"]:
            self.log(f"连接成功: {result['output']}")
        else:
            self.log(f"连接失败: {result['error']}")
        # 刷新设备列表
        self.refresh_devices()
            
    def clear_cache(self):
        """清除缓存"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        package, ok = QInputDialog.getText(self, "清除缓存", "请输入包名:")
        if ok and package:
            self.log(f"准备清除 {package} 的缓存...")
            worker = ClearCacheWorker(self.device_id, package)
            self.start_worker(worker, self.on_clear_cache_finished)
            
    def on_clear_cache_finished(self, result):
        """清除缓存完成的回调"""
        if result["success"]:
            self.log(f"清除缓存成功: {result['output']}")
        else:
            self.log(f"清除缓存失败: {result['error']}")
            
    def kill_process(self):
        """杀掉进程"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        package, ok = QInputDialog.getText(self, "杀掉进程", "请输入包名:")
        if ok and package:
            self.log(f"准备杀掉 {package} 进程...")
            worker = KillProcessWorker(self.device_id, package)
            self.start_worker(worker, self.on_kill_process_finished)
            
    def on_kill_process_finished(self, result):
        """杀掉进程完成的回调"""
        if result["success"]:
            self.log(f"杀掉进程成功: {result['output']}")
        else:
            self.log(f"杀掉进程失败: {result['error']}")
            
    def uninstall_app(self):
        """卸载应用"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        package, ok = QInputDialog.getText(self, "卸载应用", "请输入包名:")
        if ok and package:
            self.log(f"准备卸载 {package}...")
            worker = UninstallWorker(self.device_id, package)
            self.start_worker(worker, self.on_uninstall_finished)
            
    def on_uninstall_finished(self, result):
        """卸载完成的回调"""
        if result["success"]:
            self.log(f"卸载成功: {result['output']}")
        else:
            self.log(f"卸载失败: {result['error']}")
            
    def disconnect_device(self):
        """断开连接"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        self.log(f"准备断开设备 {self.device_id}...")
        worker = DisconnectWorker(self.device_id)
        self.start_worker(worker, self.on_disconnect_finished)
            
    def on_disconnect_finished(self, result):
        """断开连接完成的回调"""
        if result["success"]:
            self.log(f"断开连接成功: {result['output']}")
        else:
            self.log(f"断开连接失败: {result['error']}")
        # 刷新设备列表
        self.refresh_devices()
            
    def screen_mirror(self):
        """电视画面投射"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        try:
            # 从配置中获取scrcpy路径
            from utils.config_loader import ConfigLoader
            config = ConfigLoader()
            scrcpy_path = config.get_setting("scrcpy_path", "D:\\APPS\\scrcpy-win64-v3.2\\scrcpy.exe")
            
            if os.path.exists(scrcpy_path):
                self.log(f"正在启动设备 {self.device_id} 的屏幕投射...")
                # 使用QProcess启动scrcpy，避免阻塞GUI
                process = QProcess(self)
                process.start(scrcpy_path, ["-s", self.device_id])
                self.log("屏幕投射已打开")
            else:
                self.log(f"错误: 未找到 scrcpy.exe，请检查路径: {scrcpy_path}")
        except Exception as e:
            self.log(f"启动屏幕投射时出错: {e}")
        
    def log(self, message):
        """添加日志信息"""
        self.log_display.append(message)
        # 滚动到底部
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )