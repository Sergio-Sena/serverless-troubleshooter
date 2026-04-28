# Arquitetura — Serverless Troubleshooter

## Visão Geral

```
┌──────────────────────────────────────────────────────────────────┐
│                        AMAZON Q DEVELOPER                        │
│                     (Agente IA no VS Code)                       │
│                                                                  │
│  O agente recebe perguntas do usuário e usa as tools do MCP     │
│  Server para buscar dados reais da AWS antes de responder.      │
└────────────────────────────┬─────────────────────────────────────┘
                             │ MCP Protocol (stdio)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                         MCP SERVER                               │
│                      (Python + boto3)                            │
│                                                                  │
│  Tools expostas:                                                │
│  ┌─────────────────┐ ┌──────────────────┐ ┌──────────────────┐ │
│  │ get_logs        │ │ get_trace        │ │ get_lambda_config│ │
│  │ (CloudWatch)    │ │ (X-Ray)          │ │ (Lambda API)     │ │
│  └────────┬────────┘ └────────┬─────────┘ └────────┬─────────┘ │
└───────────┼───────────────────┼──────────────────────┼──────────┘
            │                   │                      │
            ▼                   ▼                      ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│  CloudWatch Logs │ │    AWS X-Ray     │ │    AWS Lambda API    │
│                  │ │                  │ │                      │
│ /aws/lambda/     │ │ Traces &         │ │ GetFunction          │
│   producer       │ │ Segments         │ │ GetPolicy            │
│   consumer       │ │ Service Map      │ │ ListEventSource      │
└──────────────────┘ └──────────────────┘ └──────────────────────┘
```

## Stack Serverless de Teste

A infra de teste simula um cenário real de processamento assíncrono:

```
┌──────────┐    invoke     ┌──────────────┐   send     ┌─────────┐
│  API     │──────────────>│   Producer   │──────────>│   SQS   │
│ Gateway  │               │   Lambda     │           │  Queue  │
└──────────┘               └──────────────┘           └────┬────┘
                                                           │
                                                      trigger
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │   Consumer   │
                                                    │   Lambda     │
                                                    └──────┬───────┘
                                                           │
                                                        put item
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │  DynamoDB    │
                                                    │  Table       │
                                                    └──────────────┘
```

### Cenários de Erro Planejados

| Cenário | Onde Falha | Causa | O que o Agente Deve Encontrar |
|---------|-----------|-------|-------------------------------|
| 1. Permission Denied | Consumer Lambda | Falta `sqs:ReceiveMessage` no role | Log de erro + sugestão de policy IAM |
| 2. DynamoDB Throttle | Consumer Lambda | Falta capacidade na tabela | Trace com latência alta + sugestão de auto-scaling |
| 3. Timeout | Producer Lambda | Timeout de 3s com payload grande | Log de timeout + sugestão de aumentar timeout/memória |
| 4. Dead Letter Queue | SQS → DLQ | Consumer falha 3x | Mensagens na DLQ + trace da falha original |

## Fluxo de Diagnóstico do Agente

```
Usuário: "Erro no RequestID abc-123"
    │
    ▼
1. Agente chama tool: get_logs(request_id="abc-123")
    │
    ├─> MCP Server busca no CloudWatch Logs
    ├─> Filtra por RequestID
    ├─> Retorna: logs com stack trace e erro
    │
    ▼
2. Agente identifica que é erro de Lambda e chama: get_trace(request_id="abc-123")
    │
    ├─> MCP Server busca no X-Ray
    ├─> Retorna: trace com segmentos, latências, erros por serviço
    │
    ▼
3. Agente identifica o serviço com falha e chama: get_lambda_config(function_name="consumer")
    │
    ├─> MCP Server retorna: runtime, timeout, memória, role ARN, env vars
    │
    ▼
4. Agente cruza os dados e responde:
    │
    └─> "A Lambda 'consumer' falhou com AccessDeniedException ao tentar
         sqs:ReceiveMessage. O role atual não tem essa permissão.
         Adicione esta policy: { ... }"
```

## Decisões Técnicas

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Linguagem do MCP Server | Python | boto3 é o SDK mais maduro para AWS |
| Transporte MCP | stdio | Amazon Q Developer suporta stdio nativamente |
| IaC | AWS SAM | Já domina SAM, deploy rápido de serverless |
| Agente | Amazon Q Developer | Já tem assinatura, suporta MCP, roda no IDE |
| Observabilidade | CloudWatch + X-Ray | Nativos da AWS, zero config extra com SAM |

## Segurança

- MCP Server roda local, usa credenciais AWS do perfil configurado (~/.aws/credentials)
- Permissões IAM do desenvolvedor: read-only em CloudWatch Logs, X-Ray e Lambda
- Nenhuma credencial hardcoded no MCP Server
- Stack de teste isolada com prefixo `troubleshooter-dev-`

### IAM Policy mínima para o MCP Server

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:FilterLogEvents",
        "logs:GetLogEvents",
        "logs:DescribeLogGroups",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetServiceGraph",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:GetPolicy",
        "lambda:ListEventSourceMappings"
      ],
      "Resource": "*"
    }
  ]
}
```
