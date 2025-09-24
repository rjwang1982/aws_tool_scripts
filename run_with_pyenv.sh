#!/bin/bash

# 使用 pyenv 执行 EC2 信息获取脚本

set -e

echo "正在设置 pyenv 环境..."

# 确保使用正确的 Python 版本
pyenv local 3.9.18

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python -m venv .venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 检查 AWS 凭证
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "警告: 未检测到有效的 AWS 凭证"
    echo "请运行 'aws configure' 或设置环境变量"
    exit 1
fi

# 执行脚本
echo "执行 EC2 信息获取脚本..."
python get_account_ec2_info.py

echo "脚本执行完成！"