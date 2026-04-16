# -*- coding: utf-8 -*-
"""
Message Handler - Xử lý các loại message từ WebSocket
"""
import asyncio
import base64
import logging
from typing import Optional, List
from fastapi import WebSocket

from src.services.ai_logic import fast_stream
from src.clients.text_to_speech import TTSClient
from src.services.redis_store import RedisConversationStore, HumanMessage, AIMessage
from src.services.call_handler import CallHandler

logger = logging.getLogger(__name__)


class MessageHandler:
    """Xử lý các message types từ WebSocket client"""
    
    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        tts_client: Optional[TTSClient] = None,
        redis_store: Optional[RedisConversationStore] = None
    ):
        self.websocket = websocket
        self.session_id = session_id
        self.tts_client = tts_client
        self.redis_store = redis_store
        
        # State
        self.conversation_history: List = []
        self.customer_context = ""
        self.customer_title = "Quý khách"
        
        # Call handler
        self.call_handler = CallHandler(
            customer_title=self.customer_title,
            silence_timeout=10  # Tăng lên 10 giây
        )
        
        # Bot speaking state
        self.is_bot_speaking = False
        
        # User interaction state
        self.is_user_typing = False  # Track xem user có đang typing không
        self.typing_timeout_task: Optional[asyncio.Task] = None  # Task để reset typing state
        
        # WebSocket state
        self.is_connected = True
    
    async def safe_send_json(self, data: dict) -> bool:
        """
        Safely send JSON to websocket with error handling.
        Returns True if successful, False if failed.
        """
        try:
            await self.websocket.send_json(data)
            self.is_connected = True  # Reset on success
            return True
        except Exception as e:
            logger.warning(f"[WebSocket] Failed to send {data.get('type', 'unknown')}: {e}")
            self.is_connected = False
            return False
    
    async def send_message_with_tts(self, text: str, save_to_history: bool = True):
        """Gửi message và TTS audio"""
        if save_to_history:
            msg = AIMessage(content=text)
            try:
                if self.redis_store and self.redis_store.redis:
                    await self.redis_store.save_message(self.session_id, msg)
            except Exception:
                pass
            self.conversation_history.append(msg)
        
        # Send agent_response_start để tạo bubble mới
        logger.info(f"[TTS] Sending text response, is_connected: {self.is_connected}")
        if not await self.safe_send_json({
            "type": "agent_response_start"
        }):
            logger.warning("[TTS] Failed to send start, stopping")
            return
        
        # Send text as tokens (để hiển thị từng từ)
        words = text.split()
        for word in words:
            if not await self.safe_send_json({
                "type": "agent_response_token",
                "token": word + " "
            }):
                logger.warning("[TTS] Failed to send token, stopping")
                return
        
        # Send final response
        if not await self.safe_send_json({
            "type": "agent_response",
            "text": text
        }):
            logger.warning("[TTS] Failed to send text, stopping")
            return
        
        # Send TTS
        if self.tts_client:
            logger.info("[TTS] Starting audio synthesis")
            try:
                self.is_bot_speaking = True  # Bot bắt đầu nói
                chunk_count = 0
                async for chunk in self.tts_client.synthesize(text):
                    if chunk:
                        chunk_count += 1
                        audio_base64 = base64.b64encode(chunk).decode('utf-8')
                        if not await self.safe_send_json({
                            "type": "audio_response",
                            "audio": audio_base64,
                            "sampleRate": 8000
                        }):
                            logger.warning(f"[TTS] Failed to send audio chunk {chunk_count}, stopping")
                            self.is_bot_speaking = False
                            return
                logger.info(f"[TTS] Sent {chunk_count} audio chunks")
                await self.safe_send_json({"type": "audio_end"})
                self.is_bot_speaking = False  # Bot nói xong
            except Exception as e:
                logger.error(f"[TTS] Error: {e}")
                self.is_bot_speaking = False
        else:
            logger.warning("[TTS] TTS client not configured")
    
    async def handle_text_input(self, text: str):
        """Xử lý text input từ user"""
        # Đánh dấu user KHÔNG còn typing
        self.is_user_typing = False
        
        # Cancel typing timeout task nếu có
        if self.typing_timeout_task and not self.typing_timeout_task.done():
            self.typing_timeout_task.cancel()
            self.typing_timeout_task = None
        
        # Stop timer và reset silence count
        self.call_handler.stop_silence_timer()
        self.call_handler.reset_silence_count()
        
        # Kiểm tra unclear text
        is_unclear = self.call_handler.is_unclear_text(text)
        if is_unclear:
            self.call_handler.unclear_count += 1
            logger.info(f"[Agent] Unclear text detected (count: {self.call_handler.unclear_count}/2)")
            
            # Nếu đã 2 lần không rõ → Kết thúc
            if self.call_handler.unclear_count >= 2:
                logger.info("[Agent] 2 unclear attempts - ending call")
                goodbye_msg = f"Dạ, em xin lỗi vì không nghe rõ. Em xin phép kết thúc cuộc gọi. Chúc {self.customer_title} một ngày tốt lành ạ!"
                
                await self.safe_send_json({
                    "type": "agent_response",
                    "text": goodbye_msg
                })
                
                # TTS
                if self.tts_client:
                    try:
                        self.is_bot_speaking = True  # Bot bắt đầu nói
                        async for chunk in self.tts_client.synthesize(goodbye_msg):
                            if chunk:
                                audio_base64 = base64.b64encode(chunk).decode('utf-8')
                                await self.safe_send_json({
                                    "type": "audio_response",
                                    "audio": audio_base64,
                                    "sampleRate": 8000
                                })
                        await self.safe_send_json({"type": "audio_end"})
                        self.is_bot_speaking = False  # Bot nói xong
                    except Exception as e:
                        logger.error(f"[TTS] Error: {e}")
                        self.is_bot_speaking = False
                
                # End call
                await self.safe_send_json({
                    "type": "call_ended",
                    "reason": "unclear_speech"
                })
                return
        
        # Kiểm tra rejection
        is_rejection = self.call_handler.is_rejection(text)
        if is_rejection:
            self.call_handler.rejection_count += 1
            logger.info(f"[Agent] Rejection detected (count: {self.call_handler.rejection_count}/2)")
        
        logger.info(f"[Agent] Processing: {repr(text)}")
        
        # Gửi thinking
        await self.safe_send_json({"type": "thinking"})
        
        # Thêm rejection count và unclear count vào context
        context_parts = [self.customer_context]
        
        if self.call_handler.unclear_count > 0:
            context_parts.append(f"\n[TRẠNG THÁI: Khách nói không rõ {self.call_handler.unclear_count}/2 lần]")
            if self.call_handler.unclear_count == 1:
                context_parts.append("\n[CHỈ THỊ: Lần 1 không rõ. Hỏi lại lịch sự: 'Dạ, em xin lỗi, em không nghe rõ. {gender} có thể nói lại được không ạ?']")
        
        if self.call_handler.rejection_count > 0:
            context_parts.append(f"\n[TRẠNG THÁI: Khách đã từ chối {self.call_handler.rejection_count}/2 lần]")
            if self.call_handler.rejection_count >= 2:
                context_parts.append("\n[CHỈ THỊ: Đây là lần từ chối thứ 2. BẮT BUỘC phải xác nhận và kết thúc: 'Dạ vâng ạ, em hiểu {gender} không có nhu cầu lúc này. Em cảm ơn {gender} đã lắng nghe. Chúc {gender} một ngày tốt lành ạ!']")
            elif self.call_handler.rejection_count == 1:
                context_parts.append("\n[CHỈ THỊ: Đây là lần từ chối thứ 1. Nhắc nhở về ưu đãi: 'Dạ em hiểu ạ. Nhưng tháng này đang có ưu đãi giảm 20% phí bảo hiểm và tặng kèm bảo hiểm tai nạn cá nhân. Nếu không gia hạn bây giờ thì {gender} sẽ bỏ lỡ ưu đãi này ạ. {gender} xem xét giúp em nhé?']")
        
        full_context = "".join(context_parts)
        
        # Gọi AI với streaming
        try:
            response_parts = []
            first_chunk = True
            
            async for token in fast_stream(
                text,
                self.conversation_history,
                full_context,
                self.customer_title,
                self.session_id
            ):
                response_parts.append(token)
                
                if first_chunk:
                    await self.safe_send_json({
                        "type": "agent_response_start"
                    })
                    first_chunk = False
                
                await self.safe_send_json({
                    "type": "agent_response_token",
                    "token": token
                })
            
            response = "".join(response_parts).strip()
            
            if not response:
                response = "Xin lỗi, em không hiểu. Anh/chị có thể nói rõ hơn được không?"
            
            logger.info(f"[Agent] Response: {repr(response[:100])}...")
            
            # Save to Redis
            user_msg = HumanMessage(content=text)
            ai_msg = AIMessage(content=response)
            
            try:
                if self.redis_store and self.redis_store.redis:
                    await self.redis_store.save_message(self.session_id, user_msg)
                    await self.redis_store.save_message(self.session_id, ai_msg)
            except Exception as e:
                logger.warning(f"[Redis] Failed to save messages: {e}")
            
            # Update local history
            self.conversation_history.append(user_msg)
            self.conversation_history.append(ai_msg)
            
            # Lưu response để check farewell
            self.call_handler.last_agent_response = response
            
            # Gửi response
            await self.safe_send_json({
                "type": "agent_response",
                "text": response
            })
            
            # TTS
            if self.tts_client:
                try:
                    self.is_bot_speaking = True  # Bot bắt đầu nói
                    async for chunk in self.tts_client.synthesize(response):
                        if chunk:
                            audio_base64 = base64.b64encode(chunk).decode('utf-8')
                            await self.safe_send_json({
                                "type": "audio_response",
                                "audio": audio_base64,
                                "sampleRate": 8000
                            })
                    await self.safe_send_json({"type": "audio_end"})
                    self.is_bot_speaking = False  # Bot nói xong
                except Exception as e:
                    logger.error(f"[TTS] Error: {e}")
                    self.is_bot_speaking = False
            
            # Check farewell và gửi call_ended
            if self.call_handler.is_farewell_message(response):
                logger.info("[Call] Farewell detected - ending call")
                await self.safe_send_json({
                    "type": "call_ended",
                    "reason": "farewell"
                })
        
        except Exception as e:
            logger.error(f"[Agent] Error: {e}", exc_info=True)
            await self.safe_send_json({
                "type": "error",
                "message": f"Lỗi xử lý: {str(e)}"
            })
    
    async def handle_init_call(self, data: dict):
        """Xử lý init call"""
        title = data.get("title", "Quý khách")
        name = data.get("name", "")
        vehicle_type = data.get("vehicleType", "")
        plate = data.get("plate", "")
        expire = data.get("expire", "")
        
        self.customer_title = title
        
        # Tạo context với thông tin chi tiết về ngày hết hạn và loại xe
        context_parts = [f"Khách hàng: {title} {name}"]
        
        if vehicle_type:
            context_parts.append(f"Loại xe: {vehicle_type}")
        
        context_parts.append(f"Biển số: {plate}")
        
        if expire:
            from datetime import datetime
            try:
                expire_date = datetime.strptime(expire, "%Y-%m-%d")
                today = datetime.now()
                
                # Format ngày theo dd/mm/yyyy
                expire_formatted = expire_date.strftime("%d/%m/%Y")
                
                # Tính số ngày còn lại hoặc đã quá hạn
                days_diff = (expire_date - today).days
                
                if days_diff < 0:
                    # Đã hết hạn
                    context_parts.append(f"Hạn BH: {expire_formatted} (ĐÃ HẾT HẠN {abs(days_diff)} ngày)")
                elif days_diff == 0:
                    context_parts.append(f"Hạn BH: {expire_formatted} (HẾT HẠN HÔM NAY)")
                elif days_diff <= 30:
                    context_parts.append(f"Hạn BH: {expire_formatted} (còn {days_diff} ngày)")
                else:
                    context_parts.append(f"Hạn BH: {expire_formatted} (còn {days_diff} ngày)")
            except ValueError:
                context_parts.append(f"Hạn BH: {expire}")
        
        self.customer_context = "\n".join(context_parts)
        self.call_handler.customer_title = title
        
        logger.info(f"[Agent] Init call: {self.customer_context}")
        
        # Stop timer và init call state
        self.call_handler.stop_silence_timer()
        self.call_handler.call_initiated = True
        self.call_handler.silence_count = 0

        # Save context to Redis
        try:
            if self.redis_store and self.redis_store.redis:
                await self.redis_store.save_context(
                    self.session_id,
                    self.customer_context,
                    self.customer_title
                )
        except Exception as e:
            logger.warning(f"[Redis] Failed to save context: {e}")
        
        # Gửi thinking
        await self.safe_send_json({"type": "thinking"})
        
        # Tạo lời chào với logic kiểm tra hạn bảo hiểm
        greeting = f"Dạ, em xin chào {title} {name}! Em gọi từ bộ phận bảo hiểm xe. "
        
        # Tạo phần mô tả xe
        vehicle_desc = f"xe {vehicle_type} biển số {plate}" if vehicle_type else f"xe biển số {plate}"
        
        if expire:
            from datetime import datetime
            try:
                # Parse expire date (format: YYYY-MM-DD)
                expire_date = datetime.strptime(expire, "%Y-%m-%d")
                today = datetime.now()
                
                # Format ngày theo dd/mm/yyyy
                expire_formatted = expire_date.strftime("%d/%m/%Y")
                
                # So sánh ngày
                days_diff = (expire_date - today).days
                
                if days_diff < 0:
                    # Đã hết hạn
                    greeting += f"Em thấy {vehicle_desc} đã hết hạn bảo hiểm từ ngày {expire_formatted}, {title} có muốn em tư vấn gia hạn không ạ?"
                elif days_diff == 0:
                    # Hết hạn hôm nay
                    greeting += f"Em thấy {vehicle_desc} hết hạn bảo hiểm hôm nay ({expire_formatted}), {title} có muốn em tư vấn gia hạn không ạ?"
                elif days_diff <= 7:
                    # Sắp hết hạn trong 7 ngày
                    greeting += f"Em thấy {vehicle_desc} sắp hết hạn bảo hiểm vào ngày {expire_formatted} (còn {days_diff} ngày), {title} có muốn em tư vấn gia hạn không ạ?"
                elif days_diff <= 30:
                    # Sắp hết hạn trong 30 ngày
                    greeting += f"Em thấy {vehicle_desc} sắp hết hạn bảo hiểm vào ngày {expire_formatted}, {title} có muốn em tư vấn gia hạn không ạ?"
                else:
                    # Còn hạn dài (> 30 ngày)
                    greeting += f"Em thấy {vehicle_desc} còn hạn bảo hiểm đến ngày {expire_formatted}, {title} có muốn em tư vấn về bảo hiểm không ạ?"
            except ValueError:
                # Nếu parse lỗi, dùng message mặc định
                greeting += f"Em thấy {vehicle_desc} sắp hết hạn bảo hiểm, {title} có muốn em tư vấn gia hạn không ạ?"
        else:
            greeting += f"Em muốn tư vấn bảo hiểm cho {vehicle_desc} của {title}."
        
        # Save to Redis
        init_msg = HumanMessage(content="[Cuộc gọi bắt đầu]")
        greeting_msg = AIMessage(content=greeting)
        
        try:
            if self.redis_store and self.redis_store.redis:
                await self.redis_store.save_message(self.session_id, init_msg)
                await self.redis_store.save_message(self.session_id, greeting_msg)
        except Exception as e:
            logger.warning(f"[Redis] Failed to save greeting: {e}")
        
        # Update local history
        self.conversation_history.append(init_msg)
        self.conversation_history.append(greeting_msg)
        
        # Lưu response
        self.call_handler.last_agent_response = greeting
        
        # Gửi response start
        await self.safe_send_json({
            "type": "agent_response_start"
        })
        
        # Stream greeting
        words = greeting.split()
        for word in words:
            await self.safe_send_json({
                "type": "agent_response_token",
                "token": word + " "
            })
        
        # TTS
        if self.tts_client:
            try:
                self.is_bot_speaking = True  # Bot bắt đầu nói
                async for chunk in self.tts_client.synthesize(greeting):
                    if chunk:
                        audio_base64 = base64.b64encode(chunk).decode('utf-8')
                        await self.safe_send_json({
                            "type": "audio_response",
                            "audio": audio_base64,
                            "sampleRate": 8000
                        })
                await self.safe_send_json({"type": "audio_end"})
                self.is_bot_speaking = False  # Bot nói xong
            except Exception as e:
                logger.error(f"[TTS] Error: {e}")
                self.is_bot_speaking = False
    
    async def handle_typing(self):
        """Xử lý typing indicator - User đang gõ"""
        # Đánh dấu user đang typing
        self.is_user_typing = True
        
        # STOP timer ngay lập tức khi user bắt đầu typing
        self.call_handler.stop_silence_timer()
        
        # RESET silence count vì user đang tương tác
        self.call_handler.reset_silence_count()
        
        logger.debug("[Timeout] User is typing - timer stopped, silence count reset")
        
        # Cancel typing timeout task cũ nếu có
        if self.typing_timeout_task and not self.typing_timeout_task.done():
            self.typing_timeout_task.cancel()
        
        # Tạo task mới để reset typing state sau 5 giây không có typing event
        # KHÔNG start timer ở đây - chỉ reset state
        async def reset_typing_after_timeout():
            try:
                await asyncio.sleep(5)  # Chờ 5 giây (lâu hơn throttle 1s của UI)
                self.is_user_typing = False
                logger.debug("[Timeout] User stopped typing (timeout) - state reset only, NOT starting timer")
            except asyncio.CancelledError:
                pass
        
        self.typing_timeout_task = asyncio.create_task(reset_typing_after_timeout())
    
    async def handle_audio_playback_ended(self):
        """Xử lý khi audio phát xong - CHỜ 3 GIÂY trước khi start timer"""
        # Đánh dấu bot đã nói xong
        self.is_bot_speaking = False
        
        # Kiểm tra farewell
        if self.call_handler.is_farewell_message(self.call_handler.last_agent_response):
            logger.info("[Timeout] Farewell message detected - NOT starting timer")
            return
        
        if self.call_handler.silence_count >= 2:
            logger.info("[Timeout] Goodbye already sent, not starting timer")
            return
        
        # Nếu đang ending, không start timer
        if self.call_handler.is_ending:
            logger.info("[Timeout] Call is ending - NOT starting timer")
            return
        
        # Chờ 3 giây để user có thời gian suy nghĩ trước khi bắt đầu đếm im lặng
        if self.call_handler.call_initiated:
            logger.info("[Timeout] Audio ended - waiting 3s before starting timer")
            await asyncio.sleep(3)
            
            # Kiểm tra lại xem có đang tương tác không
            # CHỈ start timer nếu:
            # 1. Call đã initiated
            # 2. Chưa đến lần nhắc thứ 2
            # 3. Bot KHÔNG đang nói
            # 4. User KHÔNG đang typing
            # 5. Call KHÔNG đang ending
            if (self.call_handler.call_initiated and 
                self.call_handler.silence_count < 2 and 
                not self.is_bot_speaking and
                not self.is_user_typing and
                not self.call_handler.is_ending):  # ⬅️ THÊM: Kiểm tra is_ending
                self.call_handler.start_silence_timer(
                    self.on_reminder,
                    self.on_goodbye
                )
                logger.info("[Timeout] Timer started after audio ended")
            else:
                logger.debug(f"[Timeout] Not starting timer - bot_speaking={self.is_bot_speaking}, user_typing={self.is_user_typing}, is_ending={self.call_handler.is_ending}")
    
    async def handle_clear_history(self):
        """Xử lý clear history"""
        try:
            if self.redis_store and self.redis_store.redis:
                await self.redis_store.clear_session(self.session_id)
        except Exception as e:
            logger.warning(f"[Redis] Failed to clear session: {e}")
        
        # Clear local state
        self.conversation_history.clear()
        self.customer_context = ""
        
        # Reset call handler
        self.call_handler.reset()
        
        await self.safe_send_json({
            "type": "info",
            "message": "Đã xóa lịch sử"
        })
    
    async def on_reminder(self, text: str):
        """Callback cho reminder"""
        # Check nếu call đã bị reset thì không gửi
        if not self.call_handler.call_initiated:
            logger.info("[Timeout] Call not initiated - skipping reminder")
            return
        await self.send_message_with_tts(text, save_to_history=True)
    
    async def on_goodbye(self, text: str):
        """Callback cho goodbye"""
        # Check nếu call đã bị reset thì không gửi
        if not self.call_handler.call_initiated:
            logger.info("[Timeout] Call not initiated - skipping goodbye")
            return
        await self.send_message_with_tts(text, save_to_history=True)
        await asyncio.sleep(1)
        await self.safe_send_json({
            "type": "call_ended",
            "reason": "silence_timeout"
        })
        await self.websocket.close()
    
    async def load_from_redis(self):
        """Load session từ Redis"""
        try:
            if self.redis_store and self.redis_store.redis:
                self.conversation_history = await self.redis_store.get_history(self.session_id)
                self.customer_context, self.customer_title = await self.redis_store.get_context(self.session_id)
                
                if self.conversation_history:
                    logger.info(f"[Session] Restored {len(self.conversation_history)} messages from Redis")
        except Exception as e:
            logger.warning(f"[Redis] Failed to load session: {e}")
    
    async def extend_ttl(self):
        """Extend TTL cho session"""
        try:
            if self.redis_store and self.redis_store.redis:
                await self.redis_store.extend_ttl(self.session_id, ttl=3600)
        except Exception as e:
            logger.warning(f"[Redis] Failed to extend TTL: {e}")
    
    def cleanup(self):
        """Cleanup khi disconnect"""
        self.call_handler.stop_silence_timer()
        
        # Cancel typing timeout task
        if self.typing_timeout_task and not self.typing_timeout_task.done():
            self.typing_timeout_task.cancel()
        
        logger.info(f"[MessageHandler] Cleanup completed (session: {self.session_id})")
