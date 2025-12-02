#!/usr/bin/env python3
"""
author: RJ.Wang
Date: 2025-03-13
email: wangrenjun@gmail.com
Description: Batch creation of AWS EC2 CPU utilization alarms with TAG filtering
"""
import boto3
import logging
from botocore.exceptions import ClientError

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

AWS_REGION = "ap-southeast-1"  # 需要修改为您的 AWS 区域
sns_topic_arn = "arn:aws:sns:xxxxxx:xxxxxx:xxxxxx"  # 需要修改为您的 SNS 主题 ARN

# 若要对不同的EC2配置不同的告警参数，可根据TAG 来筛选和分组，KEY和VALUE 值均为 None 时，将对该区域所有为 running 状态的 EC2 进行操作
TAG_KEY = None
TAG_VALUE = None
#TAG_KEY = "Monitor"  # TAG 的 Key
#TAG_VALUE = "yes"  # TAG 的 Value

ec2_client = boto3.client("ec2", region_name=AWS_REGION)
cw_client = boto3.client("cloudwatch", region_name=AWS_REGION)
sts_client = boto3.client("sts")

# 获取账号ID并缓存
account_id = sts_client.get_caller_identity()["Account"]

def get_instance_ids():
    """
    获取所有运行的EC2实例ID，并根据TAG进行筛选
    """
    paginator = ec2_client.get_paginator("describe_instances")
    instance_ids = []
    try:
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance.get("InstanceId")
                    state = instance.get("State", {}).get("Name", "unknown")
                    tags = instance.get("Tags", [])
                    
                    # 检查实例是否符合TAG筛选条件
                    tag_match = True
                    if TAG_KEY and TAG_VALUE:
                        tag_match = False
                        for tag in tags:
                            if tag.get("Key") == TAG_KEY and tag.get("Value") == TAG_VALUE:
                                tag_match = True
                                break
                    
                    if state == "running" and tag_match:
                        instance_ids.append(instance_id)
                        logger.debug(f"Found running instance with matching TAG: {instance_id}")
                    else:
                        logger.debug(f"Skipping instance (state: {state}, TAG match: {tag_match}): {instance_id}")
    except ClientError as e:
        logger.error(f"Error getting instance IDs: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting instances: {e}")
    return instance_ids

def delete_existing_alarm(alarm_name):
    """
    删除已存在的同名报警
    """
    try:
        response = cw_client.describe_alarms(AlarmNames=[alarm_name])
        if response.get("MetricAlarms"):
            cw_client.delete_alarms(AlarmNames=[alarm_name])
            logger.info(f"Deleted existing alarm: {alarm_name}")
        else:
            logger.info(f"No existing alarm found: {alarm_name}")
    except ClientError as e:
        logger.error(f"Error deleting alarm {alarm_name}: {e}")

def create_cpu_alarm(instance_id, created_alarms):
    """
    为指定实例创建CPU使用率报警
    """
    alarm_name = f"CPU-{instance_id}-Alarm"
    try:
        delete_existing_alarm(alarm_name)
        cw_client.put_metric_alarm(
            AlarmName=alarm_name,
            MetricName="CPUUtilization",
            Namespace="AWS/EC2",
            Statistic="Average",
            Period=60,
            EvaluationPeriods=2,
            Threshold=85.0,
            ComparisonOperator="GreaterThanThreshold",
            AlarmActions=[sns_topic_arn],
            OKActions=[sns_topic_arn],
            AlarmDescription=f"Alarm for CPUUtilization on instance {instance_id}",  # 增加报警描述
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}]
        )
        logger.info(f"Created CPU alarm: {alarm_name}")
        
        alarm_arn = f"arn:aws:cloudwatch:{AWS_REGION}:{account_id}:alarm:{alarm_name}"
        created_alarms.append(alarm_arn)
    except ClientError as e:
        logger.error(f"Error creating alarm for instance {instance_id}: {e}")

def main():
    """
    主函数，执行整个流程
    """
    try:
        logger.info("Starting program...")
        instance_ids = get_instance_ids()
        if not instance_ids:
            logger.info("No running instances found with matching TAG. Exiting.")
            return
        
        logger.info(f"Found {len(instance_ids)} running instances with matching TAG: {instance_ids}")
        
        created_alarms = []
        for instance_id in instance_ids:
            create_cpu_alarm(instance_id, created_alarms)
        
        total_alarms = len(created_alarms)
        logger.info(f"\nTotal new alarms created: {total_alarms}")
        logger.info("Alarm ARNs:")
        for arn in created_alarms:
            logger.info(arn)
        
        logger.info("Program completed successfully.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()