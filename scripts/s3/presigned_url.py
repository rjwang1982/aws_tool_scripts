import boto3
import urllib.parse

# 配置 S3 Bucket 名称和上传文件路径
BUCKET_NAME = "my-lambda01"
OBJECT_KEY = "uploads/example.txt"
EXPIRATION = 3600  # 预签名 URL 有效期（秒）

# 创建 Boto3 会话，支持 IAM 临时凭证
session = boto3.Session()
credentials = session.get_credentials()

# 获取当前身份信息
sts_client = session.client("sts")
identity = sts_client.get_caller_identity()

# 获取 IAM 用户或角色信息
iam_client = session.client("iam")
try:
    user = iam_client.get_user()
    iam_identity = user["User"]["UserName"]
    identity_type = "IAM User"
except iam_client.exceptions.NoSuchEntityException:
    iam_identity = identity["Arn"].split("/")[-1]  # 提取 Role 名称
    identity_type = "IAM Role"

# 获取存储桶所在的区域
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
print(f"  - Identity Type   : {identity_type}")
print(f"  - Identity Name   : {iam_identity}")
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

# 生成 curl 命令，方便调试
curl_command = f'curl -X PUT -T "README.md" "{parsed_url.geturl()}"'
print("\n🔹 Test with curl command:")
print(curl_command)
print("=" * 50)