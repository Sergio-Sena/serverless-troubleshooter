import boto3
import json
import time
from botocore.exceptions import ClientError

LOG_GROUP_PREFIX = "/aws/lambda/troubleshooter-"


def get_logs(request_id: str, log_group: str = "", minutes_ago: int = 60) -> str:
    """Busca logs de uma invocação Lambda pelo RequestID no CloudWatch Logs."""
    client = boto3.client("logs")
    end_time = int(time.time() * 1000)
    start_time = end_time - (minutes_ago * 60 * 1000)

    # Descobrir log groups se não especificado
    log_groups = []
    if log_group:
        log_groups = [log_group]
    else:
        try:
            resp = client.describe_log_groups(logGroupNamePrefix=LOG_GROUP_PREFIX)
            log_groups = [g["logGroupName"] for g in resp.get("logGroups", [])]
        except ClientError as e:
            return json.dumps({
                "error": True,
                "error_type": e.response["Error"]["Code"],
                "message": e.response["Error"]["Message"],
            })

    if not log_groups:
        return json.dumps({
            "request_id": request_id,
            "log_count": 0,
            "events": [],
            "message": f"Nenhum log group encontrado com prefixo '{LOG_GROUP_PREFIX}'.",
        })

    # Buscar logs em cada log group
    all_events = []
    found_in = ""

    for lg in log_groups:
        try:
            resp = client.filter_log_events(
                logGroupName=lg,
                filterPattern=f'"{request_id}"',
                startTime=start_time,
                endTime=end_time,
                limit=50,
            )
            events = resp.get("events", [])
            if events:
                found_in = lg
                for e in events:
                    msg = e.get("message", "").strip()
                    level = _detect_level(msg)
                    all_events.append({
                        "timestamp": e.get("timestamp"),
                        "level": level,
                        "message": msg,
                    })
                break  # Encontrou, não precisa buscar nos outros
        except ClientError:
            continue

    if not all_events:
        return json.dumps({
            "request_id": request_id,
            "log_count": 0,
            "events": [],
            "message": f"Nenhum log encontrado para RequestID '{request_id}' nos últimos {minutes_ago} minutos.",
        })

    return json.dumps({
        "request_id": request_id,
        "log_group": found_in,
        "log_count": len(all_events),
        "events": all_events,
    }, default=str)


def _detect_level(message: str) -> str:
    """Detecta nível do log pela mensagem."""
    upper = message.upper()
    if upper.startswith("START"):
        return "START"
    if upper.startswith("END"):
        return "END"
    if upper.startswith("REPORT"):
        return "REPORT"
    if "ERROR" in upper or "EXCEPTION" in upper:
        return "ERROR"
    if "WARN" in upper:
        return "WARN"
    return "INFO"
