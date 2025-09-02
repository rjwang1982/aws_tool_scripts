#!/usr/bin/env python3
"""
获取当前AWS账号的所有EC2实例信息
"""

import boto3
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

def get_current_account_info():
    """获取当前账号信息"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return {
            'account_id': identity['Account'],
            'user_arn': identity['Arn'],
            'user_id': identity['UserId']
        }
    except Exception as e:
        print(f"错误: 无法获取账号信息 - {e}")
        return None

def get_all_regions():
    """获取所有可用区域"""
    try:
        ec2 = boto3.client('ec2')
        regions = ec2.describe_regions()
        return [region['RegionName'] for region in regions['Regions']]
    except Exception as e:
        print(f"警告: 无法获取区域列表，使用默认区域 - {e}")
        return [boto3.Session().region_name or 'us-east-1']

def get_ec2_instances_in_region(region_name):
    """获取指定区域的EC2实例"""
    try:
        ec2 = boto3.client('ec2', region_name=region_name)
        response = ec2.describe_instances()
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # 获取实例名称
                name = 'N/A'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                
                instances.append({
                    'name': name,
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                    'public_ip': instance.get('PublicIpAddress', 'N/A'),
                    'vpc_id': instance.get('VpcId', 'N/A'),
                    'subnet_id': instance.get('SubnetId', 'N/A'),
                    'availability_zone': instance.get('Placement', {}).get('AvailabilityZone', 'N/A'),
                    'launch_time': instance.get('LaunchTime', '').strftime('%Y-%m-%d %H:%M:%S') if instance.get('LaunchTime') else 'N/A',
                    'region': region_name
                })
        
        return instances
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['UnauthorizedOperation', 'AccessDenied']:
            print(f"警告: 无权限访问区域 {region_name}")
        else:
            print(f"错误: 访问区域 {region_name} 失败 - {e}")
        return []

def print_summary(all_instances):
    """打印汇总信息"""
    if not all_instances:
        print("未找到任何EC2实例")
        return
    
    # 按状态统计
    state_count = {}
    region_count = {}
    type_count = {}
    
    for instance in all_instances:
        state = instance['state']
        region = instance['region']
        instance_type = instance['instance_type']
        
        state_count[state] = state_count.get(state, 0) + 1
        region_count[region] = region_count.get(region, 0) + 1
        type_count[instance_type] = type_count.get(instance_type, 0) + 1
    
    print(f"\n{'='*60}")
    print("EC2 实例汇总")
    print(f"{'='*60}")
    print(f"总实例数: {len(all_instances)}")
    
    print(f"\n按状态统计:")
    for state, count in sorted(state_count.items()):
        print(f"  {state}: {count}")
    
    print(f"\n按区域统计:")
    for region, count in sorted(region_count.items()):
        print(f"  {region}: {count}")
    
    print(f"\n按实例类型统计:")
    for itype, count in sorted(type_count.items()):
        print(f"  {itype}: {count}")

def print_detailed_info(all_instances):
    """打印详细信息"""
    if not all_instances:
        return
    
    print(f"\n{'='*60}")
    print("EC2 实例详细信息")
    print(f"{'='*60}")
    
    # 按区域分组显示
    regions = {}
    for instance in all_instances:
        region = instance['region']
        if region not in regions:
            regions[region] = []
        regions[region].append(instance)
    
    for region, instances in sorted(regions.items()):
        print(f"\n[区域: {region}]")
        print("-" * 50)
        
        for instance in instances:
            print(f"名称: {instance['name']}")
            print(f"实例ID: {instance['instance_id']}")
            print(f"类型: {instance['instance_type']}")
            print(f"状态: {instance['state']}")
            print(f"私有IP: {instance['private_ip']}")
            print(f"公网IP: {instance['public_ip']}")
            print(f"可用区: {instance['availability_zone']}")
            print(f"启动时间: {instance['launch_time']}")
            print(f"VPC: {instance['vpc_id']}")
            print(f"子网: {instance['subnet_id']}")
            print()



def main():
    """主函数"""
    print("正在获取AWS账号EC2信息...\n")
    
    # 获取账号信息
    account_info = get_current_account_info()
    if not account_info:
        return
    
    print(f"账号ID: {account_info['account_id']}")
    print(f"用户ARN: {account_info['user_arn']}")
    print()
    
    # 获取所有区域
    regions = get_all_regions()
    print(f"正在扫描 {len(regions)} 个区域...")
    
    # 收集所有实例信息
    all_instances = []
    for region in regions:
        print(f"扫描区域: {region}")
        instances = get_ec2_instances_in_region(region)
        all_instances.extend(instances)
    
    # 显示结果
    print_summary(all_instances)
    print_detailed_info(all_instances)
    
    print(f"\n扫描完成！")

if __name__ == '__main__':
    try:
        main()
    except NoCredentialsError:
        print("错误: 未找到AWS凭证，请配置AWS CLI或设置环境变量")
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"未知错误: {e}")
