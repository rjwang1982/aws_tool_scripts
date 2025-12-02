# AWS 资源标签合规性管理工具

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com

自动化管理 AWS 资源标签合规性，支持中国区和 Global 区。

## 功能

- 自动检测缺少必需标签的资源
- 批量为资源添加标签
- 支持 30+ 种 AWS 计费资源类型
- 自动识别中国区/Global 区

## 必需标签

| 标签键 | 说明 | 示例值 |
|--------|------|--------|
| `siteName` | 站点/环境名称 | production, staging |
| `businessCostType` | 成本类型 | compute, storage |
| `platform` | 平台标识 | web, api, data |

## 快速开始

### 1. 初始化 AWS Config（首次使用）

```bash
# 中国区
./setup-config.sh c5611 cn-northwest-1 config-bucket-cn

# Global 区
./setup-config.sh g0603 ap-southeast-1 config-bucket-global
```

### 2. 部署标签规则

```bash
./manage-rule.sh deploy c5611 cn-northwest-1
```

### 3. 批量打标签

```bash
# 使用默认配置
python3 auto-tag-batch.py c5611 cn-northwest-1

# 使用配置文件
python3 auto-tag-batch.py c5611 cn-northwest-1 --config

# 命令行指定
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute web
```

### 4. 查看合规状态

```bash
./manage-rule.sh status c5611 cn-northwest-1
```

## 配置说明

### 标签配置

**方式 1**: 修改 `auto-tag-batch.py` 的 `DEFAULT_TAGS`

```python
DEFAULT_TAGS = {
    'siteName': 'production',
    'businessCostType': 'infrastructure',
    'platform': 'general'
}
```

**方式 2**: 使用配置文件

```bash
cp tag-config.json.example tag-config.json
vim tag-config.json
python3 auto-tag-batch.py c5611 cn-northwest-1 --config
```

## 支持的资源类型

- 计算: EC2、ECS/EKS、Lambda
- 存储: S3、EBS、EFS/FSx
- 数据库: RDS、DynamoDB、ElastiCache、Redshift
- 网络: NAT 网关、负载均衡器、CloudFront
- 其他: 共 30+ 种计费资源类型

## 常用命令

```bash
# 启动 Config 记录器
aws --profile c5611 configservice start-configuration-recorder \
  --configuration-recorder-name default

# 触发评估
aws --profile c5611 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule

# 查看状态
./manage-rule.sh status c5611 cn-northwest-1
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `setup-config.sh` | 初始化 AWS Config |
| `manage-rule.sh` | 管理 Config 规则 |
| `auto-tag-batch.py` | 批量打标签工具 |
| `config-rule.json` | 规则配置（计费资源） |
| `tag-config.json.example` | 标签配置示例 |
