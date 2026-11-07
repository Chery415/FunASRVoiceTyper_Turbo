"""
SPEECH-PIPELINE-HYBRID-FAST: FastAPI 轉錄與校正微服務
"""

import os
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel

from core.pipeline import HybridSpeechPipeline
from core.models import HybridTranscriptionResult

app = FastAPI(
    title="SPEECH-PIPELINE-HYBRID-FAST API",
    description="極速非自回歸 ASR 與輕量 LLM 混合轉錄系統",
    version="1.0.0"
)

pipeline_instance: Optional[HybridSpeechPipeline] = None

@app.on_event("startup")
def startup_event():
    global pipeline_instance
    pipeline_instance = HybridSpeechPipeline(
        asr_model_id=os.getenv("ASR_MODEL_ID", "iic/SenseVoiceSmall"),
        llm_api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        llm_model_name=os.getenv("LLM_MODEL_NAME", "qwen2.5:3b-instruct-q4_K_M"),
        device=os.getenv("DEVICE", "cuda")
    )

class HealthResponse(BaseModel):
    status: str
    asr_model: str
    llm_api_base: str

class TextCorrectionRequest(BaseModel):
    raw_text: str
    domain_terms: Optional[List[str]] = None
    llm_timeout_seconds: float = 0.8

@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ready",
        asr_model=pipeline_instance.asr_model_id if pipeline_instance else "uninitialized",
        llm_api_base=pipeline_instance.llm_api_base if pipeline_instance else "uninitialized"
    )

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    domain_terms: Optional[str] = Form(None, description="逗號分隔之專有名詞，例如: 台積電,CoWoS,EUV"),
    enable_correction: bool = Form(True),
    llm_timeout_seconds: float = Form(0.8)
):
    terms_list = [t.strip() for t in domain_terms.split(",")] if domain_terms else None
    
    # 將上傳的音訊寫入暫存檔
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        content = await file.read()
        temp_audio.write(content)
        temp_audio_path = temp_audio.name

    try:
        result = pipeline_instance.process(
            audio_path=temp_audio_path,
            domain_terms=terms_list,
            enable_correction=enable_correction,
            llm_timeout_seconds=llm_timeout_seconds
        )
        return {
            "final_text": result.final_text,
            "raw_text": result.raw_text,
            "segments": [
                {
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "raw_text": s.raw_text,
                    "corrected_text": s.corrected_text
                }
                for s in result.segments
            ],
            "metrics": {
                "asr_latency_ms": result.asr_latency_ms,
                "llm_latency_ms": result.llm_latency_ms,
                "total_latency_ms": result.total_latency_ms,
                "is_fallback": result.is_fallback
            }
        }
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
