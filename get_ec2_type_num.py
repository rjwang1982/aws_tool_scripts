import boto3
import csv
from collections import Counter

# 是否导出为 CSV 文件
EXPORT_TO_CSV = False

# 创建 EC2 客户端
ec2_client = boto3.client('ec2')

# 获取所有实例信息
response = ec2_client.describe_instances()

# 提取所有实例类型
instance_types = []
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        instance_types.append(instance['InstanceType'])

# 统计运行中的和非运行中的实例数量
running_count = 0
non_running_count = 0

for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        if instance['State']['Name'] == 'running':
            running_count += 1
        else:
            non_running_count += 1

# 统计各个实例类型的数量
type_counts = Counter(instance_types)

# 如果没有找到任何实例
if not type_counts:
    print("未发现 EC2 实例。")
else:
    print("\nEC2 实例类型数量统计：")
    print("-" * 40)
    for instance_type, count in type_counts.items():
        print(f"{instance_type:<30} : {count:>3}")
    print("-" * 40)

# 输出运行中和非运行中的实例数量
print(f"\n运行中的 EC2 实例数量: {running_count}")
print(f"非运行中的 EC2 实例数量: {non_running_count}")

# 将结果写入 CSV 文件
if EXPORT_TO_CSV:
    with open('ec2_instance_types_count.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['InstanceType', 'Count'])
        for instance_type, count in type_counts.items():
            writer.writerow([instance_type, count])
    print("EC2 实例类型数量已导出至 ec2_instance_types_count.csv")
