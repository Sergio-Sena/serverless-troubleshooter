# ============================================================
# Data: empacota código das Lambdas em ZIP
# ============================================================

data "archive_file" "producer" {
  type        = "zip"
  source_dir  = "${path.module}/src/producer"
  output_path = "${path.module}/.build/producer.zip"
}

data "archive_file" "consumer" {
  type        = "zip"
  source_dir  = "${path.module}/src/consumer"
  output_path = "${path.module}/.build/consumer.zip"
}

# ============================================================
# IAM — Producer Role (least privilege)
# ============================================================

resource "aws_iam_role" "producer" {
  name = "${var.prefix}-producer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "producer" {
  name = "${var.prefix}-producer-policy"
  role = aws_iam_role.producer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "producer_logs" {
  role       = aws_iam_role.producer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ============================================================
# IAM — Consumer Role (least privilege)
# ============================================================

resource "aws_iam_role" "consumer" {
  name = "${var.prefix}-consumer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "consumer" {
  name = "${var.prefix}-consumer-policy"
  role = aws_iam_role.consumer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.main.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "consumer_logs" {
  role       = aws_iam_role.consumer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ============================================================
# Lambda — Producer
# ============================================================

resource "aws_lambda_function" "producer" {
  function_name    = "${var.prefix}-ProducerFunction"
  role             = aws_iam_role.producer.arn
  handler          = "app.handler"
  runtime          = var.lambda_runtime
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.producer.output_path
  source_code_hash = data.archive_file.producer.output_base64sha256

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.main.url
    }
  }

  tracing_config {
    mode = "Active"
  }
}

# ============================================================
# Lambda — Consumer
# ============================================================

resource "aws_lambda_function" "consumer" {
  function_name    = "${var.prefix}-ConsumerFunction"
  role             = aws_iam_role.consumer.arn
  handler          = "app.handler"
  runtime          = var.lambda_runtime
  timeout          = 30
  memory_size      = 128
  filename         = data.archive_file.consumer.output_path
  source_code_hash = data.archive_file.consumer.output_base64sha256

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.main.name
    }
  }

  tracing_config {
    mode = "Active"
  }
}

# ============================================================
# SQS → Consumer (Event Source Mapping)
# ============================================================

resource "aws_lambda_event_source_mapping" "sqs_consumer" {
  event_source_arn = aws_sqs_queue.main.arn
  function_name    = aws_lambda_function.consumer.arn
  batch_size       = 1
  enabled          = true
}
