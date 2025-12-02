#!/bin/bash
# EBS IOPS 简单压力测试脚本（使用 dd 命令）
# 不需要安装额外工具
# 
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-12-02

set -e

echo "=========================================="
echo "EBS IOPS 简单压力测试"
echo "=========================================="
echo ""

# 创建测试目录（使用 /var/tmp 而不是 /tmp，因为 /tmp 可能是 tmpfs）
TEST_DIR="/var/tmp/ebs_iops_test"

# 清理旧的测试文件
if [ -d "$TEST_DIR" ]; then
    echo "清理旧的测试文件..."
    rm -rf "$TEST_DIR"
fi

mkdir -p "$TEST_DIR"

# 检查可用磁盘空间
AVAILABLE_SPACE_KB=$(df "$TEST_DIR" | tail -1 | awk '{print $4}')
AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE_KB / 1024 / 1024))

echo "可用磁盘空间: ${AVAILABLE_SPACE_GB} GB"

# 根据可用空间调整并发数
if [ $AVAILABLE_SPACE_GB -lt 2 ]; then
    echo "❌ 错误: 可用空间不足 2GB"
    exit 1
elif [ $AVAILABLE_SPACE_GB -lt 5 ]; then
    PARALLEL_JOBS=4
    BLOCK_COUNT=500
elif [ $AVAILABLE_SPACE_GB -lt 10 ]; then
    PARALLEL_JOBS=8
    BLOCK_COUNT=800
else
    PARALLEL_JOBS=16
    BLOCK_COUNT=1000
fi

# 配置参数
DURATION=${1:-1800}  # 默认运行 30 分钟（1800秒）

echo "测试配置:"
echo "  测试目录: $TEST_DIR"
echo "  运行时长: $DURATION 秒"
echo "  并发任务: $PARALLEL_JOBS"
echo "  每次写入: ${BLOCK_COUNT} 个 4KB 块"
echo ""

echo "当前磁盘信息:"
df -h "$TEST_DIR"
echo ""

echo "⚠️  警告: 此测试将产生大量磁盘 IO"
echo "   按 Ctrl+C 可随时停止"
echo ""

echo "3 秒后开始..."
sleep 3
echo ""

echo "=========================================="
echo "开始测试 (运行 $DURATION 秒)"
echo "=========================================="

# 记录开始时间
START_TIME=$(date +%s)
END_TIME=$((START_TIME + DURATION))

# 后台任务计数
JOB_COUNT=0

# 启动多个并发 dd 任务
for i in $(seq 1 $PARALLEL_JOBS); do
    (
        while [ $(date +%s) -lt $END_TIME ]; do
            # 随机读写，4KB 块大小
            dd if=/dev/urandom of="$TEST_DIR/testfile_$i" bs=4k count=$BLOCK_COUNT oflag=direct 2>/dev/null
            dd if="$TEST_DIR/testfile_$i" of=/dev/null bs=4k iflag=direct 2>/dev/null
        done
    ) &
    JOB_COUNT=$((JOB_COUNT + 1))
done

echo "✓ 已启动 $JOB_COUNT 个并发任务"
echo ""

# 显示进度
while [ $(date +%s) -lt $END_TIME ]; do
    ELAPSED=$(($(date +%s) - START_TIME))
    REMAINING=$((DURATION - ELAPSED))
    echo -ne "\r进度: $ELAPSED / $DURATION 秒 (剩余 $REMAINING 秒)   "
    sleep 5
done

echo ""
echo ""
echo "等待所有任务完成..."
wait

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""

# 清理
echo "清理测试文件..."
rm -rf "$TEST_DIR"
echo "✓ 清理完成"
echo ""

echo "=========================================="
echo "后续步骤"
echo "=========================================="
echo "1. 等待 5-10 分钟让 CloudWatch 收集指标"
echo "2. 检查告警状态:"
echo ""
echo "   aws cloudwatch describe-alarms \\"
echo "     --alarm-name-prefix EBS- \\"
echo "     --region ap-southeast-1"
echo ""
echo "3. 查看 EBS 指标:"
echo ""
echo "   aws cloudwatch get-metric-statistics \\"
echo "     --namespace AWS/EBS \\"
echo "     --metric-name VolumeReadOps \\"
echo "     --dimensions Name=VolumeId,Value=<your-volume-id> \\"
echo "     --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \\"
echo "     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \\"
echo "     --period 300 \\"
echo "     --statistics Sum \\"
echo "     --region ap-southeast-1"
echo ""
echo "=========================================="
