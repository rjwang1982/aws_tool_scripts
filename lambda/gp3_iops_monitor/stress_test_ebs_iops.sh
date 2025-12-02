#!/bin/bash
# EBS IOPS 压力测试脚本
# 用于触发 CloudWatch IOPS 告警
# 
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-12-02
# 更新时间: 2025-12-02
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

# 创建测试目录（使用 /var/tmp 而不是 /tmp，因为 /tmp 可能是 tmpfs）
TEST_DIR="/var/tmp/ebs_iops_test"
echo "2. 检查并清理旧测试文件..."

# 检查是否存在旧的测试目录
if [ -d "$TEST_DIR" ]; then
    echo "⚠️  发现旧的测试目录，正在清理..."
    OLD_SIZE=$(du -sh "$TEST_DIR" 2>/dev/null | awk '{print $1}')
    echo "   旧文件大小: $OLD_SIZE"
    rm -rf "$TEST_DIR"
    echo "✓ 旧文件已清理"
fi

mkdir -p "$TEST_DIR"
echo "✓ 测试目录: $TEST_DIR"
echo ""

# 获取磁盘信息
echo "3. 当前磁盘信息..."
df -h "$TEST_DIR"
echo ""

# 检查可用磁盘空间
echo "4. 检查可用磁盘空间..."
AVAILABLE_SPACE_KB=$(df "$TEST_DIR" | tail -1 | awk '{print $4}')
AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE_KB / 1024 / 1024))

echo "可用磁盘空间: ${AVAILABLE_SPACE_GB} GB"

# 根据可用空间动态调整配置
if [ $AVAILABLE_SPACE_GB -lt 2 ]; then
    echo "❌ 错误: 可用空间不足 2GB，无法运行测试"
    echo "   当前可用: ${AVAILABLE_SPACE_GB} GB"
    echo "   建议清理磁盘空间后再试"
    exit 1
elif [ $AVAILABLE_SPACE_GB -lt 5 ]; then
    echo "⚠️  可用空间较少，使用小文件模式"
    FILE_SIZE="128M"
    NUM_JOBS=8
    IO_DEPTH=64
elif [ $AVAILABLE_SPACE_GB -lt 10 ]; then
    echo "✓ 可用空间适中，使用标准模式"
    FILE_SIZE="256M"
    NUM_JOBS=12
    IO_DEPTH=64
else
    echo "✓ 可用空间充足，使用高性能模式"
    FILE_SIZE="512M"
    NUM_JOBS=16
    IO_DEPTH=128
fi

TOTAL_SIZE_MB=$((${FILE_SIZE%M} * NUM_JOBS))
echo "预计使用空间: ${TOTAL_SIZE_MB} MB (${NUM_JOBS} 个任务 × ${FILE_SIZE})"
echo ""

# 配置参数
DURATION_MINUTES=${1:-30}  # 默认运行 30 分钟
DURATION=$((DURATION_MINUTES * 60))  # 转换为秒
BLOCK_SIZE="4k"      # 4KB 块大小（典型的随机 IO）

echo "=========================================="
echo "测试配置"
echo "=========================================="
echo "测试目录: $TEST_DIR"
echo "运行时长: $DURATION_MINUTES 分钟 ($DURATION 秒)"
echo "块大小: $BLOCK_SIZE"
echo "文件大小: $FILE_SIZE"
echo "并发任务: $NUM_JOBS"
echo "IO 深度: $IO_DEPTH"
echo "预计空间: ${TOTAL_SIZE_MB} MB"
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
    --size=$FILE_SIZE \
    --numjobs=$NUM_JOBS \
    --time_based \
    --runtime=$DURATION \
    --ramp_time=10 \
    --ioengine=libaio \
    --direct=1 \
    --verify=0 \
    --bs=$BLOCK_SIZE \
    --iodepth=$IO_DEPTH \
    --rw=randrw \
    --rwmixread=70 \
    --group_reporting

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
