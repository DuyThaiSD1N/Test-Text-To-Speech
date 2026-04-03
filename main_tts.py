import struct
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tts_client import TTSClient

app = FastAPI(title="TTS System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from dotenv import load_dotenv

load_dotenv()

url     = os.getenv("TTS_WS_URL")
api_key = os.getenv("TTS_API_KEY")
voice   = os.getenv("TTS_VOICE", "thuyanh-north")

if not url or not api_key:
    raise RuntimeError("TTS_WS_URL và TTS_API_KEY phải được cấu hình trong .env")

tts_client = TTSClient(ws_url=url, api_key=api_key, voice=voice)

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

@app.on_event("startup")
async def startup_event():
    try:
        await tts_client.connect()
        print("Connected to TTS WebSocket.")
    except Exception as e:
        print(f"Failed to connect on startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await tts_client.close()

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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static_tts", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
