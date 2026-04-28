resource "aws_sqs_queue" "main" {
  name                       = "${var.prefix}-queue"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400
}
