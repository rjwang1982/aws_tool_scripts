# EBS IOPS 告警测试指南

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-12-02  
**EC2 实例**: i-05acbf129cf3eff2c  
**操作系统**: Amazon Linux 2023 6.12

---

## 📋 测试目标

让 EBS 卷的 IOPS（ReadOps + WriteOps）超过 3000，触发 CloudWatch 告警。

---

## 🚀 快速开始

### 方法 1: 使用 fio 工具（推荐）

**优点**: 精确控制 IOPS，性能最好

```bash
# 1. 连接到 EC2 实例
ssh ec2-user@<your-ec2-ip>

# 2. 下载测试脚本
wget https://raw.githubusercontent.com/.../stress_test_ebs_iops.sh
# 或者手动创建脚本（见下文）

# 3. 运行测试（默认 5 分钟）
sudo bash stress_test_ebs_iops.sh

# 4. 自定义运行时长（例如 10 分钟）
sudo bash stress_test_ebs_iops.sh 600
```

### 方法 2: 使用 dd 命令（无需安装）

**优点**: 不需要安装额外工具，系统自带

```bash
# 1. 连接到 EC2 实例
ssh ec2-user@<your-ec2-ip>

# 2. 运行简单测试脚本
sudo bash stress_test_ebs_iops_simple.sh

# 3. 自定义运行时长（例如 10 分钟）
sudo bash stress_test_ebs_iops_simple.sh 600
```

---

## 📊 测试原理

### IOPS 计算公式

```
Total IOPS = (VolumeReadOps + VolumeWriteOps) / Period
```

- **Period**: 300 秒（5 分钟）
- **目标**: 超过 3000 IOPS
- **所需操作数**: > 900,000 次（3000 × 300）

### 测试策略

1. **高并发**: 启动多个并发任务（8-16 个）
2. **小块 IO**: 使用 4KB 块大小（典型的随机 IO）
3. **读写混合**: 70% 读 + 30% 写
4. **持续时间**: 至少 5 分钟（覆盖 2 个评估周期）

---

## 🔧 详细步骤

### 步骤 1: 准备 EC2 实例

```bash
# 连接到实例
ssh -i your-key.pem ec2-user@<ec2-public-ip>

# 检查系统信息
uname -a
# 输出: Linux ... 6.12.6-1.amzn2023.x86_64 ...

# 检查磁盘
lsblk
df -h
```

### 步骤 2: 创建测试脚本

**选项 A: 使用 fio（推荐）**

创建文件 `stress_test_ebs_iops.sh`，内容见上面的脚本。

**选项 B: 使用 dd（简单）**

创建文件 `stress_test_ebs_iops_simple.sh`，内容见上面的脚本。

### 步骤 3: 运行测试

```bash
# 给脚本执行权限
chmod +x stress_test_ebs_iops.sh

# 运行测试（5 分钟）
sudo bash stress_test_ebs_iops.sh

# 或运行更长时间（10 分钟）
sudo bash stress_test_ebs_iops.sh 600
```

### 步骤 4: 监控测试进度

**在 EC2 实例上**:

```bash
# 实时查看 IO 统计
iostat -x 5

# 查看磁盘活动
watch -n 5 'df -h && echo "" && iostat -x'

# 查看系统负载
top
```

**在本地终端**:

```bash
# 查看 CloudWatch 指标（需要等待 5-10 分钟）
aws cloudwatch get-metric-statistics \
  --namespace AWS/EBS \
  --metric-name VolumeReadOps \
  --dimensions Name=VolumeId,Value=vol-xxxxxxxxx \
  --start-time $(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region ap-southeast-1

# 查看告警状态
aws cloudwatch describe-alarms \
  --alarm-name-prefix EBS- \
  --state-value ALARM \
  --region ap-southeast-1
```

### 步骤 5: 验证告警

**通过 AWS CLI**:

```bash
# 查看所有 EBS 告警
aws cloudwatch describe-alarms \
  --alarm-name-prefix EBS- \
  --region ap-southeast-1 \
  --query 'MetricAlarms[*].[AlarmName,StateValue,StateReason]' \
  --output table

# 查看告警历史
aws cloudwatch describe-alarm-history \
  --alarm-name EBS-vol-xxxxxxxxx-IOPS-High-Alarm \
  --history-item-type StateUpdate \
  --max-records 5 \
  --region ap-southeast-1
```

**通过 AWS 控制台**:

1. 登录 AWS 控制台
2. 进入 CloudWatch 服务
3. 左侧菜单选择"告警" → "所有告警"
4. 搜索 `EBS-vol-` 找到你的告警
5. 点击告警名称查看详情

---

## 📈 预期结果

### 测试期间

```
========================================
开始 IOPS 压力测试
========================================

Jobs: 8 (f=8): [m(8)][100.0%][r=14.2MiB/s,w=6.1MiB/s][r=3640,w=1560 IOPS]
...
```

### CloudWatch 指标

5-10 分钟后，应该看到：

```
VolumeReadOps: ~630,000 (5 分钟内)
VolumeWriteOps: ~270,000 (5 分钟内)
Total IOPS: ~3,000+ (平均每秒)
```

### 告警状态

```
AlarmName: EBS-vol-xxxxxxxxx-IOPS-High-Alarm
StateValue: ALARM
StateReason: Threshold Crossed: 2 datapoints [3245.0, 3180.0] were greater than the threshold (3000.0)
```

### SNS 通知

你应该收到类似这样的邮件：

```
Subject: ALARM: "EBS-vol-xxxxxxxxx-IOPS-High-Alarm" in AP-SOUTHEAST-1

You are receiving this email because your Amazon CloudWatch Alarm 
"EBS-vol-xxxxxxxxx-IOPS-High-Alarm" in the AP-SOUTHEAST-1 region has 
entered the ALARM state.

Alarm Details:
- State Change: OK -> ALARM
- Reason: Threshold Crossed: 2 datapoints [3245.0, 3180.0] were greater 
  than the threshold (3000.0)
```

### CloudWatch 控制台视图

在 AWS CloudWatch 控制台中，你可以看到：

1. **告警列表**：
   - 告警名称：`EBS-vol-0cc377afd67b3d537-IOPS-High-Alarm`
   - 状态：ALARM（红色）或 OK（绿色）
   - 描述：GP3 卷 IOPS 超过 3000

2. **告警详情页**：
   - **图表**：显示 Total IOPS 随时间变化
   - **阈值线**：3000 IOPS（红色虚线）
   - **当前值**：实时 IOPS 数据点
   - **时间范围**：可选择 1小时、3小时、12小时、1天等

3. **操作配置**：
   - 告警时：发送到 SNS 主题
   - 恢复时：发送到 SNS 主题
   - 数据不足时：不触发告警



## 🛠️ 故障排查

### 问题 1: IOPS 没有达到 3000

**原因**: 
- 并发任务数不够
- 实例类型限制（如 t2/t3 实例有 IO 限制）
- EBS 卷配置的 IOPS 不足

**解决**:

```bash
# 增加并发任务数
# 在脚本中修改: NUM_JOBS=16 或 PARALLEL_JOBS=32

# 检查实例类型限制
aws ec2 describe-instance-types \
  --instance-types t3.medium \
  --query 'InstanceTypes[0].EbsInfo' \
  --region ap-southeast-1

# 检查 EBS 卷配置
aws ec2 describe-volumes \
  --volume-ids vol-xxxxxxxxx \
  --query 'Volumes[0].[VolumeType,Iops,Throughput]' \
  --region ap-southeast-1
```

### 问题 2: 告警没有触发

**原因**:
- 需要连续 2 个周期（10 分钟）超过阈值
- CloudWatch 数据延迟（5-10 分钟）

**解决**:

```bash
# 延长测试时间到 15 分钟
sudo bash stress_test_ebs_iops.sh 900

# 检查告警配置
aws cloudwatch describe-alarms \
  --alarm-names EBS-vol-xxxxxxxxx-IOPS-High-Alarm \
  --region ap-southeast-1
```

### 问题 3: 系统变慢或无响应

**原因**: IO 压力过大

**解决**:

```bash
# 按 Ctrl+C 停止测试

# 或在另一个终端杀死进程
pkill -f fio
pkill -f dd

# 清理测试文件
rm -rf /tmp/ebs_iops_test
```

---

## 💡 最佳实践

### 1. 测试时机

- ✅ 在非生产环境测试
- ✅ 在业务低峰期测试
- ✅ 提前通知团队成员

### 2. 测试时长

- **最短**: 10 分钟（覆盖 2 个评估周期）
- **推荐**: 15 分钟（确保触发告警）
- **最长**: 30 分钟（观察恢复过程）

### 3. 监控要点

```bash
# 测试前记录基线
aws cloudwatch get-metric-statistics \
  --namespace AWS/EBS \
  --metric-name VolumeReadOps \
  --dimensions Name=VolumeId,Value=vol-xxxxxxxxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum,Average \
  --region ap-southeast-1
```

### 4. 清理工作

```bash
# 测试完成后
# 1. 停止所有测试进程
pkill -f fio
pkill -f dd

# 2. 清理测试文件
rm -rf /tmp/ebs_iops_test

# 3. 验证磁盘空间
df -h

# 4. 检查系统负载恢复
uptime
```

---

## 📝 测试检查清单

### 测试前

- [ ] 确认在测试环境或非生产时段
- [ ] 备份重要数据
- [ ] 通知团队成员
- [ ] 确认 SNS 订阅已配置
- [ ] 记录当前 IOPS 基线

### 测试中

- [ ] 监控系统负载
- [ ] 观察 IO 统计
- [ ] 记录测试开始时间
- [ ] 保持 SSH 连接稳定

### 测试后

- [ ] 停止所有测试进程
- [ ] 清理测试文件
- [ ] 验证告警触发
- [ ] 检查 SNS 通知
- [ ] 等待告警恢复（OK 状态）
- [ ] 记录测试结果

---

## 🔗 相关命令

### 查看 EBS 卷信息

```bash
# 列出所有 EBS 卷
aws ec2 describe-volumes \
  --region ap-southeast-1 \
  --query 'Volumes[*].[VolumeId,VolumeType,Size,Iops,State]' \
  --output table

# 查看特定卷详情
aws ec2 describe-volumes \
  --volume-ids vol-xxxxxxxxx \
  --region ap-southeast-1
```

### 查看 CloudWatch 告警

```bash
# 列出所有 EBS 告警
aws cloudwatch describe-alarms \
  --alarm-name-prefix EBS- \
  --region ap-southeast-1

# 查看告警历史
aws cloudwatch describe-alarm-history \
  --alarm-name EBS-vol-xxxxxxxxx-IOPS-High-Alarm \
  --region ap-southeast-1 \
  --max-records 10
```

### 手动触发告警（测试用）

```bash
# 设置告警状态为 ALARM（仅用于测试通知）
aws cloudwatch set-alarm-state \
  --alarm-name EBS-vol-xxxxxxxxx-IOPS-High-Alarm \
  --state-value ALARM \
  --state-reason "Manual test" \
  --region ap-southeast-1
```

---

## 📞 支持

如有问题，请联系：
- **邮箱**: wangrenjun@gmail.com
- **作者**: RJ.Wang

---

**最后更新**: 2025-12-02
