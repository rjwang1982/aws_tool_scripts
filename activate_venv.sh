#!/bin/bash
# 激活虚拟环境的脚本

# 进入脚本所在目录
cd "$(dirname "$0")"

# 激活虚拟环境
source .venv/bin/activate

echo "虚拟环境已激活！"
echo "Python 路径: $(which python)"
echo "Python 版本: $(python --version)"
echo ""
echo "现在可以运行 Python 脚本了，例如："
echo "python get_account_ec2_info.py"
echo ""
echo "要退出虚拟环境，请输入: deactivate"