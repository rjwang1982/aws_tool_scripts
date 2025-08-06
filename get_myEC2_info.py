#!/usr/bin/env python3

import os
import json
import subprocess
import requests
from datetime import datetime, timezone

# 配置开关
EXPORT_YAML = False  # 设置为True时导出YAML文件，False时只打印到屏幕

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import yaml
    HAS_YAML = True if EXPORT_YAML else False  # 只有需要导出YAML时才检查
except ImportError:
    HAS_YAML = False

def get_imdsv2_token():
    """获取IMDSv2令牌"""
    try:
        response = requests.put(
            'http://169.254.169.254/latest/api/token',
            headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'},
            timeout=2
        )
        if response.status_code == 200:
            return response.text
    except requests.exceptions.RequestException:
        return None

def get_instance_metadata(path='', use_imdsv2=True):
    """获取EC2实例元数据（支持IMDSv2）"""
    base_url = 'http://169.254.169.254/latest/meta-data/'
    headers = {}
    
    if use_imdsv2:
        token = get_imdsv2_token()
        if token:
            headers['X-aws-ec2-metadata-token'] = token
        else:
            print("警告: 无法获取IMDSv2令牌，尝试使用IMDSv1")
    
    try:
        response = requests.get(base_url + path, headers=headers, timeout=2)
        if response.status_code == 200:
            return response.text
        return None
    except requests.exceptions.RequestException as e:
        print(f"元数据请求失败: {str(e)}")
        return None

def get_system_info():
    """获取系统信息"""
    info = {}
    
    # 获取发行版信息
    try:
        with open('/etc/os-release') as f:
            for line in f:
                if line.startswith('PRETTY_NAME'):
                    info['os_version'] = line.split('=')[1].strip().strip('"')
                    break
    except FileNotFoundError:
        info['os_version'] = subprocess.getoutput('uname -a')
    
    # 获取内核版本
    info['kernel'] = subprocess.getoutput('uname -r')
    
    # 获取系统架构
    info['architecture'] = subprocess.getoutput('uname -m')
    
    # 获取CPU信息
    try:
        cpu_info = subprocess.getoutput('lscpu | grep "Model name"')
        info['cpu_info'] = cpu_info.split(':')[-1].strip() if cpu_info else '未知'
    except:
        info['cpu_info'] = '未知'
    
    info['cpu_cores'] = subprocess.getoutput('nproc')
    
    # 获取内存信息
    try:
        mem_output = subprocess.getoutput('free -h').split('\n')[1].split()
        info['memory_total'] = mem_output[1] if len(mem_output) > 1 else '未知'
        info['memory_used'] = mem_output[2] if len(mem_output) > 2 else '未知'
        info['memory_free'] = mem_output[3] if len(mem_output) > 3 else '未知'
    except:
        info['memory_total'] = '未知'
        info['memory_used'] = '未知'
        info['memory_free'] = '未知'
    
    # 获取磁盘信息
    info['disk_info'] = subprocess.getoutput('df -h /')
    
    return info

def get_aws_info():
    """获取AWS信息"""
    aws_info = {'metadata_available': False}
    
    # 测试元数据服务是否可用
    test_path = 'instance-id'
    instance_id = get_instance_metadata(test_path)
    
    if not instance_id:
        print("警告: 无法访问实例元数据服务，AWS信息将不可用")
        return aws_info
    
    aws_info.update({
        'metadata_available': True,
        'instance_id': instance_id,
        'instance_type': get_instance_metadata('instance-type'),
        'availability_zone': get_instance_metadata('placement/availability-zone'),
        'private_ip': get_instance_metadata('local-ipv4'),
        'public_ip': get_instance_metadata('public-ipv4'),
        'mac_address': get_instance_metadata('mac'),
        'security_groups': get_instance_metadata('security-groups')
    })
    
    # 设置区域（如果可用区存在）
    if aws_info['availability_zone']:
        aws_info['region'] = aws_info['availability_zone'][:-1]
    
    # 尝试使用boto3获取更多信息
    if HAS_BOTO3 and aws_info.get('instance_id'):
        try:
            region = aws_info.get('region', 'us-east-1')  # 默认区域
            ec2 = boto3.client('ec2', region_name=region)
            response = ec2.describe_instances(InstanceIds=[aws_info['instance_id']])
            
            instance_data = response['Reservations'][0]['Instances'][0]
            aws_info.update({
                'vpc_id': instance_data.get('VpcId'),
                'subnet_id': instance_data.get('SubnetId'),
                'iam_role': instance_data.get('IamInstanceProfile', {}).get('Arn'),
                'tags': {tag['Key']: tag['Value'] for tag in instance_data.get('Tags', [])}
            })
        except Exception as e:
            aws_info['boto3_error'] = str(e)
    
    return aws_info

def save_yaml_file(data):
    """保存YAML文件（仅在EXPORT_YAML=True时调用）"""
    if not HAS_YAML:
        print("错误: 未安装PyYAML库，无法导出YAML格式")
        print("请先安装: pip install pyyaml")
        return False
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    yaml_filename = f'ec2_info_{timestamp}.yaml'
    
    try:
        with open(yaml_filename, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"\n详细信息已保存到: {yaml_filename}")
        return True
    except Exception as e:
        print(f"保存YAML文件失败: {str(e)}")
        return False

def main():
    print("正在收集EC2实例信息...\n")
    
    data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'system_info': get_system_info(),
        'aws_info': get_aws_info()
    }
    
    # 打印信息
    print("="*50)
    print("EC2 实例详细信息")
    print("="*50)
    
    print("\n[系统信息]")
    print(f"操作系统: {data['system_info']['os_version']}")
    print(f"内核版本: {data['system_info']['kernel']}")
    print(f"系统架构: {data['system_info']['architecture']}")
    print(f"CPU型号: {data['system_info']['cpu_info']}")
    print(f"CPU核心数: {data['system_info']['cpu_cores']}")
    print(f"内存总量: {data['system_info']['memory_total']}")
    print(f"已用内存: {data['system_info']['memory_used']}")
    print(f"可用内存: {data['system_info']['memory_free']}")
    print("\n磁盘信息:")
    print(data['system_info']['disk_info'])
    
    print("\n[AWS 信息]")
    if data['aws_info']['metadata_available']:
        print(f"实例ID: {data['aws_info']['instance_id']}")
        print(f"实例类型: {data['aws_info']['instance_type']}")
        print(f"区域: {data['aws_info'].get('region', '未知')}")
        print(f"可用区: {data['aws_info'].get('availability_zone', '未知')}")
        print(f"私有IP: {data['aws_info'].get('private_ip', '未知')}")
        print(f"公有IP: {data['aws_info'].get('public_ip', '未知')}")
        print(f"MAC地址: {data['aws_info'].get('mac_address', '未知')}")
        print(f"安全组: {data['aws_info'].get('security_groups', '未知')}")
        
        if 'vpc_id' in data['aws_info']:
            print(f"VPC ID: {data['aws_info']['vpc_id']}")
            print(f"子网ID: {data['aws_info']['subnet_id']}")
        
        if 'iam_role' in data['aws_info']:
            print(f"IAM角色: {data['aws_info']['iam_role']}")
        
        if 'tags' in data['aws_info'] and data['aws_info']['tags']:
            print("\n实例标签:")
            for key, value in data['aws_info']['tags'].items():
                print(f"  {key}: {value}")
    else:
        print("AWS元数据不可用")
    
    # 根据开关决定是否保存文件
    if EXPORT_YAML:
        save_yaml_file(data)
    else:
        print("\n信息已显示在屏幕上（未生成文件，如需保存请设置EXPORT_YAML=True)")

if __name__ == '__main__':
    main()