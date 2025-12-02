#!/usr/bin/env python3
"""
author: RJ.Wang
Date: 2025-03-13
email: wangrenjun@gmail.com
Description: 在 Cloudshell 中查询当前资源配额
"""
import boto3
import sys

def list_service_quotas(service_code, region):
    """
    查询指定服务的所有配额项及其配额代码。

    Args:
        service_code (str): AWS 服务代码（如 'ec2'）。
        region (str): AWS 区域代码（如 'us-west-2'）。
    
    Returns:
        list: 包含配额名称、配额代码和当前配额值的字典列表。
    """
    client = boto3.client('service-quotas', region_name=region)
    try:
        print(f"正在查询服务 {service_code} 的配额项...")
        response = client.list_service_quotas(ServiceCode=service_code)
        
        quotas = []
        for quota in response['Quotas']:
            quotas.append({
                "QuotaName": quota['QuotaName'],
                "QuotaCode": quota['QuotaCode'],
                "Value": quota['Value']
            })
        return quotas
    except Exception as e:
        print(f"[错误] 查询服务配额失败: {e}")
        sys.exit(1)

def display_quotas(quotas):
    """
    格式化输出配额项。

    Args:
        quotas (list): 包含配额名称、配额代码和当前配额值的字典列表。
    """
    if not quotas:
        print("未找到任何配额信息。")
        return
    
    print("\n=== 查询结果 ===")
    for quota in quotas:
        print(f"- 配额名称: {quota['QuotaName']}")
        print(f"  配额代码: {quota['QuotaCode']}")
        print(f"  配额值: {quota['Value']}\n")

def main():
    # 参数设置
    service_code = 'ec2'  # AWS 服务代码（如 'ec2', 's3', 'lambda'）
    region = 'us-west-2'  # 查询的区域

    # 查询服务的配额代码
    quotas = list_service_quotas(service_code, region)
    
    # 显示结果
    display_quotas(quotas)

if __name__ == "__main__":
    main()
