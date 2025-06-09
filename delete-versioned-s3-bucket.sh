#!/bin/bash

set -e  # 遇到错误立即退出

# 禁用 AWS CLI 分页
export AWS_PAGER=""

# 检查参数
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "用法: $0 <bucket-name> [--force]"
  echo "  --force: 跳过确认步骤，直接删除"
  exit 1
fi

BUCKET=$1
FORCE=false

# 检查是否有--force参数
if [ $# -eq 2 ] && [ "$2" == "--force" ]; then
  FORCE=true
fi

# 检查桶是否存在
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "错误: 桶 '$BUCKET' 不存在或您没有访问权限"
  exit 1
fi

# 确认删除（除非使用--force）
if [ "$FORCE" = false ]; then
  read -p "警告: 即将删除桶 '$BUCKET' 及其所有内容。确认删除? (y/n): " confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "操作已取消"
    exit 0
  fi
fi

echo "正在删除桶 $BUCKET 中的所有版本对象..."

# 删除所有未完成的分段上传
echo "正在删除未完成的分段上传..."
aws s3api list-multipart-uploads --bucket "$BUCKET" --output json --query 'Uploads[].{Key:Key,UploadId:UploadId}' 2>/dev/null |
  jq -c '.[]' 2>/dev/null | while read -r upload; do
    if [ -n "$upload" ]; then
      key=$(echo "$upload" | jq -r '.Key')
      upload_id=$(echo "$upload" | jq -r '.UploadId')
      echo "中止分段上传: $key (UploadId=$upload_id)"
      aws s3api abort-multipart-upload --bucket "$BUCKET" --key "$key" --upload-id "$upload_id"
    fi
  done

# 删除所有版本
aws s3api list-object-versions --bucket "$BUCKET" --output json \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' 2>/dev/null |
  jq -c '.Objects[]' 2>/dev/null | while read -r obj; do
    if [ -n "$obj" ]; then
      key=$(echo "$obj" | jq -r '.Key')
      versionId=$(echo "$obj" | jq -r '.VersionId')
      echo "删除对象版本: $key (versionId=$versionId)"
      aws s3api delete-object --bucket "$BUCKET" --key "$key" --version-id "$versionId"
    fi
  done

# 删除所有 delete markers
echo "正在删除 delete markers..."
aws s3api list-object-versions --bucket "$BUCKET" --output json \
  --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' 2>/dev/null |
  jq -c '.Objects[]' 2>/dev/null | while read -r obj; do
    if [ -n "$obj" ]; then
      key=$(echo "$obj" | jq -r '.Key')
      versionId=$(echo "$obj" | jq -r '.VersionId')
      echo "删除 delete marker: $key (versionId=$versionId)"
      aws s3api delete-object --bucket "$BUCKET" --key "$key" --version-id "$versionId"
    fi
  done

# 删除桶
echo "尝试删除空桶 $BUCKET ..."
if aws s3api delete-bucket --bucket "$BUCKET"; then
  echo "✅ 删除完成。"
else
  echo "❌ 删除桶失败，请检查是否还有对象或权限问题。"
  exit 1
fi