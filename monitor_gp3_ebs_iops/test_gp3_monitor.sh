#!/bin/bash
# GP3 IOPS 监控脚本测试工具
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-12-02

set -e

echo "=========================================="
echo "GP3 EBS IOPS 监控脚本测试"
echo "=========================================="
echo ""

# 获取项目根目录（脚本所在目录的上一级）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"

# 检查并激活虚拟环境
echo "0. 检查 Python 虚拟环境..."
if [ -d "$VENV_PATH" ]; then
    echo "✓ 找到虚拟环境: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
    echo "✓ 已激活虚拟环境"
else
    echo "❌ 虚拟环境不存在: $VENV_PATH"
    exit 1
fi
echo ""

# 检查 AWS CLI
echo "1. 检查 AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI 未安装"
    exit 1
fi
echo "✓ AWS CLI 已安装: $(aws --version)"
echo ""

# 检查 AWS 认证
echo "2. 检查 AWS 认证..."
if aws sts get-caller-identity &> /dev/null; then
    echo "✓ AWS 认证成功"
    aws sts get-caller-identity
else
    echo "❌ AWS 认证失败，请配置 AWS credentials"
    exit 1
fi
echo ""

# 检查 Python
echo "3. 检查 Python 环境..."
echo "✓ Python 路径: $(which python)"
echo "✓ Python 版本: $(python --version)"
echo ""

# 检查 boto3
echo "4. 检查 boto3 库..."
if python -c "import boto3" 2>/dev/null; then
    echo "✓ boto3 已安装"
    python -c "import boto3; print(f'boto3 版本: {boto3.__version__}')"
else
    echo "❌ boto3 未安装，正在安装..."
    pip install boto3
fi
echo ""

# 列出 GP3 卷
echo "5. 列出当前区域的 GP3 卷..."
REGION=${AWS_REGION:-ap-southeast-1}
echo "区域: $REGION"
echo ""

GP3_COUNT=$(aws ec2 describe-volumes \
    --filters Name=volume-type,Values=gp3 \
    --region $REGION \
    --query 'length(Volumes)' \
    --output text 2>/dev/null || echo "0")

if [ "$GP3_COUNT" -eq 0 ]; then
    echo "⚠️  未找到 GP3 卷"
else
    echo "✓ 找到 $GP3_COUNT 个 GP3 卷"
    echo ""
    echo "GP3 卷列表:"
    aws ec2 describe-volumes \
        --filters Name=volume-type,Values=gp3 \
        --region $REGION \
        --query 'Volumes[*].[VolumeId,Size,Iops,State,Tags[?Key==`Name`].Value|[0]]' \
        --output table
fi
echo ""

# 检查 SNS 主题
echo "6. 检查 SNS 主题..."
SNS_TOPIC="arn:aws:sns:ap-southeast-1:269490040603:alarmbyrj20250225"
if aws sns get-topic-attributes --topic-arn "$SNS_TOPIC" --region $REGION &>/dev/null; then
    echo "✓ SNS 主题存在: $SNS_TOPIC"
else
    echo "⚠️  SNS 主题不存在或无权限访问: $SNS_TOPIC"
fi
echo ""

echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "如果所有检查都通过，可以运行:"
echo "  python3 monitor_gp3_ebs_iops.py"
echo ""
