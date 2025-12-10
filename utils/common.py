#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用工具模块
包含各种常用的工具函数
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_current_time_str(format="%Y-%m-%d %H:%M:%S"):
    """获取当前时间字符串"""
    return datetime.now().strftime(format)

def ensure_dir_exists(dir_path):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            logger.info(f"创建目录: {dir_path}")
        except Exception as e:
            logger.error(f"创建目录 {dir_path} 失败: {e}")
            return False
    return True

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f}{size_names[i]}"

def is_valid_ip(ip):
    """简单的IP地址验证"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    
    return True

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    return filename

# 测试代码
if __name__ == "__main__":
    print(f"当前时间: {get_current_time_str()}")
    print(f"文件大小 1024: {format_file_size(1024)}")
    print(f"IP地址 192.168.1.1 有效性: {is_valid_ip('192.168.1.1')}")
    print(f"IP地址 999.168.1.1 有效性: {is_valid_ip('999.168.1.1')}")
    print(f"清理文件名 'test<>.txt': {sanitize_filename('test<>.txt')}")