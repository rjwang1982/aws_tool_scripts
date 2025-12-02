provider "aws" {
  region = "cn-northwest-1"
}

resource "aws_iam_role" "lambda_exec" {
  name = "cloudwatch_alarm_lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "alarm_checker" {
  function_name = "cloudwatch_alarm_checker"
  handler       = "alarm_checker.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "${path.module}/lambda.zip"

  environment {
    variables = {
      DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=your_token"
      DINGTALK_SECRET  = "your_signing_secret"
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic]
}

# 可选定时触发器
resource "aws_cloudwatch_event_rule" "every_5_minutes" {
  count               = var.enable_schedule ? 1 : 0
  name                = "run-every-5-mins"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  count     = var.enable_schedule ? 1 : 0
  rule      = aws_cloudwatch_event_rule.every_5_minutes[0].name
  target_id = "cloudwatch_alarm_checker"
  arn       = aws_lambda_function.alarm_checker.arn
}

resource "aws_lambda_permission" "allow_events" {
  count         = var.enable_schedule ? 1 : 0
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alarm_checker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_5_minutes[0].arn
}