import json

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class BedrockService:
    def __init__(self) -> None:
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def _invoke(self, prompt: str) -> str:
        invoke_target = settings.bedrock_inference_profile_id or settings.bedrock_model_id
        body = {
            "schemaVersion": "messages-v1",
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": 900, "temperature": 0.3, "topP": 0.9},
        }
        response = self.client.invoke_model(
            modelId=invoke_target,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        raw_body = response["body"].read()
        payload = json.loads(raw_body)
        content = payload.get("output", {}).get("message", {}).get("content", [])
        return "\n".join(part.get("text", "") for part in content if "text" in part).strip()

    def summarize(self, material_text: str) -> str:
        prompt = (
            "Kamu adalah tutor kuliah. Ringkas materi berikut dalam bahasa Indonesia, "
            "padat, terstruktur, dan mudah dipahami. Beri poin penting dan kesimpulan.\n\n"
            f"Materi:\n{material_text[:12000]}"
        )
        return self._invoke(prompt)

    def generate_quiz(self, material_text: str) -> str:
        prompt = (
            "Buat 10 soal latihan simpel dari materi berikut untuk persiapan ujian. "
            "Gunakan format:\n"
            "1) Pertanyaan\n"
            "Pilihan: A/B/C/D\n"
            "Jawaban: ...\n"
            "Penjelasan singkat: ...\n\n"
            f"Materi:\n{material_text[:12000]}"
        )
        return self._invoke(prompt)


bedrock_service = BedrockService()


def _enhance_bedrock_error(exc: Exception) -> str:
    raw = str(exc)
    if "on-demand throughput isn’t supported" in raw or "on-demand throughput isn't supported" in raw:
        return (
            f"{raw}\n"
            "Fix: set BEDROCK_INFERENCE_PROFILE_ID pada environment (ID/ARN inference profile Nova), "
            "atau isi BEDROCK_MODEL_ID dengan ID/ARN inference profile."
        )
    return raw


def safe_summarize(material_text: str) -> str:
    try:
        return bedrock_service.summarize(material_text)
    except (ClientError, BotoCoreError, Exception) as exc:
        return f"Gagal membuat summary dari Bedrock Nova: {_enhance_bedrock_error(exc)}"


def safe_generate_quiz(material_text: str) -> str:
    try:
        return bedrock_service.generate_quiz(material_text)
    except (ClientError, BotoCoreError, Exception) as exc:
        return f"Gagal membuat quiz dari Bedrock Nova: {_enhance_bedrock_error(exc)}"
