#!/usr/bin/env python3
"""
AWS 工具脚本配置文件
"""

import os

# 默认输出目录
DEFAULT_OUTPUT_DIR = "/Users/rj/SyncSpace/WorkSpace/aws_tool_scripts/output"

# 默认 AWS 区域
DEFAULT_REGIONS = [
    'us-east-1',
    'ap-southeast-1', 
    'ap-northeast-1',
    'eu-west-1'
]

# 确保输出目录存在
def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists(DEFAULT_OUTPUT_DIR):
        os.makedirs(DEFAULT_OUTPUT_DIR)
        print(f"创建输出目录: {DEFAULT_OUTPUT_DIR}")
    return DEFAULT_OUTPUT_DIR

# 获取输出文件路径
def get_output_path(filename):
    """获取完整的输出文件路径"""
    output_dir = ensure_output_dir()
    return os.path.join(output_dir, filename)