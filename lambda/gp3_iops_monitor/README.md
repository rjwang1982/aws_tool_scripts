# GP3 EBS IOPS 监控告警

**作者**: RJ.Wang  
**创建时间**: 2025-12-02

自动为 GP3 类型的 EBS 卷创建 IOPS 监控告警，当 IOPS（ReadOps + WriteOps）超过阈值时触发 SNS 通知。

---

## 使用方法

### 1. 配置参数

编辑 `monitor_gp3_ebs_iops.py`：

```python
AWS_REGION = "ap-southeast-1"
SNS_TOPIC_ARN = "arn:aws:sns:..."
IOPS_THRESHOLD = 3000
```

### 2. 创建告警

```bash
source ../.venv/bin/activate
python monitor_gp3_ebs_iops.py
```

### 3. 测试告警

在 EC2 上运行压力测试：

```bash
# 默认 30 分钟
sudo bash stress_test_ebs_iops.sh

# 自定义时长（分钟）
sudo bash stress_test_ebs_iops.sh 10
```

---

## 告警效果

![CloudWatch 告警](images/cloudwatch-alarm-example.png)

- 告警名称：`EBS-{VolumeId}-IOPS-High-Alarm`
- 指标：Total IOPS = (VolumeReadOps + VolumeWriteOps) / Period
- 评估：连续 2 个周期超过阈值才触发

---

## 配置选项

| 参数 | 默认值 |
|------|--------|
| `AWS_REGION` | `ap-southeast-1` |
| `IOPS_THRESHOLD` | `3000` |
| `USE_TAGS` | `False` |

---

## 所需权限

```json
{
    "Effect": "Allow",
    "Action": [
        "ec2:DescribeVolumes",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:DescribeAlarms",
        "cloudwatch:DeleteAlarms"
    ],
    "Resource": "*"
}
```

---

**最后更新**: 2025-12-02
