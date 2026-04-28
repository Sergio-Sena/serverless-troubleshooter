from mcp.server.fastmcp import FastMCP
from tools.cloudwatch import get_logs
from tools.xray import get_trace
from tools.lambda_info import get_lambda_config

mcp = FastMCP("serverless-troubleshooter")


@mcp.tool()
def search_logs(request_id: str, log_group: str = "", minutes_ago: int = 60) -> str:
    """Busca logs no CloudWatch Logs para uma invocação Lambda pelo RequestID.
    Use quando precisar investigar erros, exceções ou comportamento de uma Lambda.
    Retorna os log events com timestamp, nível (ERROR/INFO/WARN) e mensagem.

    Args:
        request_id: AWS Lambda Request ID (ex: abc123-def456-ghi789)
        log_group: Nome do log group. Se vazio, busca em todos com prefixo /aws/lambda/troubleshooter-
        minutes_ago: Janela de tempo em minutos para buscar. Default: 60
    """
    return get_logs(request_id, log_group, minutes_ago)


@mcp.tool()
def search_trace(request_id: str, minutes_ago: int = 60) -> str:
    """Busca trace no AWS X-Ray para uma invocação, mostrando o caminho da requisição entre serviços.
    Use para identificar qual serviço falhou, latências e gargalos.
    Retorna: trace com segmentos, duração, status (OK/ERROR/FAULT) e mapa de serviços.

    Args:
        request_id: AWS Lambda Request ID para buscar o trace correspondente
        minutes_ago: Janela de tempo em minutos para buscar. Default: 60
    """
    return get_trace(request_id, minutes_ago)


@mcp.tool()
def search_lambda_config(function_name: str) -> str:
    """Retorna a configuração atual de uma AWS Lambda function.
    Use para verificar timeout, memória, runtime, IAM role, variáveis de ambiente e triggers (SQS, etc).
    Útil para diagnosticar problemas de configuração ou permissão.

    Args:
        function_name: Nome ou ARN da Lambda function
    """
    return get_lambda_config(function_name)


if __name__ == "__main__":
    mcp.run(transport="stdio")
