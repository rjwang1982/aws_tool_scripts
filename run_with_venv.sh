#!/bin/bash
# 使用虚拟环境运行 Python 脚本

# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境 .venv 不存在"
    echo "请先创建虚拟环境: python3 -m venv .venv"
    exit 1
fi

# 检查是否提供了 Python 脚本参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <python_script> [参数...]"
    echo "示例: $0 get_account_ec2_info.py"
    exit 1
fi

# 激活虚拟环境并运行脚本
source .venv/bin/activate
echo "使用虚拟环境运行: $@"
echo "Python 路径: $(which python)"
echo ""

# 运行 Python 脚本
python "$@"

# 脚本执行完成后自动退出虚拟环境
deactivate