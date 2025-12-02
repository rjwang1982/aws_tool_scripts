#!/bin/bash

# AWS Config 初始化脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-21
# 用途: 首次启用 AWS Config 服务

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "使用方法: $0 <profile> <region> <s3-bucket-name>"
    echo ""
    echo "参数说明:"
    echo "  profile         - AWS CLI profile 名称"
    echo "  region          - AWS 区域"
    echo "  s3-bucket-name  - 用于存储 Config 数据的 S3 存储桶名称"
    echo ""
    echo "示例:"
    echo "  $0 c5611 cn-northwest-1 my-config-bucket"
    exit 1
}

if [ $# -ne 3 ]; then
    usage
fi

PROFILE=$1
REGION=$2
S3_BUCKET=$3
RECORDER_NAME="default"
DELIVERY_CHANNEL_NAME="default"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AWS Config 初始化${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 验证认证
echo -e "${YELLOW}[1/6] 验证 AWS 认证...${NC}"
ACCOUNT_ID=$(aws --profile $PROFILE sts get-caller-identity --region $REGION --query 'Account' --output text)
echo -e "${GREEN}✓ 账号ID: $ACCOUNT_ID${NC}"
echo ""

# 创建 S3 存储桶
echo -e "${YELLOW}[2/6] 创建 S3 存储桶...${NC}"
aws --profile $PROFILE s3api create-bucket \
    --bucket $S3_BUCKET \
    --region $REGION \
    --create-bucket-configuration LocationConstraint=$REGION 2>&1 || {
    echo -e "${YELLOW}存储桶可能已存在${NC}"
}
echo -e "${GREEN}✓ S3 存储桶就绪${NC}"
echo ""

# 创建 IAM 角色
echo -e "${YELLOW}[3/6] 创建 IAM 角色...${NC}"
ROLE_NAME="AWSConfigRole"

# 判断是否为中国区
if [[ $REGION == cn-* ]]; then
    ARN_PARTITION="aws-cn"
    CONFIG_SERVICE="config.amazonaws.com.cn"
else
    ARN_PARTITION="aws"
    CONFIG_SERVICE="config.amazonaws.com"
fi

cat > /tmp/config-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "$CONFIG_SERVICE"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws --profile $PROFILE iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file:///tmp/config-trust-policy.json 2>&1 || {
    echo -e "${YELLOW}角色可能已存在${NC}"
}

aws --profile $PROFILE iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:${ARN_PARTITION}:iam::aws:policy/service-role/ConfigRole 2>&1 || true

ROLE_ARN="arn:${ARN_PARTITION}:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo -e "${GREEN}✓ IAM 角色就绪: $ROLE_ARN${NC}"
echo ""

# 创建 Configuration Recorder
echo -e "${YELLOW}[4/6] 创建 Configuration Recorder...${NC}"
cat > /tmp/config-recorder.json << EOF
{
  "name": "$RECORDER_NAME",
  "roleARN": "$ROLE_ARN",
  "recordingGroup": {
    "allSupported": true,
    "includeGlobalResourceTypes": true
  }
}
EOF

aws --profile $PROFILE configservice put-configuration-recorder \
    --configuration-recorder file:///tmp/config-recorder.json \
    --region $REGION
echo -e "${GREEN}✓ Configuration Recorder 已创建${NC}"
echo ""

# 创建 Delivery Channel
echo -e "${YELLOW}[5/6] 创建 Delivery Channel...${NC}"
cat > /tmp/delivery-channel.json << EOF
{
  "name": "$DELIVERY_CHANNEL_NAME",
  "s3BucketName": "$S3_BUCKET",
  "configSnapshotDeliveryProperties": {
    "deliveryFrequency": "TwentyFour_Hours"
  }
}
EOF

aws --profile $PROFILE configservice put-delivery-channel \
    --delivery-channel file:///tmp/delivery-channel.json \
    --region $REGION
echo -e "${GREEN}✓ Delivery Channel 已创建${NC}"
echo ""

# 启动 Configuration Recorder
echo -e "${YELLOW}[6/6] 启动 Configuration Recorder...${NC}"
aws --profile $PROFILE configservice start-configuration-recorder \
    --configuration-recorder-name $RECORDER_NAME \
    --region $REGION
echo -e "${GREEN}✓ Configuration Recorder 已启动${NC}"
echo ""

# 清理临时文件
rm -f /tmp/config-trust-policy.json /tmp/config-recorder.json /tmp/delivery-channel.json

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AWS Config 初始化完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "后续操作:"
echo "1. 运行部署脚本: ./deploy.sh $PROFILE $REGION"
echo "2. 等待 Config 开始记录资源（可能需要几分钟）"
echo ""
