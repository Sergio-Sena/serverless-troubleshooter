# Regras do Projeto — Serverless Troubleshooter (DevOps com IA)

## Contexto
Projeto de AI-Ops com time de agentes especializados que interagem entre si para provisionar, monitorar e diagnosticar infraestrutura AWS. Usa MCP Servers para dar contexto atualizado à LLM.

## Abordagem
- Estruturada e profissional (NÃO é vibe coding)
- Agentes especializados com skills e responsabilidades claras
- MCP Servers plugados para contexto atualizado (Terraform, AWS, K8s)
- Orquestração entre agentes para tarefas complexas

## MCP Servers Ativos
- **serverless-troubleshooter** — MCP custom: CloudWatch Logs + X-Ray + Lambda config
- **terraform** — Documentação oficial e best practices do Terraform
- **aws-docs** — Documentação oficial da AWS
- **kubernetes** — Documentação e best practices do Kubernetes

## Stack
- IaC: Terraform (estrutura enterprise com remote state)
- Compute: AWS Lambda (serverless) + EKS (Kubernetes) futuro
- Serviços: API Gateway, Lambda, SQS, DynamoDB, CloudWatch, X-Ray
- CI/CD: GitHub Actions
- Linguagem: Python 3.11
- Região: us-east-1
- Prefixo: troubleshooter-dev-

## Time de Agentes

### @infra-agent (Infraestrutura)
- Skill: Criar e modificar código Terraform
- Usa MCP: terraform, aws-docs
- Responsabilidade: Provisionar recursos AWS com IaC
- Regras: Sempre usar variáveis, default_tags, least privilege IAM

### @deploy-agent (Deploy e CI/CD)
- Skill: Pipelines, deploy contínuo, rollback
- Usa MCP: terraform, kubernetes
- Responsabilidade: GitHub Actions, terraform plan/apply, kubectl
- Regras: Sempre plan antes de apply, ambientes separados

### @observability-agent (Observabilidade e Diagnóstico)
- Skill: Monitoramento, troubleshooting, análise de incidentes
- Usa MCP: serverless-troubleshooter, aws-docs
- Responsabilidade: CloudWatch, X-Ray, alarmes, diagnóstico de falhas
- Regras: Sempre buscar logs + traces + config antes de diagnosticar

### @orchestrator (Coordenador)
- Skill: Analisar requisição e delegar para agentes corretos
- Usa MCP: todos
- Responsabilidade: Coordenar tarefas multi-agente
- Regras: Identificar domínios, definir ordem, consolidar resultado

## Regras de Código
- Python 3.11 para Lambdas e MCP Server
- Terraform HCL para infraestrutura
- YAML para GitHub Actions
- Tratamento de erros com try/except e ClientError do boto3
- JSON como formato de retorno das tools MCP
- Sem credenciais hardcoded
- Docstrings em português

## Regras de Infraestrutura
- Terraform com provider default_tags
- Remote state S3 + DynamoDB lock
- X-Ray tracing Active em todas as Lambdas
- CloudWatch Logs retenção 7 dias
- DynamoDB PAY_PER_REQUEST
- IAM least privilege (policies inline por recurso)
- Tags obrigatórias: Project, Environment, ManagedBy

## Estrutura de Pastas
```
mcp-server/              → MCP Server custom (Python)
infra/                   → Terraform (arquivos separados por recurso)
  ├── backend.tf
  ├── variables.tf
  ├── lambda.tf
  ├── api-gateway.tf
  ├── sqs.tf
  ├── dynamodb.tf
  ├── monitoring.tf
  ├── outputs.tf
  └── src/producer/ + src/consumer/
.github/workflows/       → CI/CD (GitHub Actions)
tests/scenarios/         → Cenários de erro para demo
docs/                    → Documentação
.amazonq/
  ├── mcp.json           → MCP Servers config
  ├── agents/            → Agentes especializados
  └── rules/             → Rules do projeto
```
