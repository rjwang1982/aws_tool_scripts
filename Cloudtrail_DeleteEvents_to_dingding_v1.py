import json
import urllib3
import os
import logging
import time
import hmac
import base64
import urllib.parse
import hashlib
from datetime import datetime, timedelta, timezone

# 配置日志记录
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 调试开关（True 表示开启调试模式，False 表示关闭）
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'

# 只通知删除类事件（True 仅通知删除操作，False 允许所有事件）
NOTIFY_DELETE_EVENTS_ONLY = os.environ.get('NOTIFY_DELETE_EVENTS_ONLY', 'True').lower() == 'False'

# 钉钉机器人 Webhook 地址（从环境变量中获取）
DINGTALK_WEBHOOK = os.environ.get('DINGTALK_WEBHOOK')
# 钉钉机器人密钥（从环境变量中获取，用于加签）
DINGTALK_SECRET = os.environ.get('DINGTALK_SECRET')
# 钉钉消息图片链接（从环境变量中获取）
BANNER_IMAGE_URL = os.environ.get('BANNER_IMAGE_URL')

def lambda_handler(event, context):
    # 记录接收到的事件
    logger.info('接收到的事件: %s', json.dumps(event))
    
    try:
        # 解析 SNS 消息
        if 'Records' in event:
            sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        else:
            sns_message = event
        logger.info('解析的 SNS 消息: %s', json.dumps(sns_message))
        
        # 提取关键信息
        detail = sns_message['detail']
        event_time = detail.get('eventTime', '未知时间')
        event_name = detail.get('eventName', '未知操作')
        # **如果启用了删除类事件通知开关，则跳过非删除操作**
        delete_events = ['DeleteSecurityGroup', 'RevokeSecurityGroupIngress', 'RevokeSecurityGroupEgress', 'DeleteLoadBalancer']
        if NOTIFY_DELETE_EVENTS_ONLY and event_name not in delete_events:
            logger.info('非删除类事件，跳过通知: %s', event_name)
            return {
                'statusCode': 200,
                'body': json.dumps(f'跳过非删除类事件: {event_name}')
            }
        user_identity = detail['userIdentity']
        user_type = user_identity.get('type', '')
        user_name = user_identity.get('userName', '未知用户')
        # 如果是 AssumedRole，则设置用户名称为 "假借角色"
        if user_type == 'AssumedRole':
            user_name = "假借角色"
        user_arn = user_identity.get('arn', '未知用户 ARN')
        source_ip = detail.get('sourceIPAddress', '未知 IP')
        region = sns_message.get('region', '未知区域')
        deleted_resource = extract_deleted_resource(detail)
        
        # 转换时间为+8时区
        event_time = convert_to_utc8(event_time)
        
        # 构造钉钉消息内容
        message = f"![图片]({BANNER_IMAGE_URL})\n" \
                  f"- **事件时间**: {event_time}\n" \
                  f"- **操作名称**: {event_name}\n" \
                  f"- **用户名称**: {user_name}\n" \
                  f"- **用户 ARN**: {user_arn}\n" \
                  f"- **源 IP 地址**: {source_ip}\n" \
                  f"- **区域**: {region}\n" \
                  f"- **被操作资源**: {deleted_resource}\n\n"
        
        if DEBUG_MODE:
            logger.info('构造的钉钉消息内容: %s', message)
        
        # 发送消息到钉钉
        send_dingtalk_message(message)
        
    except Exception as e:
        logger.error('处理事件时发生错误: %s', str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(f'处理事件时发生错误: {str(e)}')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('消息发送成功')
    }

def convert_to_utc8(time_str):
    """
    将时间字符串转换为+8时区
    """
    if time_str == '未知时间':
        return time_str
    
    try:
        # 尝试解析多种时间格式
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # 如果 ISO 格式解析失败，尝试其他常见格式
            dt = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            return time_str
    
    dt_utc8 = dt.astimezone(timezone(timedelta(hours=8)))
    return dt_utc8.strftime('%Y-%m-%d %H:%M:%S')

def extract_deleted_resource(detail):
    """
    提取被删除或被修改的资源信息
    """
    resources = detail.get('resources', [])
    for resource in resources:
        if 'ARN' in resource:
            return resource['ARN']
    
    request_parameters = detail.get('requestParameters', {})
    response_elements = detail.get('responseElements', {})
    event_name = detail.get('eventName', '')

    # 处理 response_elements 可能为 None 的情况
    if response_elements is None:
        response_elements = {}

    # 处理撤销安全组规则
    if event_name in ['RevokeSecurityGroupIngress', 'RevokeSecurityGroupEgress']:
        security_group_id = request_parameters.get('groupId', '未知安全组')
        rule_details = []

        # 优先检查 responseElements['revokedSecurityGroupRuleSet']
        revoked_rules = response_elements.get('revokedSecurityGroupRuleSet', {}).get('items', [])
        if not revoked_rules:
            revoked_rules = request_parameters.get('ipPermissions', {}).get('items', [])

        for rule in revoked_rules:
            ip_protocol = rule.get('ipProtocol', '未知协议')
            from_port = rule.get('fromPort', '未知端口')
            to_port = rule.get('toPort', '未知端口')

            # 检查 IP 范围（优先使用 cidrIpv4 / cidrIpv6）
            cidr_ip_list = [ip.get('cidrIp', '未知 IP') for ip in rule.get('ipRanges', {}).get('items', [])]
            if 'cidrIpv4' in rule:
                cidr_ip_list.append(rule['cidrIpv4'])
            if 'cidrIpv6' in rule:
                cidr_ip_list.append(rule['cidrIpv6'])
            cidr_ip = ', '.join(cidr_ip_list) if cidr_ip_list else '未知 IP'

            rule_details.append(f"协议: {ip_protocol}, 端口: {from_port}-{to_port}, 被撤销 IP: {cidr_ip}")

        rule_info = "; ".join(rule_details) if rule_details else "未知规则"
        return f"安全组: {security_group_id}, 被撤销规则: {rule_info}"

    elif event_name in ['AuthorizeSecurityGroupIngress', 'AuthorizeSecurityGroupEgress']:
        if 'groupId' in request_parameters:
            rule_details = []
            for rule in request_parameters.get('ipPermissions', {}).get('items', []):
                ip_protocol = rule.get('ipProtocol', '未知协议')
                from_port = rule.get('fromPort', '未知端口')
                to_port = rule.get('toPort', '未知端口')
                cidr_ip = ', '.join([ip.get('cidrIp', '未知 IP') for ip in rule.get('ipRanges', {}).get('items', [])])
                rule_details.append(f"协议: {ip_protocol}, 端口: {from_port}-{to_port}, 允许 IP: {cidr_ip}")

            rule_info = "; ".join(rule_details) if rule_details else "未知规则"
            return f"安全组: {request_parameters['groupId']}, 新增规则: {rule_info}"

    elif event_name == 'DeleteSecurityGroup' and 'groupId' in request_parameters:
        return f"安全组: {request_parameters['groupId']} 已被删除"

    elif event_name == 'DeleteLoadBalancer' and 'loadBalancerArn' in request_parameters:
        return request_parameters['loadBalancerArn']
    
    elif event_name == 'DeleteUser' and 'userName' in request_parameters:
        return f"IAM 用户 {request_parameters['userName']} 已被删除"
    
    elif 'key' in request_parameters:
        return request_parameters['key']
    elif 'name' in request_parameters:
        return request_parameters['name']
    elif 'ARN' in response_elements:
        return response_elements['ARN']
    
    return '未知资源'

def send_dingtalk_message(content):
    """
    发送消息到钉钉，包含加签逻辑
    """
    # 获取当前时间戳（毫秒）
    timestamp = str(round(time.time() * 1000))
    
    # 计算签名
    secret_enc = DINGTALK_SECRET.encode('utf-8')
    string_to_sign = f'{timestamp}\n{DINGTALK_SECRET}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    
    # 调试模式下输出签名和时间戳
    if DEBUG_MODE:
        logger.info('钉钉消息签名: timestamp=%s, sign=%s', timestamp, sign)
    
    # 构造带签名的 URL
    webhook_url = f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "AWS 操作通知",
            "text": content
        }
    }
    
    http = urllib3.PoolManager()
    response = http.request('POST', webhook_url, body=json.dumps(payload), headers=headers)
    
    if response.status != 200:
        response_data = json.loads(response.data.decode('utf-8'))
        error_msg = f"发送钉钉消息失败: 状态码={response.status}, 错误信息={response_data.get('errmsg', '未知错误')}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    logger.info('钉钉消息发送成功')