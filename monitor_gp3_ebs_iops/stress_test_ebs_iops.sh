#!/bin/bash
# EBS IOPS 压力测试脚本
# 用于触发 CloudWatch IOPS 告警
# 
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-12-02
# 
# 适用系统: Amazon Linux 2023, Ubuntu, CentOS
# 目标: 让 EBS IOPS 超过 3000 以触发告警

set -e

echo "=========================================="
echo "EBS IOPS 压力测试脚本"
echo "=========================================="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  建议使用 sudo 运行此脚本以获得最佳性能"
    echo "   sudo bash $0"
    echo ""
fi

# 检查 fio 是否安装
echo "1. 检查 fio 工具..."
if ! command -v fio &> /dev/null; then
    echo "❌ fio 未安装，正在安装..."
    
    # 检测系统类型并安装
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            amzn|amazonlinux)
                echo "检测到 Amazon Linux，使用 dnf 安装..."
                sudo dnf install -y fio
                ;;
            ubuntu|debian)
                echo "检测到 Ubuntu/Debian，使用 apt 安装..."
                sudo apt-get update
                sudo apt-get install -y fio
                ;;
            centos|rhel|fedora)
                echo "检测到 CentOS/RHEL/Fedora，使用 yum 安装..."
                sudo yum install -y fio
                ;;
            *)
                echo "❌ 未识别的系统类型: $ID"
                echo "请手动安装 fio: https://fio.readthedocs.io/"
                exit 1
                ;;
        esac
    else
        echo "❌ 无法检测系统类型"
        exit 1
    fi
fi

echo "✓ fio 已安装: $(fio --version)"
echo ""

# 创建测试目录
TEST_DIR="/tmp/ebs_iops_test"
echo "2. 创建测试目录..."
mkdir -p "$TEST_DIR"
echo "✓ 测试目录: $TEST_DIR"
echo ""

# 获取磁盘信息
echo "3. 当前磁盘信息..."
df -h "$TEST_DIR"
echo ""

# 配置参数
DURATION=${1:-300}  # 默认运行 5 分钟（300秒）
TARGET_IOPS=3500    # 目标 IOPS（超过 3000 阈值）
BLOCK_SIZE="4k"     # 4KB 块大小（典型的随机 IO）
NUM_JOBS=8          # 并发任务数

echo "=========================================="
echo "测试配置"
echo "=========================================="
echo "测试目录: $TEST_DIR"
echo "运行时长: $DURATION 秒"
echo "目标 IOPS: $TARGET_IOPS"
echo "块大小: $BLOCK_SIZE"
echo "并发任务: $NUM_JOBS"
echo "=========================================="
echo ""

echo "⚠️  警告: 此测试将产生大量磁盘 IO 操作"
echo "   - 可能影响系统性能"
echo "   - 建议在测试环境运行"
echo "   - 按 Ctrl+C 可随时停止"
echo ""

# 倒计时
echo "5 秒后开始测试..."
for i in 5 4 3 2 1; do
    echo "$i..."
    sleep 1
done
echo ""

echo "=========================================="
echo "开始 IOPS 压力测试"
echo "=========================================="
echo ""

# 运行 fio 测试
# 使用随机读写混合模式，70% 读 + 30% 写
fio --name=iops_stress_test \
    --directory="$TEST_DIR" \
    --size=1G \
    --numjobs=$NUM_JOBS \
    --time_based \
    --runtime=$DURATION \
    --ramp_time=10 \
    --ioengine=libaio \
    --direct=1 \
    --verify=0 \
    --bs=$BLOCK_SIZE \
    --iodepth=32 \
    --rw=randrw \
    --rwmixread=70 \
    --group_reporting \
    --rate_iops=$TARGET_IOPS

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""

# 清理测试文件
echo "清理测试文件..."
rm -rf "$TEST_DIR"
echo "✓ 清理完成"
echo ""

echo "=========================================="
echo "后续步骤"
echo "=========================================="
echo "1. 等待 5-10 分钟让 CloudWatch 收集指标"
echo "2. 检查 CloudWatch 控制台查看 IOPS 指标"
echo "3. 查看 SNS 邮件/通知确认告警触发"
echo ""
echo "CloudWatch 指标路径:"
echo "  AWS Console → CloudWatch → Alarms"
echo "  或"
echo "  AWS Console → EC2 → Volumes → Monitoring"
echo "=========================================="
