# -*- coding: utf-8 -*-
"""
Call Handler - Business logic cho voice call
Xử lý farewell detection, silence timeout, và call state management
"""
import asyncio
import base64
import logging
import re
from typing import Optional, Callable, Any
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)


class CallHandler:
    """
    Xử lý logic business cho voice call:
    - Farewell detection
    - Silence timeout với 2 lần nhắc nhở
    - Call state management
    """
    
    def __init__(
        self,
        customer_title: str = "Quý khách",
        silence_timeout: int = 5
    ):
        """
        Args:
            customer_title: Danh xưng khách hàng (Anh/Chị/Cô/Chú)
            silence_timeout: Thời gian im lặng (giây) trước khi nhắc nhở
        """
        self.customer_title = customer_title
        self.silence_timeout = silence_timeout
        
        # State
        self.silence_count = 0
        self.call_initiated = False
        self.last_agent_response = ""
        self.silence_timer_task: Optional[asyncio.Task] = None
    
    @staticmethod
    def is_farewell_message(text: str) -> bool:
        """
        Kiểm tra xem message có phải là lời tạm biệt/kết thúc không.
        CHỈ detect khi có cụm từ kết thúc RÕ RÀNG, không phải chỉ "cảm ơn" đơn thuần.
        
        Args:
            text: Nội dung message cần kiểm tra
            
        Returns:
            True nếu là farewell message, False nếu không
        """
        farewell_patterns = [
            # Cụm từ chúc + danh xưng (rõ ràng là kết thúc)
            r'chúc\s+(anh|chị|cô|chú|quý khách)',
            
            # Tạm biệt / hẹn gặp lại
            r'tạm biệt',
            r'hẹn gặp lại',
            r'gặp lại\s+(anh|chị|cô|chú|quý khách)',
            
            # Kết thúc cuộc gọi
            r'kết thúc cuộc gọi',
            r'xin phép kết thúc',
            r'xin phép dừng',
            
            # Gọi lại sau
            r'gọi lại\s+(sau|cho em|nhé)',
            r'liên hệ lại\s+(sau|nhé)',
            
            # Cảm ơn + kết thúc rõ ràng
            r'cảm ơn.*?(tạm biệt|hẹn gặp lại|kết thúc)',
            r'xin cảm ơn.*?(tạm biệt|hẹn gặp lại)',
            
            # Goodbye (tiếng Anh)
            r'\b(bye|goodbye)\b',
        ]
        
        text_lower = text.lower()
        
        # Kiểm tra patterns
        for pattern in farewell_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def get_reminder_message(self) -> str:
        """Lấy message nhắc nhở lần 1"""
        return f"Alô, {self.customer_title} còn nghe em không ạ?"
    
    def get_goodbye_message(self) -> str:
        """Lấy message tạm biệt lần 2"""
        return f"Dạ, có vẻ đường dây không ổn định. {self.customer_title} tiện thì gọi lại cho em nhé. Em xin cảm ơn!"
    
    async def handle_silence_timeout(
        self,
        on_reminder: Callable[[str], Any],
        on_goodbye: Callable[[str], Any]
    ):
        """
        Xử lý khi phát hiện im lặng.
        
        Args:
            on_reminder: Callback khi gửi reminder (lần 1)
            on_goodbye: Callback khi gửi goodbye (lần 2)
        """
        try:
            await asyncio.sleep(self.silence_timeout)
            
            self.silence_count += 1
            logger.info(f"[Timeout] Silence detected (count: {self.silence_count})")
            
            if self.silence_count == 1:
                # Lần 1: Hỏi lại
                reminder = self.get_reminder_message()
                logger.info("[Timeout] Sending reminder...")
                await on_reminder(reminder)
                
            elif self.silence_count >= 2:
                # Lần 2: Ngắt máy
                goodbye = self.get_goodbye_message()
                logger.info("[Timeout] Sending goodbye and closing...")
                await on_goodbye(goodbye)
                
        except asyncio.CancelledError:
            # Timer bị cancel - đây là hành vi bình thường
            pass
    
    def start_silence_timer(
        self,
        on_reminder: Callable[[str], Any],
        on_goodbye: Callable[[str], Any]
    ):
        """
        Bắt đầu đếm thời gian im lặng.
        
        Args:
            on_reminder: Callback khi gửi reminder
            on_goodbye: Callback khi gửi goodbye
        """
        # Cancel timer cũ nếu có
        if self.silence_timer_task and not self.silence_timer_task.done():
            self.silence_timer_task.cancel()
        
        # Chỉ start timer nếu call đã initiated và chưa đến lần 2
        if self.call_initiated and self.silence_count < 2:
            self.silence_timer_task = asyncio.create_task(
                self.handle_silence_timeout(on_reminder, on_goodbye)
            )
            logger.info(f"[Timeout] Timer started ({self.silence_timeout} seconds)")
    
    def stop_silence_timer(self):
        """Dừng timer (khi user đang tương tác)"""
        if self.silence_timer_task and not self.silence_timer_task.done():
            self.silence_timer_task.cancel()
            self.silence_timer_task = None
            logger.info("[Timeout] Timer stopped")
    
    def reset_silence_count(self):
        """Reset silence count khi user tương tác"""
        self.silence_count = 0
        logger.info("[Timeout] Silence count reset to 0")
    
    def should_start_timer(self) -> bool:
        """
        Kiểm tra xem có nên start timer không.
        Không start nếu response là farewell message.
        """
        if not self.last_agent_response:
            return True
        
        return not self.is_farewell_message(self.last_agent_response)
    
    def reset(self):
        """Reset toàn bộ state"""
        self.stop_silence_timer()
        self.call_initiated = False
        self.silence_count = 0
        self.last_agent_response = ""
        logger.info("[CallHandler] State reset")
