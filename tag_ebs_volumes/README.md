# EBS 卷自动标签脚本

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-28  
**更新时间**: 2025-12-01

---

## 📋 功能概述

这是一个自动化脚本，用于将 EC2 实例的 `Name` 标签批量复制到其挂载的所有 EBS 卷上，帮助实现资源标签的统一管理。

### 核心功能

- ✅ 自动遍历指定区域的所有 EC2 实例
- ✅ 读取实例的 Name 标签
- ✅ 将 Name 标签复制到实例挂载的所有 EBS 卷
- ✅ 支持预览模式（dry-run）
- ✅ 提供详细的执行日志和统计报告

---

## 🚀 快速开始

### 前置要求

1. 已安装 AWS CLI
2. 已配置 AWS credentials 和 profile
3. 具有以下 IAM 权限：
   - `ec2:DescribeInstances`
   - `ec2:DescribeVolumes`
   - `ec2:CreateTags`

### 基本用法

```bash
# 预览模式（推荐先执行）
./tag-ebs-volumes.sh --profile <profile> --region <region> --dry-run

# 实际执行（跳过已有 Name 标签的卷）
./tag-ebs-volumes.sh --profile <profile> --region <region>

# 覆盖已有 Name 标签
./tag-ebs-volumes.sh --profile <profile> --region <region> --overwrite
```

---

## 📖 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--profile` | ✅ | AWS CLI profile 名称 | `c5611` 或 `g0603` |
| `--region` | ✅ | AWS 区域代码 | `cn-northwest-1` 或 `us-east-1` |
| `--dry-run` | ❌ | 预览模式，不实际执行标签操作 | - |
| `--overwrite` | ❌ | 覆盖已有 Name 标签（默认跳过） | - |

---

## 💡 使用示例

### 示例 1：中国区预览模式

```bash
./tag-ebs-volumes.sh --profile c5611 --region cn-northwest-1 --dry-run
```

**输出示例**：
```
========================================
EBS Volume Tagging Script
========================================
Profile: c5611
Region: cn-northwest-1
Mode: DRY RUN (Preview Only)
========================================

Processing instance: i-0123456789abcdef0 (web-server-prod)
  [DRY RUN] Would tag volume vol-0abc123def456789 with Name=web-server-prod
  [DRY RUN] Would tag volume vol-0def456abc789012 with Name=web-server-prod

========================================
Summary
========================================
Total instances processed: 1
Total volumes tagged: 2
========================================
```

### 示例 2：中国区实际执行

```bash
./tag-ebs-volumes.sh --profile c5611 --region cn-northwest-1
```

### 示例 3：Global 区实际执行

```bash
./tag-ebs-volumes.sh --profile g0603 --region us-east-1
```

### 示例 4：覆盖已有标签

```bash
# 预览覆盖模式
./tag-ebs-volumes.sh --profile c5611 --region cn-northwest-1 --dry-run --overwrite

# 实际覆盖已有标签
./tag-ebs-volumes.sh --profile c5611 --region cn-northwest-1 --overwrite
```

### 示例 5：批量处理多个区域

```bash
# 创建批量执行脚本
for region in cn-northwest-1 cn-north-1; do
  echo "Processing region: $region"
  ./tag-ebs-volumes.sh --profile c5611 --region $region
done
```

---

## 🔄 工作流程

```
1. 参数验证
   ↓
2. 获取 EC2 实例列表
   ↓
3. 遍历每个实例
   ├─ 读取 Name 标签
   ├─ 查询挂载的 EBS 卷
   └─ 为每个卷添加 Name 标签
   ↓
4. 输出统计报告
```

---

## 📊 执行逻辑

### 实例过滤规则

脚本会自动跳过以下实例：
- ❌ 没有 Name 标签的实例
- ❌ Name 标签值为空或 "None" 的实例

### 标签操作

- **默认行为**：跳过已有 Name 标签的 EBS 卷
- **覆盖模式**：使用 `--overwrite` 参数可覆盖已有 Name 标签
- 只处理当前挂载到实例的 EBS 卷
- 不会影响 EBS 卷的其他标签

---

## ⚠️ 注意事项

### 安全建议

1. **首次使用务必先执行 dry-run 模式**
   ```bash
   ./tag-ebs-volumes.sh --profile c5611 --region cn-northwest-1 --dry-run
   ```

2. **确认 AWS profile 和 region 正确**
   ```bash
   # 验证当前 profile
   aws --profile c5611 sts get-caller-identity
   ```

3. **检查 IAM 权限**
   ```bash
   # 测试权限
   aws --profile c5611 --region cn-northwest-1 ec2 describe-instances --max-items 1
   ```

### 最佳实践

- ✅ 在生产环境执行前，先在测试环境验证
- ✅ 定期执行脚本，保持标签一致性
- ✅ 结合 CloudWatch Events 实现自动化
- ✅ 保存执行日志用于审计

### 常见问题

**Q: 脚本会覆盖现有的 Name 标签吗？**  
A: 默认不会，会跳过已有 Name 标签的卷。如需覆盖，请使用 `--overwrite` 参数。

**Q: 如果实例没有 Name 标签会怎样？**  
A: 脚本会跳过该实例，不会对其 EBS 卷进行任何操作。

**Q: 脚本会处理已分离的 EBS 卷吗？**  
A: 不会，只处理当前挂载到实例的 EBS 卷。

**Q: 执行失败会回滚吗？**  
A: 不会自动回滚，建议先使用 dry-run 模式预览。

**Q: 如何只标记没有 Name 标签的卷？**  
A: 默认行为就是只标记没有 Name 标签的卷，不需要额外参数。

**Q: 如何强制更新所有卷的标签？**  
A: 使用 `--overwrite` 参数即可覆盖已有的 Name 标签。

---

## 🎯 适用场景

### 场景 1：新环境初始化
为新创建的 EC2 实例和 EBS 卷批量添加标签。

### 场景 2：成本管理
通过统一标签实现成本分配和追踪。

### 场景 3：资源清理
在清理资源前，确保所有 EBS 卷都有正确的标签。

### 场景 4：合规审计
满足企业标签策略要求，确保资源标签完整性。

### 场景 5：定期维护
作为定期维护任务，保持标签一致性。

---

## 🔧 故障排查

### 错误：无法获取 EC2 实例信息

```bash
错误: 无法获取 EC2 实例信息
```

**解决方案**：
1. 检查 AWS profile 配置
   ```bash
   aws configure list --profile c5611
   ```

2. 验证 IAM 权限
   ```bash
   aws --profile c5611 --region cn-northwest-1 ec2 describe-instances --max-items 1
   ```

3. 确认区域代码正确
   ```bash
   # 中国区
   cn-northwest-1  # 宁夏
   cn-north-1      # 北京
   
   # Global 区
   us-east-1       # 弗吉尼亚北部
   us-west-2       # 俄勒冈
   ```

### 错误：无法获取卷信息

```bash
错误: 无法获取卷信息
```

**解决方案**：
检查是否有 `ec2:DescribeVolumes` 权限。

### 错误：Failed to tag volume

```bash
✗ Failed to tag volume vol-xxxxx
```

**解决方案**：
检查是否有 `ec2:CreateTags` 权限。

---

## 📈 高级用法

### 集成到 Lambda 函数

可以将脚本逻辑改写为 Lambda 函数，配合 CloudWatch Events 实现自动化：

```python
# 伪代码示例
def lambda_handler(event, context):
    # 1. 获取所有 EC2 实例
    # 2. 遍历实例并获取 Name 标签
    # 3. 为挂载的 EBS 卷添加标签
    pass
```

### 定时任务（Cron）

```bash
# 每天凌晨 2 点执行
0 2 * * * /path/to/tag-ebs-volumes.sh --profile c5611 --region cn-northwest-1 >> /var/log/ebs-tagging.log 2>&1
```

### 结合 AWS Organizations

```bash
# 遍历多个账号
for account in account1 account2 account3; do
  for region in cn-northwest-1 cn-north-1; do
    ./tag-ebs-volumes.sh --profile $account --region $region
  done
done
```

---

## 📝 IAM 权限策略示例

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🔗 相关资源

- [AWS CLI 配置指南](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [EC2 标签最佳实践](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Tags.html)
- [EBS 卷管理](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volumes.html)

---

## 📞 支持与反馈

如有问题或建议，请联系：
- **邮箱**: wangrenjun@gmail.com
- **作者**: RJ.Wang

---

## 📄 许可证

本脚本仅供内部使用，请勿外传。

---

**最后更新**: 2025-12-01
