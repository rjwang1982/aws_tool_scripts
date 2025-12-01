#!/bin/bash

# EBS 卷自动标签脚本
# 作者: RJ.Wang
# 日期: 2025-11-28
# 功能: 将 EC2 实例的 Name 标签复制到其挂载的 EBS 卷

# 默认值
REGION=""
PROFILE=""
DRY_RUN=false

# 参数解析
while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "未知参数: $1"
      echo "用法: $0 --profile <profile> --region <region> [--dry-run]"
      exit 1
      ;;
  esac
done

# 验证必需参数
if [ -z "$PROFILE" ] || [ -z "$REGION" ]; then
  echo "错误: 缺少必需参数"
  echo "用法: $0 --profile <profile> --region <region> [--dry-run]"
  echo ""
  echo "参数说明:"
  echo "  --profile  AWS CLI profile 名称 (必需)"
  echo "  --region   AWS 区域 (必需)"
  echo "  --dry-run  预览模式，不实际执行 (可选)"
  exit 1
fi

echo "========================================"
echo "EBS Volume Tagging Script"
echo "========================================"
echo "Profile: $PROFILE"
echo "Region: $REGION"
if [ "$DRY_RUN" = true ]; then
  echo "Mode: DRY RUN (Preview Only)"
else
  echo "Mode: LIVE (Making Changes)"
fi
echo "========================================"
echo ""

# 获取所有 EC2 实例及其 Name 标签
instances=$(aws ec2 describe-instances \
  --region "$REGION" \
  --profile "$PROFILE" \
  --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
  --output text 2>&1)

if [ $? -ne 0 ]; then
  echo "错误: 无法获取 EC2 实例信息"
  echo "$instances"
  exit 1
fi

if [ -z "$instances" ]; then
  echo "未找到任何 EC2 实例"
  exit 1
fi

# 统计
total_instances=0
total_volumes=0

# 遍历每个实例
while IFS=$'\t' read -r instance_id instance_name; do
  
  # 跳过空行
  if [ -z "$instance_id" ]; then
    continue
  fi
  
  # 跳过没有 Name 标签的实例
  if [ -z "$instance_name" ] || [ "$instance_name" = "None" ]; then
    continue
  fi
  
  total_instances=$((total_instances + 1))
  echo "Processing instance: $instance_id ($instance_name)"
  
  # 获取该实例的所有 EBS 卷
  volumes=$(aws ec2 describe-volumes \
    --region "$REGION" \
    --profile "$PROFILE" \
    --filters "Name=attachment.instance-id,Values=$instance_id" \
    --query 'Volumes[].VolumeId' \
    --output text 2>&1)
  
  if [ $? -ne 0 ]; then
    echo "  错误: 无法获取卷信息"
    continue
  fi
  
  if [ -z "$volumes" ]; then
    continue
  fi
  
  # 遍历每个卷
  for volume_id in $volumes; do
    total_volumes=$((total_volumes + 1))
    
    if [ "$DRY_RUN" = true ]; then
      echo "  [DRY RUN] Would tag volume $volume_id with Name=$instance_name"
    else
      if aws ec2 create-tags \
        --region "$REGION" \
        --profile "$PROFILE" \
        --resources "$volume_id" \
        --tags "Key=Name,Value=$instance_name" 2>/dev/null; then
        echo "  ✓ Tagged volume $volume_id with Name=$instance_name"
      else
        echo "  ✗ Failed to tag volume $volume_id"
      fi
    fi
  done
  
  echo ""
  
done <<< "$instances"

# 输出统计
echo "========================================"
echo "Summary"
echo "========================================"
echo "Total instances processed: $total_instances"
echo "Total volumes tagged: $total_volumes"
echo "========================================"
