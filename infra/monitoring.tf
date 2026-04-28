# CloudWatch Log Groups com retenção controlada

resource "aws_cloudwatch_log_group" "producer" {
  name              = "/aws/lambda/${aws_lambda_function.producer.function_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "consumer" {
  name              = "/aws/lambda/${aws_lambda_function.consumer.function_name}"
  retention_in_days = var.log_retention_days
}
