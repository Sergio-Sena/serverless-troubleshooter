# Setup do GitHub + CI/CD (OIDC)

## Visão Geral

```
Developer → Push → GitHub Actions → OIDC → AWS (sem secrets!)
                      │
                      ├── PR para develop/main → CI (validate + plan)
                      ├── Merge em develop     → CD (apply automático)
                      └── Merge em main        → CD (apply com aprovação)
```

## Passo 1 — Criar repositório no GitHub

```bash
# Na raiz do projeto
cd "C:\Projetos Git\Projeto com  MCP e Aws"

git init
git add .
git commit -m "feat: projeto inicial — MCP Server + Terraform + CI/CD"

# Criar repo no GitHub (via CLI ou site)
gh repo create serverless-troubleshooter --public --source=. --push

# Ou manualmente:
git remote add origin https://github.com/Sergio-Sena/serverless-troubleshooter.git
git branch -M main
git push -u origin main
```

## Passo 2 — Deploy inicial (local, uma vez)

O OIDC Provider e a IAM Role precisam existir ANTES do pipeline funcionar.
Faça o primeiro deploy local:

```bash
cd infra
terraform init
terraform plan
terraform apply
```

Anote o output:
```bash
terraform output github_actions_role_arn
# Output: arn:aws:iam::969430605054:role/troubleshooter-dev-github-actions-role
```

## Passo 3 — Configurar GitHub Repository

### 3.1 Variáveis (Settings → Secrets and variables → Actions → Variables)

| Nome | Valor | Tipo |
|------|-------|------|
| `AWS_ROLE_ARN` | `arn:aws:iam::969430605054:role/troubleshooter-dev-github-actions-role` | Variable (não secret!) |

> ⚠️ É **Variable**, não Secret. O ARN do role não é sensível.

### 3.2 Environments (Settings → Environments)

Criar 2 environments:

**dev:**
- Sem proteção (deploy automático)

**production:**
- ✅ Required reviewers → Adicionar seu usuário
- Isso garante aprovação manual antes do deploy em prod

### 3.3 Branch Protection (Settings → Branches)

**main:**
- ✅ Require a pull request before merging
- ✅ Require status checks to pass (selecionar "Validate & Plan")
- ✅ Require branches to be up to date

**develop:**
- ✅ Require a pull request before merging

## Passo 4 — Criar branch develop

```bash
git checkout -b develop
git push -u origin develop
```

## Passo 5 — Testar o pipeline

```bash
# Criar feature branch
git checkout -b feature/teste-pipeline

# Fazer uma mudança qualquer no Terraform
# (ex: adicionar um tag)

git add .
git commit -m "test: validar pipeline CI/CD"
git push origin feature/teste-pipeline

# Abrir PR para develop no GitHub
# → CI roda automaticamente (validate + plan)
# → Plan aparece como comentário no PR

# Merge o PR
# → CD roda automaticamente (apply em dev)
```

## Fluxo Completo

```
feature/* ──PR──> develop ──PR──> main
                    │                │
                    ▼                ▼
              CI: plan          CI: plan
              CD: apply dev     CD: plan prod
                                    │
                                    ▼
                              Aprovação manual
                                    │
                                    ▼
                              CD: apply prod
```

## Como funciona o OIDC (sem secrets)

```
GitHub Actions                              AWS IAM
     │                                        │
     │ 1. Solicita token OIDC ao GitHub       │
     │    (automático, sem config)             │
     │                                        │
     │ 2. Envia token para AWS STS            │
     │ ──────────────────────────────────────> │
     │    "Sou repo Sergio-Sena/serverless-   │
     │     troubleshooter, branch develop"     │
     │                                        │
     │ 3. IAM valida:                         │
     │    - OIDC Provider existe? ✅           │
     │    - Repo está na trust policy? ✅      │
     │    - Audience é sts.amazonaws.com? ✅   │
     │                                        │
     │ 4. Retorna credenciais temporárias     │
     │ <────────────────────────────────────── │
     │    (expiram em 1h, sem access keys)    │
     │                                        │
     │ 5. Roda terraform com credenciais      │
     │ ──────────────────────────────────────> │
```

**Resultado:** Zero secrets no GitHub. Credenciais temporárias. Auditável no CloudTrail.

## Troubleshooting

### "Could not assume role"
- Verificar se `AWS_ROLE_ARN` está correto nas Variables do repo
- Verificar se o nome do repo na variável `github_repo` do Terraform bate com o repo real

### "Access Denied" no terraform apply
- A IAM policy do role pode estar faltando permissão
- Verificar `infra/cicd.tf` e adicionar a permissão necessária

### Pipeline não dispara
- Verificar se o push foi em `infra/**` (o trigger filtra por path)
- Verificar se a branch está correta (develop ou main)
