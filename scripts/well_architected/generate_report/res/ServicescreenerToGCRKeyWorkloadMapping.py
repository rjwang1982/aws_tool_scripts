import pandas as pd
import json

def execl_mapping_to_json(mapping_execl_file):
    # 读取 Excel 文件
    df = pd.read_excel(mapping_execl_file)

    # 初始化结果字典
    result = {"pillars": []}

    # 遍历每一行数据
    for _, row in df.iterrows():
        pillar_name = row['pillar']
        pillar_id = row['pillar_id']
        question_title = row['question']
        IsQuestionNeedHumanCheck = row['IsQuestionNeedHumanCheck']
        ServiceScreenerMapping = row['ServiceScreenerMapping'] 
        IsNeedHuman = row['IsNeedHuman']
        question_id=row['question_id']
        choice_id=row['choice_id']
        choice_title=row['choice']
        helpresource=row['helpresource']
        # 如果 pillar_name 不存在，则创建新的 pillar
        if not any(p['name'] == pillar_name for p in result['pillars']):
            result['pillars'].append({'name': pillar_name, 'questions': []})
        


        # 查找对应 pillar
        pillar = next((p for p in result['pillars'] if p['name'] == pillar_name), None)
        if not pillar:
            pillar = { 'id':pillar_id,'name': pillar_name,'questions': []}
            result['pillars'].append(pillar)

        # 查找对应 question
        question = next((q for q in pillar['questions'] if q['title'] == question_title and q['id'] == question_id), None)
        if not question:
            question = {'title': question_title, 'id': question_id, 'IsQuestionNeedHumanCheck':IsQuestionNeedHumanCheck,'choices': []}
            pillar['questions'].append(question)

        # 添加 choice
        if choice_id == 'option_no':
            continue
        else:
            if type(ServiceScreenerMapping) is str and ServiceScreenerMapping.startswith('[') and ServiceScreenerMapping.endswith(']') :
                #print(ServiceScreenerMapping)
                ServiceScreenerCheck = json.loads(ServiceScreenerMapping)
                choice = {'title': choice_title, 'id': choice_id, 'ServiceScreenerCheck':ServiceScreenerCheck,'helpfulResource': {'displayText': helpresource}}
            else:
                choice = {'title': choice_title, 'id': choice_id, 'ServiceScreenerCheck':["humancheck"],'NeedHumanCheck':IsNeedHuman,'helpfulResource': {'displayText': helpresource}}

            question['choices'].append(choice)

    try:
        filename = 'tmp.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f,
                    ensure_ascii=False,
                    indent=4
            )
    except Exception as e:
        print(f"Error saving JSON file: {e}")
    return filename


# 调用示例
#execl_mapping_to_json('GCR WAR key workload Mapping with Servicescreener.xlsx')

