import boto3
import botocore.exceptions
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 自定义变量
AWS_REGION = "ap-southeast-1"
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:269490040603:alarmbyrj20250225"
USE_TAGS = False  # 是否使用标签筛选，默认为False（即为所有实例创建告警）
INSTANCE_TAG_KEY = "Monitor"
INSTANCE_TAG_VALUE = "yes"

def get_aws_account_id():
    """获取当前 AWS 账户 ID"""
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()["Account"]

AWS_ACCOUNT_ID = get_aws_account_id()
logging.info(f"Detected AWS Account ID: {AWS_ACCOUNT_ID}")

def delete_existing_alarm(cloudwatch_client, alarm_name):
    """删除已有的 CloudWatch Alarm"""
    try:
        existing_alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
        if existing_alarms.get('MetricAlarms'):
            cloudwatch_client.delete_alarms(AlarmNames=[alarm_name])
            logging.info(f"Deleted existing alarm: {alarm_name}")
    except botocore.exceptions.ClientError as e:
        logging.error(f"Error deleting alarm {alarm_name}: {e}")

def create_cloudwatch_alarms(region, sns_topic_arn, use_tags=False, tag_key=None, tag_value=None):
    """为所有或符合条件的 EC2 实例创建 CloudWatch 监控告警，并返回创建的 Alarm ARN 列表"""
    ec2_client = boto3.client('ec2', region_name=region)
    cloudwatch_client = boto3.client('cloudwatch', region_name=region)

    try:
        # 获取实例列表
        if use_tags:
            # 使用标签筛选
            instances = ec2_client.describe_instances(Filters=[{'Name': f'tag:{tag_key}', 'Values': [tag_value]}])
        else:
            # 获取所有实例
            instances = ec2_client.describe_instances()

        # 提取实例ID，并过滤掉非运行状态的实例（可选）
        instance_ids = []
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':  # 仅处理运行中的实例
                    instance_ids.append(instance['InstanceId'])

        if not instance_ids:
            logging.warning("No EC2 instances found.")
            return []

        created_alarm_arns = []  # 存储创建的 Alarm ARN

        for instance_id in instance_ids:
            for metric_name, alarm_name_suffix in [
                ('StatusCheckFailed_System', 'System-Check-Failed'),
                ('StatusCheckFailed_Instance', 'Instance-Check-Failed'),
                ('EBSIOBalance%', 'EBS-Check-Failed')
            ]:
                alarm_name = f"EC2-{instance_id}-{alarm_name_suffix}-Alarm"
                alarm_arn = f"arn:aws:cloudwatch:{region}:{AWS_ACCOUNT_ID}:alarm:{alarm_name}"

                # 检查并删除已有告警
                delete_existing_alarm(cloudwatch_client, alarm_name)

                # 创建新的告警
                try:
                    # 特殊处理 EBSIOBalance% 的阈值和比较操作符
                    threshold = 1
                    comparison_operator = 'GreaterThanOrEqualToThreshold'
                    if metric_name == 'EBSIOBalance%':
                        threshold = 10
                        comparison_operator = 'LessThanOrEqualToThreshold'

                    cloudwatch_client.put_metric_alarm(
                        AlarmName=alarm_name,
                        AlarmDescription=f"Alarm for {metric_name} on instance {instance_id}",
                        ActionsEnabled=True,
                        AlarmActions=[sns_topic_arn],
                        OKActions=[sns_topic_arn],  # 状态恢复时发送 SNS 通知
                        MetricName=metric_name,
                        Namespace='AWS/EC2',
                        Statistic='Maximum',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        Period=300,
                        EvaluationPeriods=1,
                        Threshold=threshold,
                        ComparisonOperator=comparison_operator
                    )
                    logging.info(f"Created alarm: {alarm_name} (ARN: {alarm_arn})")
                    created_alarm_arns.append(alarm_arn)

                except botocore.exceptions.ClientError as e:
                    logging.error(f"Error creating alarm {alarm_name}: {e}")

        return created_alarm_arns

    except botocore.exceptions.ClientError as e:
        logging.error(f"Error accessing AWS services: {e}")
        return []

if __name__ == "__main__":
    logging.info("Starting CloudWatch Alarm creation process...")
    
    created_alarms = create_cloudwatch_alarms(
        AWS_REGION,
        SNS_TOPIC_ARN,
        use_tags=USE_TAGS,
        tag_key=INSTANCE_TAG_KEY,
        tag_value=INSTANCE_TAG_VALUE
    )
    
    logging.info(f"Total alarms created: {len(created_alarms)}")
    if created_alarms:
        logging.info("Created Alarm ARNs:")
        for alarm_arn in created_alarms:
            logging.info(alarm_arn)