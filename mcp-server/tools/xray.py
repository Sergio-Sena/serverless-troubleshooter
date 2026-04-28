import boto3
import json
import time
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError


def get_trace(request_id: str, minutes_ago: int = 60) -> str:
    """Busca trace no X-Ray para uma invocação Lambda, mostrando segmentos, latências e erros."""
    client = boto3.client("xray")
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=minutes_ago)

    # Buscar trace summaries filtrando por annotation ou tempo
    try:
        resp = client.get_trace_summaries(
            StartTime=start_time,
            EndTime=end_time,
            FilterExpression=f'annotation.RequestId = "{request_id}"',
            Sampling=False,
        )
    except ClientError as e:
        return json.dumps({
            "error": True,
            "error_type": e.response["Error"]["Code"],
            "message": e.response["Error"]["Message"],
        })

    summaries = resp.get("TraceSummaries", [])

    # Fallback: se não encontrou por annotation, busca por tempo e filtra nos segmentos
    if not summaries:
        try:
            resp = client.get_trace_summaries(
                StartTime=start_time,
                EndTime=end_time,
                Sampling=False,
            )
            summaries = resp.get("TraceSummaries", [])
        except ClientError:
            summaries = []

    if not summaries:
        return json.dumps({
            "request_id": request_id,
            "trace_id": None,
            "message": f"Nenhum trace encontrado para RequestID '{request_id}' nos últimos {minutes_ago} minutos.",
        })

    # Buscar trace completo
    trace_ids = [s["Id"] for s in summaries[:5]]  # Limitar a 5

    try:
        traces_resp = client.batch_get_traces(TraceIds=trace_ids)
    except ClientError as e:
        return json.dumps({
            "error": True,
            "error_type": e.response["Error"]["Code"],
            "message": e.response["Error"]["Message"],
        })

    # Procurar o trace que contém o RequestID
    for trace in traces_resp.get("Traces", []):
        segments = _parse_trace(trace, request_id)
        if segments is not None:
            duration = summaries[0].get("Duration", 0)
            has_error = summaries[0].get("HasError", False)
            has_fault = summaries[0].get("HasFault", False)

            status = "OK"
            if has_fault:
                status = "FAULT"
            elif has_error:
                status = "ERROR"

            service_names = [s["name"] for s in segments]
            service_map = " → ".join(service_names)

            return json.dumps({
                "request_id": request_id,
                "trace_id": trace["Id"],
                "duration_ms": round(duration * 1000),
                "status": status,
                "segments": segments,
                "service_map_summary": service_map,
            }, default=str)

    return json.dumps({
        "request_id": request_id,
        "trace_id": None,
        "message": f"Traces encontrados mas nenhum corresponde ao RequestID '{request_id}'.",
    })


def _parse_trace(trace: dict, request_id: str) -> list | None:
    """Extrai segmentos de um trace, retorna None se não contém o RequestID."""
    segments = []
    found = False

    for raw_segment in trace.get("Segments", []):
        doc = json.loads(raw_segment.get("Document", "{}"))
        name = doc.get("name", "unknown")
        start = doc.get("start_time", 0)
        end = doc.get("end_time", 0)
        duration_ms = round((end - start) * 1000)
        error = doc.get("error", False)
        fault = doc.get("fault", False)
        cause = doc.get("cause", {})

        # Verificar se este segmento contém o RequestID
        aws_data = doc.get("aws", {})
        if aws_data.get("request_id") == request_id:
            found = True

        status = "OK"
        if fault:
            status = "FAULT"
        elif error:
            status = "ERROR"

        segment_data = {
            "name": name,
            "duration_ms": duration_ms,
            "status": status,
        }

        # Extrair erro se houver
        if cause and cause.get("exceptions"):
            exceptions = cause["exceptions"]
            segment_data["error"] = {
                "type": exceptions[0].get("type", "Unknown"),
                "message": exceptions[0].get("message", ""),
            }

        # Subsegmentos
        subsegments = []
        for sub in doc.get("subsegments", []):
            sub_start = sub.get("start_time", 0)
            sub_end = sub.get("end_time", 0)
            sub_status = "OK"
            if sub.get("fault"):
                sub_status = "FAULT"
            elif sub.get("error"):
                sub_status = "ERROR"

            sub_data = {
                "name": sub.get("name", "unknown"),
                "duration_ms": round((sub_end - sub_start) * 1000),
                "status": sub_status,
            }

            sub_cause = sub.get("cause", {})
            if sub_cause and sub_cause.get("exceptions"):
                ex = sub_cause["exceptions"]
                sub_data["error"] = {
                    "type": ex[0].get("type", "Unknown"),
                    "message": ex[0].get("message", ""),
                }

            # Checar RequestID nos subsegmentos também
            sub_aws = sub.get("aws", {})
            if sub_aws.get("request_id") == request_id:
                found = True

            subsegments.append(sub_data)

        if subsegments:
            segment_data["subsegments"] = subsegments

        segments.append(segment_data)

    return segments if found or not request_id else segments
