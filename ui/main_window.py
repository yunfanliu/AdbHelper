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
                               QInputDialog, QMenu, QMenuBar, QDialogButtonBox, QTextBrowser)
from PySide6.QtCore import Qt, QTimer, QProcess, QThread, Signal
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QIcon

# 导入设备管理器
from core.device_manager import DeviceManager
from utils.common import ensure_dir_exists, get_current_time_str, sanitize_filename

logger = logging.getLogger(__name__)

# 关于对话框类
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 AdbHelper")
        self.setFixedSize(400, 350)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("AdbHelper")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("版本: V1.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 开发者信息
        info_group = QGroupBox("开发者信息")
        info_layout = QFormLayout()
        
        dev_name_label = QLabel("开发者: yunfanliu")
        email_label = QLabel("联系邮箱: 2756990675@qq.com")
        
        info_layout.addRow(dev_name_label)
        info_layout.addRow(email_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 版权信息
        copyright_group = QGroupBox("版权信息")
        copyright_layout = QVBoxLayout()
        
        copyright_label = QLabel("版权所有 © 2025 yunfanliu\n保留所有权利")
        copyright_label.setWordWrap(True)
        copyright_label.setAlignment(Qt.AlignCenter)
        
        copyright_layout.addWidget(copyright_label)
        copyright_group.setLayout(copyright_layout)
        layout.addWidget(copyright_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

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
            logger.error(f"InstallWorker异常: {e}", exc_info=True)
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
            logger.error(f"ConnectWorker异常: {e}", exc_info=True)
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
            logger.error(f"ClearCacheWorker异常: {e}", exc_info=True)
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
            logger.error(f"KillProcessWorker异常: {e}", exc_info=True)
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
            logger.error(f"UninstallWorker异常: {e}", exc_info=True)
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class RefreshDevicesWorker(QThread):
    """刷新设备的后台工作线程"""
    finished = Signal(list)
    
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
    
    def run(self):
        try:
            devices = self.device_manager.get_connected_devices()
            self.finished.emit(devices)
        except Exception as e:
            logger.error(f"RefreshDevicesWorker异常: {e}", exc_info=True)
            self.finished.emit([])

class ShowMyDevicesWorker(QThread):
    """获取我的设备的后台工作线程"""
    finished = Signal(list)
    
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
    
    def run(self):
        try:
            devices = self.device_manager.get_usable_devices()
            self.finished.emit(devices)
        except Exception as e:
            logger.error(f"ShowMyDevicesWorker异常: {e}", exc_info=True)
            self.finished.emit([])

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
            logger.error(f"DisconnectWorker异常: {e}", exc_info=True)
            self.finished.emit({"success": False, "output": None, "error": str(e)})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_id = None
        self.device_manager = DeviceManager()
        self.current_worker = None  # 用于互斥操作（刷新/连接/断开）
        self.install_workers = []  # 用于并发安装操作
        self.init_ui()
        
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("AdbHelper V1.0")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部按钮区域
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新设备")
        self.my_devices_btn = QPushButton("我的设备")
        self.connect_btn = QPushButton("连接IP")
        self.disconnect_btn = QPushButton("断开连接")
        self.install_btn = QPushButton("安装应用")
        self.kill_process_btn = QPushButton("杀掉进程")
        self.clear_cache_btn = QPushButton("清除缓存")
        self.capture_log_btn = QPushButton("抓日志")
        self.screenshot_btn = QPushButton("截图")
        self.uninstall_btn = QPushButton("卸载应用")
        self.screen_mirror_btn = QPushButton("设备画面")
        self.settings_btn = QPushButton("设置")
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.my_devices_btn)
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.kill_process_btn)
        button_layout.addWidget(self.clear_cache_btn)
        button_layout.addWidget(self.capture_log_btn)
        button_layout.addWidget(self.screenshot_btn)
        button_layout.addWidget(self.uninstall_btn)
        button_layout.addWidget(self.screen_mirror_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addStretch()
        
        # 创建包名显示区域
        package_group = QGroupBox("常用包名")
        package_layout = QVBoxLayout(package_group)
        
        self.package_list = QTextEdit()
        self.package_list.setReadOnly(True)
        self.load_packages()
        package_layout.addWidget(self.package_list)
        
        # 创建设备列表区域
        device_group = QGroupBox("设备列表")
        device_layout = QVBoxLayout(device_group)
        
        self.device_list = QListWidget()
        device_layout.addWidget(self.device_list)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 设置为不确定模式
        
        # 创建日志显示区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
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
        self.capture_log_btn.clicked.connect(self.capture_log)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        self.uninstall_btn.clicked.connect(self.uninstall_app)
        self.screen_mirror_btn.clicked.connect(self.screen_mirror)
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        self.device_list.itemClicked.connect(self.select_device)
        self.device_list.itemDoubleClicked.connect(self.connect_device_from_list)
        
        # 延迟初始化设备列表，等待窗口显示后再刷新
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, self.refresh_devices)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        # 关于动作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def load_packages(self):
        """从packages.json加载并显示包名列表"""
        from utils.config_loader import ConfigLoader
        config = ConfigLoader()
        groups = config.get_package_groups()

        # 只有当有包名配置时才显示，否则显示提示信息
        if groups:
            lines = []
            for group_name, packages in groups.items():
                lines.append(f"{group_name}:")
                for pkg in packages:
                    lines.append(pkg)
                lines.append("")  # 分组之间空行
            self.package_list.setText("\n".join(lines))
        else:
            self.package_list.setText("未找到包名配置文件或配置文件为空")
        
    def refresh_devices(self):
        """刷新ADB连接的设备列表"""
        # 如果有正在运行的 worker，先等待它完成
        if self.current_worker is not None:
            self.log("操作正在进行中，请稍候...")
            return
        
        try:
            self.log("正在刷新ADB设备列表...")
            worker = RefreshDevicesWorker(self.device_manager)
            worker.finished.connect(self.on_refresh_devices_finished)
            self.progress_bar.setVisible(True)
            worker.start()
            self.current_worker = worker
        except Exception as e:
            logger.error(f"refresh_devices异常: {e}", exc_info=True)
            self.log(f"启动刷新设备操作时出错: {e}")
            self.progress_bar.setVisible(False)
            self.current_worker = None
    
    def on_refresh_devices_finished(self, devices):
        """刷新设备列表完成的回调"""
        try:
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
            logger.error(f"on_refresh_devices_finished异常: {e}", exc_info=True)
            self.log(f"刷新ADB设备列表时出错: {e}")
        finally:
            self.progress_bar.setVisible(False)
            # 使用 deleteLater 确保 worker 完全清理
            if self.current_worker:
                self.current_worker.deleteLater()
            self.current_worker = None
            
    def show_my_devices(self):
        """显示我的设备列表（在操作日志中展示可连接的设备IP）"""
        # 如果有正在运行的 worker，先等待它完成
        if self.current_worker is not None:
            self.log("操作正在进行中，请稍候...")
            return
        
        try:
            self.log("正在获取我的设备列表...")
            worker = ShowMyDevicesWorker(self.device_manager)
            worker.finished.connect(self.on_show_my_devices_finished)
            self.progress_bar.setVisible(True)
            worker.start()
            self.current_worker = worker
        except Exception as e:
            logger.error(f"show_my_devices异常: {e}", exc_info=True)
            self.log(f"启动获取我的设备操作时出错: {e}")
            self.progress_bar.setVisible(False)
            self.current_worker = None
    
    def on_show_my_devices_finished(self, my_devices):
        """显示我的设备完成的回调"""
        try:
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
            logger.error(f"on_show_my_devices_finished异常: {e}", exc_info=True)
            self.log(f"获取我的设备时出错: {e}")
        finally:
            self.progress_bar.setVisible(False)
            # 使用 deleteLater 确保 worker 完全清理
            if self.current_worker:
                self.current_worker.deleteLater()
            self.current_worker = None
            
    def show_usable_devices(self):
        """显示可使用设备（保持向后兼容）"""
        self.show_my_devices()
        
    def connect_ip(self):
        """连接IP"""
        try:
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
        except Exception as e:
            logger.error(f"connect_ip异常: {e}", exc_info=True)
            self.log(f"启动连接IP操作时出错: {e}")
            
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
            
    def start_worker(self, worker, callback):
        """启动后台工作线程"""
        # 如果有正在运行的 worker，先等待它完成
        if self.current_worker is not None:
            self.log("操作正在进行中，请稍候...")
            return False
        
        try:
            self.current_worker = worker
            self.current_worker.finished.connect(callback)
            self.current_worker.finished.connect(self.on_worker_finished)
            self.progress_bar.setVisible(True)
            self.current_worker.start()
            return True
        except Exception as e:
            logger.error(f"start_worker异常: {e}", exc_info=True)
            self.log(f"启动工作线程时出错: {e}")
            self.progress_bar.setVisible(False)
            self.current_worker = None
            return False
        
    def on_worker_finished(self):
        """工作线程完成后的处理"""
        self.progress_bar.setVisible(False)
        # 使用 deleteLater 确保 worker 完全清理
        if self.current_worker:
            self.current_worker.deleteLater()
        self.current_worker = None
        
    def install_app(self):
        """安装应用"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", "", "APK Files (*.apk)")
            if file_path:
                self.log(f"准备安装 {file_path} 到设备 {self.device_id}...")
                worker = InstallWorker(self.device_id, file_path)
                # 安装操作允许并发，不使用 start_worker
                worker.finished.connect(lambda result: self.on_install_finished(result, worker))
                worker.start()
                self.install_workers.append(worker)
                self.log(f"当前正在安装的任务数: {len(self.install_workers)}")
        except Exception as e:
            logger.error(f"install_app异常: {e}", exc_info=True)
            self.log(f"启动安装应用操作时出错: {e}")
            
    def on_install_finished(self, result, worker):
        """安装完成的回调"""
        # 从列表中移除已完成的 worker
        if worker in self.install_workers:
            self.install_workers.remove(worker)
        
        try:
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
        except Exception as e:
            logger.error(f"on_install_finished异常: {e}", exc_info=True)
            self.log(f"处理安装结果时出错: {e}")
        
        self.log(f"剩余安装任务数: {len(self.install_workers)}")
            
    def on_connect_finished(self, result):
        """连接完成的回调"""
        try:
            if result["success"]:
                self.log(f"连接成功: {result['output']}")
                # 连接成功后立即刷新设备列表
                QTimer.singleShot(1000, self.refresh_devices)
            else:
                self.log(f"连接失败: {result['error']}")
        except Exception as e:
            logger.error(f"on_connect_finished异常: {e}", exc_info=True)
            self.log(f"处理连接结果时出错: {e}")
            
    def clear_cache(self):
        """清除缓存"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        try:
            package, ok = QInputDialog.getText(self, "清除缓存", "请输入包名:")
            if ok and package:
                self.log(f"准备清除 {package} 的缓存...")
                worker = ClearCacheWorker(self.device_id, package)
                self.start_worker(worker, self.on_clear_cache_finished)
        except Exception as e:
            logger.error(f"clear_cache异常: {e}", exc_info=True)
            self.log(f"启动清除缓存操作时出错: {e}")
            
    def on_clear_cache_finished(self, result):
        """清除缓存完成的回调"""
        try:
            if result["success"]:
                self.log(f"清除缓存成功: {result['output']}")
            else:
                self.log(f"清除缓存失败: {result['error']}")
        except Exception as e:
            logger.error(f"on_clear_cache_finished异常: {e}", exc_info=True)
            self.log(f"处理清除缓存结果时出错: {e}")
            
    def kill_process(self):
        """杀掉进程"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        try:
            package, ok = QInputDialog.getText(self, "杀掉进程", "请输入包名:")
            if ok and package:
                self.log(f"准备杀掉 {package} 进程...")
                worker = KillProcessWorker(self.device_id, package)
                self.start_worker(worker, self.on_kill_process_finished)
        except Exception as e:
            logger.error(f"kill_process异常: {e}", exc_info=True)
            self.log(f"启动杀掉进程操作时出错: {e}")
            
    def on_kill_process_finished(self, result):
        """杀掉进程完成的回调"""
        try:
            if result["success"]:
                self.log(f"杀掉进程成功: {result['output']}")
            else:
                self.log(f"杀掉进程失败: {result['error']}")
        except Exception as e:
            logger.error(f"on_kill_process_finished异常: {e}", exc_info=True)
            self.log(f"处理杀掉进程结果时出错: {e}")
            
    def uninstall_app(self):
        """卸载应用"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        try:
            package, ok = QInputDialog.getText(self, "卸载应用", "请输入包名:")
            if ok and package:
                self.log(f"准备卸载 {package}...")
                worker = UninstallWorker(self.device_id, package)
                self.start_worker(worker, self.on_uninstall_finished)
        except Exception as e:
            logger.error(f"uninstall_app异常: {e}", exc_info=True)
            self.log(f"启动卸载应用操作时出错: {e}")
            
    def on_uninstall_finished(self, result):
        """卸载完成的回调"""
        try:
            if result["success"]:
                self.log(f"卸载成功: {result['output']}")
            else:
                self.log(f"卸载失败: {result['error']}")
        except Exception as e:
            logger.error(f"on_uninstall_finished异常: {e}", exc_info=True)
            self.log(f"处理卸载结果时出错: {e}")
            
    def disconnect_device(self):
        """断开连接"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return
            
        try:
            self.log(f"准备断开设备 {self.device_id}...")
            worker = DisconnectWorker(self.device_id)
            self.start_worker(worker, self.on_disconnect_finished)
        except Exception as e:
            logger.error(f"disconnect_device异常: {e}", exc_info=True)
            self.log(f"启动断开连接操作时出错: {e}")
            
    def on_disconnect_finished(self, result):
        """断开连接完成的回调"""
        try:
            if result["success"]:
                self.log(f"断开连接成功: {result['output']}")
            else:
                self.log(f"断开连接失败: {result['error']}")
        except Exception as e:
            logger.error(f"on_disconnect_finished异常: {e}", exc_info=True)
            self.log(f"处理断开连接结果时出错: {e}")
        # 延迟刷新设备列表，确保当前 worker 清理完毕
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_devices)
            
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

    def capture_log(self):
        """抓取当前设备的日志到本地文件（CMD窗口实时显示）"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return

        from utils.config_loader import ConfigLoader
        from core.adb_utils import ADBUtils
        
        config = ConfigLoader()
        log_dir = config.get_setting("log_output_dir", config.get_setting("default_save_path", "./logs"))
        if not ensure_dir_exists(log_dir):
            self.log(f"创建日志目录失败: {log_dir}")
            return

        package_name, ok = QInputDialog.getText(self, "抓取日志", "请输入包名(可留空，留空则抓取全部日志):")
        if not ok:
            return

        timestamp = get_current_time_str("%Y%m%d_%H%M%S")
        base_name = (package_name.strip() if package_name else None) or "all"
        filename = sanitize_filename(f"log_{base_name}_{timestamp}.txt")
        output_path = os.path.abspath(os.path.join(log_dir, filename))

        try:
            # 获取adb路径
            adb_exe = ADBUtils.get_adb_executable()
            if " " in adb_exe:
                adb_cmd = f'"{adb_exe}"'
            else:
                adb_cmd = adb_exe
            
            # 构建 CMD 命令，打开新窗口实时抓取日志
            if package_name and package_name.strip():
                # 有包名，过滤日志
                cmd = f'start "ADB日志抓取" cmd /k "{adb_cmd} -s {self.device_id} logcat | findstr {package_name.strip()} > \"{output_path}\""'
            else:
                # 无包名，抓全部
                cmd = f'start "ADB日志抓取" cmd /k "{adb_cmd} -s {self.device_id} logcat > \"{output_path}\""'
            
            subprocess.Popen(cmd, shell=True)
            self.log(f"已开启日志抓取窗口，日志将实时保存到: {output_path}")
            self.log("关闭 CMD 窗口则停止抓取")
        except Exception as e:
            self.log(f"抓取日志时出错: {e}")

    def take_screenshot(self):
        """对当前设备进行截图并保存到本地"""
        if not self.device_id:
            self.log("请先选择一个设备")
            return

        from utils.config_loader import ConfigLoader
        config = ConfigLoader()
        screenshot_dir = config.get_setting("screenshot_output_dir", "./screenshots")
        if not ensure_dir_exists(screenshot_dir):
            self.log(f"创建截图目录失败: {screenshot_dir}")
            return

        timestamp = get_current_time_str("%Y%m%d_%H%M%S")
        filename = sanitize_filename(f"screenshot_{self.device_id}_{timestamp}.png")
        local_path = os.path.join(screenshot_dir, filename)
        remote_path = "/sdcard/temp_screenshot.png"

        try:
            from core.adb_utils import ADBUtils
            # 1. 在设备上截图
            cmd_capture = f'-s {self.device_id} shell screencap -p {remote_path}'
            result1 = ADBUtils.run_adb_command(cmd_capture, timeout=60)
            if not result1["success"]:
                self.log(f"截图失败: {result1['error']}")
                return

            # 2. 拉取到本地
            cmd_pull = f'-s {self.device_id} pull {remote_path} "{local_path}"'
            result2 = ADBUtils.run_adb_command(cmd_pull, timeout=120)
            if not result2["success"]:
                self.log(f"拉取截图失败: {result2['error']}")
                return

            # 3. 删除远端临时文件
            ADBUtils.run_adb_command(f'-s {self.device_id} shell rm {remote_path}')

            self.log(f"截图已保存到: {local_path}")
        except Exception as e:
            self.log(f"截图时出错: {e}")

    def open_settings_dialog(self):
        """打开设置对话框，选择配置文件路径"""
        from utils.config_loader import ConfigLoader
        config = ConfigLoader()

        # 创建一个简单的表单对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        form_layout = QFormLayout(dialog)

        packages_edit = QLineEdit(dialog)
        packages_edit.setText(config.packages_config_path)
        devices_edit = QLineEdit(dialog)
        devices_edit.setText(config.devices_config_path)
        scrcpy_edit = QLineEdit(dialog)
        scrcpy_edit.setText(config.get_setting("scrcpy_path", ""))
        log_dir_edit = QLineEdit(dialog)
        log_dir_edit.setText(config.get_setting("log_output_dir", config.get_setting("default_save_path", "./logs")))
        screenshot_dir_edit = QLineEdit(dialog)
        screenshot_dir_edit.setText(config.get_setting("screenshot_output_dir", "./screenshots"))

        browse_packages_btn = QPushButton("浏览", dialog)
        browse_devices_btn = QPushButton("浏览", dialog)
        browse_scrcpy_btn = QPushButton("浏览", dialog)
        browse_log_btn = QPushButton("浏览", dialog)
        browse_screenshot_btn = QPushButton("浏览", dialog)

        # 常用包名路径
        pkg_layout = QHBoxLayout()
        pkg_layout.addWidget(packages_edit)
        pkg_layout.addWidget(browse_packages_btn)
        form_layout.addRow("常用包名配置路径:", pkg_layout)

        # 设备MAC映射路径
        dev_layout = QHBoxLayout()
        dev_layout.addWidget(devices_edit)
        dev_layout.addWidget(browse_devices_btn)
        form_layout.addRow("设备MAC映射路径:", dev_layout)

        # scrcpy路径
        scrcpy_layout = QHBoxLayout()
        scrcpy_layout.addWidget(scrcpy_edit)
        scrcpy_layout.addWidget(browse_scrcpy_btn)
        form_layout.addRow("scrcpy路径:", scrcpy_layout)

        # 日志输出目录
        log_layout = QHBoxLayout()
        log_layout.addWidget(log_dir_edit)
        log_layout.addWidget(browse_log_btn)
        form_layout.addRow("日志输出目录:", log_layout)

        # 截图输出目录
        screenshot_layout = QHBoxLayout()
        screenshot_layout.addWidget(screenshot_dir_edit)
        screenshot_layout.addWidget(browse_screenshot_btn)
        form_layout.addRow("截图输出目录:", screenshot_layout)

        # 确认/取消按钮
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("确定", dialog)
        cancel_btn = QPushButton("取消", dialog)
        btn_box.addStretch()
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        form_layout.addRow(btn_box)

        def browse_packages():
            path, ok = QFileDialog.getOpenFileName(
                dialog,
                "选择包名配置文件",
                os.path.dirname(config.packages_config_path),
                "JSON Files (*.json);;All Files (*.*)",
            )
            if ok and path:
                packages_edit.setText(path)

        def browse_devices():
            path, ok = QFileDialog.getOpenFileName(
                dialog,
                "选择设备映射配置文件",
                os.path.dirname(config.devices_config_path),
                "Text Files (*.txt);;All Files (*.*)",
            )
            if ok and path:
                devices_edit.setText(path)

        def browse_scrcpy():
            path, ok = QFileDialog.getOpenFileName(
                dialog,
                "选择scrcpy.exe",
                os.path.dirname(scrcpy_edit.text().strip() or config.get_setting("scrcpy_path", "")),
                "scrcpy.exe (scrcpy.exe);;All Files (*.*)",
            )
            if ok and path:
                scrcpy_edit.setText(path)

        def browse_log():
            path = QFileDialog.getExistingDirectory(
                dialog,
                "选择日志输出目录",
                os.path.abspath(log_dir_edit.text().strip() or config.get_setting("log_output_dir", "./logs")),
            )
            if path:
                log_dir_edit.setText(path)

        def browse_screenshot():
            path = QFileDialog.getExistingDirectory(
                dialog,
                "选择截图输出目录",
                os.path.abspath(screenshot_dir_edit.text().strip() or config.get_setting("screenshot_output_dir", "./screenshots")),
            )
            if path:
                screenshot_dir_edit.setText(path)

        browse_packages_btn.clicked.connect(browse_packages)
        browse_devices_btn.clicked.connect(browse_devices)
        browse_scrcpy_btn.clicked.connect(browse_scrcpy)
        browse_log_btn.clicked.connect(browse_log)
        browse_screenshot_btn.clicked.connect(browse_screenshot)

        def accept():
            packages_path = packages_edit.text().strip()
            devices_path = devices_edit.text().strip()
            scrcpy_path = scrcpy_edit.text().strip()
            log_output_dir = log_dir_edit.text().strip()
            screenshot_output_dir = screenshot_dir_edit.text().strip()
            config.update_paths(
                packages_path=packages_path or None,
                devices_path=devices_path or None,
                scrcpy_path=scrcpy_path or None,
                log_output_dir=log_output_dir or None,
                screenshot_output_dir=screenshot_output_dir or None,
            )
            # 重新加载包名配置，实时更新UI
            self.load_packages()
            self.log("配置已更新：")
            if packages_path:
                self.log(f"常用包名配置路径: {packages_path}")
            if devices_path:
                self.log(f"设备MAC映射路径: {devices_path}")
            if scrcpy_path:
                self.log(f"scrcpy路径: {scrcpy_path}")
            if log_output_dir:
                self.log(f"日志输出目录: {log_output_dir}")
            if screenshot_output_dir:
                self.log(f"截图输出目录: {screenshot_output_dir}")
            dialog.accept()

        def reject():
            self.log("配置未更改")
            dialog.reject()

        ok_btn.clicked.connect(accept)
        cancel_btn.clicked.connect(reject)

        dialog.exec()

    def log(self, message):
        """添加日志信息"""
        self.log_display.append(message)
        # 滚动到底部
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )