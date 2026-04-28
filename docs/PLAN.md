# Plano de Execução — Serverless Troubleshooter

## Resumo das Fases

```
Fase 0          Fase 1           Fase 2           Fase 3           Fase 4
Setup           MCP Hello World  Stack de Teste   Integração       Demo & Polish
(0.5 dia)       (1-2 dias)       (1 dia)          (2-3 dias)       (1 dia)
─────────────>──────────────>───────────────>────────────────>──────────────>
```

**Tempo total estimado: 6-8 dias**

---

## Fase 0 — Setup do Ambiente

**Objetivo:** Ter tudo instalado e configurado para começar a desenvolver.

**Tarefas:**
- [ ] Instalar Python 3.11+ e criar virtualenv
- [ ] Instalar AWS SAM CLI
- [ ] Configurar credenciais AWS (~/.aws/credentials) com perfil dedicado
- [ ] Criar IAM policy read-only (CloudWatch, X-Ray, Lambda) — ver ARCHITECTURE.md
- [ ] Instalar MCP SDK Python: `pip install mcp`
- [ ] Verificar que Amazon Q Developer está ativo no VS Code com MCP habilitado
- [ ] Inicializar repositório Git com branch `develop`

**Critério de conclusão:** `aws sts get-caller-identity` retorna o perfil correto e `sam --version` funciona.

---

## Fase 1 — MCP Server Hello World

**Objetivo:** MCP Server rodando e sendo chamado pelo Amazon Q Developer.

**Tarefas:**
- [ ] Criar `mcp-server/server.py` com MCP SDK
- [ ] Implementar tool `get_lambda_info(function_name)` — retorna versão, runtime e memória de uma Lambda
- [ ] Testar localmente com MCP Inspector (`npx @modelcontextprotocol/inspector`)
- [ ] Configurar no Amazon Q Developer (arquivo de config MCP)
- [ ] Validar: perguntar ao Amazon Q "Qual a versão da Lambda X?" e ele usar a tool

**Critério de conclusão:** Amazon Q chama a tool do MCP Server e retorna dados reais de uma Lambda existente na conta.

**Entregáveis:**
- `mcp-server/server.py` funcional
- `mcp-server/requirements.txt`
- Config do MCP no Amazon Q testada

---

## Fase 2 — Stack Serverless de Teste

**Objetivo:** Ter uma stack deployada que gera erros controlados para o agente diagnosticar.

**Tarefas:**
- [ ] Criar `infra/template.yaml` com SAM:
  - API Gateway → Producer Lambda → SQS Queue → Consumer Lambda → DynamoDB
  - X-Ray tracing habilitado em todas as Lambdas
  - CloudWatch Logs com retenção de 7 dias
- [ ] Implementar Producer Lambda (recebe POST, envia para SQS)
- [ ] Implementar Consumer Lambda (lê SQS, grava no DynamoDB)
- [ ] Deploy: `sam build && sam deploy --guided`
- [ ] Testar fluxo feliz: POST → SQS → DynamoDB (item aparece)
- [ ] Criar cenário de erro 1: remover permissão `sqs:ReceiveMessage` do Consumer
- [ ] Validar que o erro gera logs no CloudWatch e trace no X-Ray

**Critério de conclusão:** Stack deployada, fluxo feliz funciona, e erro de permissão gera logs/traces visíveis no console AWS.

**Entregáveis:**
- `infra/template.yaml`
- `infra/src/producer/app.py`
- `infra/src/consumer/app.py`

---

## Fase 3 — Tools de Diagnóstico + Integração

**Objetivo:** MCP Server com todas as tools de diagnóstico, agente fazendo troubleshooting completo.

**Tarefas:**
- [ ] Implementar tool `get_logs(request_id, log_group?, minutes_ago?)`
  - Busca no CloudWatch Logs filtrando por RequestID
  - Retorna logs formatados com timestamp e mensagem
- [ ] Implementar tool `get_trace(request_id)`
  - Busca trace no X-Ray pelo RequestID
  - Retorna: segmentos, latências, erros, serviços envolvidos
- [ ] Expandir tool `get_lambda_config(function_name)`
  - Retorna: runtime, timeout, memória, role ARN, variáveis de ambiente, event source mappings
- [ ] Testar cada tool isoladamente com MCP Inspector
- [ ] Testar fluxo completo com Amazon Q Developer:
  1. Forçar erro na stack
  2. Pegar RequestID do log
  3. Perguntar ao agente: "Analise o erro do RequestID X"
  4. Agente deve chamar get_logs → get_trace → get_lambda_config → sugerir fix

**Critério de conclusão:** Agente diagnostica corretamente o erro de permissão IAM e sugere a policy correta, usando as 3 tools em sequência.

**Entregáveis:**
- `mcp-server/tools/cloudwatch.py`
- `mcp-server/tools/xray.py`
- `mcp-server/tools/lambda_info.py`
- `mcp-server/server.py` atualizado com todas as tools

---

## Fase 4 — Demo, Cenários Extras e Documentação Final

**Objetivo:** Projeto pronto para portfólio com múltiplos cenários de demo.

**Tarefas:**
- [ ] Criar cenário de erro 2: DynamoDB throttle (ProvisionedThroughputExceededException)
- [ ] Criar cenário de erro 3: Lambda timeout
- [ ] Documentar cada cenário em `tests/scenarios/`
- [ ] Gravar demo ou criar GIF do fluxo completo
- [ ] Atualizar README.md com resultados reais
- [ ] Limpar código, adicionar docstrings
- [ ] Push final para GitHub

**Critério de conclusão:** 3 cenários de erro funcionando, README com demo, código limpo no GitHub.

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Amazon Q não suportar MCP custom via stdio | Alto | Testar na Fase 1 antes de investir mais. Fallback: usar Claude Desktop como agente |
| X-Ray traces demoram para aparecer | Médio | Adicionar `time.sleep` nos testes ou usar `minutes_ago=10` na busca |
| Custos AWS da stack de teste | Baixo | Tudo serverless (pay-per-use), DynamoDB on-demand, destruir stack após demo |
| Rate limiting nas APIs de observabilidade | Baixo | Implementar retry com backoff no MCP Server |

## Custos Estimados (Stack de Teste)

| Serviço | Estimativa Mensal |
|---------|------------------|
| Lambda (poucas invocações) | ~$0.00 (free tier) |
| SQS (poucas mensagens) | ~$0.00 (free tier) |
| DynamoDB on-demand | ~$0.00 (free tier) |
| CloudWatch Logs (7 dias retenção) | ~$0.10 |
| X-Ray (traces) | ~$0.00 (free tier 100k traces) |
| **Total** | **< $0.50/mês** |
