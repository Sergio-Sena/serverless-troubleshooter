# 🤖 Guia de Agentes — Serverless Troubleshooter

## Modelo de Trabalho

Este projeto usa **agentes especializados + MCP Servers** para provisionar e diagnosticar infraestrutura AWS de forma estruturada e profissional.

```
┌─────────────────────────────────────────────────────┐
│                   USUÁRIO                            │
│          "Crie a infra e diagnostique o erro"        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              @orchestrator                            │
│     Analisa → Delega → Consolida                     │
└──────┬──────────────┬───────────────┬───────────────┘
       │              │               │
       ▼              ▼               ▼
┌──────────┐  ┌──────────────┐  ┌─────────────────┐
│ @infra   │  │ @deploy      │  │ @observability  │
│ -agent   │  │ -agent       │  │ -agent          │
│          │  │              │  │                 │
│ Terraform│  │ CI/CD        │  │ Diagnóstico     │
│ IAM      │  │ GitHub       │  │ CloudWatch      │
│ AWS      │  │ Actions      │  │ X-Ray           │
└────┬─────┘  └──────┬───────┘  └────────┬────────┘
     │               │                   │
     ▼               ▼                   ▼
┌─────────────────────────────────────────────────────┐
│                  MCP SERVERS                         │
│  terraform │ aws-docs │ kubernetes │ troubleshooter  │
│  (docs     │ (docs    │ (docs      │ (CloudWatch     │
│  atualizad)│ AWS)     │ K8s)       │  + X-Ray)       │
└─────────────────────────────────────────────────────┘
```

## Agentes

### @orchestrator — Coordenador
Analisa requisições complexas e delega para os agentes certos na ordem certa.

```
@orchestrator Preciso criar um novo recurso SQS, deployar e configurar alarmes.
```
Resultado: Ele vai chamar @infra-agent → @deploy-agent → @observability-agent em sequência.

---

### @infra-agent — Infraestrutura
Cria e modifica código Terraform. Consulta o MCP Server do Terraform para garantir sintaxe e best practices atualizadas.

```
@infra-agent Adicione uma Dead Letter Queue ao SQS existente.
@infra-agent Crie um alarme CloudWatch para erros na Consumer Lambda.
```

---

### @deploy-agent — Deploy e CI/CD
Gerencia pipelines, deploy contínuo e rollback.

```
@deploy-agent Crie um pipeline GitHub Actions para CI/CD.
@deploy-agent Faça deploy da stack em dev.
```

---

### @observability-agent — Observabilidade
Diagnostica falhas usando o MCP Server custom (CloudWatch + X-Ray).

```
@observability-agent Investigue o erro do RequestID abc-123
@observability-agent A Consumer Lambda está lenta, analise os traces.
```

Fluxo automático:
1. search_logs → encontra o erro
2. search_trace → identifica o serviço
3. search_lambda_config → verifica configuração
4. Diagnóstico com causa raiz + correção exata

---

## MCP Servers

| Server | O que faz | Por que importa |
|--------|-----------|-----------------|
| terraform | Traz documentação atualizada do Terraform | LLM não depende do treinamento antigo |
| aws-docs | Documentação oficial da AWS | Configurações e limites atualizados |
| kubernetes | Docs do K8s | Para expansão futura com EKS |
| serverless-troubleshooter | Acessa CloudWatch + X-Ray em tempo real | Diagnóstico com dados reais da conta |

---

## Exemplos Práticos

### Provisionar + Deploy + Monitorar
```
@orchestrator
Preciso adicionar uma DLQ ao SQS, deployar a mudança e criar um alarme 
para quando mensagens caírem na DLQ.
```

### Diagnóstico de incidente
```
@observability-agent
A Lambda consumer está falhando com o RequestID 
abc123-def456. O que aconteceu e como corrigir?
```

### Criar recurso novo
```
@infra-agent
Adicione um tópico SNS para notificações de erro, 
com subscription por email.
```

### Pipeline CI/CD
```
@deploy-agent
Crie GitHub Actions com: validate em PRs, 
apply automático em develop, apply com aprovação em main.
```
