# -*- coding: utf-8 -*-
"""
Audio Processor - Xử lý audio recording và ASR
"""
import asyncio
import base64
import logging
from typing import Optional
from fastapi import WebSocket

from src.clients.speech_to_text import ASRClient

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Xử lý audio recording và speech-to-text"""
    
    def __init__(
        self,
        websocket: WebSocket,
        asr_uri: str,
        asr_token: str
    ):
        self.websocket = websocket
        self.asr_uri = asr_uri
        self.asr_token = asr_token
        
        # State
        self.is_recording = False
        self.audio_queue: Optional[asyncio.Queue] = None
        self.is_processing = False  # Flag để prevent duplicate processing
    
    async def start_recording(self):
        """Bắt đầu ghi âm"""
        logger.info("[Audio] Recording started")
        self.is_recording = True
        self.audio_queue = asyncio.Queue()
        
        await self.websocket.send_json({
            "type": "recording_started"
        })
    
    async def add_audio_chunk(self, audio_base64: str):
        """Thêm audio chunk vào queue"""
        if not self.is_recording or not self.audio_queue:
            return
        
        audio_bytes = base64.b64decode(audio_base64)
        await self.audio_queue.put(audio_bytes)
    
    async def stop_recording_and_process(self):
        """Dừng ghi âm và xử lý với ASR"""
        if not self.is_recording or not self.audio_queue:
            return None
        
        # Prevent duplicate processing
        if self.is_processing:
            logger.warning("[Audio] Already processing - skipping duplicate call")
            return None
        
        self.is_processing = True
        logger.info("[Audio] Recording stopped, processing...")
        self.is_recording = False
        
        try:
            # Signal end of stream
            await self.audio_queue.put(None)
            
            # Send thinking status
            await self.websocket.send_json({"type": "thinking"})
            
            # Process audio with ASR
            asr_client = ASRClient(uri=self.asr_uri, token=self.asr_token)
            
            async def audio_generator():
                while True:
                    chunk = await self.audio_queue.get()
                    if chunk is None:
                        break
                    yield chunk
                yield None  # Sentinel
            
            transcript_parts = []
            last_final_transcript = ""
            result_count = 0
            
            async for result in asr_client.stream_audio(audio_generator()):
                result_count += 1
                logger.info(f"[ASR] Result #{result_count}: {result}")
                
                if "transcript" in result and result["transcript"]:
                    is_final = result.get("isFinal", False)
                    
                    if is_final:
                        # Lưu final transcript (có thể có nhiều final, lấy cái cuối)
                        last_final_transcript = result["transcript"]
                        logger.info(f"[ASR] ✅ Final transcript: {last_final_transcript}")
                    else:
                        # Log partial nhưng KHÔNG gửi lên client
                        logger.info(f"[ASR] Partial: {result['transcript']}")
                
                if result.get("error"):
                    logger.error(f"[ASR] Error: {result['error']}")
                    await self.websocket.send_json({
                        "type": "error",
                        "message": f"Lỗi ASR: {result['error']}"
                    })
                    break
            
            logger.info(f"[ASR] Stream ended. Total results: {result_count}, Final transcript: '{last_final_transcript}'")
            
            # Close ASR client
            await asr_client.close()
            
            # Check nếu không có transcript
            if not last_final_transcript:
                await self.websocket.send_json({
                    "type": "error",
                    "message": "Không nhận diện được giọng nói"
                })
                return None
            
            # Gửi transcript lên UI để hiển thị user bubble
            await self.websocket.send_json({
                "type": "transcript",
                "text": last_final_transcript,
                "isFinal": True
            })
            
            logger.info(f"[ASR] Returning final transcript: {last_final_transcript}")
            return last_final_transcript
        
        except Exception as e:
            logger.error(f"[ASR] Error: {e}", exc_info=True)
            await self.websocket.send_json({
                "type": "error",
                "message": f"Lỗi xử lý audio: {str(e)}"
            })
            return None
        finally:
            self.is_processing = False  # Reset flag
