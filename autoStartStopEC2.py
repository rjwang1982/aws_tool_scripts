import boto3
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 全局变量存储配置
CONFIG = {}

def load_config():
    """
    加载环境变量配置。
    """
    global CONFIG
    CONFIG = {
        "region": os.getenv('AWS_REGION', 'ap-southeast-1'),          # 区域
        "tag_key": os.getenv('TAG_KEY', 'autoStartStop'),          # 标签键
        "tag_value": os.getenv('TAG_VALUE', 'T')             # 标签值
    }
    logger.info(f"Configuration loaded: {CONFIG}")

def get_instance_ids():
    """
    获取具有特定标签的实例ID列表。
    """
    ec2 = boto3.client('ec2', region_name=CONFIG["region"])
    filters = [{'Name': f'tag:{CONFIG["tag_key"]}', 'Values': [CONFIG["tag_value"]]}]
    logger.debug(f"Filters applied to search for instances: {filters}")
    
    try:
        instances = ec2.describe_instances(Filters=filters)
        instance_ids = [
            instance['InstanceId']
            for reservation in instances['Reservations']
            for instance in reservation['Instances']
        ]
        logger.info(f"Found instances with IDs: {instance_ids}")
        return instance_ids
    except Exception as e:
        logger.error(f"Failed to retrieve instances. Exception: {e}")
        return []

def manage_instances(instance_ids, action):
    """
    启动或停止指定实例，记录成功和失败的实例。
    """
    if not instance_ids:
        logger.warning(f"No instances found to {action}. Skipping operation.")
        return {"success": [], "failed": []}

    ec2 = boto3.client('ec2', region_name=CONFIG["region"])
    success, failed = [], []
    logger.debug(f"Performing '{action}' action on instances: {instance_ids}")

    for instance_id in instance_ids:
        try:
            if action == 'start':
                response = ec2.start_instances(InstanceIds=[instance_id])
                logger.info(f"Successfully started instance: {instance_id}")
            elif action == 'stop':
                response = ec2.stop_instances(InstanceIds=[instance_id])
                logger.info(f"Successfully stopped instance: {instance_id}")
            else:
                logger.error(f"Invalid action: {action}. Must be 'start' or 'stop'.")
                failed.append(instance_id)
                continue
            success.append(instance_id)
        except Exception as e:
            logger.error(f"Failed to {action} instance {instance_id}. Exception: {e}")
            failed.append(instance_id)
    
    logger.info(f"Action '{action}' completed. Success: {success}, Failed: {failed}")
    return {"success": success, "failed": failed}

def lambda_handler(event, context):
    """
    Lambda 函数入口。
    """
    logger.debug(f"Received event: {event}")
    if not CONFIG:
        load_config()

    action = event.get('action')
    if action not in ['start', 'stop']:
        logger.error(f"Invalid action '{action}' in event. Must be 'start' or 'stop'.")
        return {"success": [], "failed": []}

    logger.info(f"Executing '{action}' operation.")
    instance_ids = get_instance_ids()
    if instance_ids:
        logger.info(f"Instance IDs to {action}: {instance_ids}")
    return manage_instances(instance_ids, action)