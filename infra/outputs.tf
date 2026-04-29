output "api_url" {
  description = "URL do API Gateway para POST /send"
  value       = "${aws_apigatewayv2_stage.dev.invoke_url}/send"
}

output "producer_function_name" {
  description = "Nome da Lambda Producer"
  value       = aws_lambda_function.producer.function_name
}

output "consumer_function_name" {
  description = "Nome da Lambda Consumer"
  value       = aws_lambda_function.consumer.function_name
}

output "queue_url" {
  description = "URL da fila SQS"
  value       = aws_sqs_queue.main.url
}

output "queue_arn" {
  description = "ARN da fila SQS"
  value       = aws_sqs_queue.main.arn
}

output "table_name" {
  description = "Nome da tabela DynamoDB"
  value       = aws_dynamodb_table.main.name
}

output "producer_role_arn" {
  description = "ARN do IAM Role da Producer"
  value       = aws_iam_role.producer.arn
}

output "consumer_role_arn" {
  description = "ARN do IAM Role da Consumer"
  value       = aws_iam_role.consumer.arn
}

output "github_actions_role_arn" {
  description = "ARN do IAM Role para GitHub Actions (OIDC)"
  value       = aws_iam_role.github_actions.arn
}

output "site_url" {
  description = "URL do site"
  value       = "https://troubleshooter.${var.domain_name}"
}

output "site_bucket" {
  description = "Nome do bucket S3 do site"
  value       = aws_s3_bucket.site.id
}

output "cloudfront_distribution_id" {
  description = "ID da distribuição CloudFront"
  value       = aws_cloudfront_distribution.site.id
}
