# 🔍 Serverless Troubleshooter — AI-Ops com MCP + Terraform

> Time de agentes IA especializados que provisionam e diagnosticam infraestrutura serverless AWS usando MCP Servers para contexto atualizado.

**Abordagem estruturada e profissional — não é vibe coding.**

---

## O Problema

Diagnosticar falhas em sistemas distribuídos serverless é complexo:
- Logs espalhados entre múltiplas Lambdas
- Traces fragmentados no X-Ray
- Erros de permissão IAM difíceis de rastrear
- Correlação manual entre RequestID → Logs → Traces → Root Cause

## A Solução

MCP Servers que dão ao Amazon Q Developer acesso direto ao CloudWatch Logs, X-Ray e documentação atualizada do Terraform/AWS. O agente recebe um RequestID, busca os dados automaticamente, identifica o erro e sugere a correção exata.

```
Usuário: "Erro no RequestID abc-123, o que aconteceu?"
    │
    ▼
┌─────────────────────────────────────┐
│  Amazon Q Developer (Agente IA)     │
│  Usa MCP Servers como ferramentas   │
└──────────┬──────────────────────────┘
           │
    ┌──────▼──────────────────────────┐
    │         MCP SERVERS             │
    │  troubleshooter │ terraform     │
    │  aws-docs       │ kubernetes    │
    └──┬──────┬───────┬──────────────┘
       │      │       │
       ▼      ▼       ▼
  CloudWatch  X-Ray   Terraform Docs
    Logs      Traces  (atualizado)
       │      │
       ▼      ▼
  "Lambda falhou por falta de permissão dynamodb:PutItem.
   Adicione esta policy ao role: { ... }"
```

## Demo — Diagnóstico Real

### Fluxo feliz
```bash
$ curl -X POST https://hmpsvwpjz5.execute-api.us-east-1.amazonaws.com/dev/send \
  -H "Content-Type: application/json" -d '{"message": "teste"}'

{"message_id": "d6ab2ffc-...", "request_id": "2b8a5848-...", "status": "sent"}
# ✅ Item gravado no DynamoDB com status "processed"
```

### Cenário de erro: Permission Denied
Após remover `dynamodb:PutItem` do Consumer role:

```
Usuário: "Investigue o erro do RequestID 87aa9a0b-206f-5a22-8c7f-f86013b27749"

Agente chama search_logs →
  [ERROR] AccessDeniedException - User: troubleshooter-dev-consumer-role 
  is not authorized to perform: dynamodb:PutItem

Agente chama search_lambda_config →
  role_arn: troubleshooter-dev-consumer-role
  TABLE_NAME: troubleshooter-dev-table

Agente diagnostica →
  "O IAM Role não possui dynamodb:PutItem. Adicione esta policy: {...}"
```

**Tempo de diagnóstico: ~3 segundos (3 chamadas MCP)**

## Arquitetura

### Stack Serverless
```
API Gateway → Producer Lambda → SQS Queue → Consumer Lambda → DynamoDB
                                                    │
                                              CloudWatch Logs
                                              X-Ray Traces
```

### Time de Agentes
```
@orchestrator (coordena tudo)
  ├── @infra-agent      → Terraform + AWS (MCP: terraform, aws-docs)
  ├── @deploy-agent     → CI/CD + Deploy  (MCP: terraform, kubernetes)
  └── @observability-agent → Diagnóstico  (MCP: troubleshooter, aws-docs)
```

### CI/CD (GitHub Actions + OIDC)
```
feature/* ──PR──> develop ──PR──> main
                    │                │
              CI: validate+plan  CI: validate+plan
              CD: apply dev      CD: apply prod (aprovação manual)
```
**Zero secrets** — usa OIDC para credenciais temporárias.

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Agente IA | Amazon Q Developer (IDE) |
| MCP Servers | Python + boto3 (custom) + Terraform + AWS Docs + K8s (oficiais) |
| IaC | Terraform (remote state S3, default_tags, least privilege) |
| Compute | AWS Lambda (Python 3.11, X-Ray Active) |
| Messaging | Amazon SQS |
| Database | Amazon DynamoDB (on-demand) |
| API | Amazon API Gateway (HTTP API) |
| Observabilidade | CloudWatch Logs + AWS X-Ray |
| CI/CD | GitHub Actions + OIDC (sem secrets) |

## Estrutura do Projeto

```
├── .amazonq/
│   ├── agents/              # Agentes especializados (4)
│   ├── rules/               # Rules do projeto
│   └── mcp.json             # MCP Servers config (4)
├── .github/workflows/
│   ├── ci.yml               # Validate + Plan em PRs
│   └── cd.yml               # Apply em merge
├── infra/                   # Terraform
│   ├── backend.tf           # Provider + remote state S3
│   ├── variables.tf         # Variáveis tipadas
│   ├── lambda.tf            # Lambdas + IAM roles
│   ├── api-gateway.tf       # HTTP API + integração
│   ├── sqs.tf               # Fila SQS
│   ├── dynamodb.tf          # Tabela DynamoDB
│   ├── monitoring.tf        # CloudWatch Log Groups
│   ├── cicd.tf              # OIDC Provider + GitHub Actions role
│   ├── outputs.tf           # URLs, ARNs, nomes
│   └── src/
│       ├── producer/app.py  # Lambda: recebe POST, envia SQS
│       └── consumer/app.py  # Lambda: lê SQS, grava DynamoDB
├── mcp-server/              # MCP Server custom
│   ├── server.py            # Entry point (FastMCP, stdio)
│   └── tools/
│       ├── cloudwatch.py    # search_logs (por RequestID)
│       ├── xray.py          # search_trace (segmentos, erros)
│       └── lambda_info.py   # search_lambda_config
├── tests/scenarios/         # Cenários de erro documentados
│   ├── permission-denied.md
│   ├── lambda-timeout.md
│   └── dynamodb-throttle.md
└── docs/                    # Documentação completa
```

## Quick Start

### 1. Deploy da infra
```bash
cd infra
terraform init
terraform plan
terraform apply
```

### 2. Instalar MCP Server
```bash
cd mcp-server
pip install -r requirements.txt
```

### 3. Configurar no Amazon Q Developer
O arquivo `.amazonq/mcp.json` já está configurado com 4 MCP Servers.

### 4. Testar
```bash
# Enviar mensagem
curl -X POST $(terraform output -raw api_url) \
  -H "Content-Type: application/json" \
  -d '{"message": "teste"}'

# Diagnosticar erro (no Amazon Q):
# "Investigue o erro do RequestID <id>"
```

### 5. Destruir
```bash
cd infra
terraform destroy
```

## Cenários de Erro

| Cenário | Erro | O que o agente encontra |
|---------|------|------------------------|
| [Permission Denied](tests/scenarios/permission-denied.md) | AccessDeniedException: dynamodb:PutItem | Log de erro + sugere policy IAM |
| [Lambda Timeout](tests/scenarios/lambda-timeout.md) | Task timed out after 1.00 seconds | REPORT com timeout + sugere aumentar timeout/memória |
| [DynamoDB Throttle](tests/scenarios/dynamodb-throttle.md) | ProvisionedThroughputExceededException | Trace com latência + sugere on-demand |

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md) — Diagramas e fluxos
- [Setup GitHub + CI/CD](docs/SETUP-GITHUB-CICD.md) — OIDC, pipelines, environments
- [Spec do MCP Server](docs/MCP-SERVER-SPEC.md) — Tools, inputs/outputs
- [Guia de Agentes](GUIA-AGENTES.md) — Como usar o time de agentes
- [Plano de Execução](docs/PLAN.md) — Fases e cronograma
- [MVP](docs/MVP.md) — Critérios de aceite

## Autor

**Sergio Sena** — [GitHub](https://github.com/Sergio-Sena) | [LinkedIn](https://linkedin.com/in/sergio-sena)
