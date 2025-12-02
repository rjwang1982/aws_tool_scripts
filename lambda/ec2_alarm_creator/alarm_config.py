"""
Configuration module for CloudWatch alarms.
"""

# Dictionary containing configurations for different types of CloudWatch alarms
ALARM_CONFIGS = {
    'cpu': {
        'utilization': {
            'name': 'CPU-Utilization',
            'metric': 'CPUUtilization',
            'namespace': 'AWS/EC2',
            'comparison': 'GreaterThanThreshold',
            'description': '{resource_id}: CPU utilization exceeds {threshold}%',
            'dimensions_key': 'InstanceId'
        },
        'credit_balance': {
            'name': 'CPU-Credit-Balance',
            'metric': 'CPUCreditBalance',
            'namespace': 'AWS/EC2',
            'comparison': 'LessThanThreshold',
            'description': '{resource_id}: CPU credit balance is below {threshold}',
            'dimensions_key': 'InstanceId'
        }
    },
    'network': {
        'in_bytes': {
            'name': 'Network-In',
            'metric': 'NetworkIn',
            'namespace': 'AWS/EC2',
            'comparison': 'GreaterThanThreshold',
            'description': '{resource_id}: Network in exceeds {threshold} bytes',
            'dimensions_key': 'InstanceId'
        },
        'out_bytes': {
            'name': 'Network-Out',
            'metric': 'NetworkOut',
            'namespace': 'AWS/EC2',
            'comparison': 'GreaterThanThreshold',
            'description': '{resource_id}: Network out exceeds {threshold} bytes',
            'dimensions_key': 'InstanceId'
        }
    }
}