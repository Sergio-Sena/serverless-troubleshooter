import boto3
import json
from botocore.exceptions import ClientError


def get_lambda_config(function_name: str) -> str:
    """Retorna configuração de uma Lambda: runtime, timeout, memória, role, env vars e event source mappings."""
    client = boto3.client("lambda")

    try:
        config = client.get_function_configuration(FunctionName=function_name)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return json.dumps({"error": True, "error_type": code, "message": msg})

    result = {
        "function_name": config["FunctionName"],
        "function_arn": config["FunctionArn"],
        "runtime": config.get("Runtime", "N/A"),
        "handler": config.get("Handler", "N/A"),
        "timeout_seconds": config.get("Timeout"),
        "memory_mb": config.get("MemorySize"),
        "code_size_bytes": config.get("CodeSize"),
        "last_modified": config.get("LastModified"),
        "role_arn": config.get("Role"),
        "tracing_config": config.get("TracingConfig", {}).get("Mode", "PassThrough"),
        "environment_variables": config.get("Environment", {}).get("Variables", {}),
    }

    # Event source mappings (SQS triggers, etc)
    try:
        mappings = client.list_event_source_mappings(FunctionName=function_name)
        result["event_source_mappings"] = [
            {
                "source_arn": m["EventSourceArn"],
                "batch_size": m.get("BatchSize"),
                "enabled": m.get("State") == "Enabled",
                "state": m.get("State"),
            }
            for m in mappings.get("EventSourceMappings", [])
        ]
    except ClientError:
        result["event_source_mappings"] = []

    return json.dumps(result, default=str)
