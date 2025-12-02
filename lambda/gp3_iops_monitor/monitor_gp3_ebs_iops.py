#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GP3 EBS IOPS 监控告警脚本

功能：
- 自动发现所有 GP3 类型的 EBS 卷
- 为每个 GP3 卷创建 IOPS 监控告警（ReadOps + WriteOps）
- 当 IOPS 超过 3000 时触发告警
- 自动删除旧的告警并创建新的

作者：RJ.Wang
邮箱：wangrenjun@gmail.com
创建时间：2025-12-02
"""

import boto3
import botocore.exceptions
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==================== 自定义配置 ====================
AWS_REGION = "ap-southeast-1"
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:269490040603:alarmbyrj20250225"
IOPS_THRESHOLD = 3000  # IOPS 告警阈值
USE_TAGS = False  # 是否使用标签筛选，默认为 False（即为所有 GP3 卷创建告警）
VOLUME_TAG_KEY = "Monitor"
VOLUME_TAG_VALUE = "yes"
# ===================================================

def get_aws_account_id():
    """获取当前 AWS 账户 ID"""
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()["Account"]
    logging.info(f"检测到 AWS 账户 ID: {account_id}")
    return account_id

AWS_ACCOUNT_ID = get_aws_account_id()

def delete_existing_alarm(cloudwatch_client, alarm_name):
    """删除已有的 CloudWatch Alarm"""
    try:
        existing_alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
        if existing_alarms.get('MetricAlarms'):
            cloudwatch_client.delete_alarms(AlarmNames=[alarm_name])
            logging.info(f"已删除现有告警: {alarm_name}")
            time.sleep(0.5)  # 避免 API 限流
    except botocore.exceptions.ClientError as e:
        logging.error(f"删除告警 {alarm_name} 时出错: {e}")

def get_gp3_volumes(ec2_client, use_tags=False, tag_key=None, tag_value=None):
    """获取所有 GP3 类型的 EBS 卷"""
    try:
        filters = [{'Name': 'volume-type', 'Values': ['gp3']}]
        
        if use_tags:
            filters.append({'Name': f'tag:{tag_key}', 'Values': [tag_value]})
        
        volumes = ec2_client.describe_volumes(Filters=filters)
        
        gp3_volumes = []
        for volume in volumes['Volumes']:
            volume_info = {
                'VolumeId': volume['VolumeId'],
                'Size': volume['Size'],
                'State': volume['State'],
                'Iops': volume.get('Iops', 3000),  # GP3 默认 3000 IOPS
                'AvailabilityZone': volume['AvailabilityZone']
            }
            
            # 获取卷的名称标签
            volume_name = 'N/A'
            for tag in volume.get('Tags', []):
                if tag['Key'] == 'Name':
                    volume_name = tag['Value']
                    break
            volume_info['Name'] = volume_name
            
            # 获取挂载的实例 ID
            attachments = volume.get('Attachments', [])
            if attachments:
                volume_info['InstanceId'] = attachments[0].get('InstanceId', 'N/A')
                volume_info['Device'] = attachments[0].get('Device', 'N/A')
            else:
                volume_info['InstanceId'] = 'Unattached'
                volume_info['Device'] = 'N/A'
            
            gp3_volumes.append(volume_info)
        
        return gp3_volumes
    
    except botocore.exceptions.ClientError as e:
        logging.error(f"获取 GP3 卷列表时出错: {e}")
        return []

def create_gp3_iops_alarms(region, sns_topic_arn, iops_threshold, use_tags=False, tag_key=None, tag_value=None):
    """为所有 GP3 卷创建 IOPS 监控告警"""
    ec2_client = boto3.client('ec2', region_name=region)
    cloudwatch_client = boto3.client('cloudwatch', region_name=region)
    
    # 获取所有 GP3 卷
    gp3_volumes = get_gp3_volumes(ec2_client, use_tags, tag_key, tag_value)
    
    if not gp3_volumes:
        logging.warning("未找到 GP3 类型的 EBS 卷")
        return []
    
    logging.info(f"找到 {len(gp3_volumes)} 个 GP3 卷")
    
    created_alarm_arns = []
    
    for volume in gp3_volumes:
        volume_id = volume['VolumeId']
        volume_name = volume['Name']
        instance_id = volume['InstanceId']
        
        logging.info(f"处理卷: {volume_id} (名称: {volume_name}, 实例: {instance_id}, 配置 IOPS: {volume['Iops']})")
        
        # 创建 IOPS 告警（使用数学表达式：ReadOps + WriteOps）
        alarm_name = f"EBS-{volume_id}-IOPS-High-Alarm"
        alarm_arn = f"arn:aws:cloudwatch:{region}:{AWS_ACCOUNT_ID}:alarm:{alarm_name}"
        
        # 删除已有告警
        delete_existing_alarm(cloudwatch_client, alarm_name)
        
        try:
            # 使用 Metric Math 计算总 IOPS (ReadOps + WriteOps)
            cloudwatch_client.put_metric_alarm(
                AlarmName=alarm_name,
                AlarmDescription=f"GP3 卷 {volume_id} ({volume_name}) IOPS 超过 {iops_threshold}。实例: {instance_id}",
                ActionsEnabled=True,
                AlarmActions=[sns_topic_arn],
                OKActions=[sns_topic_arn],
                Metrics=[
                    {
                        'Id': 'm1',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/EBS',
                                'MetricName': 'VolumeReadOps',
                                'Dimensions': [
                                    {
                                        'Name': 'VolumeId',
                                        'Value': volume_id
                                    }
                                ]
                            },
                            'Period': 300,
                            'Stat': 'Sum'
                        },
                        'ReturnData': False
                    },
                    {
                        'Id': 'm2',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/EBS',
                                'MetricName': 'VolumeWriteOps',
                                'Dimensions': [
                                    {
                                        'Name': 'VolumeId',
                                        'Value': volume_id
                                    }
                                ]
                            },
                            'Period': 300,
                            'Stat': 'Sum'
                        },
                        'ReturnData': False
                    },
                    {
                        'Id': 'e1',
                        'Expression': '(m1+m2)/PERIOD(m1)',
                        'Label': 'Total IOPS',
                        'ReturnData': True
                    }
                ],
                EvaluationPeriods=2,
                DatapointsToAlarm=2,
                Threshold=iops_threshold,
                ComparisonOperator='GreaterThanThreshold',
                TreatMissingData='notBreaching'
            )
            
            logging.info(f"✓ 已创建告警: {alarm_name}")
            created_alarm_arns.append(alarm_arn)
            time.sleep(0.5)  # 避免 API 限流
            
        except botocore.exceptions.ClientError as e:
            logging.error(f"✗ 创建告警 {alarm_name} 时出错: {e}")
    
    return created_alarm_arns

def main():
    """主函数"""
    logging.info("=" * 60)
    logging.info("开始 GP3 EBS IOPS 监控告警创建流程")
    logging.info("=" * 60)
    logging.info(f"区域: {AWS_REGION}")
    logging.info(f"IOPS 阈值: {IOPS_THRESHOLD}")
    logging.info(f"SNS 主题: {SNS_TOPIC_ARN}")
    logging.info(f"使用标签筛选: {USE_TAGS}")
    if USE_TAGS:
        logging.info(f"标签筛选条件: {VOLUME_TAG_KEY}={VOLUME_TAG_VALUE}")
    logging.info("=" * 60)
    
    created_alarms = create_gp3_iops_alarms(
        AWS_REGION,
        SNS_TOPIC_ARN,
        IOPS_THRESHOLD,
        use_tags=USE_TAGS,
        tag_key=VOLUME_TAG_KEY,
        tag_value=VOLUME_TAG_VALUE
    )
    
    logging.info("=" * 60)
    logging.info(f"总共创建告警数量: {len(created_alarms)}")
    
    if created_alarms:
        logging.info("\n已创建的告警 ARN 列表:")
        for i, alarm_arn in enumerate(created_alarms, 1):
            logging.info(f"{i}. {alarm_arn}")
    
    logging.info("=" * 60)
    logging.info("GP3 EBS IOPS 监控告警创建流程完成")
    logging.info("=" * 60)

if __name__ == "__main__":
    main()
