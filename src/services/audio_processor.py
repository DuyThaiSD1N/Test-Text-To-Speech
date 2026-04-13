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
        
        logger.info("[Audio] Recording stopped, processing...")
        self.is_recording = False
        
        # Signal end of stream
        await self.audio_queue.put(None)
        
        # Send thinking status
        await self.websocket.send_json({"type": "thinking"})
        
        # Process audio with ASR
        try:
            asr_client = ASRClient(uri=self.asr_uri, token=self.asr_token)
            
            async def audio_generator():
                while True:
                    chunk = await self.audio_queue.get()
                    if chunk is None:
                        break
                    yield chunk
                yield None  # Sentinel
            
            transcript_parts = []
            async for result in asr_client.stream_audio(audio_generator()):
                if "transcript" in result and result["transcript"]:
                    transcript_parts.append(result["transcript"])
                    logger.info(f"[ASR] Partial: {result['transcript']}")
                    
                    # Send partial transcript to client
                    await self.websocket.send_json({
                        "type": "transcript",
                        "text": result["transcript"],
                        "isFinal": result.get("isFinal", False)
                    })
                
                if result.get("error"):
                    logger.error(f"[ASR] Error: {result['error']}")
                    await self.websocket.send_json({
                        "type": "error",
                        "message": f"Lỗi ASR: {result['error']}"
                    })
                    break
            
            # Close ASR client
            await asr_client.close()
            
            # Get final transcript
            final_transcript = " ".join(transcript_parts).strip()
            
            if not final_transcript:
                await self.websocket.send_json({
                    "type": "error",
                    "message": "Không nhận diện được giọng nói"
                })
                return None
            
            logger.info(f"[ASR] Final transcript: {final_transcript}")
            return final_transcript
        
        except Exception as e:
            logger.error(f"[ASR] Error: {e}", exc_info=True)
            await self.websocket.send_json({
                "type": "error",
                "message": f"Lỗi xử lý audio: {str(e)}"
            })
            return None
