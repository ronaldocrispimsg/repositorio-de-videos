import os
import asyncio
import subprocess
import shutil
from typing import Optional

import aiofiles
import aiohttp
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from dotenv import load_dotenv

load_dotenv()

# URL do RabbitMQ (use o IP PRIVADO)
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://videobox:123456@10.x.x.x/")

# Onde o PROCESS cria arquivos temporários e saídas HLS
TMP_HLS = os.getenv("TMP_HLS", "/tmp/hls")
os.makedirs(TMP_HLS, exist_ok=True)

TMP_DOWNLOADS = os.getenv("TMP_DOWNLOADS", "/tmp/videos_download")
os.makedirs(TMP_DOWNLOADS, exist_ok=True)

# Pasta local para armazenar os artefatos antes de enviar ao repo_stream
EXPORT_PATH = os.getenv("EXPORT_PATH", "/srv/videobox/export")
os.makedirs(EXPORT_PATH, exist_ok=True)

CLEAN_TMP = os.getenv("CLEAN_TMP", "true").lower() in {"1", "true", "yes"}

REPO_STREAM_URL = os.getenv("REPO_STREAM_URL", "http://repo_stream:8001").rstrip("/")

broker = RabbitBroker(RABBIT_URL)
app = FastStream(broker)


async def _download_from_backend(download_url: str, video_id: str) -> Optional[str]:
    target_path = os.path.join(TMP_DOWNLOADS, f"{video_id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as resp:
                if resp.status != 200:
                    print(f"[process] Falha ao baixar vídeo ({resp.status})")
                    return None
                async with aiofiles.open(target_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 512):
                        await f.write(chunk)
    except aiohttp.ClientError as exc:
        print(f"[process] Erro HTTP ao baixar vídeo: {exc}")
        return None
    return target_path


async def _upload_to_repo(video_id: str, source_dir: str, playlist_name: str) -> Optional[str]:
    segments_url = f"{REPO_STREAM_URL}/videos/{video_id}/segments"
    complete_url = f"{REPO_STREAM_URL}/videos/{video_id}/complete"
    try:
        async with aiohttp.ClientSession() as session:
            for root, _, files in os.walk(source_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, source_dir)
                    form = aiohttp.FormData()
                    form.add_field("relative_path", relative_path)
                    with open(file_path, "rb") as fp:
                        form.add_field(
                            "file",
                            fp,
                            filename=file_name,
                            content_type="application/octet-stream",
                        )
                        resp = await session.post(segments_url, data=form)
                    if resp.status != 200:
                        text = await resp.text()
                        print(f"[process] Falha ao enviar segmento {relative_path}: {resp.status} - {text}")
                        return None

            resp = await session.post(complete_url, json={"playlist_name": playlist_name})
            if resp.status != 200:
                text = await resp.text()
                print(f"[process] Falha ao finalizar upload: {resp.status} - {text}")
                return None
            data = await resp.json()
            return data.get("stream_url")
    except aiohttp.ClientError as exc:
        print(f"[process] Erro HTTP ao enviar para repo_stream: {exc}")
        return None


@broker.subscriber("video.uploaded")
async def process_video(event):
    video_id = event["video_id"]
    download_url = event.get("download_url")
    source_path = event.get("path")

    print(f"[process] Vídeo recebido: {video_id}")

    # Baixa o vídeo do backend (fluxo distribuído)
    if download_url:
        source_path = await _download_from_backend(download_url, video_id)
        if not source_path:
            return
        print(f"[process] Download concluído em {source_path}")
    elif not source_path or not os.path.exists(source_path):
        print("[process] Caminho do vídeo inválido e nenhuma URL de download fornecida.")
        return

    # Avisar que está processando
    await broker.publish(
        {"video_id": video_id, "status": "processing"},
        routing_key="video.processing",
    )

    video_temp_dir = os.path.join(TMP_HLS, video_id)
    os.makedirs(video_temp_dir, exist_ok=True)

    print("[process] Iniciando transcode REAL...")
    playlist_name = "playlist.m3u8"
    playlist_path = os.path.join(video_temp_dir, playlist_name)

    cmd = [
        "ffmpeg",
        "-i",
        source_path,
        "-codec:v",
        "h264",
        "-codec:a",
        "aac",
        "-start_number",
        "0",
        "-hls_time",
        "4",
        "-hls_list_size",
        "0",
        "-f",
        "hls",
        playlist_path,
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("[process] ERRO NO FFMPEG:")
        print(result.stderr.decode())
        return

    print("[process] Transcode FINALIZADO com sucesso.")

    export_video_dir = os.path.join(EXPORT_PATH, video_id)
    if os.path.exists(export_video_dir):
        shutil.rmtree(export_video_dir)
    shutil.copytree(video_temp_dir, export_video_dir)

    stream_url = await _upload_to_repo(video_id, export_video_dir, playlist_name)
    if not stream_url:
        print("[process] Falha ao publicar arquivos no repo_stream.")
        return

    print(f"[process] Arquivos enviados para repo_stream. URL: {stream_url}")

    await broker.publish(
        {"video_id": video_id, "status": "ready", "stream_url": stream_url},
        routing_key="video.ready",
    )

    if CLEAN_TMP:
        shutil.rmtree(video_temp_dir, ignore_errors=True)
        shutil.rmtree(export_video_dir, ignore_errors=True)
        if download_url and source_path and os.path.exists(source_path):
            os.remove(source_path)


if __name__ == "__main__":
    import anyio

    anyio.run(app.run)
