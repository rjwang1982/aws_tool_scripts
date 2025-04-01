import boto3
import urllib.parse
import os

# 配置 S3 Bucket 名称
BUCKET_NAME = "my-lambda01"
EXPIRATION = 3600  # 预签名 URL 有效期（秒）

# 获取用户要上传的本地文件路径
local_file_path = input("请输入要上传的文件路径: ").strip()

# 确保文件存在
if not os.path.isfile(local_file_path):
    print(f"❌ 错误: 文件 '{local_file_path}' 不存在！")
    exit(1)

# 提取文件名，确保 S3 保存的对象名与本地文件相同
file_name = os.path.basename(local_file_path)

# S3 存储路径（可选：你可以加上 `uploads/` 目录）
OBJECT_KEY = f"uploads/{file_name}"

# 创建 Boto3 会话
session = boto3.Session()
credentials = session.get_credentials()

# 获取 AWS 账户和 IAM 身份信息
sts_client = session.client("sts")
identity = sts_client.get_caller_identity()

# 获取 S3 Bucket 区域
s3_client = session.client("s3")
response = s3_client.get_bucket_location(Bucket=BUCKET_NAME)
region = response.get("LocationConstraint", "us-east-1")  # 默认 us-east-1

# 重新创建 S3 客户端，指定正确的区域
s3_client = session.client("s3", region_name=region)

# 生成 Pre-signed URL
presigned_url = s3_client.generate_presigned_url(
    "put_object",
    Params={"Bucket": BUCKET_NAME, "Key": OBJECT_KEY},
    ExpiresIn=EXPIRATION,
)

# 输出调试信息
print("=" * 50)
print("🔹 AWS Identity Information")
print(f"  - AWS Account ID  : {identity['Account']}")
print(f"  - Identity ARN    : {identity['Arn']}")
print("=" * 50)

print("\n🔹 S3 Bucket Information")
print(f"  - Bucket Name     : {BUCKET_NAME}")
print(f"  - Object Key      : {OBJECT_KEY}")
print(f"  - Bucket Region   : {region}")
print("=" * 50)

print("\n🔹 Generated Pre-signed URL")
print(f"{presigned_url}")
print("=" * 50)

# 解析 URL，避免 URL 编码问题
parsed_url = urllib.parse.urlparse(presigned_url)

# 生成 curl 命令，方便上传
curl_command = f'curl -X PUT -T "{local_file_path}" "{parsed_url.geturl()}"'
print("\n🔹 Upload with curl command:")
print(curl_command)
print("=" * 50)