#!/usr/bin/env python3
"""
获取当前AWS账号的所有EC2实例信息
"""

import boto3
from datetime import datetime
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    """获取指定区域的EC2实例（支持分页）"""
    try:
        ec2 = boto3.client('ec2', region_name=region_name)
        paginator = ec2.get_paginator('describe_instances')
        
        instances = []
        for page in paginator.paginate():
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    # 获取实例名称
                    name = next((tag['Value'] for tag in instance.get('Tags', []) 
                               if tag['Key'] == 'Name'), 'N/A')
                    
                    # 修复LaunchTime处理
                    launch_time = 'N/A'
                    if instance.get('LaunchTime'):
                        launch_time = instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S')
                    
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
                        'launch_time': launch_time,
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

def collect_instances_parallel(regions, max_workers=10):
    """并行收集所有区域的实例信息"""
    all_instances = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_region = {
            executor.submit(get_ec2_instances_in_region, region): region 
            for region in regions
        }
        
        for future in as_completed(future_to_region):
            region = future_to_region[future]
            try:
                instances = future.result()
                if instances:
                    print(f"区域 {region}: 找到 {len(instances)} 个实例")
                all_instances.extend(instances)
            except Exception as e:
                print(f"区域 {region} 处理失败: {e}")
    
    return all_instances

def print_summary(all_instances):
    """打印汇总信息"""
    if not all_instances:
        print("未找到任何EC2实例")
        return
    
    # 使用Counter进行统计
    state_count = Counter(instance['state'] for instance in all_instances)
    region_count = Counter(instance['region'] for instance in all_instances)
    type_count = Counter(instance['instance_type'] for instance in all_instances)
    
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
    
    # 使用defaultdict按区域分组
    regions = defaultdict(list)
    for instance in all_instances:
        regions[instance['region']].append(instance)
    
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
    
    # 并行收集所有实例信息
    all_instances = collect_instances_parallel(regions)
    
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
