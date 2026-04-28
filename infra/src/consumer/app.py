import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    """Consumer Lambda — processa mensagens da SQS e grava no DynamoDB."""
    request_id = context.aws_request_id

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[ERROR] request_id={request_id} Falha ao parsear mensagem: {e}")
            raise

        message_id = body.get("message_id", "unknown")
        message = body.get("message", "")
        producer_request_id = body.get("request_id", "")

        print(
            f"[INFO] request_id={request_id} "
            f"Processando message_id={message_id} "
            f"producer_request_id={producer_request_id}"
        )

        try:
            table.put_item(Item={
                "id": message_id,
                "message": message,
                "producer_request_id": producer_request_id,
                "consumer_request_id": request_id,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "status": "processed",
            })
        except ClientError as e:
            print(
                f"[ERROR] request_id={request_id} "
                f"Falha ao gravar no DynamoDB: {e.response['Error']['Code']} "
                f"- {e.response['Error']['Message']}"
            )
            raise

        print(f"[INFO] request_id={request_id} Item gravado: id={message_id}")

    return {"statusCode": 200, "body": "OK"}
