# 🔍 Serverless Troubleshooter — AI-Ops com MCP

> Agente de IA que diagnostica falhas em arquiteturas serverless (Lambda + SQS + DynamoDB) usando MCP Server conectado ao CloudWatch Logs e X-Ray.

---

## O Problema

Diagnosticar falhas em sistemas distribuídos serverless é complexo:
- Logs espalhados entre múltiplas Lambdas
- Traces fragmentados no X-Ray
- Erros de permissão IAM difíceis de rastrear
- Correlação manual entre RequestID → Logs → Traces → Root Cause

## A Solução

Um MCP Server que dá ao agente de IA (Amazon Q Developer) acesso direto ao CloudWatch Logs e X-Ray. O agente recebe um RequestID, busca os dados automaticamente, identifica o gargalo ou exceção, e sugere a correção exata.

```
Usuário: "Erro no RequestID abc-123, o que aconteceu?"
    │
    ▼
┌─────────────────────────────────┐
│  Amazon Q Developer (Agente)    │
│  Usa MCP Server como ferramenta │
└──────────┬──────────────────────┘
           │
    ┌──────▼──────┐
    │  MCP Server │
    │  (Python)   │
    └──┬──────┬───┘
       │      │
       ▼      ▼
  CloudWatch  X-Ray
    Logs      Traces
       │      │
       ▼      ▼
  "Lambda falhou por falta de permissão sqs:SendMessage.
   Adicione esta policy ao role da Lambda: ..."
```

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Agente IA | Amazon Q Developer (IDE) |
| MCP Server | Python + boto3 + MCP SDK |
| Infra de Teste | AWS SAM (Lambda + SQS + DynamoDB) |
| Observabilidade | CloudWatch Logs + X-Ray |
| IaC | SAM template.yaml |

## Estrutura do Projeto

```
Proejto com MCP/
├── mcp-server/           # MCP Server (Python)
│   ├── server.py         # Servidor MCP com tools
│   ├── tools/            # Ferramentas expostas ao agente
│   │   ├── cloudwatch.py # Busca logs por RequestID
│   │   ├── xray.py       # Busca traces e segmentos
│   │   └── lambda_info.py# Info de configuração da Lambda
│   └── requirements.txt
├── infra/                # Stack serverless de teste
│   ├── template.yaml     # SAM template
│   └── src/              # Código das Lambdas
│       ├── producer/     # Lambda que envia para SQS
│       └── consumer/     # Lambda que processa da SQS
├── tests/                # Cenários de erro para demo
│   └── scenarios/
├── docs/
│   ├── ARCHITECTURE.md   # Arquitetura e fluxos
│   ├── PLAN.md           # Plano de execução por fases
│   ├── MVP.md            # Escopo do MVP
│   ├── MCP-SERVER-SPEC.md# Especificação do MCP Server
│   └── DEPLOY_PASSO_A_PASSO.md
└── README.md
```

## Quick Start

```bash
# 1. Deploy da stack de teste
cd infra
sam build && sam deploy --guided

# 2. Instalar MCP Server
cd mcp-server
pip install -r requirements.txt

# 3. Configurar no Amazon Q Developer
# Adicionar MCP Server nas configurações do IDE

# 4. Testar: forçar erro e perguntar ao agente
# "Analise o erro do RequestID xyz-456"
```

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md) — Diagramas e fluxos técnicos
- [Plano de Execução](docs/PLAN.md) — Fases e cronograma
- [MVP](docs/MVP.md) — Escopo mínimo viável
- [Spec do MCP Server](docs/MCP-SERVER-SPEC.md) — Tools, inputs/outputs
- [Deploy](docs/DEPLOY_PASSO_A_PASSO.md) — Git flow e deploy

## Autor

**Sergio Sena** — [GitHub](https://github.com/Sergio-Sena) | [LinkedIn](https://linkedin.com/in/sergio-sena)
