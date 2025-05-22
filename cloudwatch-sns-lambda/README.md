# cloudwatch-sns-lambda

该项目基于 **AWS Lambda + CloudWatch + SNS + 钉钉 Webhook**，实现告警自动收集并通过多通道通知。

---

## 📦 项目结构

```plain
cloudwatch-sns-lambda/
├── lambda/
│   └── alarm_checker.py     # Lambda 函数源码（支持钉钉签名）
├── main.tf                  # Terraform 主配置
├── variables.tf             # 变量配置（可扩展）
└── lambda.zip               # 打包上传的 Lambda ZIP 文件（自动生成）
```

---

## 🚀 快速部署

### 前提条件

- 已安装并配置 Terraform
- 已配置好 AWS CLI 并具备部署权限
- 钉钉机器人已启用“加签安全设置”

### 步骤

```bash
unzip cloudwatch-sns-lambda.zip
cd cloudwatch-sns-lambda
terraform init
terraform apply
```

---

## ⚙️ 环境变量配置

```hcl
  environment {
    variables = {
      DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=your_token"
      DINGTALK_SECRET  = "your_signing_secret"
    }
  }
```

---

## 🧠 功能说明

- 拉取所有 `ALARM` 状态的 CloudWatch 告警
- 每条告警同时发送到 SNS + 钉钉 Webhook（签名验证）

---

## 🔄 可选触发方式（建议）

```hcl
resource "aws_cloudwatch_event_rule" "every_5_minutes" {
  name        = "run-every-5-mins"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule = aws_cloudwatch_event_rule.every_5_minutes.name
  target_id = "cloudwatch_alarm_checker"
  arn = aws_lambda_function.alarm_checker.arn
}

resource "aws_lambda_permission" "allow_events" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alarm_checker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_5_minutes.arn
}
```

---

## 🛡️ 权限说明

自动附加 `AWSLambdaBasicExecutionRole`，可手动扩展 CloudWatch / SNS 权限。

---

## 📞 联系我们 / 问题反馈

需要支持企业微信、飞书、S3 告警记录、容错机制等请联系维护者。
