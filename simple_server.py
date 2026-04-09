# -*- coding: utf-8 -*-
"""
Simple Voice Agent Server - Viết lại từ đầu
"""
import asyncio
import json
import os
import logging
import uuid
from fastapi import FastAPI, WebSocket
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

# Import AI logic
from ai_logic import process_user_message_stream_simple
from langchain_core.messages import HumanMessage, AIMessage
from text_to_speech import TTSClient
from redis_store import RedisConversationStore

# TTS Client
TTS_WS_URL = os.getenv("TTS_WS_URL")
TTS_API_KEY = os.getenv("TTS_API_KEY")
TTS_VOICE = os.getenv("TTS_VOICE", "thuyanh-north")

tts_client = None
if TTS_WS_URL and TTS_API_KEY:
    tts_client = TTSClient(ws_url=TTS_WS_URL, api_key=TTS_API_KEY, voice=TTS_VOICE)
    logger.info(f"[TTS] Initialized with voice: {TTS_VOICE}")
else:
    logger.warning("[TTS] Not configured - will work without audio")

# Redis Store (Optional)
redis_store = None
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"

if USE_REDIS:
    redis_store = RedisConversationStore()

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
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
    
    # ═══════════════════════════════════════════════════════
    # SESSION ID (Unique per connection)
    # ═══════════════════════════════════════════════════════
    session_id = str(uuid.uuid4())
    logger.info(f"[Session] Created: {session_id}")
    
    # ═══════════════════════════════════════════════════════
    # LOAD FROM REDIS (if available)
    # ═══════════════════════════════════════════════════════
    conversation_history = []
    customer_context = ""
    customer_title = "Quý khách"
    
    try:
        if redis_store and redis_store.redis:
            conversation_history = await redis_store.get_history(session_id)
            customer_context, customer_title = await redis_store.get_context(session_id)
            
            if conversation_history:
                logger.info(f"[Session] Restored {len(conversation_history)} messages from Redis")
    except Exception as e:
        logger.warning(f"[Redis] Failed to load session: {e}")
    
    try:
        while True:
            # Nhận message từ client
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")
            
            logger.info(f"[WebSocket] Received: {msg_type}")
            
            # Extend TTL on activity
            try:
                if redis_store and redis_store.redis:
                    await redis_store.extend_ttl(session_id, ttl=3600)
            except Exception as e:
                logger.warning(f"[Redis] Failed to extend TTL: {e}")
            
            if msg_type == "text_input":
                # Xử lý text input
                text = msg.get("text", "").strip()
                if not text:
                    continue
                
                logger.info(f"[Agent] Processing: {repr(text)}")
                
                # Gửi thinking
                await websocket.send_json({"type": "thinking"})
                
                # Gọi AI
                try:
                    response_parts = []
                    async for token in process_user_message_stream_simple(
                        text, 
                        conversation_history, 
                        customer_context, 
                        customer_title
                    ):
                        response_parts.append(token)
                    
                    response = "".join(response_parts).strip()
                    
                    if not response:
                        response = "Xin lỗi, em không hiểu. Anh/chị có thể nói rõ hơn được không?"
                    
                    logger.info(f"[Agent] Response: {repr(response[:100])}...")
                    
                    # ═══════════════════════════════════════════════════════
                    # SAVE TO REDIS
                    # ═══════════════════════════════════════════════════════
                    user_msg = HumanMessage(content=text)
                    ai_msg = AIMessage(content=response)
                    
                    try:
                        if redis_store and redis_store.redis:
                            await redis_store.save_message(session_id, user_msg)
                            await redis_store.save_message(session_id, ai_msg)
                            logger.info(f"[Redis] Saved 2 messages for session {session_id}")
                    except Exception as e:
                        logger.warning(f"[Redis] Failed to save messages: {e}")
                    
                    # Update local history
                    conversation_history.append(user_msg)
                    conversation_history.append(ai_msg)
                    
                    # Gửi response
                    await websocket.send_json({
                        "type": "agent_response",
                        "text": response
                    })
                    logger.info("[Agent] ✅ Response sent to client")
                    
                    # TTS - Gửi audio
                    if tts_client:
                        try:
                            import base64
                            logger.info("[TTS] Starting synthesis...")
                            async for chunk in tts_client.synthesize(response):
                                if chunk:
                                    audio_base64 = base64.b64encode(chunk).decode('utf-8')
                                    await websocket.send_json({
                                        "type": "audio_response",
                                        "audio": audio_base64,
                                        "sampleRate": 8000
                                    })
                            
                            await websocket.send_json({"type": "audio_end"})
                            logger.info("[TTS] ✅ Audio sent")
                        except Exception as tts_err:
                            logger.error(f"[TTS] Error: {tts_err}")
                    
                except Exception as e:
                    logger.error(f"[Agent] Error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Lỗi xử lý: {str(e)}"
                    })
            
            elif msg_type == "init_call":
                # Khởi tạo cuộc gọi
                data = msg.get("data", {})
                title = data.get("title", "Quý khách")
                name = data.get("name", "")
                plate = data.get("plate", "")
                expire = data.get("expire", "")
                
                customer_title = title
                customer_context = f"Khách hàng: {title} {name}\nBiển số: {plate}\nHạn BH: {expire}"
                
                logger.info(f"[Agent] Init call: {customer_context}")
                
                # ═══════════════════════════════════════════════════════
                # SAVE CONTEXT TO REDIS
                # ═══════════════════════════════════════════════════════
                try:
                    if redis_store and redis_store.redis:
                        await redis_store.save_context(
                            session_id,
                            customer_context,
                            customer_title
                        )
                        logger.info(f"[Redis] Saved context for session {session_id}")
                except Exception as e:
                    logger.warning(f"[Redis] Failed to save context: {e}")
                
                # Gửi thinking
                await websocket.send_json({"type": "thinking"})
                
                # Tạo lời chào
                greeting = f"Dạ, em xin chào {title} {name}! Em gọi từ bộ phận bảo hiểm xe. "
                if expire:
                    greeting += f"Em thấy xe biển số {plate} sắp hết hạn bảo hiểm, {title} có muốn em tư vấn gia hạn không ạ?"
                else:
                    greeting += f"Em muốn tư vấn bảo hiểm cho xe {plate} của {title}."
                
                # ═══════════════════════════════════════════════════════
                # SAVE TO REDIS
                # ═══════════════════════════════════════════════════════
                init_msg = HumanMessage(content="[Cuộc gọi bắt đầu]")
                greeting_msg = AIMessage(content=greeting)
                
                try:
                    if redis_store and redis_store.redis:
                        await redis_store.save_message(session_id, init_msg)
                        await redis_store.save_message(session_id, greeting_msg)
                        logger.info(f"[Redis] Saved greeting for session {session_id}")
                except Exception as e:
                    logger.warning(f"[Redis] Failed to save greeting: {e}")
                
                # Update local history
                conversation_history.append(init_msg)
                conversation_history.append(greeting_msg)
                
                # Gửi response
                await websocket.send_json({
                    "type": "agent_response",
                    "text": greeting
                })
                logger.info("[Agent] ✅ Greeting sent")
                
                # TTS - Gửi audio
                if tts_client:
                    try:
                        import base64
                        logger.info("[TTS] Starting greeting synthesis...")
                        async for chunk in tts_client.synthesize(greeting):
                            if chunk:
                                audio_base64 = base64.b64encode(chunk).decode('utf-8')
                                await websocket.send_json({
                                    "type": "audio_response",
                                    "audio": audio_base64,
                                    "sampleRate": 8000
                                })
                        
                        await websocket.send_json({"type": "audio_end"})
                        logger.info("[TTS] ✅ Greeting audio sent")
                    except Exception as tts_err:
                        logger.error(f"[TTS] Error: {tts_err}")
            
            elif msg_type == "clear_history":
                # ═══════════════════════════════════════════════════════
                # CLEAR FROM REDIS
                # ═══════════════════════════════════════════════════════
                try:
                    if redis_store and redis_store.redis:
                        await redis_store.clear_session(session_id)
                        logger.info(f"[Redis] Cleared session {session_id}")
                except Exception as e:
                    logger.warning(f"[Redis] Failed to clear session: {e}")
                
                conversation_history.clear()
                customer_context = ""
                
                await websocket.send_json({
                    "type": "info",
                    "message": "Đã xóa lịch sử"
                })
    
    except Exception as e:
        logger.error(f"[WebSocket] Error: {e}", exc_info=True)
    finally:
        logger.info(f"[WebSocket] Client disconnected (session: {session_id})")

# Mount static files
app.mount("/", StaticFiles(directory="simple_ui", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_SERVER_PORT", "8002"))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
