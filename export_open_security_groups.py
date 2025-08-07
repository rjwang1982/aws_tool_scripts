#!/usr/bin/env python3
"""
导出 AWS 账号中所有来源地址为 0.0.0.0/0 的安全组规则到 CSV 文件
Author: Assistant
Date: 2025-01-07
"""

import boto3
import csv
import json
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

def get_all_regions():
    """获取所有可用的 AWS 区域"""
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        response = ec2.describe_regions()
        return [region['RegionName'] for region in response['Regions']]
    except Exception as e:
        print(f"获取区域列表失败: {e}")
        return ['us-east-1']  # 默认返回一个区域

def analyze_security_groups_in_region(region_name):
    """分析指定区域的安全组规则"""
    print(f"正在分析区域: {region_name}")
    
    try:
        ec2 = boto3.client('ec2', region_name=region_name)
        
        # 获取所有安全组
        paginator = ec2.get_paginator('describe_security_groups')
        security_groups = []
        
        for page in paginator.paginate():
            security_groups.extend(page['SecurityGroups'])
        
        open_rules = []
        
        for sg in security_groups:
            sg_id = sg['GroupId']
            sg_name = sg['GroupName']
            sg_description = sg['Description']
            vpc_id = sg.get('VpcId', 'EC2-Classic')
            
            # 检查入站规则
            for rule in sg.get('IpPermissions', []):
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        open_rules.append({
                            'Region': region_name,
                            'SecurityGroupId': sg_id,
                            'SecurityGroupName': sg_name,
                            'Description': sg_description,
                            'VpcId': vpc_id,
                            'RuleType': 'Inbound',
                            'Protocol': rule.get('IpProtocol', ''),
                            'FromPort': rule.get('FromPort', ''),
                            'ToPort': rule.get('ToPort', ''),
                            'CidrIp': '0.0.0.0/0',
                            'RuleDescription': ip_range.get('Description', ''),
                            'Tags': json.dumps({tag['Key']: tag['Value'] for tag in sg.get('Tags', [])})
                        })
            
            # 检查出站规则
            for rule in sg.get('IpPermissionsEgress', []):
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        open_rules.append({
                            'Region': region_name,
                            'SecurityGroupId': sg_id,
                            'SecurityGroupName': sg_name,
                            'Description': sg_description,
                            'VpcId': vpc_id,
                            'RuleType': 'Outbound',
                            'Protocol': rule.get('IpProtocol', ''),
                            'FromPort': rule.get('FromPort', ''),
                            'ToPort': rule.get('ToPort', ''),
                            'CidrIp': '0.0.0.0/0',
                            'RuleDescription': ip_range.get('Description', ''),
                            'Tags': json.dumps({tag['Key']: tag['Value'] for tag in sg.get('Tags', [])})
                        })
        
        print(f"区域 {region_name} 发现 {len(open_rules)} 条开放规则")
        return open_rules
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnauthorizedOperation':
            print(f"区域 {region_name}: 没有权限访问")
        elif error_code == 'OptInRequired':
            print(f"区域 {region_name}: 需要先启用该区域")
        else:
            print(f"区域 {region_name} 出错: {e}")
        return []
    except Exception as e:
        print(f"区域 {region_name} 出现未知错误: {e}")
        return []

def format_port_range(from_port, to_port, protocol):
    """格式化端口范围显示"""
    if protocol == '-1':
        return 'All'
    elif from_port == to_port:
        return str(from_port) if from_port != '' else 'All'
    else:
        return f"{from_port}-{to_port}" if from_port != '' and to_port != '' else 'All'

def export_to_csv(all_open_rules, filename):
    """导出结果到 CSV 文件"""
    if not all_open_rules:
        print("没有发现任何开放的安全组规则")
        return
    
    # 处理端口显示
    for rule in all_open_rules:
        rule['PortRange'] = format_port_range(
            rule['FromPort'], 
            rule['ToPort'], 
            rule['Protocol']
        )
    
    # CSV 字段定义
    fieldnames = [
        'Region',
        'SecurityGroupId', 
        'SecurityGroupName',
        'Description',
        'VpcId',
        'RuleType',
        'Protocol',
        'PortRange',
        'FromPort',
        'ToPort',
        'CidrIp',
        'RuleDescription',
        'Tags'
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_open_rules)
        
        print(f"\n✅ 成功导出 {len(all_open_rules)} 条开放规则到文件: {filename}")
        
        # 统计信息
        regions = set(rule['Region'] for rule in all_open_rules)
        inbound_count = sum(1 for rule in all_open_rules if rule['RuleType'] == 'Inbound')
        outbound_count = sum(1 for rule in all_open_rules if rule['RuleType'] == 'Outbound')
        
        print(f"📊 统计信息:")
        print(f"   - 涉及区域: {len(regions)} 个")
        print(f"   - 入站规则: {inbound_count} 条")
        print(f"   - 出站规则: {outbound_count} 条")
        print(f"   - 涉及区域: {', '.join(sorted(regions))}")
        
    except Exception as e:
        print(f"❌ 导出 CSV 文件失败: {e}")

def main():
    """主函数"""
    print("🔍 开始扫描 AWS 账号中的开放安全组规则...")
    print("=" * 60)
    
    try:
        # 检查 AWS 凭证
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        print(f"当前 AWS 账号: {account_id}")
        print(f"当前用户/角色: {identity.get('Arn', 'Unknown')}")
        print("-" * 60)
        
    except NoCredentialsError:
        print("❌ 错误: 未找到 AWS 凭证")
        print("请确保已配置 AWS CLI 或设置了相关环境变量")
        return
    except Exception as e:
        print(f"❌ 验证 AWS 凭证时出错: {e}")
        return
    
    # 获取所有区域
    regions = get_all_regions()
    print(f"将扫描 {len(regions)} 个区域")
    print("-" * 60)
    
    # 收集所有开放规则
    all_open_rules = []
    
    for region in regions:
        try:
            rules = analyze_security_groups_in_region(region)
            all_open_rules.extend(rules)
        except KeyboardInterrupt:
            print("\n⚠️  用户中断操作")
            break
        except Exception as e:
            print(f"处理区域 {region} 时出错: {e}")
            continue
    
    print("-" * 60)
    
    # 生成文件名（使用配置的输出目录）
    try:
        from config import get_output_path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = get_output_path(f'open_security_groups_{timestamp}.csv')
    except ImportError:
        # 如果没有配置文件，使用当前目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'open_security_groups_{timestamp}.csv'
    
    # 导出到 CSV
    export_to_csv(all_open_rules, filename)
    
    # 安全提醒
    if all_open_rules:
        print("\n⚠️  安全提醒:")
        print("   - 开放 0.0.0.0/0 的规则存在安全风险")
        print("   - 建议仅在必要时使用，并定期审查")
        print("   - 考虑使用更具体的 IP 范围或安全组引用")

if __name__ == '__main__':
    main()