# Cenário 3 — DynamoDB Throttle

## Descrição
A tabela DynamoDB é alterada de on-demand para provisioned com 1 WCU, causando `ProvisionedThroughputExceededException` ao receber múltiplas escritas simultâneas.

## Como reproduzir

1. Mudar tabela para provisioned com 1 WCU:
```bash
aws dynamodb update-table \
  --table-name troubleshooter-dev-table \
  --billing-mode PROVISIONED \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=1 \
  --region us-east-1
```

2. Enviar múltiplas mensagens rápidas:
```bash
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -s -X POST $(terraform output -raw api_url) \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"throttle test $i\"}" &
done
wait
```

3. Aguardar ~10 segundos para o Consumer processar.

## O que o agente encontra

### search_logs
```
[ERROR] request_id=xxx Falha ao gravar no DynamoDB: 
ProvisionedThroughputExceededException - The level of configured provisioned 
throughput for the table was exceeded.
```

### search_trace
```json
{
  "segments": [{
    "name": "troubleshooter-dev-ConsumerFunction",
    "status": "ERROR",
    "subsegments": [{
      "name": "DynamoDB",
      "status": "ERROR",
      "error": {
        "type": "ProvisionedThroughputExceededException"
      }
    }]
  }]
}
```

### search_lambda_config
```json
{
  "function_name": "troubleshooter-dev-ConsumerFunction",
  "environment_variables": {"TABLE_NAME": "troubleshooter-dev-table"}
}
```

### Causa raiz
Tabela DynamoDB com provisioned throughput de 1 WCU não suporta múltiplas escritas simultâneas.

### Correção sugerida
Mudar para on-demand (PAY_PER_REQUEST):
```bash
aws dynamodb update-table \
  --table-name troubleshooter-dev-table \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

Ou via Terraform em `dynamodb.tf`:
```hcl
resource "aws_dynamodb_table" "main" {
  billing_mode = "PAY_PER_REQUEST"
}
```

## Restaurar
```bash
cd infra
terraform apply -target=aws_dynamodb_table.main -auto-approve
```
