# Cenário 1 — Permission Denied (DynamoDB PutItem)

## Descrição
A Consumer Lambda não tem permissão `dynamodb:PutItem` no IAM Role, causando `AccessDeniedException` ao tentar gravar no DynamoDB.

## Como reproduzir

1. Remover permissão do Consumer role:
```bash
aws iam put-role-policy \
  --role-name troubleshooter-dev-consumer-role \
  --policy-name troubleshooter-dev-consumer-policy \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],"Resource":"arn:aws:sqs:us-east-1:969430605054:troubleshooter-dev-queue"},{"Effect":"Allow","Action":["xray:PutTraceSegments","xray:PutTelemetryRecords"],"Resource":"*"}]}'
```

2. Enviar mensagem:
```bash
curl -X POST https://hmpsvwpjz5.execute-api.us-east-1.amazonaws.com/dev/send \
  -H "Content-Type: application/json" \
  -d '{"message": "teste erro permissao"}'
```

3. Aguardar ~10 segundos para o Consumer processar e falhar.

## Dados reais do teste

| Campo | Valor |
|-------|-------|
| Producer RequestID | 415c63a5-a9df-4bbf-8ca1-a4c1ed6f4581 |
| Consumer RequestID | 87aa9a0b-206f-5a22-8c7f-f86013b27749 |
| Erro | AccessDeniedException: dynamodb:PutItem |

## Diagnóstico do agente

### search_logs
```
[ERROR] request_id=87aa9a0b-206f-5a22-8c7f-f86013b27749 Falha ao gravar no DynamoDB: 
AccessDeniedException - User: troubleshooter-dev-consumer-role is not authorized to 
perform: dynamodb:PutItem on resource: troubleshooter-dev-table
```

### search_lambda_config
```json
{
  "function_name": "troubleshooter-dev-ConsumerFunction",
  "role_arn": "arn:aws:iam::969430605054:role/troubleshooter-dev-consumer-role",
  "environment_variables": {"TABLE_NAME": "troubleshooter-dev-table"}
}
```

### Causa raiz identificada
IAM Role `troubleshooter-dev-consumer-role` não possui `dynamodb:PutItem` na tabela `troubleshooter-dev-table`.

### Correção sugerida
```json
{
  "Effect": "Allow",
  "Action": ["dynamodb:PutItem"],
  "Resource": "arn:aws:dynamodb:us-east-1:969430605054:table/troubleshooter-dev-table"
}
```

## Restaurar
```bash
cd infra
terraform apply -target=aws_iam_role_policy.consumer -auto-approve
```
