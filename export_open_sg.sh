#!/bin/bash
# 使用 AWS CLI 导出开放的安全组规则

# 配置
REGIONS=("us-east-1" "ap-southeast-1" "ap-northeast-1")  # 修改为你需要的区域
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="open_security_groups_${TIMESTAMP}.csv"

# 创建 CSV 头部
echo "Region,SecurityGroupId,SecurityGroupName,VpcId,RuleType,Protocol,FromPort,ToPort,CidrIp,Description" > "$OUTPUT_FILE"

echo "开始扫描开放的安全组规则..."

for region in "${REGIONS[@]}"; do
    echo "正在扫描区域: $region"
    
    # 获取所有安全组
    aws ec2 describe-security-groups --region "$region" --output json | \
    jq -r --arg region "$region" '
    .SecurityGroups[] as $sg |
    (
        # 处理入站规则
        ($sg.IpPermissions[]? | 
         select(.IpRanges[]?.CidrIp == "0.0.0.0/0") |
         .IpRanges[] | select(.CidrIp == "0.0.0.0/0") |
         [$region, $sg.GroupId, $sg.GroupName, ($sg.VpcId // "EC2-Classic"), "Inbound", 
          ($sg.IpPermissions[] | select(.IpRanges[]?.CidrIp == "0.0.0.0/0") | .IpProtocol), 
          ($sg.IpPermissions[] | select(.IpRanges[]?.CidrIp == "0.0.0.0/0") | .FromPort // ""), 
          ($sg.IpPermissions[] | select(.IpRanges[]?.CidrIp == "0.0.0.0/0") | .ToPort // ""), 
          .CidrIp, (.Description // "")] | @csv),
        
        # 处理出站规则  
        ($sg.IpPermissionsEgress[]? | 
         select(.IpRanges[]?.CidrIp == "0.0.0.0/0") |
         .IpRanges[] | select(.CidrIp == "0.0.0.0/0") |
         [$region, $sg.GroupId, $sg.GroupName, ($sg.VpcId // "EC2-Classic"), "Outbound", 
          ($sg.IpPermissionsEgress[] | select(.IpRanges[]?.CidrIp == "0.0.0.0/0") | .IpProtocol), 
          ($sg.IpPermissionsEgress[] | select(.IpRanges[]?.CidrIp == "0.0.0.0/0") | .FromPort // ""), 
          ($sg.IpPermissionsEgress[] | select(.IpRanges[]?.CidrIp == "0.0.0.0/0") | .ToPort // ""), 
          .CidrIp, (.Description // "")] | @csv)
    )' >> "$OUTPUT_FILE" 2>/dev/null
    
    # 统计该区域的规则数量
    count=$(grep "^$region," "$OUTPUT_FILE" | wc -l)
    echo "区域 $region: 发现 $count 条开放规则"
done

# 统计总数
total_rules=$(($(wc -l < "$OUTPUT_FILE") - 1))  # 减去头部行

echo "=================================="
echo "扫描完成！"
echo "总共发现 $total_rules 条开放规则"
echo "结果已保存到: $OUTPUT_FILE"
echo "=================================="

# 显示前几行预览
if [ $total_rules -gt 0 ]; then
    echo "文件预览:"
    head -6 "$OUTPUT_FILE"
    if [ $total_rules -gt 5 ]; then
        echo "..."
    fi
fi