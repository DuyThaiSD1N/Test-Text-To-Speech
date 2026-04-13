# -*- coding: utf-8 -*-
"""
Simple Voice Agent Server
"""
import asyncio
import os
import logging
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import services
from src.clients.text_to_speech import TTSClient
from src.services.redis_store import RedisConversationStore
from src.services.message_handler import MessageHandler
from src.services.audio_processor import AudioProcessor

# ═══════════════════════════════════════════════════════════════════════
# TTS CLIENT
# ═══════════════════════════════════════════════════════════════════════
TTS_WS_URL = os.getenv("TTS_WS_URL")
TTS_API_KEY = os.getenv("TTS_API_KEY")
TTS_VOICE = os.getenv("TTS_VOICE", "thuyanh-north")

tts_client = None
if TTS_WS_URL and TTS_API_KEY:
    tts_client = TTSClient(ws_url=TTS_WS_URL, api_key=TTS_API_KEY, voice=TTS_VOICE)
    logger.info(f"[TTS] Initialized with voice: {TTS_VOICE}")
else:
    logger.warning("[TTS] Not configured - will work without audio")

# ═══════════════════════════════════════════════════════════════════════
# REDIS STORE (Optional)
# ═══════════════════════════════════════════════════════════════════════
redis_store = None
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"

if USE_REDIS:
    redis_store = RedisConversationStore()

# ═══════════════════════════════════════════════════════════════════════
# ASR CONFIG
# ═══════════════════════════════════════════════════════════════════════
ASR_GRPC_URI = os.getenv("ASR_GRPC_URI")
ASR_TOKEN = os.getenv("ASR_TOKEN")

if ASR_GRPC_URI and ASR_TOKEN:
    logger.info(f"[ASR] Configured with URI: {ASR_GRPC_URI}")
else:
    logger.warning("[ASR] Not configured - voice input disabled")


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    # Pre-warm LLM connection
    logger.info("[LLM] Pre-warming connection...")
    try:
        from src.services.ai_logic import get_llm
        from langchain_core.messages import HumanMessage
        llm = get_llm()
        await llm.ainvoke([HumanMessage(content="test")])
        logger.info("[LLM] ✅ Pre-warmed successfully")
    except Exception as e:
        logger.warning(f"[LLM] Pre-warm failed: {e}")
    
    # Pre-connect to TTS server
    if tts_client:
        try:
            logger.info("[TTS] Pre-connecting...")
            await tts_client.connect()
            logger.info("[TTS] Pre-connected successfully!")
        except Exception as e:
            logger.warning(f"[TTS] Pre-connect failed: {e}")
    
    # Connect to Redis (if enabled)
    if USE_REDIS and redis_store:
        try:
            await redis_store.connect()
            logger.info("[Redis] ✅ Connected and ready")
        except Exception as e:
            logger.error(f"[Redis] ❌ Connection failed: {e}")
            logger.warning("[Redis] Will continue without Redis (in-memory only)")
    else:
        logger.info("[Redis] Disabled - using in-memory storage only")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if redis_store:
        await redis_store.close()
    logger.info("[Server] Shutdown complete")


@app.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("[WebSocket] Client connected")
    
    # Create session
    session_id = str(uuid.uuid4())
    logger.info(f"[Session] Created: {session_id}")
    
    # Initialize handlers
    message_handler = MessageHandler(
        websocket=websocket,
        session_id=session_id,
        tts_client=tts_client,
        redis_store=redis_store
    )
    
    audio_processor = None
    if ASR_GRPC_URI and ASR_TOKEN:
        audio_processor = AudioProcessor(
            websocket=websocket,
            asr_uri=ASR_GRPC_URI,
            asr_token=ASR_TOKEN
        )
    
    # Load from Redis
    await message_handler.load_from_redis()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            logger.info(f"[WebSocket] Received: {msg_type}")
            
            # Extend TTL on activity
            await message_handler.extend_ttl()
            
            # ═══════════════════════════════════════════════════════
            # ROUTE MESSAGE TO APPROPRIATE HANDLER
            # ═══════════════════════════════════════════════════════
            
            if msg_type == "text_input":
                text = data.get("text", "").strip()
                if text:
                    await message_handler.handle_text_input(text)
            
            elif msg_type == "init_call":
                call_data = data.get("data", {})
                await message_handler.handle_init_call(call_data)
            
            elif msg_type == "typing":
                await message_handler.handle_typing()
            
            elif msg_type == "audio_playback_ended":
                await message_handler.handle_audio_playback_ended()
            
            elif msg_type == "audio_start":
                if audio_processor:
                    message_handler.call_handler.stop_silence_timer()
                    await audio_processor.start_recording()
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "ASR không được cấu hình"
                    })
            
            elif msg_type == "audio_chunk":
                if audio_processor and audio_processor.is_recording:
                    audio_data = data.get("audio", "")
                    if audio_data:
                        await audio_processor.add_audio_chunk(audio_data)
            
            elif msg_type == "audio_end":
                if audio_processor and audio_processor.is_recording:
                    message_handler.call_handler.stop_silence_timer()
                    
                    # Process audio
                    transcript = await audio_processor.stop_recording_and_process()
                    
                    if transcript:
                        # Reset silence count
                        message_handler.call_handler.reset_silence_count()
                        
                        # Process with AI
                        await message_handler.handle_text_input(transcript)
                    else:
                        # Start timer lại nếu không nhận diện được
                        if message_handler.call_handler.call_initiated:
                            message_handler.call_handler.start_silence_timer(
                                message_handler.on_reminder,
                                message_handler.on_goodbye
                            )
            
            elif msg_type == "clear_history":
                await message_handler.handle_clear_history()
    
    except WebSocketDisconnect:
        logger.info(f"[WebSocket] Client disconnected normally (session: {session_id})")
    except Exception as e:
        # Chỉ log error nếu không phải lỗi disconnect bình thường
        if "1000" not in str(e):  # 1000 = normal closure
            logger.error(f"[WebSocket] Error: {e}", exc_info=True)
        else:
            logger.info(f"[WebSocket] Connection closed (session: {session_id})")
    finally:
        # Cleanup
        message_handler.cleanup()


# Mount static files
app.mount("/", StaticFiles(directory="simple_ui", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_SERVER_PORT", "8002"))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
