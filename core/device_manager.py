#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设备管理模块
负责设备识别、自动命名和网络发现功能
"""

import os
import subprocess
import logging
import re

logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, devices_config_path=None):
        from utils.config_loader import ConfigLoader
        config = ConfigLoader()
        self.devices_config_path = devices_config_path or config.devices_config_path
        self.mac_to_name = self._load_mac_mapping()
    
    def _load_mac_mapping(self):
        """加载MAC地址到设备名称的映射"""
        mac_to_name = {}
        # 只有当配置文件存在时才加载，否则返回空字典
        if os.path.exists(self.devices_config_path):
            try:
                with open(self.devices_config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('=')
                            if len(parts) == 2:
                                mac = parts[0].strip().lower()  # 转换为小写以便比较
                                name = parts[1].strip()
                                mac_to_name[mac] = name
            except FileNotFoundError:
                logger.warning(f"设备配置文件不存在: {self.devices_config_path}")
            except PermissionError:
                logger.error(f"没有权限读取设备配置文件: {self.devices_config_path}")
            except Exception as e:
                logger.error(f"加载设备配置文件时出错: {e}", exc_info=True)
        else:
            logger.warning(f"设备配置文件不存在: {self.devices_config_path}")
        
        logger.debug(f"加载了 {len(mac_to_name)} 个设备映射")
        return mac_to_name
    
    def get_connected_devices(self):
        """获取已连接的ADB设备"""
        try:
            from core.adb_utils import ADBUtils
            devices = ADBUtils.get_connected_devices()
            return devices
        except Exception as e:
            logger.error(f"执行adb devices命令时出错: {e}")
            return []
    
    def get_device_mac(self, device_ip):
        """通过IP地址获取设备的MAC地址"""
        try:
            # 获取ARP表
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                # 查找对应IP的MAC地址
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if device_ip in line:
                        # 使用正则表达式提取MAC地址
                        mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                        if mac_match:
                            return mac_match.group(0).lower()
            return None
        except subprocess.TimeoutExpired:
            logger.error("获取ARP表超时")
            return None
        except Exception as e:
            logger.error(f"获取设备MAC地址时出错: {e}")
            return None
    
    def get_device_name(self, device_id):
        """获取设备名称"""
        # 尝试从IP获取MAC地址，再获取设备名称
        try:
            # 提取IP地址部分（去除端口）
            ip_part = device_id.split(':')[0]
            mac = self.get_device_mac(ip_part)
            
            if mac and mac in self.mac_to_name:
                return self.mac_to_name[mac]
            
            # 如果没有找到映射，返回设备ID而不是默认名称
            return device_id
        except Exception as e:
            logger.error(f"获取设备名称时出错: {e}")
            return device_id
    
    def get_usable_devices(self):
        """获取可使用设备（通过ARP表和MAC映射文件）"""
        try:
            # 获取ARP表
            arp_result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=30)
            if arp_result.returncode != 0:
                logger.error(f"获取ARP表失败: {arp_result.stderr}")
                return []
            
            # 解析ARP表
            arp_lines = arp_result.stdout.strip().split('\n')
            usable_devices = []
            
            # 只有当有MAC映射时才继续
            if not self.mac_to_name:
                logger.warning("没有加载MAC地址映射，无法获取可使用设备")
                return []
            
            # 遍历MAC到名称的映射
            for mac, name in self.mac_to_name.items():
                # 在ARP表中查找此MAC地址
                for arp_line in arp_lines:
                    # 标准化MAC地址格式以便比较
                    normalized_mac = mac.lower().replace('-', ':')
                    normalized_arp_line = arp_line.lower().replace('-', ':')
                    
                    if normalized_mac in normalized_arp_line:
                        # 提取IP地址
                        ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', arp_line)
                        if ip_match:
                            ip = ip_match.group(0)
                            usable_devices.append({
                                'ip': ip,
                                'name': name,
                                'mac': mac
                            })
                        break  # 找到后跳出循环
            
            return usable_devices
        except subprocess.TimeoutExpired:
            logger.error("获取ARP表超时")
            return []
        except Exception as e:
            logger.error(f"获取可使用设备时出错: {e}")
            return []

# 测试代码
if __name__ == "__main__":
    manager = DeviceManager()
    
    # 测试获取连接设备
    devices = manager.get_connected_devices()
    print("连接的设备:")
    for device in devices:
        print(f"  {device['id']} ({device['status']})")
    
    # 测试获取可使用设备
    usable = manager.get_usable_devices()
    print("\n可使用设备:")
    for device in usable:
        print(f"  {device['name']} ({device['ip']})")