# GP3 EBS IOPS 监控告警脚本使用说明

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-12-02

---

## 📋 功能说明

这个脚本用于自动为所有 GP3 类型的 EBS 卷创建 IOPS 监控告警。

### 核心功能

1. **自动发现 GP3 卷**: 扫描指定区域的所有 GP3 类型 EBS 卷
2. **IOPS 计算**: 监控 `VolumeReadOps + VolumeWriteOps` 的总和
3. **智能告警**: 当 IOPS 超过阈值（默认 3000）时触发告警
4. **自动清理**: 删除旧告警并创建新告警，避免重复
5. **状态通知**: 告警触发和恢复时都会发送 SNS 通知

---

## 🎯 监控指标详解

### IOPS 计算公式

```
Total IOPS = (VolumeReadOps + VolumeWriteOps) / Period
```

- **VolumeReadOps**: 5 分钟内的读操作总数
- **VolumeWriteOps**: 5 分钟内的写操作总数
- **Period**: 统计周期（300 秒 = 5 分钟）

### 告警条件

- **阈值**: 默认 3000 IOPS（可配置）
- **评估周期**: 2 个数据点
- **触发条件**: 连续 2 个周期 IOPS > 3000
- **统计方法**: Sum（总和）

---

## 🚀 快速开始

### 1. 配置脚本参数

编辑 `monitor_gp3_ebs_iops.py` 文件中的配置部分：

```python
# ==================== 自定义配置 ====================
AWS_REGION = "ap-southeast-1"  # AWS 区域
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:269490040603:alarmbyrj20250225"  # SNS 主题
IOPS_THRESHOLD = 3000  # IOPS 告警阈值
USE_TAGS = False  # 是否使用标签筛选
VOLUME_TAG_KEY = "Monitor"  # 标签键
VOLUME_TAG_VALUE = "yes"  # 标签值
# ===================================================
```

### 2. 运行脚本

```bash
# 进入脚本目录
cd monitor_gp3_ebs_iops

# 激活项目虚拟环境
source ../.venv/bin/activate

# 运行脚本
python monitor_gp3_ebs_iops.py
```

### 3. 使用 AWS Profile

如果需要指定 AWS Profile：

```bash
# 激活虚拟环境
source ../.venv/bin/activate

# Global 区域
AWS_PROFILE=g0603 python monitor_gp3_ebs_iops.py

# 中国区域
AWS_PROFILE=c5611 python monitor_gp3_ebs_iops.py
```

---

## ⚙️ 配置选项

### 基础配置

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `AWS_REGION` | AWS 区域 | `ap-southeast-1` | `us-east-1` |
| `SNS_TOPIC_ARN` | SNS 主题 ARN | - | `arn:aws:sns:...` |
| `IOPS_THRESHOLD` | IOPS 告警阈值 | `3000` | `5000` |

### 标签筛选配置

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `USE_TAGS` | 是否启用标签筛选 | `False` | `True` |
| `VOLUME_TAG_KEY` | 标签键 | `Monitor` | `Environment` |
| `VOLUME_TAG_VALUE` | 标签值 | `yes` | `production` |

---

## 🎨 CloudWatch 控制台示例

### 告警创建成功后的效果

运行脚本后，在 AWS CloudWatch 控制台可以看到创建的告警：

![CloudWatch 告警示例](images/cloudwatch-alarm-example.png)

**告警列表视图**：
- 告警名称：`EBS-vol-0cc377afd67b3d537-IOPS-High-Alarm`
- 状态：正常（绿色）或告警（红色）
- 指标：Total IOPS

**告警详情页面**：
- 图表显示：Total IOPS 趋势图
- 阈值线：3000 IOPS（红色虚线）
- 当前值：实时 IOPS 数据
- 操作配置：
  - 告警时：发送 SNS 通知到 `arn:aws:sns:ap-southeast-1:269490040603:alarmbyrj20250225`
  - 恢复时：同样发送 SNS 通知

**指标数学表达式**：
```
Total IOPS = (VolumeReadOps + VolumeWriteOps) / Period
```

如截图所示，告警成功创建后会显示：
- 左侧告警列表中的告警状态
- 右侧详情页面的 IOPS 趋势图
- 阈值线和当前 IOPS 值
- 操作配置（SNS 通知设置）

---

## 📊 输出示例

### 正常运行输出

```
2025-12-02 10:00:00 - INFO - ============================================================
2025-12-02 10:00:00 - INFO - 开始 GP3 EBS IOPS 监控告警创建流程
2025-12-02 10:00:00 - INFO - ============================================================
2025-12-02 10:00:00 - INFO - 检测到 AWS 账户 ID: 269490040603
2025-12-02 10:00:00 - INFO - 区域: ap-southeast-1
2025-12-02 10:00:00 - INFO - IOPS 阈值: 3000
2025-12-02 10:00:00 - INFO - SNS 主题: arn:aws:sns:ap-southeast-1:269490040603:alarmbyrj20250225
2025-12-02 10:00:00 - INFO - 使用标签筛选: False
2025-12-02 10:00:00 - INFO - ============================================================
2025-12-02 10:00:01 - INFO - 找到 5 个 GP3 卷
2025-12-02 10:00:01 - INFO - 处理卷: vol-0123456789abcdef0 (名称: web-server-root, 实例: i-0123456789abcdef0, 配置 IOPS: 3000)
2025-12-02 10:00:02 - INFO - ✓ 已创建告警: EBS-vol-0123456789abcdef0-IOPS-High-Alarm
2025-12-02 10:00:03 - INFO - 处理卷: vol-0123456789abcdef1 (名称: db-server-data, 实例: i-0123456789abcdef1, 配置 IOPS: 16000)
2025-12-02 10:00:04 - INFO - ✓ 已创建告警: EBS-vol-0123456789abcdef1-IOPS-High-Alarm
2025-12-02 10:00:05 - INFO - ============================================================
2025-12-02 10:00:05 - INFO - 总共创建告警数量: 5
2025-12-02 10:00:05 - INFO - 
已创建的告警 ARN 列表:
2025-12-02 10:00:05 - INFO - 1. arn:aws:cloudwatch:ap-southeast-1:269490040603:alarm:EBS-vol-0123456789abcdef0-IOPS-High-Alarm
2025-12-02 10:00:05 - INFO - 2. arn:aws:cloudwatch:ap-southeast-1:269490040603:alarm:EBS-vol-0123456789abcdef1-IOPS-High-Alarm
2025-12-02 10:00:05 - INFO - ============================================================
2025-12-02 10:00:05 - INFO - GP3 EBS IOPS 监控告警创建流程完成
2025-12-02 10:00:05 - INFO - ============================================================
```

---

## 🔍 告警命名规则

告警名称格式：`EBS-{VolumeId}-IOPS-High-Alarm`

示例：
- `EBS-vol-0123456789abcdef0-IOPS-High-Alarm`
- `EBS-vol-0987654321fedcba0-IOPS-High-Alarm`

---

## 📧 SNS 告警通知示例

### 告警触发时

```
AlarmName: EBS-vol-0123456789abcdef0-IOPS-High-Alarm
AlarmDescription: GP3 卷 vol-0123456789abcdef0 (web-server-root) IOPS 超过 3000。实例: i-0123456789abcdef0
NewStateValue: ALARM
NewStateReason: Threshold Crossed: 1 datapoint [3245.0] was greater than the threshold (3000.0).
```

### 告警恢复时

```
AlarmName: EBS-vol-0123456789abcdef0-IOPS-High-Alarm
AlarmDescription: GP3 卷 vol-0123456789abcdef0 (web-server-root) IOPS 超过 3000。实例: i-0123456789abcdef0
NewStateValue: OK
NewStateReason: Threshold Crossed: 1 datapoint [2850.0] was not greater than the threshold (3000.0).
```

---

## 🛠️ 高级用法

### 1. 仅监控特定标签的卷

```python
USE_TAGS = True
VOLUME_TAG_KEY = "Environment"
VOLUME_TAG_VALUE = "production"
```

### 2. 调整 IOPS 阈值

```python
# 对于高性能数据库，可以设置更高的阈值
IOPS_THRESHOLD = 10000
```

### 3. 多区域部署

```bash
# 为多个区域创建告警
for region in ap-southeast-1 us-east-1 eu-west-1; do
    sed -i '' "s/AWS_REGION = .*/AWS_REGION = \"$region\"/" monitor_gp3_ebs_iops.py
    python monitor_gp3_ebs_iops.py
done
```

---

## 📝 注意事项

### GP3 IOPS 限制

- **基准 IOPS**: 3000（免费）
- **最大 IOPS**: 16000
- **IOPS/GB 比例**: 最大 500:1

### 告警最佳实践

1. **阈值设置**: 建议设置为配置 IOPS 的 80-90%
2. **评估周期**: 默认 2 个周期可避免短暂峰值误报
3. **数据缺失处理**: 设置为 `notBreaching` 避免数据缺失时误报

### 成本考虑

- CloudWatch 告警：前 10 个免费，之后 $0.10/告警/月
- SNS 通知：前 1000 次免费，之后 $0.50/百万次

---

## 🐛 故障排查

### 问题 1: 未找到 GP3 卷

**原因**: 区域配置错误或没有 GP3 卷

**解决**:
```bash
# 检查指定区域的 GP3 卷
aws ec2 describe-volumes --filters Name=volume-type,Values=gp3 --region ap-southeast-1
```

### 问题 2: 权限不足

**原因**: IAM 权限不足

**所需权限**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeVolumes",
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:DescribeAlarms",
                "cloudwatch:DeleteAlarms",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

### 问题 3: SNS 主题不存在

**原因**: SNS 主题 ARN 错误或不存在

**解决**:
```bash
# 列出所有 SNS 主题
aws sns list-topics --region ap-southeast-1

# 创建新的 SNS 主题
aws sns create-topic --name ebs-iops-alerts --region ap-southeast-1
```

---

## 🔗 相关资源

- [AWS EBS GP3 文档](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html#EBSVolumeTypes_gp3)
- [CloudWatch EBS 指标](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using_cloudwatch_ebs.html)
- [CloudWatch 告警数学表达式](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/using-metric-math.html)

---

## 📞 支持

如有问题或建议，请联系：
- **邮箱**: wangrenjun@gmail.com
- **作者**: RJ.Wang

---

**最后更新**: 2025-12-02
