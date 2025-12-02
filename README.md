# AWS 运维自动化工具集

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com

AWS 管理工具脚本集合，包含 EC2 管理、安全审计、监控告警、网络工具等自动化脚本。

## 快速开始

```bash
# 克隆项目
git clone https://github.com/rjwang1982/aws_tool_scripts.git
cd aws_tool_scripts

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 配置 AWS 凭证
aws configure --profile c5611  # 中国区
aws configure --profile g0603  # Global 区
```

## 核心功能

### EC2 管理
- `auto_start_stop.py` - 基于标签自动启停实例
- `get_instance_info.py` - 获取实例详细信息
- `find_low_cpu_instances.py` - 查找低 CPU 使用率实例
- `batch_remove_termination_protection.py` - 批量删除终止保护

### 安全审计
- `export_open_security_groups.py` - 导出 0.0.0.0/0 开放的安全组
- `run_security_audit.py` - 综合安全审计

### 监控告警
- `batch_create_ec2_alarms.py` - 批量创建 EC2 告警
- `cloudtrail_to_dingtalk.py` - CloudTrail 事件钉钉通知
- `cloudwatch_sns_dingtalk/` - CloudWatch + SNS + 钉钉集成（Lambda）
- `gp3_iops_monitor/` - GP3 EBS IOPS 监控（Lambda）

### 网络工具
- `cidr_calculator.py` - CIDR 子网划分计算器

### 其他
- `s3/presigned_url.py` - S3 预签名 URL 生成
- `quotas/list_service_quotas.py` - 服务配额查询

## 使用示例

```bash
# EC2 实例信息
python scripts/ec2/get_instance_info.py

# 安全组审计
python scripts/security/export_open_security_groups.py

# 批量创建告警
python scripts/monitoring/batch_create_ec2_alarms.py

# 子网划分
python scripts/networking/cidr_calculator.py 10.0.0.0/16 8
```

## AWS Profile 配置

| 区域 | Profile | Region | ARN 前缀 |
|------|---------|--------|----------|
| 中国区 | c5611 | cn-northwest-1 | arn:aws-cn: |
| Global 区 | g0603 | ap-southeast-1 | arn:aws: |

---

**最后更新**: 2025-12-02
