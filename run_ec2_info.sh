#!/bin/bash
# 专门运行 EC2 信息获取脚本

# 进入脚本所在目录
cd "$(dirname "$0")"

# 设置网络代理（如果需要）
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890

# 激活虚拟环境
source .venv/bin/activate

echo "正在使用虚拟环境运行 EC2 信息获取脚本..."
echo "Python 路径: $(which python)"
echo ""

# 运行脚本
python get_account_ec2_info.py

# 退出虚拟环境
deactivate