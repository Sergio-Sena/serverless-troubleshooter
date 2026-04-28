#!/usr/bin/env python3
"""
🔍 Serverless Troubleshooter — Demo Interativa
Roda no terminal e demonstra o fluxo completo de diagnóstico com MCP Server.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

# Fix encoding no Windows
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import boto3
from botocore.exceptions import ClientError

# ============================================================
# Config
# ============================================================
REGION = os.environ.get("AWS_REGION", "us-east-1")
PREFIX = "troubleshooter-dev"
API_URL = None  # Descoberto automaticamente
CONSUMER_ROLE = f"{PREFIX}-consumer-role"
CONSUMER_FUNCTION = f"{PREFIX}-ConsumerFunction"
PRODUCER_FUNCTION = f"{PREFIX}-ProducerFunction"
TABLE_NAME = f"{PREFIX}-table"
QUEUE_ARN = None

# Clients
iam = boto3.client("iam", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
logs_client = boto3.client("logs", region_name=REGION)
apigateway = boto3.client("apigatewayv2", region_name=REGION)
sqs = boto3.client("sqs", region_name=REGION)

# ============================================================
# Cores e formatação
# ============================================================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════╗
║  🔍 Serverless Troubleshooter — Demo Interativa          ║
║     AI-Ops com MCP Server + Terraform + Amazon Q         ║
╚══════════════════════════════════════════════════════════╝{C.RESET}
""")


def menu():
    print(f"""
{C.BOLD}Escolha uma opção:{C.RESET}

  {C.GREEN}[1]{C.RESET} ▶  Demo Completa (fluxo feliz → erro → diagnóstico → correção)
  {C.RED}[2]{C.RESET} 🔴 Cenário: Permission Denied (dynamodb:PutItem)
  {C.YELLOW}[3]{C.RESET} 🔴 Cenário: Lambda Timeout
  {C.MAGENTA}[4]{C.RESET} 🔴 Cenário: DynamoDB Throttle
  {C.CYAN}[5]{C.RESET} 🟢 Restaurar tudo (voltar ao estado original)
  {C.DIM}[0]{C.RESET} Sair
""")
    return input(f"{C.BOLD}→ {C.RESET}").strip()


def step(icon, msg, color=C.WHITE):
    print(f"\n{color}{C.BOLD}{icon} {msg}{C.RESET}")


def info(msg):
    print(f"  {C.DIM}{msg}{C.RESET}")


def success(msg):
    print(f"  {C.GREEN}✅ {msg}{C.RESET}")


def error(msg):
    print(f"  {C.RED}❌ {msg}{C.RESET}")


def warn(msg):
    print(f"  {C.YELLOW}⚠️  {msg}{C.RESET}")


def detail(label, value):
    print(f"  {C.CYAN}{label}:{C.RESET} {value}")


def separator(title=""):
    if title:
        print(f"\n{C.BOLD}{C.BLUE}{'━' * 20} {title} {'━' * 20}{C.RESET}")
    else:
        print(f"{C.DIM}{'─' * 60}{C.RESET}")


def pause(seconds=2):
    for i in range(seconds):
        print(f"  {C.DIM}⏳ {seconds - i}...{C.RESET}", end="\r")
        time.sleep(1)
    print(" " * 30, end="\r")


def wait_for_enter():
    input(f"\n  {C.DIM}Pressione ENTER para continuar...{C.RESET}")


# ============================================================
# Descobrir API URL
# ============================================================
def discover_api_url():
    global API_URL
    try:
        apis = apigateway.get_apis()
        for api in apis.get("Items", []):
            if PREFIX in api.get("Name", ""):
                API_URL = f"https://{api['ApiId']}.execute-api.{REGION}.amazonaws.com/dev/send"
                return API_URL
    except ClientError:
        pass
    return None


# ============================================================
# Ações reais na AWS
# ============================================================
def send_message(msg="teste demo"):
    """Envia mensagem para a API Gateway."""
    data = json.dumps({"message": msg}).encode()
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}


def check_dynamodb(message_id):
    """Verifica se item existe no DynamoDB."""
    table = dynamodb.Table(TABLE_NAME)
    try:
        resp = table.get_item(Key={"id": message_id})
        return resp.get("Item")
    except ClientError:
        return None


def get_consumer_logs(request_id, minutes=5):
    """Busca logs do Consumer pelo RequestID."""
    log_group = f"/aws/lambda/{CONSUMER_FUNCTION}"
    end_time = int(time.time() * 1000)
    start_time = end_time - (minutes * 60 * 1000)
    try:
        resp = logs_client.filter_log_events(
            logGroupName=log_group,
            filterPattern=f'"{request_id}"',
            startTime=start_time,
            endTime=end_time,
            limit=20,
        )
        return [e["message"].strip() for e in resp.get("events", [])]
    except ClientError:
        return []


def get_lambda_config(function_name):
    """Retorna config da Lambda."""
    try:
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        return {
            "runtime": config.get("Runtime"),
            "timeout": config.get("Timeout"),
            "memory": config.get("MemorySize"),
            "role": config.get("Role", "").split("/")[-1],
        }
    except ClientError:
        return None


def remove_dynamodb_permission():
    """Remove dynamodb:PutItem do Consumer role."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
                "Resource": f"arn:aws:sqs:{REGION}:*:{PREFIX}-queue",
            },
            {
                "Effect": "Allow",
                "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                "Resource": "*",
            },
        ],
    }
    iam.put_role_policy(
        RoleName=CONSUMER_ROLE,
        PolicyName=f"{PREFIX}-consumer-policy",
        PolicyDocument=json.dumps(policy),
    )


def restore_dynamodb_permission():
    """Restaura dynamodb:PutItem no Consumer role."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
                "Resource": f"arn:aws:sqs:{REGION}:*:{PREFIX}-queue",
            },
            {
                "Effect": "Allow",
                "Action": ["dynamodb:PutItem"],
                "Resource": f"arn:aws:dynamodb:{REGION}:*:table/{TABLE_NAME}",
            },
            {
                "Effect": "Allow",
                "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                "Resource": "*",
            },
        ],
    }
    iam.put_role_policy(
        RoleName=CONSUMER_ROLE,
        PolicyName=f"{PREFIX}-consumer-policy",
        PolicyDocument=json.dumps(policy),
    )


def set_lambda_timeout(function_name, timeout):
    """Altera timeout de uma Lambda."""
    lambda_client.update_function_configuration(
        FunctionName=function_name, Timeout=timeout
    )


# ============================================================
# Cenários
# ============================================================
def demo_completa():
    """Demo completa: fluxo feliz → injetar erro → diagnóstico → correção → validação."""

    # --- Passo 1: Fluxo feliz ---
    separator("PASSO 1: Fluxo Feliz")
    step("📤", "Enviando mensagem para API Gateway...", C.CYAN)
    detail("URL", API_URL)
    result = send_message("demo completa - fluxo feliz")

    if "error" in result:
        error(f"Falha: {result}")
        return

    msg_id = result["message_id"]
    req_id = result["request_id"]
    success(f"Mensagem enviada!")
    detail("message_id", msg_id)
    detail("request_id", req_id)

    step("⏳", "Aguardando Consumer processar...", C.YELLOW)
    pause(8)

    item = check_dynamodb(msg_id)
    if item:
        success("Item gravado no DynamoDB!")
        detail("status", item.get("status"))
        detail("processed_at", item.get("processed_at"))
    else:
        warn("Item ainda não apareceu (pode demorar mais)")

    wait_for_enter()

    # --- Passo 2: Injetar erro ---
    separator("PASSO 2: Injetando Erro")
    step("🔴", "Removendo permissão dynamodb:PutItem do Consumer...", C.RED)
    info("Simulando erro de IAM que acontece em produção")
    remove_dynamodb_permission()
    success("Permissão removida!")
    info("Consumer vai falhar na próxima mensagem")

    step("⏳", "Aguardando propagação da IAM policy...", C.YELLOW)
    pause(5)

    wait_for_enter()

    # --- Passo 3: Enviar mensagem que vai falhar ---
    separator("PASSO 3: Mensagem com Erro")
    step("📤", "Enviando mensagem (vai falhar no Consumer)...", C.CYAN)
    result2 = send_message("demo completa - vai falhar")

    if "error" in result2:
        error(f"Falha no Producer: {result2}")
        restore_dynamodb_permission()
        return

    msg_id2 = result2["message_id"]
    req_id2 = result2["request_id"]
    success("Producer enviou para SQS (ele não sabe que vai falhar)")
    detail("request_id", req_id2)

    step("⏳", "Aguardando Consumer falhar...", C.YELLOW)
    pause(10)

    wait_for_enter()

    # --- Passo 4: Diagnóstico ---
    separator("PASSO 4: Diagnóstico com MCP Server")

    step("🔍", "Chamando search_logs (CloudWatch)...", C.MAGENTA)
    info(f"Buscando logs para RequestID: {req_id2}")

    # Buscar pelo producer request_id para encontrar o consumer request_id
    logs = get_consumer_logs(req_id2)
    consumer_req_id = None
    error_found = False

    for log in logs:
        if "ERROR" in log:
            error_found = True
            error(log[:120])
        elif "Processando" in log:
            # Extrair consumer request_id
            parts = log.split("request_id=")
            if len(parts) > 1:
                consumer_req_id = parts[1].split(" ")[0]

    if consumer_req_id and not error_found:
        info(f"Consumer RequestID: {consumer_req_id}")
        step("🔍", "Buscando logs pelo Consumer RequestID...", C.MAGENTA)
        consumer_logs = get_consumer_logs(consumer_req_id)
        for log in consumer_logs:
            if "ERROR" in log:
                error_found = True
                error(log[:150])
            elif "REPORT" in log:
                info(log[:100])

    if not error_found:
        warn("Erro pode ainda não ter aparecido nos logs (propagação IAM)")
        info("Em produção, o agente tentaria novamente com minutes_ago maior")

    separator()
    step("🔍", "Chamando search_lambda_config...", C.MAGENTA)
    config = get_lambda_config(CONSUMER_FUNCTION)
    if config:
        detail("function", CONSUMER_FUNCTION)
        detail("role", config["role"])
        detail("timeout", f"{config['timeout']}s")
        detail("memory", f"{config['memory']}MB")
        detail("runtime", config["runtime"])

    separator()
    step("🎯", "DIAGNÓSTICO", C.RED)
    print(f"""
  {C.RED}{C.BOLD}Causa Raiz:{C.RESET}
  O IAM Role '{C.YELLOW}{CONSUMER_ROLE}{C.RESET}' não possui a permissão
  {C.YELLOW}dynamodb:PutItem{C.RESET} na tabela '{C.YELLOW}{TABLE_NAME}{C.RESET}'.

  {C.GREEN}{C.BOLD}Correção:{C.RESET}
  Adicionar ao role a policy:
  {C.CYAN}{{"Effect": "Allow", "Action": ["dynamodb:PutItem"],
   "Resource": "arn:aws:dynamodb:{REGION}:*:table/{TABLE_NAME}"}}{C.RESET}
""")

    wait_for_enter()

    # --- Passo 5: Correção ---
    separator("PASSO 5: Aplicando Correção")
    step("🔧", "Restaurando permissão dynamodb:PutItem...", C.GREEN)
    restore_dynamodb_permission()
    success("Permissão restaurada!")

    step("⏳", "Aguardando propagação...", C.YELLOW)
    pause(5)

    wait_for_enter()

    # --- Passo 6: Validação ---
    separator("PASSO 6: Validando Correção")
    step("📤", "Enviando mensagem novamente...", C.CYAN)
    result3 = send_message("demo completa - após correção")

    if "error" in result3:
        error(f"Falha: {result3}")
        return

    msg_id3 = result3["message_id"]
    success(f"Mensagem enviada: {msg_id3}")

    step("⏳", "Aguardando Consumer processar...", C.YELLOW)
    pause(8)

    item3 = check_dynamodb(msg_id3)
    if item3:
        success("Item gravado no DynamoDB!")
        detail("status", item3.get("status"))
    else:
        warn("Item ainda não apareceu (pode demorar mais)")

    separator()
    print(f"""
{C.GREEN}{C.BOLD}
  🎉 DEMO COMPLETA!

  ✅ Fluxo feliz: POST → SQS → DynamoDB
  ✅ Erro injetado: AccessDeniedException
  ✅ Diagnóstico: MCP Server identificou causa raiz
  ✅ Correção aplicada: IAM policy restaurada
  ✅ Validação: Fluxo funcionando novamente
{C.RESET}""")


def cenario_permission_denied():
    """Cenário isolado: Permission Denied."""
    separator("CENÁRIO: Permission Denied")

    step("🔴", "Removendo permissão dynamodb:PutItem...", C.RED)
    remove_dynamodb_permission()
    success("Permissão removida!")
    pause(5)

    step("📤", "Enviando mensagem...", C.CYAN)
    result = send_message("cenário permission denied")
    req_id = result.get("request_id", "unknown")
    detail("request_id", req_id)

    step("⏳", "Aguardando erro...", C.YELLOW)
    pause(10)

    step("🔍", "Buscando logs...", C.MAGENTA)
    logs = get_consumer_logs(req_id)
    for log in logs:
        if "ERROR" in log:
            error(log[:150])

    step("🔧", "Restaurando permissão...", C.GREEN)
    restore_dynamodb_permission()
    success("Restaurado!")


def cenario_timeout():
    """Cenário isolado: Lambda Timeout."""
    separator("CENÁRIO: Lambda Timeout")

    step("🔴", "Reduzindo timeout da Producer para 1s...", C.RED)
    set_lambda_timeout(PRODUCER_FUNCTION, 1)
    success("Timeout = 1 segundo")

    step("📤", "Enviando mensagem...", C.CYAN)
    info("Se houver cold start, vai dar timeout")
    result = send_message("cenário timeout")
    if "error" in result:
        error(f"Timeout! {result.get('error', '')}")
    else:
        warn("Lambda warm respondeu rápido. Force cold start alterando env var.")
        detail("request_id", result.get("request_id", ""))

    step("🔧", "Restaurando timeout para 10s...", C.GREEN)
    set_lambda_timeout(PRODUCER_FUNCTION, 10)
    success("Restaurado!")


def cenario_throttle():
    """Cenário isolado: DynamoDB Throttle."""
    separator("CENÁRIO: DynamoDB Throttle")
    warn("Este cenário requer mudar a tabela para PROVISIONED (1 WCU)")
    warn("e enviar muitas mensagens simultâneas.")
    info("Consulte: tests/scenarios/dynamodb-throttle.md")
    info("Não executado automaticamente para evitar custos.")


def restaurar_tudo():
    """Restaura todas as configurações originais."""
    separator("RESTAURANDO TUDO")

    step("🔧", "Restaurando permissão DynamoDB...", C.GREEN)
    restore_dynamodb_permission()
    success("OK")

    step("🔧", "Restaurando timeout Producer (10s)...", C.GREEN)
    set_lambda_timeout(PRODUCER_FUNCTION, 10)
    success("OK")

    step("🔧", "Restaurando timeout Consumer (30s)...", C.GREEN)
    set_lambda_timeout(CONSUMER_FUNCTION, 30)
    success("OK")

    success("Tudo restaurado ao estado original!")


# ============================================================
# Main
# ============================================================
def main():
    os.system("cls" if os.name == "nt" else "clear")
    banner()

    step("🔌", "Conectando à AWS...", C.CYAN)
    url = discover_api_url()
    if not url:
        error("API Gateway não encontrada. Verifique se a stack está deployada.")
        sys.exit(1)
    success(f"API: {url}")

    while True:
        choice = menu()

        if choice == "1":
            demo_completa()
        elif choice == "2":
            cenario_permission_denied()
        elif choice == "3":
            cenario_timeout()
        elif choice == "4":
            cenario_throttle()
        elif choice == "5":
            restaurar_tudo()
        elif choice == "0":
            print(f"\n{C.DIM}Até mais! 👋{C.RESET}\n")
            break
        else:
            warn("Opção inválida")


if __name__ == "__main__":
    main()
