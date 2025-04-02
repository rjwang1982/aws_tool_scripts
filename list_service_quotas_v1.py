#!/usr/bin/env python3
"""
Author: RJ.Wang
Date: 2025-03-13
Email: wangrenjun@gmail.com
Description: Query AWS service quotas and output to CSV with better performance and flexibility.
"""
import boto3
import csv
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

SAVE_TO_CSV = 0  # 是否生成 CSV 文件
DEFAULT_REGIONS = ["ap-southeast-1", "ap-northeast-2"]  # 默认查询的 AWS 区域

def list_service_quotas(service_code, region):
    """Query all quota items for a given service in a specific region."""
    client = boto3.client('service-quotas', region_name=region)
    quotas = []
    try:
        paginator = client.get_paginator('list_service_quotas')
        for page in paginator.paginate(ServiceCode=service_code):
            for quota in page['Quotas']:
                quotas.append({
                    "ServiceCode": service_code,
                    "Region": region,
                    "QuotaName": quota['QuotaName'],
                    "QuotaCode": quota['QuotaCode'],
                    "Value": quota['Value']
                })
    except Exception as e:
        print(f"[Warning] Could not retrieve quotas for {service_code} in {region}: {e}")
    return quotas

def save_to_csv(quotas, output_file=None):
    """Save quota information to a CSV file."""
    if not quotas:
        print("No quota information found.")
        return

    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'service_quotas_{timestamp}.csv'
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ServiceCode', 'Region', 'QuotaName', 'QuotaCode', 'Value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(quotas)
        
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"[Error] Failed to write CSV file: {e}")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Query AWS service quotas and save to CSV.")
    parser.add_argument("-s", "--services", nargs="+", default=["ec2", "lambda", "s3"], help="List of AWS services to query")
    parser.add_argument("-r", "--regions", nargs="+", default=DEFAULT_REGIONS, help="List of AWS regions to query")
    parser.add_argument("-o", "--output", help="Output CSV filename")
    parser.add_argument("--no-csv", action="store_true", default=not SAVE_TO_CSV, help="Disable saving output to CSV")
    return parser.parse_args()

def main():
    args = parse_arguments()
    all_quotas = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(list_service_quotas, service, region): (service, region)
                   for service in args.services for region in args.regions}
        
        for future in futures:
            result = future.result()
            if result:
                all_quotas.extend(result)

    for quota in all_quotas:
        print(f"{quota['ServiceCode']} ({quota['Region']}): {quota['QuotaName']} = {quota['Value']}")

    if not args.no_csv:
        save_to_csv(all_quotas, args.output)

if __name__ == "__main__":
    main()