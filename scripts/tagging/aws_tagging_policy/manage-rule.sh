#!/bin/bash

# AWS Config 规则管理脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-21

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

RULE_NAME="required-tags-rule"

# 使用说明
usage() {
    echo "使用方法: $0 <action> [profile] [region] [config-file]"
    echo ""
    echo "操作 (action):"
    echo "  deploy   - 部署 Config 规则"
    echo "  delete   - 删除 Config 规则"
    echo "  status   - 查看规则状态"
    echo ""
    echo "参数 (可选):"
    echo "  profile     - AWS CLI profile (默认: c5611)"
    echo "  region      - AWS 区域 (默认: cn-northwest-1)"
    echo "  config-file - 配置文件 (默认: config-rule.json)"
    echo ""
    echo "配置文件选项:"
    echo "  config-rule.json              - 原始配置（向后兼容）"
    echo "  config-rule-all-resources.json - 所有资源（100+ 种）"
    echo "  config-rule-billable.json     - 仅计费资源（40 种）"
    echo ""
    echo "示例:"
    echo "  $0 deploy                                    # 使用默认配置"
    echo "  $0 deploy c5611 cn-northwest-1             # 指定 profile 和 region"
    echo "  $0 deploy c5611 cn-northwest-1 config-rule-billable.json  # 仅检查计费资源"
    echo "  $0 delete                                    # 删除规则"
    echo "  $0 status                                    # 查看状态"
    exit 1
}

# 检查参数
if [ $# -lt 1 ]; then
    usage
fi

ACTION=$1
PROFILE=${2:-c5611}
REGION=${3:-cn-northwest-1}
CONFIG_FILE=${4:-config-rule.json}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AWS Config 规则管理${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "操作:      $ACTION"
echo "Profile:   $PROFILE"
echo "Region:    $REGION"
echo "配置文件:  $CONFIG_FILE"
echo "规则:      $RULE_NAME"
echo ""

# 验证配置文件是否存在
if [ "$ACTION" == "deploy" ] && [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗ 配置文件不存在: $CONFIG_FILE${NC}"
    echo ""
    echo "可用的配置文件:"
    echo "  - config-rule.json              (原始配置)"
    echo "  - config-rule-all-resources.json (所有资源)"
    echo "  - config-rule-billable.json     (仅计费资源)"
    exit 1
fi

# 验证 AWS 认证
echo -e "${YELLOW}验证 AWS 认证...${NC}"
ACCOUNT_INFO=$(aws --profile $PROFILE sts get-caller-identity --region $REGION --output json 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ AWS 认证失败${NC}"
    echo "$ACCOUNT_INFO"
    exit 1
fi

ACCOUNT_ID=$(echo $ACCOUNT_INFO | jq -r '.Account')
USER_ARN=$(echo $ACCOUNT_INFO | jq -r '.Arn')
echo -e "${GREEN}✓ 认证成功${NC}"
echo "  账号ID: $ACCOUNT_ID"
echo "  用户ARN: $USER_ARN"
echo ""

# 执行操作
case $ACTION in
    deploy)
        echo -e "${YELLOW}检查 AWS Config 状态...${NC}"
        CONFIG_STATUS=$(aws --profile $PROFILE configservice describe-configuration-recorder-status --region $REGION 2>&1)
        if [ $? -ne 0 ]; then
            echo -e "${RED}警告: AWS Config 可能未启用${NC}"
            echo "请先运行: ./setup-config.sh $PROFILE $REGION <bucket-name>"
            echo ""
            read -p "是否继续部署规则? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            echo -e "${GREEN}✓ AWS Config 已启用${NC}"
        fi
        echo ""

        echo -e "${YELLOW}部署 Config 规则...${NC}"
        aws --profile $PROFILE configservice put-config-rule \
            --config-rule file://$CONFIG_FILE \
            --region $REGION

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 规则部署成功${NC}"
            echo ""
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}部署完成！${NC}"
            echo -e "${GREEN}========================================${NC}"
            echo ""
            echo "后续操作:"
            echo "1. 查看状态: ./manage-rule.sh status $PROFILE $REGION"
            echo "2. 查看控制台: https://console.aws.amazon.com/config/"
        else
            echo -e "${RED}✗ 规则部署失败${NC}"
            exit 1
        fi
        ;;

    delete)
        echo -e "${YELLOW}检查规则是否存在...${NC}"
        RULE_EXISTS=$(aws --profile $PROFILE configservice describe-config-rules \
            --config-rule-names $RULE_NAME \
            --region $REGION 2>&1 || echo "NOT_FOUND")

        if [[ $RULE_EXISTS == *"NOT_FOUND"* ]] || [[ $RULE_EXISTS == *"does not exist"* ]]; then
            echo -e "${YELLOW}规则不存在，无需删除${NC}"
            exit 0
        fi
        echo -e "${GREEN}✓ 规则存在${NC}"
        echo ""

        echo -e "${RED}警告: 此操作将删除 Config 规则，无法恢复！${NC}"
        read -p "确认删除? (yes/no) " -r
        echo
        if [[ ! $REPLY == "yes" ]]; then
            echo "已取消删除操作"
            exit 0
        fi

        echo -e "${YELLOW}删除 Config 规则...${NC}"
        aws --profile $PROFILE configservice delete-config-rule \
            --config-rule-name $RULE_NAME \
            --region $REGION

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 规则删除成功${NC}"
            echo ""
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}删除完成！${NC}"
            echo -e "${GREEN}========================================${NC}"
        else
            echo -e "${RED}✗ 规则删除失败${NC}"
            exit 1
        fi
        ;;

    status)
        echo -e "${YELLOW}查询规则状态...${NC}"
        RULE_INFO=$(aws --profile $PROFILE configservice describe-config-rules \
            --config-rule-names $RULE_NAME \
            --region $REGION \
            --output json 2>&1 || echo "NOT_FOUND")

        if [[ $RULE_INFO == *"NOT_FOUND"* ]] || [[ $RULE_INFO == *"does not exist"* ]]; then
            echo -e "${RED}✗ 规则不存在${NC}"
            echo ""
            echo "部署规则: ./manage-rule.sh deploy $PROFILE $REGION"
            exit 1
        fi

        echo -e "${GREEN}✓ 规则存在${NC}"
        echo ""
        echo "规则信息:"
        echo "$RULE_INFO" | jq '.ConfigRules[0] | {ConfigRuleName, ConfigRuleState, Description}'
        echo ""

        echo -e "${YELLOW}查询合规性状态...${NC}"
        COMPLIANCE=$(aws --profile $PROFILE configservice describe-compliance-by-config-rule \
            --config-rule-names $RULE_NAME \
            --region $REGION \
            --output json 2>&1)

        if [ $? -eq 0 ]; then
            echo ""
            echo "合规性摘要:"
            echo "$COMPLIANCE" | jq '.ComplianceByConfigRules[0].Compliance'
            echo ""
            echo "查看详细信息:"
            echo "  控制台: https://console.aws.amazon.com/config/"
            echo "  命令行: ./check-compliance.sh $PROFILE $REGION"
        else
            echo -e "${YELLOW}⚠ 暂无合规性数据（可能正在首次评估）${NC}"
        fi
        ;;

    *)
        echo -e "${RED}错误: 未知操作 '$ACTION'${NC}"
        echo ""
        usage
        ;;
esac

echo ""
