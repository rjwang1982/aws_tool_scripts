import boto3
import sagemaker
from sagemaker.huggingface import HuggingFaceModel
from sagemaker.jumpstart.model import JumpStartModel
import json

# 获取 SageMaker 会话和角色
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()

def deploy_llama3_jumpstart():
    """使用 SageMaker JumpStart 部署 Llama 3"""
    try:
        # 创建 Llama 3 8B 模型
        model = JumpStartModel(model_id="meta-textgeneration-llama-3-8b")
        
        # 部署模型
        predictor = model.deploy(
            initial_instance_count=1,
            instance_type="ml.g5.xlarge",
            endpoint_name="llama3-8b-endpoint"
        )
        
        print(f"模型已部署到端点: {predictor.endpoint_name}")
        return predictor
        
    except Exception as e:
        print(f"JumpStart 部署失败: {e}")
        return None

def deploy_llama3_huggingface():
    """使用 Hugging Face 容器部署 Llama 3"""
    
    # 推理脚本
    inference_code = '''
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json

def model_fn(model_dir):
    """加载模型"""
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    return {"model": model, "tokenizer": tokenizer}

def predict_fn(data, model_dict):
    """推理函数"""
    model = model_dict["model"]
    tokenizer = model_dict["tokenizer"]
    
    prompt = data.get("inputs", "")
    max_length = data.get("parameters", {}).get("max_length", 100)
    
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            do_sample=True,
            temperature=0.7
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"generated_text": response}
'''
    
    # 保存推理脚本
    with open("inference.py", "w") as f:
        f.write(inference_code)
    
    # 创建 Hugging Face 模型
    huggingface_model = HuggingFaceModel(
        model_data="s3://huggingface-pytorch-inference-toolkit/llama3-8b/",  # 需要上传模型到 S3
        transformers_version="4.37.0",
        pytorch_version="2.1.0",
        py_version="py310",
        role=role,
        entry_point="inference.py"
    )
    
    try:
        # 部署模型
        predictor = huggingface_model.deploy(
            initial_instance_count=1,
            instance_type="ml.g5.xlarge",
            endpoint_name="llama3-hf-endpoint"
        )
        
        print(f"Hugging Face 模型已部署: {predictor.endpoint_name}")
        return predictor
        
    except Exception as e:
        print(f"Hugging Face 部署失败: {e}")
        return None

def test_endpoint(predictor):
    """测试端点"""
    test_prompt = "What is artificial intelligence?"
    
    try:
        response = predictor.predict({
            "inputs": test_prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7
            }
        })
        
        print(f"测试输入: {test_prompt}")
        print(f"模型输出: {response}")
        
    except Exception as e:
        print(f"测试失败: {e}")

def main():
    print("开始部署 Llama 3 模型...")
    
    # 方法1: 尝试 JumpStart 部署
    predictor = deploy_llama3_jumpstart()
    
    # 如果 JumpStart 失败，尝试 Hugging Face 方法
    if predictor is None:
        print("尝试 Hugging Face 部署方法...")
        predictor = deploy_llama3_huggingface()
    
    # 测试端点
    if predictor:
        test_endpoint(predictor)
    else:
        print("所有部署方法都失败了")

if __name__ == "__main__":
    main()
