# --- HTTP API ---
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.prefix}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "dev" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "dev"
  auto_deploy = true
}

# --- Integração com Producer Lambda ---
resource "aws_apigatewayv2_integration" "producer" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.producer.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "send" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /send"
  target    = "integrations/${aws_apigatewayv2_integration.producer.id}"
}

# --- Permissão para API Gateway invocar Lambda ---
resource "aws_lambda_permission" "apigw_producer" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.producer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
