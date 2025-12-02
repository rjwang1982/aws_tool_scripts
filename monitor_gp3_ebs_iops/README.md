# GP3 EBS IOPS 监控告警

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-12-02

---

## 功能说明

自动为所有 GP3 类型的 EBS 卷创建 IOPS 监控告警，当 IOPS（ReadOps + WriteOps）超过 3000 时触发 SNS 通知。

---

## 快速开始

### 1. 配置参数

编辑 `monitor_gp3_ebs_iops.py`：

```python
AWS_REGION = "ap-southeast-1"
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:269490040603:alarmbyrj20250225"
IOPS_THRESHOLD = 3000
```

### 2. 运行脚本

```bash
# 激活虚拟环境
source ../.venv/bin/activate

# 创建告警
python monitor_gp3_ebs_iops.py

# 使用指定 AWS Profile
AWS_PROFILE=g0603 python monitor_gp3_ebs_iops.py
```

### 3. 测试告警

在 EC2 实例上运行压力测试：

```bash
# 上传测试脚本到 EC2
scp stress_test_ebs_iops.sh ec2-user@<ec2-ip>:/tmp/

# SSH 连接到 EC2
ssh ec2-user@<ec2-ip>

# 运行测试（默认 30 分钟）
sudo bash /tmp/stress_test_ebs_iops.sh

# 自定义时长（例如 10 分钟）
sudo bash /tmp/stress_test_ebs_iops.sh 10

# 自定义时长（例如 60 分钟）
sudo bash /tmp/stress_test_ebs_iops.sh 60
```

---

## 告警效果

![CloudWatch 告警示例](images/cloudwatch-alarm-example.png)

告警创建后在 CloudWatch 控制台可以看到：
- 告警名称：`EBS-{VolumeId}-IOPS-High-Alarm`
- 指标：Total IOPS = (VolumeReadOps + VolumeWriteOps) / Period
- 阈值：3000 IOPS
- 评估周期：连续 2 个周期超过阈值才触发

---

## 环境检查

运行前确认：

```bash
# 检查 AWS 认证
aws sts get-caller-identity

# 检查 boto3
python -c "import boto3; print(boto3.__version__)"

# 列出 GP3 卷
aws ec2 describe-volumes \
  --filters Name=volume-type,Values=gp3 \
  --region ap-southeast-1 \
  --query 'Volumes[*].[VolumeId,Size,Iops,State]' \
  --output table
```

---

## 配置选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `AWS_REGION` | AWS 区域 | `ap-southeast-1` |
| `SNS_TOPIC_ARN` | SNS 主题 ARN | - |
| `IOPS_THRESHOLD` | IOPS 告警阈值 | `3000` |
| `USE_TAGS` | 是否使用标签筛选 | `False` |
| `VOLUME_TAG_KEY` | 标签键 | `Monitor` |
| `VOLUME_TAG_VALUE` | 标签值 | `yes` |

---

## 故障排查

### 问题 1: 未找到 GP3 卷

检查区域配置是否正确：

```bash
aws ec2 describe-volumes \
  --filters Name=volume-type,Values=gp3 \
  --region <your-region>
```

### 问题 2: 权限不足

确保 IAM 用户/角色有以下权限：

```json
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
```

### 问题 3: 压力测试磁盘空间不足

脚本会自动检测可用空间并调整参数：
- < 2GB：拒绝运行
- 2-5GB：小文件模式（128M × 4 任务）
- 5-10GB：标准模式（256M × 6 任务）
- > 10GB：高性能模式（512M × 8 任务）

---

## 文件说明

- `monitor_gp3_ebs_iops.py` - 主监控脚本
- `stress_test_ebs_iops.sh` - EBS IOPS 压力测试脚本
- `images/cloudwatch-alarm-example.png` - 告警效果截图

---

**最后更新**: 2025-12-02
