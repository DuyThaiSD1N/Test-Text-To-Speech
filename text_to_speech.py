import asyncio
import base64
import json
import logging
import re
from dataclasses import dataclass
from typing import AsyncIterator

import websockets

logger = logging.getLogger(__name__)

@dataclass
class TTSChunk:
    raw_pcm: bytes
    is_final: bool = False
    duration: float = 0.0
    sample_rate: int = 8000
    text: str = ""
    origin_text: str = ""

class TTSClient:
    def __init__(self, ws_url: str, api_key: str, voice: str, tempo: float = 1.0, max_text_length: int = 500):
        self.ws_url = ws_url
        self.api_key = api_key
        self.voice = voice
        self.tempo = tempo
        self.max_text_length = max_text_length
        
        self.ws = None
        self._lock = asyncio.Lock()
        self._receive_task = None
        self.result_queue = None
        self.is_auth = False
        self.sample_rate = 8000

    async def connect(self):
        """Connect to WebSocket and authenticate"""
        async with self._lock:
            if self.ws is not None:
                try:
                    await self.ws.close()
                except Exception:
                    pass
                finally:
                    self.ws = None
            
            if self._receive_task and not self._receive_task.done():
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
            
            self.result_queue = asyncio.Queue(maxsize=100)
            
            try:
                self.ws = await asyncio.wait_for(
                    websockets.connect(self.ws_url),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                raise Exception("[TTS] Connection timeout")
            except Exception as e:
                raise Exception(f"[TTS] Failed to connect WebSocket: {e}")
            
            logger.info(f"voice {self.voice} tempo {self.tempo}")
            auth_msg = {
                "text": " ", 
                "voice_settings": {
                    "voiceId": self.voice,
                    "resample_rate": 8000,
                    "tempo": self.tempo,
                },
                "generator_config": {
                    "chunk_length_schedule": [1],
                },
                "xi_api_key": self.api_key,
            }
            
            try:
                await asyncio.wait_for(
                    self.ws.send(json.dumps(auth_msg)),
                    timeout=5.0
                )
            except Exception as e:
                await self.ws.close()
                raise Exception(f"[TTS] Failed to send auth: {e}")
            
            try:
                response = await asyncio.wait_for(
                    self.ws.recv(),
                    timeout=5.0
                )
                auth_resp = json.loads(response)
            except asyncio.TimeoutError:
                await self.ws.close()
                raise Exception("[TTS] Failed to read auth response: timeout")
            except Exception as e:
                await self.ws.close()
                raise Exception(f"[TTS] Failed to read auth response: {e}")
            
            status = auth_resp.get("status")
            if status != "authenticated":
                error_msg = auth_resp.get("error", "unknown error")
                await self.ws.close()
                raise Exception(f"[TTS] Authentication failed: {error_msg}")
            
            self.is_auth = True
            if "sampling_rate" in auth_resp:
                self.sample_rate = int(auth_resp["sampling_rate"])
            else:
                self.sample_rate = 8000
            
            logger.info(f"[TTS] WebSocket authenticated: voice={self.voice}, sample_rate={self.sample_rate}")
            
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("[TTS] Receive loop task started")

    async def send_text(self, text: str, end_of_input: bool) -> None:
        async with self._lock:
            if not self.is_auth:
                raise Exception("[TTS] Not authenticated")
            if self.ws is None:
                raise Exception("[TTS] WebSocket not connected")
            
            msg = {
                "text": text,
                "end_of_input": end_of_input,
            }
            try:
                await self.ws.send(json.dumps(msg))
                logger.info(f"[TTS] sent text: '{text}', end_of_input={end_of_input}")
            except Exception as e:
                raise Exception(f"[TTS] Failed to send text: {e}")

    async def reset(self) -> None:
        async with self._lock:
            if not self.is_auth or self.ws is None:
                raise Exception("[TTS] Not ready")
            msg = {"reset": True}
            try:
                await self.ws.send(json.dumps(msg))
            except Exception as e:
                raise Exception(f"[TTS] Failed to send reset: {e}")

    async def _receive_loop(self) -> None:
        logger.info("[TTS] Receive loop started")
        try:
            while True:
                if self.ws is None:
                    break
                
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=60.0)
                    msg = json.loads(response)
                except asyncio.CancelledError:
                    break
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"[TTS] receive error: {e}")
                    break
                
                if "error" in msg:
                    continue
                if msg.get("status") == "reset":
                    continue
                
                chunk = TTSChunk(raw_pcm=b"")
                if "audio" in msg and msg["audio"]:
                    try:
                        chunk.raw_pcm = base64.b64decode(msg["audio"])
                    except Exception:
                        pass
                
                if "isFinal" in msg:
                    chunk.is_final = bool(msg["isFinal"])
                if "duration" in msg:
                    chunk.duration = float(msg["duration"])
                if "sample_rate" in msg:
                    chunk.sample_rate = int(msg["sample_rate"])
                if "text" in msg:
                    chunk.text = str(msg["text"])
                if "origin_text" in msg:
                    chunk.origin_text = str(msg["origin_text"])
                
                if self.result_queue:
                    try:
                        await self.result_queue.put(chunk)
                    except Exception:
                        pass
                
                if chunk.is_final:
                    pass
        except Exception:
            pass
        finally:
            if self.result_queue:
                try:
                    await self.result_queue.put(None)
                except Exception:
                    pass

    async def get_result_channel(self) -> AsyncIterator[TTSChunk]:
        if self.result_queue is None:
            raise Exception("[TTS] Not connected")
        while True:
            chunk = await self.result_queue.get()
            if chunk is None:
                break
            yield chunk

    def _normalize_roman_numerals(self, text: str):
        """Chuyển đổi số La Mã sang số Ả Rập để TTS đọc đúng."""
        roman_map = {
            'XX': '20', 'XIX': '19', 'XVIII': '18', 'XVII': '17', 'XVI': '16',
            'XV': '15', 'XIV': '14', 'XIII': '13', 'XII': '12', 'XI': '11',
            'X': '10', 'IX': '9', 'VIII': '8', 'VII': '7', 'VI': '6',
            'V': '5', 'IV': '4', 'III': '3', 'II': '2', 'I': '1'
        }
        
        # Regex tìm các số La Mã đứng độc lập hoặc sau các từ như "khóa", "thế kỷ", "thứ"
        # Tránh khớp với các từ bình thường có chứa chữ cái La Mã
        for roman, arabic in roman_map.items():
            # Sử dụng boundary \b để đảm bảo khớp nguyên từ
            pattern = rf'\b{roman}\b'
            text = re.sub(pattern, arabic, text)
        return text

    def _split_text_by_sentences(self, text: str, max_length: int = 500):
        if len(text) <= max_length:
            return [text]
        
        sentence_endings = r'[.!?;]'
        sentences = re.split(f'({sentence_endings})', text)
        
        combined = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                combined.append(sentences[i] + sentences[i+1])
            else:
                combined.append(sentences[i])
        
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            combined.append(sentences[-1])
        
        chunks = []
        current_chunk = ""
        for sentence in combined:
            sentence = sentence.strip()
            if not sentence: continue
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += (" " + sentence if current_chunk else sentence)
            else:
                if current_chunk: chunks.append(current_chunk)
                current_chunk = sentence
        if current_chunk: chunks.append(current_chunk)
        
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= max_length:
                final_chunks.append(chunk)
            else:
                parts = chunk.split(',')
                temp_chunk = ""
                for part in parts:
                    if len(temp_chunk) + len(part) + 1 <= max_length:
                        temp_chunk += ("," + part if temp_chunk else part)
                    else:
                        if temp_chunk: final_chunks.append(temp_chunk)
                        temp_chunk = part
                if temp_chunk: final_chunks.append(temp_chunk)
        
        very_final_chunks = []
        for chunk in final_chunks:
            if len(chunk) <= max_length:
                very_final_chunks.append(chunk)
            else:
                words = chunk.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= max_length:
                        temp_chunk += (" " + word if temp_chunk else word)
                    else:
                        if temp_chunk: very_final_chunks.append(temp_chunk)
                        temp_chunk = word
                if temp_chunk: very_final_chunks.append(temp_chunk)
        
        return [c.strip() for c in very_final_chunks if c.strip()]

    async def _ensure_connected(self):
        if self.ws is None:
            await self.connect()

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        await self._ensure_connected()
        
        # Tiền xử lý văn bản (Số La Mã -> Số đếm)
        text = self._normalize_roman_numerals(text)
        
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await asyncio.wait_for(self._receive_task, timeout=1.0)
            except Exception:
                pass
            self._receive_task = None
        
        text_chunks = self._split_text_by_sentences(text, self.max_text_length)
        
        for i, chunk_text in enumerate(text_chunks):
            is_last_chunk = (i == len(text_chunks) - 1)
            try:
                await self.send_text(chunk_text, is_last_chunk)
            except Exception as e:
                try:
                    await self._ensure_connected()
                    await self.send_text(chunk_text, is_last_chunk)
                except Exception:
                    continue
            
            chunk_received = False
            timeout_seconds = 2
            max_timeout_count = 3
            timeout_count = 0
            
            while True:
                try:
                    if self.ws is None: break
                    
                    response = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=timeout_seconds
                    )
                    msg = json.loads(response)
                    
                    timeout_count = 0
                    if "error" in msg: break
                    if msg.get("status") == "reset": continue
                    
                    if "audio" in msg and msg["audio"]:
                        try:
                            pcm = base64.b64decode(msg["audio"])
                            chunk_received = True
                            yield pcm
                        except Exception:
                            pass
                    
                    if msg.get("isFinal", False):
                        break
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    if not chunk_received:
                        if timeout_count < max_timeout_count: continue
                        else: break
                    else:
                        if timeout_count >= 2: break
                        timeout_seconds = 1
                        continue
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception:
                    break
        
        if self.ws is not None and self.is_auth:
            self._receive_task = asyncio.create_task(self._receive_loop())

    async def close(self):
        async with self._lock:
            if self._receive_task and not self._receive_task.done():
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
            if self.ws is not None:
                try:
                    await self.ws.close()
                except Exception:
                    pass
                finally:
                    self.ws = None
                    self.is_auth = False
