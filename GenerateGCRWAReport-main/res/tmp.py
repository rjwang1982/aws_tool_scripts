#使用utf-8

import json
import sys

def parse_json(json_str):
    try:
        obj = json.loads(json_str)
        return obj
    except json.JSONDecodeError as e:
        print("解析JSON时发生错误：")
        print("错误信息：", e)
        return None

#load json from file name
def load_json_from_file(file_name):
    try:
        with open(file_name, 'r') as f:
            json_str = f.read()
            return parse_json(json_str)
    except Exception as e:
        print("读取文件时发生错误：")
        print("错误信息：", e)
        return None

if __name__ == "__main__":
    json_obj = load_json_from_file("watoolmap.json")
    if json_obj is not None:
        print(json_obj)
    else:
        print("无法解析JSON")
