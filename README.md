# AWS 工具脚本集合

这是一个实用的 AWS 管理工具脚本集合，包含了 EC2 管理、安全审计、监控告警、网络工具等多个方面的自动化脚本。

## 作者信息

- **作者**: RJ.Wang
- **邮箱**: wangrenjun@gmail.com
- **项目**: AWS 运维自动化工具集

## 📁 项目结构

```
aws_tool_scripts/
├── 📊 EC2 管理工具
│   ├── autoStartStopEC2.py                    # EC2 自动启停脚本
│   ├── get_myEC2_info.py                      # 获取 EC2 实例详细信息
│   ├── get_ec2_type_num.py                    # 统计 EC2 实例类型数量
│   └── getEC2CPUUtilizationLessthan30percent.py # 查找低 CPU 使用率实例
│
├── 🔒 安全审计工具
│   ├── export_open_security_groups.py         # 导出开放安全组规则
│   ├── export_open_sg_simple.py              # 简化版安全组导出
│   ├── export_open_sg.sh                     # 安全组导出脚本
│   ├── run_security_audit.py                 # 安全审计工具
│   └── batch_del_ec2_terminalProtect.py      # 批量删除 EC2 终止保护
│
├── 📈 监控告警工具
│   ├── batchCreateEC2Alarms.py               # 批量创建 EC2 告警
│   ├── create_ec2_status_alarm_delete_old_for_running_v2.py # EC2 状态告警管理
│   ├── eu-prod-scan-alarm.py                 # 生产环境扫描告警
│   ├── Cloudtrail_DeleteEvents_to_dingding_v1.py # CloudTrail 删除事件钉钉告警
│   └── cloudwatch-sns-lambda/                # CloudWatch SNS Lambda 集成
│
├── 🌐 网络工具
│   ├── cidr_subnet_delimitation_tool.py      # CIDR 子网划分工具
│   └── cidr_subnet_webtool/                  # Web 版 CIDR 工具
│
├── ☁️ EKS 管理工具
│   └── get_my_eks_info.py                    # 获取 EKS 集群信息
│
├── 📦 S3 工具
│   ├── s3_presigned_url.py                   # S3 预签名 URL 生成
│   ├── s3_presigned_url_v1.py               # S3 预签名 URL 生成 v1
│   └── delete-versioned-s3-bucket.sh        # 删除版本化 S3 存储桶
│
├── 📋 配额管理工具
│   ├── list_service_quotas.py                # 查询服务配额
│   └── list_service_quotas_v1.py            # 查询服务配额 v1
│
├── 🛠️ 通用工具
│   ├── config.py                             # 配置文件
│   ├── credentials.py                        # 凭证管理
│   ├── file_utils.py                         # 文件工具
│   ├── cloudshell_init.sh                    # CloudShell 初始化脚本
│   └── wa-tool-service-screener.sh          # Well-Architected 工具
│
└── 📊 报告工具
    └── GenerateGCRWAReport-main/             # 生成 GCR WA 报告
```

## 🚀 主要功能

### 1. EC2 管理工具

#### autoStartStopEC2.py
- **功能**: 基于标签自动启停 EC2 实例
- **用途**: Lambda 函数，根据标签 `autoStartStop=T` 管理实例
- **配置**: 通过环境变量设置区域、标签键值

```bash
# 环境变量配置
AWS_REGION=ap-southeast-1
TAG_KEY=autoStartStop
TAG_VALUE=T
```

#### get_myEC2_info.py
- **功能**: 获取 EC2 实例的详细信息
- **特性**: 支持 IMDSv2、导出 YAML 格式
- **用途**: 实例信息收集和文档化

#### getEC2CPUUtilizationLessthan30percent.py
- **功能**: 查找 CPU 使用率低于 30% 的 EC2 实例
- **用途**: 成本优化，识别未充分利用的资源

### 2. 安全审计工具

#### export_open_security_groups.py
- **功能**: 导出所有来源为 0.0.0.0/0 的安全组规则
- **输出**: CSV 格式报告
- **覆盖**: 全区域扫描

#### run_security_audit.py
- **功能**: 综合安全审计工具
- **检查项**: 安全组、IAM、S3 等安全配置

### 3. 监控告警工具

#### batchCreateEC2Alarms.py
- **功能**: 批量为 EC2 实例创建 CPU 使用率告警
- **特性**: 支持标签过滤、SNS 通知
- **配置**: 可自定义告警阈值和 SNS 主题

#### Cloudtrail_DeleteEvents_to_dingding_v1.py
- **功能**: 监控 CloudTrail 删除事件并发送钉钉告警
- **特性**: 支持加签验证、图片消息
- **用途**: 高危操作实时监控

### 4. 网络工具

#### cidr_subnet_delimitation_tool.py
- **功能**: CIDR 子网划分计算器
- **特性**: 命令行工具，支持子网详细信息输出
- **用法**: 
```bash
python cidr_subnet_delimitation_tool.py 192.168.0.0/24 4
```

#### cidr_subnet_webtool/
- **功能**: Web 版 CIDR 子网划分工具
- **技术**: Flask Web 应用
- **特性**: 图形化界面，实时计算

### 5. EKS 管理工具

#### get_my_eks_info.py
- **功能**: 获取 EKS 集群详细信息
- **特性**: 集群状态、节点组、网络配置
- **输出**: 结构化集群信息

### 6. S3 工具

#### s3_presigned_url.py
- **功能**: 生成 S3 预签名 URL
- **特性**: 支持上传/下载、自定义过期时间
- **安全**: 显示当前 IAM 身份信息

#### delete-versioned-s3-bucket.sh
- **功能**: 删除启用版本控制的 S3 存储桶
- **特性**: 安全删除所有版本和删除标记

### 7. 配额管理工具

#### list_service_quotas.py
- **功能**: 查询 AWS 服务配额
- **支持**: 多服务、多区域查询
- **输出**: 配额名称、代码、当前值

## 🛠️ 安装和使用

### 前置要求

```bash
# Python 依赖
pip install boto3 requests pyyaml flask

# AWS CLI 配置
aws configure
```

### 基本使用

1. **克隆项目**
```bash
git clone https://github.com/rjwang1982/aws_tool_scripts.git
cd aws_tool_scripts
```

2. **配置 AWS 凭证**
```bash
aws configure
# 或设置环境变量
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=ap-southeast-1
```

3. **运行脚本**
```bash
# 获取 EC2 信息
python get_myEC2_info.py

# 导出安全组
python export_open_security_groups.py

# 子网划分
python cidr_subnet_delimitation_tool.py 10.0.0.0/16 8
```

## 📋 配置说明

### config.py
全局配置文件，包含：
- 默认输出目录
- 默认 AWS 区域列表
- 输出路径管理函数

### credentials.py
凭证管理工具，支持：
- 多 Profile 管理
- 临时凭证处理
- 权限验证

## 🔧 Lambda 部署

### EC2 自动启停
```bash
# 打包部署
zip -r autoStartStopEC2.zip autoStartStopEC2.py

# 环境变量
AWS_REGION=ap-southeast-1
TAG_KEY=autoStartStop
TAG_VALUE=T
```

### CloudTrail 告警
```bash
# 环境变量配置
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your_secret
DEBUG_MODE=false
NOTIFY_DELETE_EVENTS_ONLY=true
```

## 📊 输出格式

### CSV 报告
- 安全组规则导出
- EC2 实例统计
- 配额使用情况

### JSON 格式
- EKS 集群信息
- EC2 详细信息
- 告警配置

### YAML 格式
- EC2 实例配置
- 网络拓扑信息

## 🔒 安全注意事项

1. **凭证管理**
   - 使用 IAM 角色而非长期凭证
   - 定期轮换访问密钥
   - 遵循最小权限原则

2. **网络安全**
   - 定期审计 0.0.0.0/0 开放的安全组
   - 监控高危删除操作
   - 启用 CloudTrail 日志

3. **成本控制**
   - 监控低使用率实例
   - 定期清理未使用资源
   - 设置预算告警

## 🚨 告警配置

### CloudWatch 告警
- CPU 使用率告警
- 磁盘使用率告警
- 实例状态检查告警

### 钉钉集成
- 实时删除操作通知
- 告警状态推送
- 支持@特定人员

## 📈 监控指标

### EC2 监控
- CPU 使用率
- 内存使用率
- 磁盘使用率
- 网络流量

### 安全监控
- 开放安全组数量
- 高危操作频率
- 权限变更记录

## 🔄 自动化流程

### 定时任务
- EC2 自动启停（基于标签）
- 安全组定期审计
- 资源使用率报告

### 事件驱动
- CloudTrail 事件监控
- 资源创建/删除通知
- 配额接近限制告警

## 🛡️ 最佳实践

1. **标签管理**
   - 统一标签策略
   - 自动化标签应用
   - 基于标签的资源管理

2. **监控策略**
   - 分层监控体系
   - 渐进式告警机制
   - 自动化响应流程

3. **成本优化**
   - 定期资源审计
   - 自动化清理策略
   - 预算控制机制

## 📚 扩展功能

### 计划中的功能
- RDS 监控工具
- Lambda 函数管理
- VPC 网络分析
- 成本分析报告

### 贡献指南
欢迎提交 Issue 和 Pull Request 来改进这个工具集。

## 📄 许可证

本项目仅供学习和内部使用，请遵守 AWS 服务条款。

## 🆘 故障排除

### 常见问题

1. **权限不足**
   - 检查 IAM 策略配置
   - 确认必要的服务权限

2. **区域配置**
   - 验证 AWS_DEFAULT_REGION 设置
   - 确认服务在目标区域可用

3. **依赖问题**
   - 安装所需的 Python 包
   - 检查 boto3 版本兼容性

### 日志调试
```bash
# 启用详细日志
export AWS_CLI_FILE_ENCODING=UTF-8
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 运行脚本并查看详细输出
python -v your_script.py
```

---

**⚠️ 重要提醒**: 
- 在生产环境使用前请充分测试
- 定期备份重要配置和数据
- 遵循公司的安全策略和合规要求
