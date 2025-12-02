# GP3 IOPS 监控 vs EC2 状态监控对比

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-12-02

---

## 📊 功能对比

| 特性 | EC2 状态监控 | GP3 IOPS 监控 |
|------|-------------|--------------|
| **监控对象** | EC2 实例 | EBS GP3 卷 |
| **监控指标** | StatusCheckFailed_System<br>StatusCheckFailed_Instance<br>EBSIOBalance% | VolumeReadOps + VolumeWriteOps |
| **指标命名空间** | AWS/EC2 | AWS/EBS |
| **筛选条件** | 实例状态 = running | 卷类型 = gp3 |
| **告警阈值** | 固定值（1 或 10） | 可配置（默认 3000） |
| **数学表达式** | 否 | 是（ReadOps + WriteOps） |
| **告警数量** | 每实例 3 个 | 每卷 1 个 |

---

## 🔍 核心差异

### 1. 监控维度 (Dimensions)

**EC2 监控**:
```python
Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}]
```

**GP3 监控**:
```python
Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}]
```

### 2. 指标获取方式

**EC2 监控** - 直接使用单个指标:
```python
cloudwatch_client.put_metric_alarm(
    MetricName='StatusCheckFailed_System',
    Namespace='AWS/EC2',
    Statistic='Maximum',
    # ...
)
```

**GP3 监控** - 使用 Metric Math 组合多个指标:
```python
cloudwatch_client.put_metric_alarm(
    Metrics=[
        {
            'Id': 'm1',
            'MetricStat': {
                'Metric': {
                    'MetricName': 'VolumeReadOps',
                    # ...
                },
                'Stat': 'Sum'
            }
        },
        {
            'Id': 'm2',
            'MetricStat': {
                'Metric': {
                    'MetricName': 'VolumeWriteOps',
                    # ...
                },
                'Stat': 'Sum'
            }
        },
        {
            'Id': 'e1',
            'Expression': '(m1+m2)/PERIOD(m1)',  # 计算 IOPS
            'ReturnData': True
        }
    ]
)
```

### 3. 资源发现逻辑

**EC2 监控**:
```python
# 获取运行中的实例
instances = ec2_client.describe_instances()
for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        if instance['State']['Name'] == 'running':
            instance_ids.append(instance['InstanceId'])
```

**GP3 监控**:
```python
# 获取 GP3 类型的卷
volumes = ec2_client.describe_volumes(
    Filters=[{'Name': 'volume-type', 'Values': ['gp3']}]
)
# 包含已挂载和未挂载的卷
```

### 4. 告警描述信息

**EC2 监控**:
```python
AlarmDescription=f"Alarm for {metric_name} on instance {instance_id}"
```

**GP3 监控**:
```python
AlarmDescription=f"GP3 卷 {volume_id} ({volume_name}) IOPS 超过 {iops_threshold}。实例: {instance_id}"
```

---

## 📈 技术实现对比

### EC2 监控 - 简单指标告警

```python
# 3 个独立的告警
for metric_name in ['StatusCheckFailed_System', 
                    'StatusCheckFailed_Instance', 
                    'EBSIOBalance%']:
    cloudwatch_client.put_metric_alarm(
        AlarmName=f"EC2-{instance_id}-{alarm_name_suffix}-Alarm",
        MetricName=metric_name,
        Namespace='AWS/EC2',
        Statistic='Maximum',
        Threshold=threshold,
        ComparisonOperator=comparison_operator,
        # ...
    )
```

### GP3 监控 - 复合指标告警

```python
# 1 个使用数学表达式的告警
cloudwatch_client.put_metric_alarm(
    AlarmName=f"EBS-{volume_id}-IOPS-High-Alarm",
    Metrics=[
        # m1: VolumeReadOps
        {'Id': 'm1', 'MetricStat': {...}},
        # m2: VolumeWriteOps
        {'Id': 'm2', 'MetricStat': {...}},
        # e1: (m1+m2)/PERIOD(m1) = IOPS
        {'Id': 'e1', 'Expression': '(m1+m2)/PERIOD(m1)'}
    ],
    Threshold=3000,
    ComparisonOperator='GreaterThanThreshold',
    # ...
)
```

---

## 🎯 使用场景

### EC2 状态监控适用于:

- ✅ 监控实例健康状态
- ✅ 检测系统级故障
- ✅ 检测实例级故障
- ✅ 监控 EBS IO 性能平衡

### GP3 IOPS 监控适用于:

- ✅ 监控存储性能
- ✅ 检测 IOPS 瓶颈
- ✅ 优化成本（避免过度配置）
- ✅ 容量规划

---

## 💡 关键技术点

### 1. Metric Math 表达式

GP3 监控使用了 CloudWatch Metric Math 功能：

```python
'Expression': '(m1+m2)/PERIOD(m1)'
```

**解释**:
- `m1`: VolumeReadOps（5分钟内的读操作总数）
- `m2`: VolumeWriteOps（5分钟内的写操作总数）
- `PERIOD(m1)`: 统计周期（300秒）
- 结果: 每秒的平均 IOPS

### 2. 统计方法差异

**EC2 监控**:
```python
Statistic='Maximum'  # 使用最大值
```

**GP3 监控**:
```python
Stat='Sum'  # 使用总和，然后除以周期得到平均值
```

### 3. 评估周期

**EC2 监控**:
```python
Period=300,
EvaluationPeriods=1  # 单个周期即触发
```

**GP3 监控**:
```python
Period=300,
EvaluationPeriods=2,
DatapointsToAlarm=2  # 连续 2 个周期才触发
```

---

## 📊 告警命名规范

### EC2 监控

```
EC2-{InstanceId}-System-Check-Failed-Alarm
EC2-{InstanceId}-Instance-Check-Failed-Alarm
EC2-{InstanceId}-EBS-Check-Failed-Alarm
```

示例:
```
EC2-i-0123456789abcdef0-System-Check-Failed-Alarm
EC2-i-0123456789abcdef0-Instance-Check-Failed-Alarm
EC2-i-0123456789abcdef0-EBS-Check-Failed-Alarm
```

### GP3 监控

```
EBS-{VolumeId}-IOPS-High-Alarm
```

示例:
```
EBS-vol-0123456789abcdef0-IOPS-High-Alarm
```

---

## 🔧 扩展性对比

### EC2 监控扩展

如需添加新指标（如 CPU 使用率）:

```python
for metric_name in ['StatusCheckFailed_System', 
                    'StatusCheckFailed_Instance', 
                    'EBSIOBalance%',
                    'CPUUtilization']:  # 新增
    # 创建告警
```

### GP3 监控扩展

如需监控其他 EBS 指标（如吞吐量）:

```python
# 创建新的告警，使用类似的 Metric Math
Metrics=[
    {'Id': 'm1', 'MetricStat': {'Metric': {'MetricName': 'VolumeReadBytes'}}},
    {'Id': 'm2', 'MetricStat': {'Metric': {'MetricName': 'VolumeWriteBytes'}}},
    {'Id': 'e1', 'Expression': '(m1+m2)/PERIOD(m1)/1024/1024'}  # MB/s
]
```

---

## 📝 最佳实践建议

### 组合使用

建议同时使用两个脚本：

1. **EC2 监控**: 监控实例健康状态
2. **GP3 监控**: 监控存储性能

### 告警分组

通过 SNS 主题分组：

```python
# 关键告警
SNS_TOPIC_ARN_CRITICAL = "arn:aws:sns:region:account:critical-alerts"

# 性能告警
SNS_TOPIC_ARN_PERFORMANCE = "arn:aws:sns:region:account:performance-alerts"
```

### 定期执行

使用 cron 或 EventBridge 定期运行：

```bash
# 每天凌晨 2 点更新告警
0 2 * * * /path/to/monitor_gp3_ebs_iops.py
```

---

## 🎓 学习要点

### 从 EC2 监控学到的

1. ✅ 基础告警创建流程
2. ✅ 资源筛选和过滤
3. ✅ 告警删除和更新
4. ✅ 日志记录最佳实践

### GP3 监控的新技术

1. ✅ Metric Math 表达式
2. ✅ 多指标组合告警
3. ✅ 复杂阈值计算
4. ✅ 更详细的资源信息获取

---

## 📚 参考资源

- [CloudWatch Metric Math](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/using-metric-math.html)
- [EBS CloudWatch Metrics](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using_cloudwatch_ebs.html)
- [EC2 CloudWatch Metrics](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/viewing_metrics_with_cloudwatch.html)

---

**最后更新**: 2025-12-02
