#!/usr/bin/env python3
"""
文件操作工具类
"""

import os
from datetime import datetime

class FileManager:
    def __init__(self, base_dir="/Users/rj/SyncSpace/WorkSpace/aws_tool_scripts"):
        self.base_dir = base_dir
        self.output_dir = os.path.join(base_dir, "output")
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [self.base_dir, self.output_dir]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"创建目录: {directory}")
    
    def get_output_path(self, filename, subfolder=None):
        """获取输出文件的完整路径"""
        if subfolder:
            target_dir = os.path.join(self.output_dir, subfolder)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
        else:
            target_dir = self.output_dir
        
        return os.path.join(target_dir, filename)
    
    def get_timestamped_filename(self, prefix, extension="csv"):
        """生成带时间戳的文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.{extension}"
        return self.get_output_path(filename)
    
    def list_output_files(self, pattern="*"):
        """列出输出目录中的文件"""
        import glob
        pattern_path = os.path.join(self.output_dir, pattern)
        return glob.glob(pattern_path)

# 创建全局实例
file_manager = FileManager()