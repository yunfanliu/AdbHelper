#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置加载器模块
用于读取和解析配置文件
"""

import json
import os
import sys
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, packages_config_path=None, 
                 settings_config_path=None, devices_config_path=None):
        # 打包后 config 目录在 exe 同级，不在 _MEIPASS 内
        if getattr(sys, "frozen", False):
            # PyInstaller 打包后，exe 所在目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境，项目根目录
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 初始化配置文件路径
        self.settings_config_path = settings_config_path or os.path.join(base_dir, "config", "settings.json")
        self.packages_data = {}
        self.settings_data = {}
        
        # 先加载 settings 配置
        self.load_settings_config()
        
        # 从 settings 中获取自定义路径，如果没有则使用默认路径
        self.packages_config_path = packages_config_path or self.settings_data.get("packages_path") or os.path.join(base_dir, "config", "packages.json")
        self.devices_config_path = devices_config_path or self.settings_data.get("devices_path") or os.path.join(base_dir, "config", "devices.txt")
        
        # 加载包名配置
        self.load_packages_config()
    
    
    def load_packages_config(self):
        """加载包名配置文件"""
        # 只有当配置文件存在时才加载，否则保持空字典
        if os.path.exists(self.packages_config_path):
            try:
                with open(self.packages_config_path, 'r', encoding='utf-8') as f:
                    self.packages_data = json.load(f)
                logger.info(f"成功加载包名配置文件: {self.packages_config_path}")
            except FileNotFoundError:
                logger.warning(f"包名配置文件不存在: {self.packages_config_path}")
            except PermissionError:
                logger.error(f"没有权限读取包名配置文件: {self.packages_config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"包名配置文件格式错误: {e}")
            except Exception as e:
                logger.error(f"加载包名配置文件时出错: {e}", exc_info=True)
        else:
            logger.warning(f"包名配置文件不存在: {self.packages_config_path}")
    
    def load_settings_config(self):
        """加载设置配置文件"""
        if os.path.exists(self.settings_config_path):
            try:
                with open(self.settings_config_path, 'r', encoding='utf-8') as f:
                    self.settings_data = json.load(f)
                logger.info(f"成功加载设置配置文件: {self.settings_config_path}")
            except FileNotFoundError:
                logger.warning(f"设置配置文件不存在: {self.settings_config_path}")
            except PermissionError:
                logger.error(f"没有权限读取设置配置文件: {self.settings_config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"设置配置文件格式错误: {e}")
            except Exception as e:
                logger.error(f"加载设置配置文件时出错: {e}", exc_info=True)
        else:
            logger.warning(f"设置配置文件不存在: {self.settings_config_path}")
    
    def create_default_packages_config(self):
        """创建默认包名配置"""
        self.packages_data = {}
        
        # 不再自动创建默认配置文件
        logger.info("跳过创建默认包名配置文件")
    
    def create_default_settings_config(self):
        """创建默认设置配置"""
        self.settings_data = {}
        
        # 不再自动创建默认配置文件
        logger.info("跳过创建默认设置配置文件")
    
    def get_package_groups(self):
        """获取包名分组"""
        return self.packages_data
    
    def get_setting(self, key, default=None):
        """获取设置值"""
        return self.settings_data.get(key, default)
    
    def get_all_settings(self):
        """获取所有设置"""
        return self.settings_data.copy()

    def update_paths(self, packages_path=None, devices_path=None, scrcpy_path=None, log_output_dir=None, screenshot_output_dir=None):
        """更新配置文件路径并保存到settings中"""
        changed = False
        if packages_path:
            self.packages_config_path = packages_path
            self.settings_data["packages_path"] = packages_path
            changed = True
        if devices_path:
            self.devices_config_path = devices_path
            self.settings_data["devices_path"] = devices_path
            changed = True
        if scrcpy_path:
            self.settings_data["scrcpy_path"] = scrcpy_path
            changed = True
        if log_output_dir:
            self.settings_data["log_output_dir"] = log_output_dir
            changed = True
        if screenshot_output_dir:
            self.settings_data["screenshot_output_dir"] = screenshot_output_dir
            changed = True
        if changed:
            try:
                os.makedirs(os.path.dirname(self.settings_config_path), exist_ok=True)
                with open(self.settings_config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings_data, f, ensure_ascii=False, indent=4)
                logger.info(f"更新设置配置文件: {self.settings_config_path}")
            except FileNotFoundError:
                logger.error(f"无法创建设置配置文件目录: {self.settings_config_path}")
            except PermissionError:
                logger.error(f"没有权限更新设置配置文件: {self.settings_config_path}")
            except Exception as e:
                logger.error(f"更新设置配置文件时出错: {e}", exc_info=True)

# 测试代码
if __name__ == "__main__":
    config_loader = ConfigLoader()
    print("包名配置:")
    for group, packages in config_loader.get_package_groups().items():
        print(f"  {group}: {packages}")
    
    print("\n设置配置:")
    for key, value in config_loader.get_all_settings().items():
        print(f"  {key}: {value}")