import json
import boto3
from botocore.exceptions import ClientError
from multiprocessing import Process, Queue
import time
import pandas as pd
import res.ServicescreenerToGCRKeyWorkloadMapping as ServicescreenerToGCRKeyWorkloadMapping
import sys
import os


questionNeedHumanCheck=[]
def is_valid_aws_region(region):
    # List of valid AWS regions
    valid_regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'ap-south-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
        'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 'eu-central-1',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1',
        'sa-east-1'
    ]
    return region in valid_regions


# Load JSON files
def load_json(file_path):
    with open(file_path, 'r') as file:
        json_str = file.read()
        return json.loads(json_str)

SS_Finding_fix = load_json("res/SS_Finding_fix.json")

def import_custom_lens(client, lens_filename):
    # Create a custom lens from upload json file
    try:
        with open(lens_filename, 'r') as file:
            lens_data = json.load(file)
            lens_name = lens_data['name']
            
            # Check if lens already exists
                # List all custom lenses to find if lens exists
        existing_lens = client.list_lenses(
            LensType='CUSTOM_SELF',
            LensName = lens_name
        )
        if len(existing_lens['LensSummaries']) > 0:
            LensAlias = existing_lens['LensSummaries'][0]['LensArn']
            print("Custom lens %s exist" % str(lens_name))
            # Lens exists, update it
            response = client.import_lens(
                JSONString=json.dumps(lens_data),
                LensAlias=LensAlias
            )
            #print (response)
            print("Custom lens %s updated" % str(lens_name))
        else:
            response = client.import_lens(
                JSONString=json.dumps(lens_data),
            )
            #print(response)
            LensAlias = response['LensArn']
            print("Custom lens %s created" % str(lens_name))
            #print(response)
        #publish to major version,use the format like 2024100711
        CurrentTime = time.strftime('%Y%m%d%H%M')
        LensVersion = str(CurrentTime)
        response = client.create_lens_version(
                LensAlias=LensAlias,
                LensVersion=LensVersion,
                IsMajorVersion=True,
        )
        print("Custom lens %s published" % str(lens_name))
        #print(response)
        return response['LensArn']              
    except BaseException as e:
        print(f"Error creating custom lens: {e.__traceback__.tb_lineno},{str(e)}")
        exit(1)
    
# Create a workload in the Well-Architected Tool
def create_workload(client, workload_name, lens_arn, region):
    try:
        response = client.create_workload(
            WorkloadName=workload_name,
            Lenses=[lens_arn],
            Description='Workload created for custom lens review',
            Environment='PRODUCTION', # Adjust as necessary
            AwsRegions=[region],
            ReviewOwner='owner@example.com'  # Replace with actual owner email
        )
        return response['WorkloadId']
    except ClientError as e:
        print(f"Error creating workload: {e.__traceback__.tb_lineno},{str(e)}")
        return None

# Update workload with answers from map.json
def update_workload(client, workload_id, answers,lens_arn):
    for pillar in answers.keys():
        for question in answers[pillar]:
            try:
                response = client.update_answer(
                    WorkloadId=workload_id,
                    LensAlias=lens_arn,
                    QuestionId=question['QuestionId'],
                    SelectedChoices=question['SelectedChoices'],
                    Notes=question.get('Notes', '')
                )
                #print(f"Answer updated for question {question['QuestionId']}")
            except ClientError as e:
                #print(f"Error updating answer: {e.__traceback__.tb_lineno}, {str(e)}")
                print(f"Failed to update answer for question {question['QuestionId']},{question['SelectedChoices']},{question.get('Notes', '')}")
                return None

# Generate a report for the workload
def generate_report(client, workload_id, lens_arn):
    try:
        report_response = client.generate_report(
            WorkloadId=workload_id,
            LensArn=lens_arn,
            ReportFormat='PDF'  # Choose desired format (PDF or CSV)
        )
        return report_response['ReportId']
    except ClientError as e:
        print(f"Error generating report: {e}")
        return None

def has_intersection(list1, list2):
    intersection = [item for item in list1 if item in list2]
    return intersection

def generate_wa_qa_choice(pillar,ss_result,result_quene):
    pillar_answer = []
    for question in pillar["questions"]:
        choiceId = []
        notes = []
        unselect_choice = []
        choiceNeedHumanCheck = []
        finds_to_note = ""
        need_discussion = ""
        fix_reason_string = ""
        for choice in question['choices']:
            if choice["id"] in ["option_no"]:
                continue
            if choice["ServiceScreenerCheck"][0] == "humancheck":
                choiceNeedHumanCheck.append([choice['title'],choice['NeedHumanCheck']])
                if question['title'] not in questionNeedHumanCheck:
                    questionNeedHumanCheck.append(question['title'])
                continue

            ServiceScreenerCheck = choice["ServiceScreenerCheck"]
            sheets = {}
            for item in ServiceScreenerCheck:
                service, check = item.split('.')
                if service not in sheets:
                    sheets[service] = []
                sheets[service].append(check)
            finds_empty = True

            for service in sheets.keys():
                df = pd.read_excel(ss_result, sheet_name=service.upper())
                finds = df[df["Check"].isin(sheets[service])]
                real_findings = finds['Check'].unique().tolist()
                if finds.empty:
                    continue  
                else:
                    finds_empty = False
                    if choice['id'] not in unselect_choice:
                        unselect_choice.append(choice['id'])
                    ## 加上常规发现及解决方案
                    finds_to_note = finds_to_note + choice['title'] +" 不符合的配置:" + service + ":" + ",".join(map(str,real_findings)) + "\n"
                    fix_reason = []
                    if service in SS_Finding_fix.keys():
                        for finding_fix_reason in SS_Finding_fix[service]:
                            has_finding_fix = has_intersection(real_findings,finding_fix_reason['findings_name'])
                            if len(has_finding_fix) > 0:
                                finding_fix_reason['findings_name'] = has_finding_fix
                                fix_reason.append(finding_fix_reason)
                    
                    for i in fix_reason:
                        fix_reason_string = fix_reason_string + "检查项："+ ",".join(map(str,i['findings_name'])) + "\n" + "解释:" + i["reason"] + "\n" + "建议的操作:" + i["suggest_action"] + "\n"                   
            
            if finds_empty is True:
                # 反选，只有ss结果里没有任何匹配的发现，才能选择该选项
                if choice['id'] not in choiceId:
                    choiceId.append(choice['id'])
        if question['IsQuestionNeedHumanCheck'].lower().strip() == 'no' and len(unselect_choice) == (len(question['choices'])): 
            #如果该question可以全部通过ss自动话填写，且选项全部有ss结果Findings，则选择option no，代表全部命中
                choiceId.append("option_no")
        if len(choiceNeedHumanCheck) > 0:
            need_discussion = "以下选项需要和客户讨论:" +"\n" + ",".join(map(str,choiceNeedHumanCheck))+ "\n"

        answers = {
            'QuestionId': (question['id']),
            'SelectedChoices': choiceId,
            'Notes': 'Service Screener Check: ' + finds_to_note + fix_reason_string + need_discussion
        }

        pillar_answer.append(answers)
    print(pillar['name'] + "支柱以下问题有选项需要与客户讨论：")
    for question in questionNeedHumanCheck:
        print(question) 

    result_quene.put((pillar['name'], pillar_answer))
                
                
def generate_answers_data(watoolmapfile,ss_result):
    pillars = load_json(watoolmapfile)
    qa_answer = {}
    processes = []
    max_processes = 2
    result_queue = Queue()
    for i in range(0, len(pillars["pillars"]), max_processes):
        batch = pillars["pillars"][i:i+max_processes]
        for pillar in batch:
            p = Process(target=generate_wa_qa_choice, args=(pillar,ss_result,result_queue))
            processes.append((p, pillar['name']))
            p.start()
        # 等待当前批次的所有进程完成
        for p in processes:
            p[0].join()  # 等待进程结束

        # 从队列中获取结果并存入 qa_answer 字典
        while not result_queue.empty():
            pillar_name, answer = result_queue.get()
            #print(pillar_name, answer)
            qa_answer[pillar_name] = answer
        processes = []

    #print(qa_answer)
    return qa_answer


def main():
    # Get region from user input
    region = input("Please enter AWS region (e.g. us-west-2): ")
    if not is_valid_aws_region(region):
        print(f"Error: {region} is not a valid AWS region")
        exit(1)

    # mapping with gcr wa question with service screener findings 
    watoolmapfile = ServicescreenerToGCRKeyWorkloadMapping.execl_mapping_to_json('res/GCR WAR key workload Mapping with Servicescreener20250210.xlsx')
    client = boto3.client('wellarchitected',region_name = region )
    lens_filename="res/GCR WAR key workload custom lens.json"

    # Initialize the AWS Well-Architected Tool client
    if len(sys.argv) < 2:
        print("Error: 请提供service screener的检查结果")
        sys.exit(1)
        
    ss_zip_file = sys.argv[1]
    if not ss_zip_file.endswith('.zip'):
        print("Error: Input file must be a zip file")
        sys.exit(1)

    if not os.path.exists(ss_zip_file):
        print(f"Error: File {ss_zip_file} does not exist")
        sys.exit(1)

    try:
        import zipfile
        zip_dir = os.path.splitext(ss_zip_file)[0]
        with zipfile.ZipFile(ss_zip_file, 'r') as zip_ref:
            zip_ref.extractall(zip_dir)
    except zipfile.BadZipFile:
        print(f"Error: {ss_zip_file} is not a valid zip file")
        sys.exit(1)
    except Exception as e:
        print(f"Error extracting zip file: {str(e)}")
        sys.exit(1)
    ss_dir = zip_dir + "/aws"
    if not os.path.exists(ss_dir):
        print(f"Error: Directory {ss_dir} could not be created")
        sys.exit(1)  

    # Get subdirectories that start with numbers
    account_dirs = [d for d in os.listdir(ss_dir) if os.path.isdir(os.path.join(ss_dir, d)) and d[0].isdigit()]
    if not account_dirs:
        print(f"Error: No account directories found in {ss_dir}")
        sys.exit(1)
    
    # Get workload name from user input
    workload_name = input("请输入workload名称： ")        
    
    for account in account_dirs:
        ss_result = os.path.join(ss_dir, account, "workItem.xlsx")
    
        answers_data = generate_answers_data(watoolmapfile,ss_result)

        # Create a custom lens (assuming you already have the lens ARN)
        lens_arn = import_custom_lens(client,lens_filename=lens_filename)  

        workload_name_with_accountid = workload_name + "_" + account
        workload_id = create_workload(client, workload_name_with_accountid, lens_arn, region)
        

        if workload_id:
            print(f"Workload created successfully: {workload_id}")
            # Update the workload with answers from map.json
            update_response = update_workload(client, workload_id, answers_data,lens_arn)

        

if __name__ == "__main__":
    main()
