#!/usr/bin/env python3
"""
author: RJ.Wang
Date: 2025-03-13
email: wangrenjun@gmail.com
Description: 在 Cloudshell 中查找该 Region 所有平均 CPU 占用低于 30% 的 EC2 实例
"""
import boto3
from datetime import datetime, timedelta, timezone
import csv

# 初始化 EC2 和 CloudWatch 客户端
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')

# 设置时间范围 - 过去 24 小时
end_time = datetime.now(timezone.utc)  # 使用 timezone-aware 的当前 UTC 时间
start_time = end_time - timedelta(days=1)

# 开关：是否输出到 CSV 文件
output_to_csv = False  # 默认不输出到 CSV 文件

# 定义 CPU 使用率阈值
cpu_threshold = 30.0

# 获取所有运行中的 EC2 实例
def get_running_instances():
    instances = []
    response = ec2_client.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            # 查找实例名称
            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), "N/A")
            instances.append((instance_id, instance_name))
    return instances

# 获取实例的平均 CPU 使用率
def get_average_cpu_utilization(instance_id):
    response = cloudwatch_client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,  # 每小时一个数据点
        Statistics=['Average']
    )
    # 计算一天内的平均 CPU 使用率
    data_points = response['Datapoints']
    if not data_points:
        return None  # 没有数据点的情况
    average_cpu = sum(dp['Average'] for dp in data_points) / len(data_points)
    return average_cpu

# 查找 CPU 使用率低于阈值的实例并排序
def find_low_cpu_instances():
    low_cpu_instances = []
    instances = get_running_instances()
    
    for instance_id, instance_name in instances:
        avg_cpu = get_average_cpu_utilization(instance_id)
        if avg_cpu is not None and avg_cpu < cpu_threshold:
            low_cpu_instances.append((instance_id, instance_name, avg_cpu))
    
    # 按 CPU 使用率从低到高排序
    low_cpu_instances.sort(key=lambda x: x[2])
    return low_cpu_instances

# 将结果写入 CSV 文件
def write_to_csv(data, filename="low_cpu_instances.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # 写入标题行
        writer.writerow(["Instance ID", "Instance Name", "Average CPU Utilization (%)"])
        # 写入数据行
        for instance_id, instance_name, avg_cpu in data:
            writer.writerow([instance_id, instance_name, f"{avg_cpu:.2f}"])

# 主函数
def main():
    low_cpu_instances = find_low_cpu_instances()
    
    # 默认将信息输出到屏幕
    print(f"\n{'Instance ID':<20} {'Instance Name':<30} {'Average CPU Utilization (%)':<20}")
    print(f"{'-' * 70}")
    for instance_id, instance_name, avg_cpu in low_cpu_instances:
        print(f"{instance_id:<20} {instance_name:<30} {avg_cpu:<20.2f}")
    
    # 如果开关设置为 True，则输出到 CSV 文件
    if output_to_csv:
        write_to_csv(low_cpu_instances)
        print(f"\nResults have been saved to low_cpu_instances.csv")

# 执行主函数
if __name__ == "__main__":
    main()