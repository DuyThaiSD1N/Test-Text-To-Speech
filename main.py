import os
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import struct
from tts_client import TTSClient
from stt_client import ASRClient

load_dotenv()

# TTS Configuration
TTS_WS_URL = os.getenv("TTS_WS_URL")
TTS_API_KEY = os.getenv("TTS_API_KEY")
TTS_VOICE   = os.getenv("TTS_VOICE", "thuyanh-north")

if not TTS_WS_URL or not TTS_API_KEY:
    raise RuntimeError("TTS_WS_URL và TTS_API_KEY phải được cấu hình trong .env")

tts_client = TTSClient(ws_url=TTS_WS_URL, api_key=TTS_API_KEY, voice=TTS_VOICE)

class TTSRequest(BaseModel):
    text: str

def create_wav_header(sample_rate: int, num_channels: int, bytes_per_sample: int, data_size: int) -> bytes:
    header = b'RIFF'
    header += struct.pack('<I', 36 + data_size)
    header += b'WAVE'
    header += b'fmt '
    header += struct.pack('<I', 16)
    header += struct.pack('<H', 1) 
    header += struct.pack('<H', num_channels)
    header += struct.pack('<I', sample_rate)
    header += struct.pack('<I', sample_rate * num_channels * bytes_per_sample)
    header += struct.pack('<H', num_channels * bytes_per_sample)
    header += struct.pack('<H', bytes_per_sample * 8)
    header += b'data'
    header += struct.pack('<I', data_size)
    return header

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        await tts_client.connect()
        print("Connected to TTS WebSocket.")
    except Exception as e:
        print(f"Failed to connect on startup: {e}")
    
    yield
    
    # Shutdown logic
    await tts_client.close()

app = FastAPI(title="Synthesize AI System API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- TTS ENDPOINT ---
@app.post("/api/tts")
async def generate_tts(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        pcm_data = b""
        async for chunk in tts_client.synthesize(request.text):
            pcm_data += chunk
            
        if not pcm_data:
            raise HTTPException(status_code=500, detail="Failed to synthesize audio")
            
        wav_header = create_wav_header(8000, 1, 2, len(pcm_data))
        wav_data = wav_header + pcm_data
        
        return Response(content=wav_data, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- STT WEBSOCKET ENDPOINT ---
@app.websocket("/ws/asr")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[ASR Proxy] New client connected")
    
    asr_client = None
    is_stream_started = False
    chunks_received = 0
    audio_queue = asyncio.Queue()
    
    async def audio_generator():
        nonlocal chunks_received, asr_client, is_stream_started
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                break
            yield chunk

    async def process_asr_stream():
        nonlocal asr_client
        nonlocal is_stream_started
        try:
            print("[ASR Proxy] Starting process_asr_stream...")
            async for result in asr_client.stream_audio(audio_generator()):
                print(f"[ASR Proxy] Received result from ASR client: {result}")
                if "error" in result:
                    await websocket.send_json({"type": "error", "message": result["error"]})
                else:
                    await websocket.send_json({"type": "transcript", "data": result})
            await websocket.send_json({"type": "end"})
        except Exception as e:
            print(f"[ASR Proxy] gRPC Stream Error: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})
        finally:
            print("[ASR Proxy] gRPC Stream ended")
            is_stream_started = False
            
    receive_task = None
    
    try:
        while True:
            message = await websocket.receive()
            # print(f"[ASR Proxy] received raw message: {message.get('type')}")
            
            if message["type"] == "websocket.disconnect":
                print("[ASR Proxy] Client disconnected")
                break
                
            if "bytes" in message and message["bytes"]:
                if not asr_client or not is_stream_started:
                    # print("[ASR Proxy] Warning: received bytes while stream not started")
                    continue
                # print(f"[ASR Proxy] received {len(message['bytes'])} audio bytes")
                await audio_queue.put(message["bytes"])
                if chunks_received % 50 == 0:
                    print(f"[ASR Proxy] received {len(message['bytes'])} audio bytes (chunk #{chunks_received})")
                chunks_received += 1
                
            elif "text" in message and message["text"]:
                import json
                try:
                    msg = json.loads(message["text"])
                    print(f"[ASR Proxy] Received text command: {msg.get('type')}")
                    if msg.get("type") == "start":
                        print("[ASR Proxy] Received START command")
                        if is_stream_started:
                            print("[ASR Proxy] Stream already started, ignoring.")
                            continue
                        asr_client = ASRClient()
                        is_stream_started = True
                        while not audio_queue.empty():
                            audio_queue.get_nowait()
                        receive_task = asyncio.create_task(process_asr_stream())
                        
                    elif msg.get("type") == "stop":
                        print("[ASR Proxy] Received STOP command")
                        await audio_queue.put(None)
                        if asr_client:
                            await asr_client.close()
                        if receive_task:
                            receive_task.cancel()
                        is_stream_started = False
                except Exception as e:
                    print(f"[ASR Proxy] Error processing JSON: {e}")
    except Exception as e:
        print(f"[ASR Proxy] Disconnected with error: {e}")
    finally:
        await audio_queue.put(None)
        if asr_client:
            await asr_client.close()
        if receive_task:
            receive_task.cancel()

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
