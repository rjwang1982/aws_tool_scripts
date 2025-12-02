import pandas as pd
import json

def json_to_excel(input_json, output_excel):
    with open(input_json, 'r') as f:
        data = json.load(f)
    # 提取数据
    rows = []
    for pillar in data['pillars']:
        name = pillar['name']
        for question in pillar['questions']:
            for choice in question['choices']:
                rows.append({
                    'pillar_id': pillar['id'],
                    'pillar': name,
                    'question_id':question['id'],
                    'question': question['title'],
                    'description':question['description'],
                    'choice': choice['title'],
                    'choice_id':choice['id'],
                    'helpresource': choice['helpfulResource']['displayText']
                })

    # 创建 DataFrame
    df = pd.DataFrame(rows)

    # 保存为 Excel 文件
    #df.to_excel('output.xlsx', index=False)
                
        #print   (column)
    df.to_excel(output_excel, index=False)

    

# 调用示例
json_to_excel('GCR WAR key workload custom lens.json', 'GCR WAR key workload custom lens.xlsx')
