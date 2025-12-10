#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ADB工具封装模块
提供设备列表获取、日志抓取、应用安装等核心功能
"""

import subprocess
import logging
import os
import sys

logger = logging.getLogger(__name__)

class ADBUtils:
    @staticmethod
    def get_adb_executable():
        """获取ADB可执行文件路径，优先使用本地adb目录"""
        try:
            if getattr(sys, "frozen", False):
                # PyInstaller打包后，资源在临时目录
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_adb = os.path.join(base_dir, "adb", "adb.exe")
            if os.path.exists(local_adb):
                return local_adb
        except Exception as e:
            logger.warning(f"获取本地ADB路径时出错: {e}")
        # 如果找不到本地ADB，则返回None而不是默认的"adb"
        return None

    @staticmethod
    def run_adb_command(command, timeout=30):
        """执行ADB命令并返回结果"""
        try:
            adb_exe = ADBUtils.get_adb_executable()
            # 如果没有找到ADB可执行文件，直接返回错误
            if not adb_exe:
                return {"success": False, "output": None, "error": "未找到ADB工具，请确保项目adb目录下有adb.exe文件"}
            
            if " " in adb_exe:
                adb_prefix = f'"{adb_exe}"'
            else:
                adb_prefix = adb_exe
            full_command = f"{adb_prefix} {command}"
            logger.debug(f"执行命令: {full_command}")
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip(), "error": None}
            else:
                logger.error(f"命令执行失败: {result.stderr}")
                return {"success": False, "output": result.stdout.strip(), "error": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时: {command}")
            return {"success": False, "output": None, "error": "命令执行超时"}
        except FileNotFoundError:
            logger.error(f"ADB executable not found: {adb_exe}")
            return {"success": False, "output": None, "error": "未找到ADB工具，请确保项目adb目录下有adb.exe文件"}
        except Exception as e:
            logger.error(f"执行ADB命令时出错: {e}")
            return {"success": False, "output": None, "error": str(e)}

    @staticmethod
    def get_connected_devices():
        """获取已连接的设备列表"""
        result = ADBUtils.run_adb_command("devices")
        if not result["success"]:
            return []
        
        # 检查是否有有效的设备列表
        output = result["output"].strip()
        if not output or "List of devices attached" not in output:
            return []
        
        devices = []
        lines = result["output"].split('\n')[1:]  # 跳过标题行
        
        for line in lines:
            if line.strip() and not line.startswith('*'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    device_id = parts[0].strip()
                    status = parts[1].strip()
                    # 只添加状态为device的设备
                    if status == "device":
                        devices.append({
                            'id': device_id,
                            'status': status
                        })
        
        return devices

    @staticmethod
    def get_device_info(device_id):
        """获取设备信息"""
        info = {}
        
        # 获取设备型号
        model_result = ADBUtils.run_adb_command(f"-s {device_id} shell getprop ro.product.model")
        if model_result["success"]:
            info['model'] = model_result["output"]
        
        # 获取Android版本
        version_result = ADBUtils.run_adb_command(f"-s {device_id} shell getprop ro.build.version.release")
        if version_result["success"]:
            info['android_version'] = version_result["output"]
        
        # 获取设备品牌
        brand_result = ADBUtils.run_adb_command(f"-s {device_id} shell getprop ro.product.brand")
        if brand_result["success"]:
            info['brand'] = brand_result["output"]
        
        return info

    @staticmethod
    def install_apk(device_id, apk_path):
        """在指定设备上安装APK"""
        if not os.path.exists(apk_path):
            return {"success": False, "output": None, "error": "APK文件不存在"}
        
        # 验证设备是否连接
        devices = ADBUtils.get_connected_devices()
        device_connected = any(device['id'] == device_id for device in devices)
        if not device_connected:
            return {"success": False, "output": None, "error": f"设备 {device_id} 未连接或不可用"}
        
        # 检查APK文件是否有效
        if not ADBUtils._is_valid_apk(apk_path):
            return {"success": False, "output": None, "error": "APK文件无效或已损坏"}
        
        # 尝试多种安装方式，按优先级排序
        install_methods = [
            # 最常用：覆盖安装 + 降级安装
            f'-s {device_id} install -r -d "{apk_path}"',
            # 覆盖安装 + 测试应用 + 降级
            f'-s {device_id} install -r -t -d "{apk_path}"',
            # 覆盖安装（不带降级）
            f'-s {device_id} install -r "{apk_path}"',
            # 覆盖 + 测试应用
            f'-s {device_id} install -r -t "{apk_path}"',
            # 基础安装
            f'-s {device_id} install "{apk_path}"',
        ]
        
        logger.info(f"开始安装APK到设备 {device_id}")
        logger.info(f"APK路径: {apk_path}")
        logger.info(f"设备状态: 已连接" if device_connected else f"设备状态: 未连接")
        
        for i, method in enumerate(install_methods, 1):
            logger.info(f"尝试安装方法 {i}/{len(install_methods)}: {method}")
            result = ADBUtils.run_adb_command(method, timeout=30)  # 缩短超时时间到30秒
            
            if result["success"]:
                logger.info(f"安装成功，使用方法: {method}")
                return result
            
            error_msg = result['error']
            logger.warning(f"安装方法失败: {method}, 错误: {error_msg}")
            
            # 快速失败：遇到以下明确错误时，跳过剩余方法
            skip_errors = [
                'INSTALL_FAILED_ALREADY_EXISTS',  # 已安装相同包名
                'INSTALL_FAILED_INVALID_APK',     # APK无效
                'INSTALL_FAILED_INSUFFICIENT_STORAGE',  # 存储空间不足
            ]
            
            if any(skip_err in error_msg for skip_err in skip_errors):
                logger.info(f"检测到明确错误，跳过剩余安装方法")
                return {"success": False, "output": None, "error": error_msg}
        
        # 如果所有方法都失败了，进行诊断
        logger.info("所有安装方法都失败了，开始诊断问题...")
        diagnosis = ADBUtils.diagnose_install_issue(device_id, apk_path)
        diagnosis_text = "\n".join(diagnosis)
        
        return {"success": False, "output": None, "error": f"所有安装方法都失败了\n诊断信息:\n{diagnosis_text}"}
    
    @staticmethod
    def _is_valid_apk(apk_path):
        """简单检查APK文件是否有效"""
        try:
            # 检查文件扩展名
            if not apk_path.lower().endswith('.apk'):
                return False
            
            # 检查文件大小
            size = os.path.getsize(apk_path)
            if size == 0:
                return False
            
            # 简单的魔术字节检查
            with open(apk_path, 'rb') as f:
                header = f.read(4)
                # APK文件通常以PK开头（ZIP格式）
                if header[:2] == b'PK':
                    return True
            return False
        except FileNotFoundError:
            logger.warning(f"APK文件不存在: {apk_path}")
            return False
        except PermissionError:
            logger.warning(f"没有权限访问APK文件: {apk_path}")
            return False
        except Exception as e:
            logger.error(f"检查APK文件有效性时出错: {e}", exc_info=True)
            return False

    @staticmethod
    def uninstall_app(device_id, package_name):
        """在指定设备上卸载应用"""
        command = f'-s {device_id} uninstall {package_name}'
        return ADBUtils.run_adb_command(command)

    @staticmethod
    def clear_app_cache(device_id, package_name):
        """清除应用缓存"""
        command = f'-s {device_id} shell pm clear {package_name}'
        return ADBUtils.run_adb_command(command)

    @staticmethod
    def force_stop_app(device_id, package_name):
        """强制停止应用"""
        command = f'-s {device_id} shell am force-stop {package_name}'
        return ADBUtils.run_adb_command(command)

    @staticmethod
    def connect_device(ip_address):
        """连接设备"""
        command = f'connect {ip_address}'
        result = ADBUtils.run_adb_command(command)
        
        # 检查连接结果，确保设备真正连接成功
        if result["success"]:
            # 检查输出中是否包含成功连接的信息
            output = result["output"].lower()
            if "connected to" in output or "already connected to" in output:
                # 连接成功，返回成功结果
                return result
            elif "cannot connect to" in output or "failed to connect" in output:
                # 明确的连接失败
                return {"success": False, "output": result["output"], "error": "连接失败，请检查设备是否已开启网络ADB调试"}
            else:
                # 不确定的结果，尝试验证设备是否真的连接上了
                # 通过获取设备列表来验证
                devices = ADBUtils.get_connected_devices()
                # 检查连接的设备中是否包含目标IP
                for device in devices:
                    if ip_address in device['id']:
                        return result  # 确实连接成功了
                
                # 如果设备列表中没有找到，说明连接实际上失败了
                return {"success": False, "output": result["output"], "error": "连接失败，请检查设备是否已开启网络ADB调试"}
        
        return result

    @staticmethod
    def disconnect_device(device_id):
        """断开设备连接"""
        command = f'disconnect {device_id}'
        return ADBUtils.run_adb_command(command)

    @staticmethod
    def diagnose_install_issue(device_id, apk_path):
        """诊断安装问题"""
        diagnosis = []
        
        # 1. 检查APK文件
        if not os.path.exists(apk_path):
            diagnosis.append("❌ APK文件不存在")
        else:
            diagnosis.append("✅ APK文件存在")
            # 检查文件大小
            size = os.path.getsize(apk_path)
            diagnosis.append(f"📄 APK文件大小: {size} 字节")
        
        # 2. 检查设备连接
        devices = ADBUtils.get_connected_devices()
        device_connected = any(device['id'] == device_id for device in devices)
        if not device_connected:
            diagnosis.append("❌ 设备未连接")
        else:
            diagnosis.append("✅ 设备已连接")
            # 获取设备信息
            device_info = ADBUtils.get_device_info(device_id)  # 修正：使用类的静态方法
            if device_info:
                diagnosis.append(f"📱 设备型号: {device_info.get('model', '未知')}")
                diagnosis.append(f"🤖 Android版本: {device_info.get('android_version', '未知')}")
        
        # 3. 检查ADB服务状态
        adb_version = ADBUtils.run_adb_command("version")
        if adb_version["success"]:
            diagnosis.append("✅ ADB服务正常运行")
            diagnosis.append(f"🔧 ADB版本: {adb_version['output']}")
        else:
            diagnosis.append("❌ ADB服务异常")
            diagnosis.append(f"🔧 ADB错误: {adb_version['error']}")
        
        # 4. 检查设备存储空间
        storage_check = ADBUtils.run_adb_command(f"-s {device_id} shell df /data")
        if storage_check["success"]:
            diagnosis.append("✅ 可以访问设备存储信息")
        else:
            diagnosis.append("⚠️ 无法访问设备存储信息")
        
        return diagnosis

# 保持向后兼容的函数
def run_adb_command(command):
    """执行ADB命令并返回结果"""
    return ADBUtils.run_adb_command(command)["output"]

def get_connected_devices():
    """获取已连接的设备列表"""
    return ADBUtils.get_connected_devices()

def pull_logs(device_id, package_name, output_path):
    """从指定设备拉取指定应用的日志"""
    command = f"-s {device_id} logcat -d -v threadtime | grep {package_name}"
    output = run_adb_command(command)
    
    if output:
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            return True
        except FileNotFoundError:
            logger.error(f"日志输出路径不存在且无法创建: {output_path}")
            return False
        except PermissionError:
            logger.error(f"没有权限写入日志文件: {output_path}")
            return False
        except Exception as e:
            logger.error(f"保存日志文件时出错: {e}", exc_info=True)
            return False
    return False

def install_apk(device_id, apk_path):
    """在指定设备上安装APK"""
    result = ADBUtils.install_apk(device_id, apk_path)
    return result["success"]

def get_device_info(device_id):
    """获取设备信息"""
    return ADBUtils.get_device_info(device_id)