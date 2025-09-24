# Llama 3 SageMaker 部署指南

## 前置条件

1. **AWS 账户配置**
   ```bash
   aws configure
   ```

2. **安装依赖**
   ```bash
   pip install -r llama3_requirements.txt
   ```

3. **IAM 权限**
   确保你的 IAM 用户/角色有以下权限：
   - SageMaker 完整访问权限
   - S3 读写权限
   - IAM PassRole 权限

## 部署步骤

### 方法1: SageMaker JumpStart (推荐)

```python
python llama3_sagemaker_deploy.py
```

### 方法2: 手动部署

1. **下载 Llama 3 模型**
   ```bash
   # 从 Hugging Face 下载
   git lfs clone https://huggingface.co/meta-llama/Llama-3-8B-Instruct
   ```

2. **上传到 S3**
   ```bash
   aws s3 cp Llama-3-8B-Instruct/ s3://your-bucket/llama3-8b/ --recursive
   ```

3. **修改脚本中的 S3 路径**
   ```python
   model_data="s3://your-bucket/llama3-8b/"
   ```

## 实例类型选择

| 模型大小 | 推荐实例类型 | GPU 内存 | 成本/小时 |
|---------|-------------|----------|----------|
| 7B      | ml.g5.xlarge | 24GB     | ~$1.00   |
| 13B     | ml.g5.2xlarge | 48GB    | ~$2.00   |
| 70B     | ml.p4d.24xlarge | 320GB | ~$32.00  |

## 测试端点

```python
import boto3

runtime = boto3.client('sagemaker-runtime')

response = runtime.invoke_endpoint(
    EndpointName='llama3-8b-endpoint',
    ContentType='application/json',
    Body=json.dumps({
        "inputs": "What is machine learning?",
        "parameters": {
            "max_length": 200,
            "temperature": 0.7
        }
    })
)

result = json.loads(response['Body'].read().decode())
print(result['generated_text'])
```

## 清理资源

```python
# 删除端点
predictor.delete_endpoint()

# 删除模型
predictor.delete_model()
```

## 注意事项

1. **成本控制**: 及时删除不用的端点
2. **模型许可**: 确保遵守 Llama 3 的使用许可
3. **安全**: 不要在生产环境中暴露端点
4. **监控**: 设置 CloudWatch 告警监控成本和性能

## 故障排除

### 常见错误

1. **权限不足**
   ```
   解决方案: 检查 IAM 角色权限
   ```

2. **实例容量不足**
   ```
   解决方案: 更换区域或实例类型
   ```

3. **模型加载失败**
   ```
   解决方案: 检查 S3 路径和模型文件完整性
   ```
