#!/bin/bash
# AWS 工具运行脚本
# 自动激活虚拟环境、设置代理并运行 AWS 工具

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置网络代理
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890

# 激活虚拟环境
source aws_venv/bin/activate

# 检查 AWS 账号信息
echo "当前 AWS 账号信息："
aws sts get-caller-identity --no-paginate

echo ""
echo "运行 AWS 工具脚本..."

# 运行指定的脚本，如果没有参数则运行 EC2 信息脚本
if [ $# -eq 0 ]; then
    python get_account_ec2_info.py
else
    python "$1"
fi