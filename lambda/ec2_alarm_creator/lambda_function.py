import boto3
from alarm_config import ALARM_CONFIGS
import os
import json

# Initialize AWS clients
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')

def create_cloudwatch_alarm(resource_id, metric_category, metric_type, threshold):
    """
    Create CloudWatch alarm for various metrics (CPU, Network, etc.).
    
    Args:
        resource_id: Resource ID (e.g., EC2 instance ID)
        metric_category: Category of metric (e.g., 'cpu', 'network')
        metric_type: Type of metric (e.g., 'utilization', 'in_bytes')
        threshold: Alarm threshold value
    """
    try:
        if metric_category not in ALARM_CONFIGS:
            raise ValueError(f"Invalid metric category: {metric_category}")
        
        category_config = ALARM_CONFIGS[metric_category]
        if metric_type not in category_config:
            raise ValueError(f"Invalid metric type: {metric_type}")

        config = category_config[metric_type]
        description = config['description'].format(resource_id=resource_id, threshold=threshold)
        
        cloudwatch_client.put_metric_alarm(
            AlarmName=f'{resource_id}-{config["name"]}',
            ComparisonOperator=config["comparison"],
            EvaluationPeriods=1,
            MetricName=config["metric"],
            Namespace=config["namespace"],
            Period=300,  # 5 minutes
            Statistic='Average',
            Threshold=threshold,
            ActionsEnabled=True,
            AlarmDescription=description,
            Dimensions=[
                {
                    'Name': config["dimensions_key"],
                    'Value': resource_id
                }
            ]
        )
    except ValueError as e:
        print(f"Invalid configuration: {str(e)}")

def lambda_handler(event, context):
    # Parse the EventBridge event
    print(f"Received event: {json.dumps(event)}")
    
    # Extract instance details from the event
    sns_message = event['Records'][0]['Sns']['Message']
    message_data = json.loads(sns_message)
    
    # Extract the instance ID and state
    instance_id = message_data['detail']['instance-id']
    state = message_data['detail']['state']
    
    if state == 'running':
        # Get instance tags
        response = ec2_client.describe_tags(
            Filters=[
                {
                    'Name': 'resource-id',
                    'Values': [instance_id]
                }
            ]
        )
        
        for tag in response['Tags']:
            key = tag['Key']
            value = tag['Value']
            
            if key == 'cpu_utilization':
                try:
                    create_cloudwatch_alarm(instance_id, 'cpu', 'utilization', float(value))
                except ValueError:
                    print(f"Invalid CPU threshold value: {value}")
            
            if key == 'cpu_credit_balance':
                try:
                    create_cloudwatch_alarm(instance_id, 'cpu', 'credit_balance', float(value))
                except ValueError:
                    print(f"Invalid CPU credit balance threshold value: {value}")
    
    elif state == 'terminated':
        # Delete all alarms for the instance
        try:
            # List all alarms for the instance
            response = cloudwatch_client.describe_alarms()
            for alarm in response['MetricAlarms']:
                # Check if alarm belongs to this instance
                if alarm['Dimensions'] and \
                   alarm['Dimensions'][0]['Name'] == 'InstanceId' and \
                   alarm['Dimensions'][0]['Value'] == instance_id:
                    # Delete the alarm
                    cloudwatch_client.delete_alarms(
                        AlarmNames=[alarm['AlarmName']]
                    )
                    print(f"Deleted alarm: {alarm['AlarmName']}")
        except Exception as e:
            print(f"Error deleting alarms: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed EC2 instance state change')
    }