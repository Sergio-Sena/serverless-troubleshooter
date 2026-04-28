# Especificação do MCP Server — Serverless Troubleshooter

## Visão Geral

O MCP Server expõe 3 tools via protocolo MCP (stdio) que permitem ao Amazon Q Developer consultar dados de observabilidade da AWS em tempo real.

```
Transporte: stdio
Linguagem:  Python 3.11
SDK:        mcp (PyPI)
AWS SDK:    boto3
```

---

## Configuração no Amazon Q Developer

O Amazon Q Developer suporta MCP Servers configurados no arquivo `~/.aws/amazonq/mcp.json`:

```json
{
  "mcpServers": {
    "serverless-troubleshooter": {
      "command": "python",
      "args": ["C:/Projetos Git/Proejto com MCP/mcp-server/server.py"],
      "env": {
        "AWS_PROFILE": "troubleshooter-dev",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

> **Nota:** Ajustar o path e o AWS_PROFILE conforme seu ambiente. O MCP Server herda as credenciais do perfil AWS configurado.

---

## Tool 1: get_logs

**Propósito:** Buscar logs de uma invocação Lambda pelo RequestID.

**Input Schema:**
```json
{
  "request_id": {
    "type": "string",
    "description": "AWS Lambda Request ID (ex: abc123-def456-ghi789)",
    "required": true
  },
  "log_group": {
    "type": "string",
    "description": "Nome do log group. Se omitido, busca em todos os log groups com prefixo /aws/lambda/troubleshooter-",
    "required": false
  },
  "minutes_ago": {
    "type": "integer",
    "description": "Janela de tempo em minutos para buscar logs. Default: 60",
    "required": false,
    "default": 60
  }
}
```

**Output (sucesso):**
```json
{
  "request_id": "abc123-def456",
  "log_group": "/aws/lambda/troubleshooter-dev-ConsumerFunction",
  "log_count": 5,
  "events": [
    {
      "timestamp": "2025-01-15T10:30:00Z",
      "level": "START",
      "message": "START RequestId: abc123-def456 Version: $LATEST"
    },
    {
      "timestamp": "2025-01-15T10:30:01Z",
      "level": "ERROR",
      "message": "[ERROR] AccessDeniedException: User: arn:aws:sts::123456:assumed-role/ConsumerRole is not authorized to perform: sqs:ReceiveMessage on resource: arn:aws:sqs:us-east-1:123456:troubleshooter-queue"
    },
    {
      "timestamp": "2025-01-15T10:30:01Z",
      "level": "END",
      "message": "END RequestId: abc123-def456"
    }
  ]
}
```

**Output (não encontrado):**
```json
{
  "request_id": "abc123-def456",
  "log_count": 0,
  "events": [],
  "message": "Nenhum log encontrado para este RequestID nos últimos 60 minutos."
}
```

**Implementação (boto3):**
```python
# API usada: CloudWatch Logs
client = boto3.client('logs')

# 1. Listar log groups (se não especificado)
client.describe_log_groups(logGroupNamePrefix="/aws/lambda/troubleshooter-")

# 2. Filtrar eventos pelo RequestID
client.filter_log_events(
    logGroupName=log_group,
    filterPattern=f'"{request_id}"',
    startTime=start_time_ms,
    endTime=end_time_ms
)
```

---

## Tool 2: get_trace

**Propósito:** Buscar trace do X-Ray para uma invocação, mostrando o caminho da requisição entre serviços.

**Input Schema:**
```json
{
  "request_id": {
    "type": "string",
    "description": "AWS Lambda Request ID para buscar o trace correspondente",
    "required": true
  }
}
```

**Output (sucesso):**
```json
{
  "request_id": "abc123-def456",
  "trace_id": "1-abc-def",
  "duration_ms": 1523,
  "status": "ERROR",
  "segments": [
    {
      "name": "API Gateway",
      "duration_ms": 1520,
      "status": "OK",
      "annotations": {}
    },
    {
      "name": "ProducerFunction",
      "duration_ms": 450,
      "status": "OK",
      "subsegments": [
        {
          "name": "SQS SendMessage",
          "duration_ms": 120,
          "status": "OK"
        }
      ]
    },
    {
      "name": "ConsumerFunction",
      "duration_ms": 1050,
      "status": "ERROR",
      "error": {
        "type": "AccessDeniedException",
        "message": "not authorized to perform: sqs:ReceiveMessage"
      },
      "subsegments": []
    }
  ],
  "service_map_summary": "API Gateway → ProducerFunction → SQS → ConsumerFunction (ERROR)"
}
```

**Implementação (boto3):**
```python
# API usada: X-Ray
client = boto3.client('xray')

# 1. Buscar trace summaries filtrando por annotation ou tempo
client.get_trace_summaries(
    StartTime=start_time,
    EndTime=end_time,
    FilterExpression=f'annotation.request_id = "{request_id}"'
)

# 2. Buscar trace completo
client.batch_get_traces(TraceIds=[trace_id])
```

> **Nota:** O X-Ray não indexa por Lambda RequestID diretamente. A estratégia é:
> 1. Adicionar o RequestID como annotation no código da Lambda
> 2. Ou buscar traces por tempo e filtrar pelo RequestID nos segmentos

---

## Tool 3: get_lambda_config

**Propósito:** Retornar a configuração atual de uma Lambda para o agente avaliar se há problemas de configuração.

**Input Schema:**
```json
{
  "function_name": {
    "type": "string",
    "description": "Nome ou ARN da Lambda function",
    "required": true
  }
}
```

**Output (sucesso):**
```json
{
  "function_name": "troubleshooter-dev-ConsumerFunction-abc123",
  "runtime": "python3.11",
  "handler": "app.handler",
  "timeout_seconds": 30,
  "memory_mb": 128,
  "code_size_bytes": 1234,
  "last_modified": "2025-01-15T10:00:00Z",
  "role_arn": "arn:aws:iam::123456:role/troubleshooter-dev-ConsumerRole",
  "environment_variables": {
    "TABLE_NAME": "troubleshooter-dev-table",
    "QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456/troubleshooter-queue"
  },
  "tracing_config": "Active",
  "event_source_mappings": [
    {
      "source": "arn:aws:sqs:us-east-1:123456:troubleshooter-queue",
      "batch_size": 10,
      "enabled": true,
      "state": "Enabled"
    }
  ]
}
```

**Implementação (boto3):**
```python
# APIs usadas: Lambda
client = boto3.client('lambda')

# 1. Configuração da função
client.get_function_configuration(FunctionName=function_name)

# 2. Event source mappings
client.list_event_source_mappings(FunctionName=function_name)
```

---

## Estrutura de Arquivos do MCP Server

```
mcp-server/
├── server.py              # Entry point — registra tools e inicia servidor
├── tools/
│   ├── __init__.py
│   ├── cloudwatch.py      # Implementação de get_logs
│   ├── xray.py            # Implementação de get_trace
│   └── lambda_info.py     # Implementação de get_lambda_config
└── requirements.txt
```

### requirements.txt

```
mcp>=1.0.0
boto3>=1.34.0
```

---

## Tratamento de Erros

Todas as tools seguem o mesmo padrão de erro:

```json
{
  "error": true,
  "error_type": "ResourceNotFoundException",
  "message": "Lambda function 'xyz' not found in region us-east-1"
}
```

| Erro AWS | Mensagem retornada ao agente |
|----------|------------------------------|
| ResourceNotFoundException | "Recurso não encontrado: {details}" |
| AccessDeniedException | "Sem permissão para acessar {service}. Verifique a IAM policy do perfil AWS." |
| ThrottlingException | "Rate limit atingido. Tente novamente em alguns segundos." |
| InvalidParameterValue | "Parâmetro inválido: {details}" |

---

## Testes Manuais com MCP Inspector

Antes de integrar com o Amazon Q, testar cada tool isoladamente:

```bash
# Instalar inspector
npx @modelcontextprotocol/inspector

# Rodar MCP Server em modo debug
cd mcp-server
python server.py

# No inspector:
# 1. Conectar ao server via stdio
# 2. Listar tools disponíveis
# 3. Chamar get_lambda_config com function_name de uma Lambda existente
# 4. Validar output
```
