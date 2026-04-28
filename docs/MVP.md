# MVP — Serverless Troubleshooter

## Definição do MVP

O MVP é a menor versão funcional que demonstra o valor do projeto:

> **Um agente (Amazon Q Developer) que, dado um RequestID, busca logs e traces automaticamente via MCP Server e diagnostica a causa raiz de um erro em uma Lambda.**

---

## O que ENTRA no MVP

### 1. MCP Server com 3 tools

```
┌─────────────────────────────────────────────────┐
│                  MCP Server                      │
│                                                  │
│  tool: get_logs                                  │
│  ├─ input:  request_id (str), log_group? (str)  │
│  └─ output: lista de log events com timestamp   │
│                                                  │
│  tool: get_trace                                 │
│  ├─ input:  request_id (str)                    │
│  └─ output: trace com segmentos e erros         │
│                                                  │
│  tool: get_lambda_config                         │
│  ├─ input:  function_name (str)                 │
│  └─ output: runtime, timeout, memória, role     │
└─────────────────────────────────────────────────┘
```

### 2. Stack de teste mínima

```yaml
Recursos SAM:
  - ProducerFunction (Python 3.11, X-Ray ativo)
  - ConsumerFunction (Python 3.11, X-Ray ativo)
  - SQS Queue
  - DynamoDB Table (on-demand)
  - API Gateway (HTTP API)
```

### 3. Um cenário de erro funcional

**Cenário: Permission Denied no SQS**
- Consumer Lambda sem permissão `sqs:ReceiveMessage`
- Erro aparece no CloudWatch Logs
- Trace no X-Ray mostra o segmento com falha
- Agente diagnostica e sugere a policy IAM correta

---

## O que NÃO entra no MVP

| Feature | Motivo | Fase Futura |
|---------|--------|-------------|
| Múltiplos cenários de erro | Complexidade desnecessária para validar o conceito | Fase 4 |
| Tool de sugestão automática de fix | O agente já sugere com base nos dados | Backlog |
| Dashboard web | Foco é no agente no IDE | Backlog |
| Suporte a ECS/EKS | Escopo é serverless | Backlog |
| Alertas automáticos | Foco é diagnóstico sob demanda | Backlog |
| Multi-account/multi-region | Complexidade desnecessária | Backlog |

---

## Critérios de Aceite do MVP

### CA-1: MCP Server conecta ao Amazon Q Developer
- [ ] Server inicia sem erros
- [ ] Amazon Q lista as 3 tools disponíveis
- [ ] Tools são chamáveis pelo agente

### CA-2: get_logs retorna dados reais
- [ ] Dado um RequestID válido, retorna os logs da invocação
- [ ] Dado um RequestID inválido, retorna mensagem clara "Nenhum log encontrado"
- [ ] Logs incluem timestamp, nível (ERROR/INFO) e mensagem

### CA-3: get_trace retorna dados reais
- [ ] Dado um RequestID válido, retorna o trace com segmentos
- [ ] Cada segmento mostra: serviço, duração, status (ok/error/fault)
- [ ] Erros incluem a mensagem de exceção

### CA-4: get_lambda_config retorna configuração
- [ ] Dado um function_name válido, retorna: runtime, timeout, memória, role ARN
- [ ] Dado um function_name inválido, retorna erro claro

### CA-5: Fluxo completo de diagnóstico
- [ ] Usuário pergunta: "Analise o erro do RequestID abc-123"
- [ ] Agente chama get_logs → identifica erro
- [ ] Agente chama get_trace → correlaciona com serviço
- [ ] Agente chama get_lambda_config → verifica configuração
- [ ] Agente responde com: causa raiz + sugestão de correção
- [ ] Tempo total < 30 segundos

### CA-6: Stack de teste funcional
- [ ] `sam deploy` cria todos os recursos sem erro
- [ ] Fluxo feliz funciona (POST → SQS → DynamoDB)
- [ ] Cenário de erro gera logs e traces visíveis
- [ ] `sam delete` remove tudo limpo

---

## Fluxo de Validação do MVP

```
1. Deploy da stack
   sam build && sam deploy
        │
        ▼
2. Testar fluxo feliz
   curl -X POST https://api-url/send -d '{"message": "teste"}'
   → Verificar item no DynamoDB ✓
        │
        ▼
3. Forçar erro (remover permissão SQS do Consumer role)
   → Enviar nova mensagem
   → Consumer falha
        │
        ▼
4. Pegar RequestID do CloudWatch Logs
        │
        ▼
5. Perguntar ao Amazon Q Developer:
   "Analise o erro do RequestID abc-123 na stack troubleshooter"
        │
        ▼
6. Validar que o agente:
   ✓ Chamou get_logs
   ✓ Chamou get_trace
   ✓ Chamou get_lambda_config
   ✓ Identificou: AccessDeniedException em sqs:ReceiveMessage
   ✓ Sugeriu: adicionar permissão ao IAM role
```

---

## Definição de Pronto (DoD)

O MVP está pronto quando:
- [ ] Todos os 6 critérios de aceite passam
- [ ] Código no GitHub com README atualizado
- [ ] Fluxo completo executado pelo menos 3 vezes com sucesso
- [ ] Nenhum hardcode de credenciais ou ARNs
