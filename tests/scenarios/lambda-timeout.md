# Cenário 2 — Lambda Timeout

## Descrição
A Producer Lambda tem timeout configurado muito baixo (1s), causando `Task timed out` quando o cold start + envio para SQS excede o limite.

## Como reproduzir

1. Reduzir timeout para 1 segundo:
```bash
aws lambda update-function-configuration \
  --function-name troubleshooter-dev-ProducerFunction \
  --timeout 1 --region us-east-1
```

2. Forçar cold start (aguardar ~15 min de inatividade ou alterar env var):
```bash
aws lambda update-function-configuration \
  --function-name troubleshooter-dev-ProducerFunction \
  --environment "Variables={QUEUE_URL=$(terraform output -raw queue_url),FORCE_COLD_START=$(date +%s)}"
```

3. Enviar mensagem imediatamente:
```bash
curl -X POST $(terraform output -raw api_url) \
  -H "Content-Type: application/json" \
  -d '{"message": "teste timeout"}'
```

## O que o agente encontra

### search_logs
```
REPORT RequestId: xxx Duration: 1000.00 ms Billed Duration: 1000 ms
Task timed out after 1.00 seconds
```

### search_lambda_config
```json
{
  "function_name": "troubleshooter-dev-ProducerFunction",
  "timeout_seconds": 1,
  "memory_mb": 128
}
```

### Causa raiz
Timeout de 1 segundo é insuficiente para cold start (init ~430ms) + envio SQS (~120ms).

### Correção sugerida
Aumentar timeout para 10s e/ou memória para 256MB (mais memória = mais CPU = init mais rápido):
```bash
aws lambda update-function-configuration \
  --function-name troubleshooter-dev-ProducerFunction \
  --timeout 10 --memory-size 256
```

Ou via Terraform em `lambda.tf`:
```hcl
resource "aws_lambda_function" "producer" {
  timeout     = 10
  memory_size = 256
}
```

## Restaurar
```bash
cd infra
terraform apply -target=aws_lambda_function.producer -auto-approve
```
