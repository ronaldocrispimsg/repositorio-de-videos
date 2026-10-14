import os
import uuid
import json
import asyncio
from typing import Dict, Any
import aiofiles
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# CONFIGURAÇÃO RABBITMQ
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://videobox:123456@IP_RABBITMQ/")

# Onde o backend salva o video bruto
VIDEO_STORAGE = os.getenv("VIDEO_STORAGE", "/home/admin/videos_raw")
os.makedirs(VIDEO_STORAGE, exist_ok=True)

FILE_BASE_URL = os.getenv("FILE_BASE_URL", "http://backend:8000").rstrip("/")

# Persistência simples de status
VIDEO_STATE_FILE = os.getenv("VIDEO_STATE_FILE", os.path.join(VIDEO_STORAGE, "videos_state.json"))

# FastStream + RabbitMQ
broker = RabbitBroker(RABBIT_URL)
stream_app = FastStream(broker)

# Backend HTTP
app = FastAPI()

state_lock = asyncio.Lock()
video_state: Dict[str, Dict[str, Any]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou seu domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _load_state():
    if os.path.exists(VIDEO_STATE_FILE):
        try:
            with open(VIDEO_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    video_state.update(data)
        except json.JSONDecodeError as e:
            print(f"[Videos Repo] - Ocorreu um erro: {e}")

async def _save_state():
    tmp_file = f"{VIDEO_STATE_FILE}.tmp"
    async with aiofiles.open(tmp_file, "w", encoding="utf-8") as f:
        await f.write(json.dumps(video_state, ensure_ascii=False, indent=2))
    os.replace(tmp_file, VIDEO_STATE_FILE)

async def _update_video(video_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with state_lock:
        current = video_state.get(video_id, {})
        current.update(payload)
        video_state[video_id] = current
        await _save_state()
        return current

# Inicia/para o FastStream junto com o FastAPI para processar eventos RabbitMQ
@app.on_event("startup")
async def start_stream():
    _load_state()
    await stream_app.start()


@app.on_event("shutdown")
async def stop_stream() -> None:
    await stream_app.stop()

# UPLOAD DE VIDEO
@app.post("/upload")
async def upload(file: UploadFile):
    video_id = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(VIDEO_STORAGE, video_id)
    download_url = f"{FILE_BASE_URL}/videos/{video_id}/file"

    # Salvar arquivo
    async with aiofiles.open(filepath, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)

    # Publicar evento no RabbitMQ
    payload = {"video_id": video_id, "path": filepath, "download_url": download_url}
    await broker.publish(payload, routing_key="video.uploaded")

    updated = await _update_video(
        video_id,
        {
            "video_id": video_id,
            "filename": file.filename,
            "path": filepath,
            "status": "uploaded",
            "download_url": download_url,
        },
    )

    return updated


# EVENTO: PROCESS FINALIZOU
@broker.subscriber("video.processing")
async def video_processing(event):
    video_id = event["video_id"]
    await _update_video(video_id, {"status": event.get("status", "processing")})
    print(f"[backend] Video em processamento: {video_id}")


@broker.subscriber("video.ready")
async def ready(event):
    video_id = event["video_id"]
    updated = await _update_video(
        video_id,
        {
            "status": event.get("status", "ready"),
            "stream_url": event.get("stream_url"),
        },
    )
    print("[backend] Video pronto:", updated)


# CONSULTAS DE STATUS
@app.get("/videos")
async def list_videos():
    async with state_lock:
        return list(video_state.values())


@app.get("/videos/{video_id}")
async def video_detail(video_id: str):
    async with state_lock:
        video = video_state.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    return video


@app.get("/videos/{video_id}/file")
async def download_video(video_id: str):
    async with state_lock:
        video = video_state.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    path = video.get("path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=410, detail="Arquivo indisponível")
    filename = video.get("filename", os.path.basename(path))
    return FileResponse(path, filename=filename, media_type="application/octet-stream")

# HEALTH CHECK
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
