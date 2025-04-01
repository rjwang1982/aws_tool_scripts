#!/usr/bin/env python3
"""
author: RJ.Wang
Date: 2025-03-13
email: wangrenjun@gmail.com
Description: Query current resource quotas in Cloudshell and output to CSV
"""
import boto3
import sys
import csv
from datetime import datetime

def list_service_quotas(service_code, region):
    """
    Query all quota items and their quota codes for the specified service.

    Args:
        service_code (str): AWS service code (e.g., 'ec2').
        region (str): AWS region code (e.g., 'us-west-2').
    
    Returns:
        list: List of dictionaries containing quota information.
    """
    client = boto3.client('service-quotas', region_name=region)
    try:
        print(f"Querying quotas for service {service_code}...")
        response = client.list_service_quotas(ServiceCode=service_code)
        
        quotas = []
        for quota in response['Quotas']:
            quotas.append({
                "ServiceCode": service_code,
                "Region": region,
                "QuotaName": quota['QuotaName'],
                "QuotaCode": quota['QuotaCode'],
                "Value": quota['Value']
            })
        return quotas
    except Exception as e:
        print(f"[Error] Failed to query service quotas: {e}")
        sys.exit(1)

def save_to_csv(quotas, output_file=None):
    """
    Save quota information to a CSV file.

    Args:
        quotas (list): List of dictionaries containing quota information.
        output_file (str): Optional output file name.
    """
    if not quotas:
        print("No quota information found.")
        return
    
    if output_file is None:
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'service_quotas_{timestamp}.csv'
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ServiceCode', 'Region', 'QuotaName', 'QuotaCode', 'Value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for quota in quotas:
                writer.writerow(quota)
        
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"[Error] Failed to write CSV file: {e}")
        sys.exit(1)

def main():
    # Setting
    services = ['ec2', 'lambda', 's3']  # Add more services as needed
    regions = ['us-west-2', 'us-east-1']  # Add more regions as needed
    
    all_quotas = []
    
    # Query quotas for each service in each region
    for service in services:
        for region in regions:
            quotas = list_service_quotas(service, region)
            all_quotas.extend(quotas)
    
    # Save results to CSV
    save_to_csv(all_quotas)

if __name__ == "__main__":
    main()
