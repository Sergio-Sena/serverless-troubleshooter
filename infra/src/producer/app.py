import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["QUEUE_URL"]


def handler(event, context):
    """Producer Lambda — recebe POST /send e envia mensagem para SQS."""
    request_id = context.aws_request_id

    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return _response(400, {"error": "JSON inválido no body"})

    message = body.get("message")
    if not message:
        return _response(400, {"error": "Campo 'message' é obrigatório"})

    message_id = str(uuid.uuid4())
    payload = {
        "message_id": message_id,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }

    try:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(payload),
            MessageAttributes={
                "RequestId": {"DataType": "String", "StringValue": request_id}
            },
        )
    except ClientError as e:
        print(f"[ERROR] Falha ao enviar para SQS: {e}")
        return _response(500, {
            "error": "Falha ao enviar mensagem para SQS",
            "detail": e.response["Error"]["Message"],
        })

    print(f"[INFO] Mensagem enviada: message_id={message_id} request_id={request_id}")

    return _response(200, {
        "message_id": message_id,
        "request_id": request_id,
        "status": "sent",
    })


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
