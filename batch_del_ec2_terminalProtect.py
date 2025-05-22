import boto3

# 创建 boto3 客户端
ec2 = boto3.client('ec2', region_name='us-east-1')  # 替换为你的区域
sts = boto3.client('sts')

# 获取账户信息和区域
account_id = sts.get_caller_identity()['Account']
region = ec2.meta.region_name

# 用户确认是否处理所有实例
choice = input("是否取消所有 EC2 实例的终止保护？(yes/no, 默认 no): ").strip().lower()
if choice != 'yes':
    tag_key = input("请输入标签键 (例如 'Environment'): ").strip()
    tag_value = input("请输入标签值 (例如 'dev'): ").strip()
    filters = [{'Name': f'tag:{tag_key}', 'Values': [tag_value]}]
    response = ec2.describe_instances(Filters=filters)
    print(f"\n只会处理具有标签 {tag_key}={tag_value} 的实例\n")
else:
    response = ec2.describe_instances()
    print("\n将处理所有实例\n")

# 记录成功处理的实例 ARN
successful_arns = []

# 遍历实例
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        try:
            # 查询终止保护状态
            attr = ec2.describe_instance_attribute(
                InstanceId=instance_id,
                Attribute='disableApiTermination'
            )
            is_protected = attr['DisableApiTermination']['Value']
            print(f"实例 {instance_id} 当前终止保护状态: {'开启' if is_protected else '关闭'}")

            if is_protected:
                ec2.modify_instance_attribute(
                    InstanceId=instance_id,
                    DisableApiTermination={'Value': False}
                )
                arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
                successful_arns.append(arn)
                print(f"--> ✅ 已取消终止保护: {instance_id}")
                print(f"    ARN: {arn}")
            else:
                print(f"--> ⚠️ 实例 {instance_id} 未开启终止保护，跳过")

        except Exception as e:
            print(f"❌ 处理实例 {instance_id} 时出错: {e}")

# 打印汇总结果
if successful_arns:
    print("\n✅ 以下实例成功取消终止保护：")
    for arn in successful_arns:
        print(arn)
else:
    print("\n⚠️ 没有实例被修改。")
