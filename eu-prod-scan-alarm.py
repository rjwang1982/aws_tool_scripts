import time
import json
import os
import requests
import re
import datetime
import boto3
import hashlib
import base64
import hmac
from urllib.parse import quote

# 创建 CloudWatch 和 SNS 的客户端
cloudwatch = boto3.client('cloudwatch')
title = '![1.png](https://isc-file.oss-cn-hangzhou.aliyuncs.com/aws-au/aws-eu-alarm.png)'
ec2 = boto3.client('ec2')
headers = {'Content-Type': 'application/json;charset=utf-8'}
current_time = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
token_test = 'd34a8ad4d9ad0c4abc3bf13ef47a9e1'
token_common = 'd34a8ad4d9adfceb4ebf13ef47a9e1'
token_center = 'd34a8ad4d9adf13ef47a9e1'
token_juicefs = 'd34a8ad4d9adfceef47a9e1' 
token_yewu = 'd34a8ad4d9adfca8c17391'
url = "https://oapi.dingtalk.com/robot/send?access_token="
api_url = url + token_test
#api_url = url + token_common
api_url_center = url +token_center
api_juicefs = url + token_juicefs
api_yewu =  url + token_yewu


#发送阿里短信变量
access_key_id = 'LTAI'
access_key_secret = 'kffSCXHQuXW'
sign_name = 'iSolar'
template_code = 'SMS_48019'
phone_number = '13677'
phone_number_wtl = '13687'

def percentEncode(s):
    return quote(s.encode('utf-8'),safe ='~')

def isBasicAlarm(alarmName):
    if alarmName and alarmName.lower().find('Aurora')==-1 and ((alarmName.find('Disk')!=-1 or alarmName.lower().find('mem')!=-1 or alarmName.lower().find('StatusCheckFailed')!=-1 or alarmName.lower().find('cpu')!=-1)) and alarmName.find('kafka')==-1 and alarmName.find('Kafka')==-1 and  alarmName.lower().find('Redis')==-1:
        return  True
    else:
        return False

def isAuoraAlarm(alarmName):
    if alarmName and alarmName.lower().find('Aurora')!=-1:
        return True
    else:
        return False

def isRedisAlarm(alarmName):
    if alarmName and alarmName.find('Redis')!=-1:
        return True
    else:
        return False

def isKafkaAlarm(alarmName):
    if alarmName and (alarmName.find('Kafka')!=-1 or alarmName.find('kafka')!=-1):
        return True
    else:
        return False

def isJuicefsAlarm(alarmName):
    if alarmName and alarmName.find('juicefs')!=-1:
        return True
    else:
        return False



def processAurora(alarm):
    threshold_match = re.search(r"threshold \((\d+(\.\d+)?(E\d+)?)\)", alarm['StateReason'])
    if threshold_match:
        threshold = threshold_match.group(1)
    matches = re.findall(r"\[(.*?)\]", alarm['StateReason'])
    if matches:
    # 从匹配的字符串中进一步提取浮点数
        data_points = re.findall(r"\d+\.\d+", matches[0])
        datapoints_count = len(data_points)  # 统计数据位点的个数
        rounded_numbers = [str(round(float(match), 1)) for match in data_points]
        if data_points:
        # 直接获取最后一个数据位点的数值
            last_data_point = float(data_points[-1])  # 获取最后一个数据位点的数值
            last_data_point_rounded = round(last_data_point, 1) #四舍五入
    if alarm['AlarmName'].lower().find('mem')!=-1:
        new_state_reason = f"{datapoints_count}分钟内内存使用率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
    elif alarm['AlarmName'].lower().find('cpu')!=-1:
        new_state_reason = f"{datapoints_count}分钟内cpu使用率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
    else:
        new_state_reason = f"{datapoints_count}分钟内数据库HLL队列长度超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
    
    
    content = "### {title}".format(title=title) + \
              "\n> #### **时间**: "  + current_time  + \
              "\n> #### **状态**: " + str(alarm['StateValue']) + \
              "\n> #### **告警名称**: " + str(alarm['AlarmName']) + \
              "\n> #### **告警描述**: " + str(alarm['AlarmDescription']) + \
              "\n> #### **实例名称**: " + str(alarm['Dimensions'][1]['Value']) + \
              "\n> #### **告警指标**: " + str(alarm['MetricName']) + \
              "\n> #### **告警阈值**: " + str(threshold)+ \
              "\n> #### **当前数值**: " + str(last_data_point_rounded) + \
              "\n> #### **告警原因**: " + str(new_state_reason)
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }

    content_aurora = "时间: "+ current_time+",状态: " + str(alarm['StateValue'])+",告警名称: " + str(alarm['AlarmName'])+",告警描述: " + str(alarm['AlarmDescription'])+",告警指标: " + str(alarm['MetricName'])+",实例名称: " + str(alarm['Dimensions'][1]['Value']) +",当前指标: " + str(last_data_point_rounded) + ",告警原因:" + str(new_state_reason)
    
    template_param = {'awsmessage' : content_aurora}  # 根据模板中的参数进行替换

    if alarm['AlarmName'].lower().find('mem')!=-1 or alarm['AlarmName'].lower().find('cpu')!=-1:
        result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param)
        print(result)
        request_aurora = requests.post(url=api_url, data=json.dumps(msg), headers=headers).content.decode("utf8")
    else:
        request_aurora = requests.post(url=api_yewu, data=json.dumps(msg), headers=headers).content.decode("utf8")

def processRedis(alarm):
    threshold_match = re.search(r"threshold \((\d+(\.\d+)?(E\d+)?)\)", alarm['StateReason'])
    if threshold_match:
        threshold = threshold_match.group(1)
    matches = re.findall(r"\[(.*?)\]", alarm['StateReason'])
    if matches:
    # 从匹配的字符串中进一步提取浮点数
        data_points = re.findall(r"\d+\.\d+", matches[0])
        datapoints_count = len(data_points)  # 统计数据位点的个数
        rounded_numbers = [str(round(float(match), 1)) for match in data_points]
        if data_points:
        # 直接获取最后一个数据位点的数值
            last_data_point = float(data_points[-1])  # 获取最后一个数据位点的数值
            last_data_point_rounded = round(last_data_point, 1) #四舍五入
    new_state_reason = f"{datapoints_count}分钟内可用内存率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
    content = "### {title}".format(title=title) + \
              "\n> #### **时间**: "  + current_time  + \
              "\n> #### **状态**: " + str(alarm['StateValue']) + \
              "\n> #### **告警名称**: " + str(alarm['AlarmName']) + \
              "\n> #### **告警描述**: " + str(alarm['AlarmDescription']) + \
              "\n> #### **实例名称**: " + str(alarm['Dimensions'][0]['Value']) + \
              "\n> #### **告警指标**: " + str(alarm['MetricName']) + \
              "\n> #### **告警阈值**: " + str(threshold)+ \
              "\n> #### **当前数值**: " + str(last_data_point_rounded) + \
              "\n> #### **告警原因**: " + str(new_state_reason)
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }

    content_redis = "时间: "+ current_time+",状态: " + str(alarm['StateValue'])+",告警名称: " + str(alarm['AlarmName'])+",告警描述: " + str(alarm['AlarmDescription'])+",告警指标: " + str(alarm['MetricName'])+",实例名称: " + str(alarm['Dimensions'][0]['Value']) +",当前指标: " + str(last_data_point_rounded) + ",告警原因:" + str(new_state_reason)
    
    template_param = {'awsmessage' : content_redis}  # 根据模板中的参数进行替换
    
    result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param)
    print(result)
    #request_redis = requests.post(url=api_test, data=json.dumps(msg), headers=headers).content.decode("utf8")
    if alarm['AlarmName'].lower().find('juicefs')!=-1:
        request_redis = requests.post(url=api_juicefs, data=json.dumps(msg), headers=headers).content.decode("utf8")
    else:
        request_redis = requests.post(url=api_url, data=json.dumps(msg), headers=headers).content.decode("utf8")
    

def processJuicefs(alarm):
    threshold_match = re.search(r"threshold \((\d+(\.\d+)?(E\d+)?)\)", alarm['StateReason'])
    if threshold_match:
        threshold = threshold_match.group(1)
    matches = re.findall(r"\[(.*?)\]", alarm['StateReason'])
    if matches:
    # 从匹配的字符串中进一步提取浮点数
        data_points = re.findall(r"\d+\.\d+", matches[0])
        datapoints_count = len(data_points)  # 统计数据位点的个数
        rounded_numbers = [str(round(float(match), 1)) for match in data_points]
        if data_points:
        # 直接获取最后一个数据位点的数值
            last_data_point = float(data_points[-1])  # 获取最后一个数据位点的数值
            last_data_point_rounded = round(last_data_point, 1) #四舍五入
    new_state_reason = f"{datapoints_count}分钟内可用内存率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
    content = "### {title}".format(title=title) + \
              "\n> #### **时间**: "  + current_time  + \
              "\n> #### **状态**: " + str(alarm['StateValue']) + \
              "\n> #### **告警名称**: " + str(alarm['AlarmName']) + \
              "\n> #### **告警描述**: " + str(alarm['AlarmDescription']) + \
              "\n> #### **实例名称**: " + str(alarm['Dimensions'][0]['Value']) + \
              "\n> #### **告警指标**: " + str(alarm['MetricName']) + \
              "\n> #### **告警阈值**: " + str(threshold)+ \
              "\n> #### **当前数值**: " + str(last_data_point_rounded) + \
              "\n> #### **告警原因**: " + str(new_state_reason)
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }

    content_redis = "时间: "+ current_time+",状态: " + str(alarm['StateValue'])+",告警名称: " + str(alarm['AlarmName'])+",告警描述: " + str(alarm['AlarmDescription'])+",告警指标: " + str(alarm['MetricName'])+",实例名称: " + str(alarm['Dimensions'][0]['Value']) +",当前指标: " + str(last_data_point_rounded) + ",告警原因:" + str(new_state_reason)
    
    template_param = {'awsmessage' : content_redis}  # 根据模板中的参数进行替换
    
    result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param)
    print(result)
    #request_redis = requests.post(url=api_test, data=json.dumps(msg), headers=headers).content.decode("utf8")
    request_juicefs = requests.post(url=api_juicefs, data=json.dumps(msg), headers=headers).content.decode("utf8")
   

def processKafka(alarm):
    threshold_match = re.search(r"threshold \((\d+\.\d+)\)", alarm['StateReason'])
    if threshold_match:
        threshold = threshold_match.group(1)
    matches = re.findall(r"\[(.*?)\]", alarm['StateReason'])
    if matches:
    # 从匹配的字符串中进一步提取浮点数
        data_points = re.findall(r"\d+\.\d+", matches[0])
        datapoints_count = len(data_points)  # 统计数据位点的个数
        rounded_numbers = [str(round(float(match), 1)) for match in data_points]
        if data_points:
        # 直接获取最后一个数据位点的数值
            last_data_point = float(data_points[-1])  # 获取最后一个数据位点的数值
            last_data_point_rounded = round(last_data_point, 1) #四舍五入
    new_state_reason = f"{datapoints_count}分钟内存储空间使用率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
    content = "### {title}".format(title=title) + \
              "\n> #### **时间**: "  + current_time  + \
              "\n> #### **状态**: " + str(alarm['StateValue']) + \
              "\n> #### **告警名称**: " + str(alarm['AlarmName']) + \
              "\n> #### **告警描述**: " + str(alarm['AlarmDescription']) + \
              "\n> #### **实例名称**: " + str(alarm['Dimensions'][0]['Value']) + \
              "\n> #### **告警指标**: " + str(alarm['MetricName']) + \
              "\n> #### **告警阈值**: " + str(threshold) + "%" + \
              "\n> #### **当前数值**: " + str(last_data_point_rounded) + "%" + \
              "\n> #### **告警原因**: " + str(new_state_reason)
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }

    content_kafka = "时间: "+ current_time+",状态: " + str(alarm['StateValue'])+",告警名称: " + str(alarm['AlarmName'])+",告警描述: " + str(alarm['AlarmDescription'])+",告警指标: " + str(alarm['MetricName'])+",实例名称: " + str(alarm['Dimensions'][0]['Value']) + ",当前指标: " + str(last_data_point_rounded) + ",告警原因:" + str(new_state_reason)
    
    template_param = {'awsmessage' : content_kafka}  # 根据模板中的参数进行替换
    
    result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param)
    print(result)
    request_kafka = requests.post(url=api_url, data=json.dumps(msg), headers=headers).content.decode("utf8")
    #request_kafka = requests.post(url=api_test, data=json.dumps(msg), headers=headers).content.decode("utf8")
    
def processBasic(alarm):
        dimensions = alarm['Dimensions']
        instanceId = ''
        path = ''
        instance_name = ''
        instance_ip = ''
        content_ec = ''
        
        for dimension in dimensions:
            if(dimension['Name'] == 'InstanceId'):
                instanceId = dimension['Value']
            
            if(dimension['Name'] == 'path'):
                path = dimension['Value']
                
        # 使用 describe_instances 函数获取实例信息
        response = ec2.describe_instances(InstanceIds=[instanceId])
        print(response)
        # 提取实例的名称（Name 标签）
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        print("实例 {instanceId} 的名称为: {instance_name}")
                    
                    
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ip = instance['PrivateIpAddress']
                print("实例 {instance_ip} 的名称为: {PrivateIpAddress}")
                
        ##判断为磁盘告警类型
        if  alarm['MetricName'] == 'disk_used_percent':
        ##优化告警内容代码
            threshold_match = re.search(r"threshold \((\d+\.\d+)\)", alarm['StateReason'])
            if threshold_match:
                threshold = threshold_match.group(1)
            matches = re.findall(r"\[(.*?)\]", alarm['StateReason'])
            if matches:
            # 从匹配的字符串中进一步提取浮点数
                data_points = re.findall(r"\d+\.\d+", matches[0])
                datapoints_count = len(data_points)  # 统计数据位点的个数
                rounded_numbers = [str(round(float(match), 1)) for match in data_points]
                if data_points:
            # 直接获取最后一个数据位点的数值
                    last_data_point = float(data_points[-1])  # 获取最后一个数据位点的数值
                    last_data_point_rounded = round(last_data_point, 1) #四舍五入
            new_state_reason = f"{datapoints_count}分钟内磁盘使用率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
            ##定义短信内容    
            content_ec = "时间: "+ current_time+",状态: " + str(alarm['StateValue'])+ ",告警名称:" + str(alarm['AlarmName']) +",告警描述: " + str(alarm['AlarmDescription'])+",告警指标: " + str(alarm['MetricName'])+",实例名称: " + str(instance_name) + ",实例IP: " + str(instance_ip) + ",磁盘目录: " + str(path) + ",当前指标: " + str(last_data_point_rounded) + ",告警原因: " + str(new_state_reason)
            content = "### {title}".format(title=title) + \
                  "\n> #### **时间**: "  + current_time  + \
                  "\n> #### **状态**: " + str(alarm['StateValue']) + \
                  "\n> #### **告警名称**: " + str(alarm['AlarmName']) + \
                  "\n> #### **告警描述**: " + str(alarm['AlarmDescription']) + \
                  "\n> #### **告警指标**: " + str(alarm['MetricName']) + \
                  "\n> #### **实例名称**: " + str(instance_name) + \
                  "\n> #### **实例ID**: " + str(instanceId) + \
                  "\n> #### **告警阈值**: " + str(threshold) + "%" + \
                  "\n> #### **当前数值**: " + str(last_data_point_rounded) + "%"  + \
                  "\n> #### **告警原因**: " + str(new_state_reason) + \
                  "\n> #### **实例IP**: " + str(instance_ip) + \
                  "\n> #### **磁盘目录**: " + str(path)
                  
        else:
        ##优化告警内容代码
            threshold_match = re.search(r"threshold \((\d+\.\d+)\)", alarm['StateReason'])
            if threshold_match:
                threshold = threshold_match.group(1)
            matches = re.findall(r"\[(.*?)\]", alarm['StateReason'])
            if matches:
            # 从匹配的字符串中进一步提取浮点数
                data_points = re.findall(r"\d+\.\d+", matches[0])
                datapoints_count = len(data_points)  # 统计数据位点的个数
                rounded_numbers = [str(round(float(match), 1)) for match in data_points]
                if data_points:
            # 直接获取最后一个数据位点的数值
                    last_data_point = float(data_points[-1])  # 获取最后一个数据位点的数值
                    last_data_point_rounded = round(last_data_point, 1) #四舍五入
            if alarm['AlarmName'].lower().find('mem')!=-1:
                new_state_reason = f"{datapoints_count}分钟内内存使用率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
            elif alarm['AlarmName'].lower().find('cpu')!=-1:
                new_state_reason = f"{datapoints_count}分钟内cpu使用率超过阈值{threshold}，分别为：" + ", ".join(rounded_numbers) + "。"
            else:
                new_state_reason = f"{datapoints_count}分钟内失败状态检查超过阈值{threshold}，请检查实例是否正常！"
            
            content_ec = "时间: "+ current_time+",状态: " + str(alarm['StateValue'])+",告警名称: " + str(alarm['AlarmName'])+",告警描述: " + str(alarm['AlarmDescription'])+",告警指标: " + str(alarm['MetricName'])+",实例名称: " + str(instance_name) + ",实例IP:" + str(instance_ip) + ",当前指标: " + str(last_data_point_rounded) + ",告警原因: " + str(new_state_reason)
            content = "### {title}".format(title=title) + \
                  "\n> #### **时间**: "  + current_time  + \
                  "\n> #### **状态**: " + str(alarm['StateValue']) + \
                  "\n> #### **告警名称**: " + str(alarm['AlarmName']) + \
                  "\n> #### **告警描述**: " + str(alarm['AlarmDescription']) + \
                  "\n> #### **实例名称**: " + str(instance_name) + \
                  "\n> #### **实例ID**: " + str(instanceId) + \
                  "\n> #### **实例IP**: " + str(instance_ip) + \
                  "\n> #### **告警指标**: " + str(alarm['MetricName']) + \
                  "\n> #### **告警阈值**: " + str(threshold) + "%" + \
                  "\n> #### **当前数值**: " + str(last_data_point_rounded)+ "%"  + \
                  "\n> #### **告警原因**: " + str(new_state_reason)
        
        print(content_ec)
                      
        msg = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            }
        }
    
        template_param = {'awsmessage' : content_ec}  # 根据模板中的参数进行替换
    
        
        if instance_name.find('中央研究院')!=-1:
            request_center = requests.post(url=api_url_center, data=json.dumps(msg), headers=headers).content.decode("utf8")
        elif instance_name.find('澳洲站_中后台_数据中台组_clickhouse')!=-1:
            result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number_wtl, template_param)
            print(result)
        elif instance_name.find('澳洲站_中后台_数据中台组_doris')!=-1:
            result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number_wtl, template_param)
            print(result)
        elif alarm['AlarmName'].find('Disk')!=-1:
        # request
            result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param)
            print(result)
            request = requests.post(url=api_url, data=json.dumps(msg), headers=headers).content.decode("utf8")
        
        elif alarm['AlarmName'].lower().find('mem')!=-1:
            result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param)
            print(result)
            request = requests.post(url=api_url, data=json.dumps(msg), headers=headers).content.decode("utf8")
        
        elif alarm['AlarmName'].lower().find('cpu')!=-1:
            result = send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param)
            print(result)
            request = requests.post(url=api_url, data=json.dumps(msg), headers=headers).content.decode("utf8")


##调用阿里短信服务推送函数
def send_sms(access_key_id, access_key_secret, sign_name, template_code, phone_number, template_param):
    # 阿里云短信接口请求地址
    url_ali = 'https://dysmsapi.aliyuncs.com/'
    
    # 构建请求参数
    params = {
        'AccessKeyId': access_key_id,
        'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        'Format': 'JSON',
        'SignatureMethod': 'HMAC-SHA1',
        'SignatureVersion': '1.0',
        'SignatureNonce': str(int(time.time() * 1000)),
        'Action': 'SendSms',
        'Version': '2017-05-25',
        'RegionId': 'cn-hangzhou',
        'PhoneNumbers': phone_number,
        'SignName': sign_name,
        'TemplateCode': template_code,
        'TemplateParam': json.dumps(template_param)
    }
    
    print(sign_name)
    
    # 对参数进行排序
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    
    # 构建待签名字符串
    #query_string = '&'.join([f'{p[0]}={requests.utils.quote(p[1])}' for p in sorted_params])
    #string_to_sign = 'GET&%2F&' + requests.utils.quote(query_string)
    query_string = '&'.join([f'{p[0]}={percentEncode(p[1])}' for p in sorted_params])
    string_to_sign = 'GET&%2F&' + percentEncode(query_string)    
    
    
    
    # 计算签名
    sign = base64.b64encode(hmac.new((access_key_secret + '&').encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1).digest()).decode('utf-8')
    
    # 添加签名到请求参数中
    params['Signature'] = sign
    
    print(params)
    # 发送 POST 请求
    response = requests.get(url_ali, params=params)
    
    return response.json()      
    
    

def lambda_handler(event, context):
    # 获取当前所有的告警
    print ("1")
    alarms = cloudwatch.describe_alarms(
            StateValue='ALARM'
        )['MetricAlarms']
        
    print(len(alarms))
    print(alarms)

    
# 构建告警信息
    for alarm in alarms:
        if isBasicAlarm(alarm['AlarmName']):
            processBasic(alarm)
        if isAuoraAlarm(alarm['AlarmName']):
            processAurora(alarm)
        if isKafkaAlarm(alarm['AlarmName']):
            processKafka(alarm)
        if isRedisAlarm(alarm['AlarmName']):
            processRedis(alarm)
        if isJuicefsAlarm(alarm['AlarmName']):
            processJuicefs(alarm)
        
        
    
    return {
        'statusCode': 200,
        'body': 'Alarm details sent to SNS topic.'
    }