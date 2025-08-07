#!/usr/bin/env python3
"""
简化版：导出指定区域中来源地址为 0.0.0.0/0 的安全组规则
"""

import boto3
import csv
from datetime import datetime

# 配置区域（可以修改为你需要的区域）
REGIONS = ['us-east-1', 'ap-southeast-1', 'ap-northeast-1']  # 修改为你需要的区域

def export_open_security_groups():
    """导出开放的安全组规则"""
    all_rules = []
    
    for region in REGIONS:
        print(f"正在扫描区域: {region}")
        
        try:
            ec2 = boto3.client('ec2', region_name=region)
            
            # 获取所有安全组
            response = ec2.describe_security_groups()
            
            for sg in response['SecurityGroups']:
                # 检查入站规则
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            all_rules.append({
                                'Region': region,
                                'SecurityGroupId': sg['GroupId'],
                                'SecurityGroupName': sg['GroupName'],
                                'VpcId': sg.get('VpcId', 'EC2-Classic'),
                                'RuleType': 'Inbound',
                                'Protocol': rule.get('IpProtocol', ''),
                                'FromPort': rule.get('FromPort', ''),
                                'ToPort': rule.get('ToPort', ''),
                                'Description': ip_range.get('Description', '')
                            })
                
                # 检查出站规则
                for rule in sg.get('IpPermissionsEgress', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            all_rules.append({
                                'Region': region,
                                'SecurityGroupId': sg['GroupId'],
                                'SecurityGroupName': sg['GroupName'],
                                'VpcId': sg.get('VpcId', 'EC2-Classic'),
                                'RuleType': 'Outbound',
                                'Protocol': rule.get('IpProtocol', ''),
                                'FromPort': rule.get('FromPort', ''),
                                'ToPort': rule.get('ToPort', ''),
                                'Description': ip_range.get('Description', '')
                            })
            
            print(f"区域 {region}: 发现 {len([r for r in all_rules if r['Region'] == region])} 条开放规则")
            
        except Exception as e:
            print(f"区域 {region} 扫描失败: {e}")
    
    # 导出到 CSV
    if all_rules:
        try:
            from file_utils import file_manager
            filename = file_manager.get_timestamped_filename('open_security_groups_simple')
        except ImportError:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'open_security_groups_{timestamp}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Region', 'SecurityGroupId', 'SecurityGroupName', 'VpcId', 
                         'RuleType', 'Protocol', 'FromPort', 'ToPort', 'Description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rules)
        
        print(f"\n✅ 成功导出 {len(all_rules)} 条规则到: {filename}")
    else:
        print("没有发现任何开放的安全组规则")

if __name__ == '__main__':
    export_open_security_groups()