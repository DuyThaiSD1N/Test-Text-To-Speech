# -*- coding: utf-8 -*-
"""
Call Handler - Business logic cho voice call
Xử lý farewell detection, silence timeout, và call state management
"""
import asyncio
import logging
import re
from typing import Optional, Callable, Any

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
        silence_timeout: int = 10  # Tăng lên 10 giây
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
        self.is_ending = False  # Flag để tránh loop
        self.rejection_count = 0  # Đếm số lần từ chối
        self.unclear_count = 0  # Đếm số lần nói không rõ
    
    @staticmethod
    def is_unclear_text(text: str) -> bool:
        """
        Kiểm tra xem text có phải là gibberish/không rõ ràng không.
        
        Args:
            text: Nội dung message cần kiểm tra
            
        Returns:
            True nếu là unclear text, False nếu rõ ràng
        """
        text = text.strip()
        
        # Text quá ngắn (< 3 ký tự)
        if len(text) < 3:
            return True
        
        # Chỉ toàn ký tự đặc biệt hoặc số
        if re.match(r'^[^a-zA-ZÀ-ỹ]+$', text):
            return True
        
        # Tỷ lệ consonant liên tiếp quá cao (gibberish) - 3+ consonants
        consonant_clusters = re.findall(r'[bcdfghjklmnpqrstvwxyz]{3,}', text.lower())
        # Loại trừ các cluster hợp lệ trong tiếng Việt
        valid_clusters = ['ngh', 'kh', 'ch', 'th', 'ph', 'nh', 'tr', 'ng']
        invalid_clusters = [c for c in consonant_clusters if c not in valid_clusters]
        if len(invalid_clusters) > 0:
            return True
        
        # Random characters (ít vowels)
        vowels = len(re.findall(r'[aeiouàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]', text.lower()))
        total_letters = len(re.findall(r'[a-zA-ZÀ-ỹ]', text))
        
        if total_letters > 5 and vowels / total_letters < 0.2:
            return True
        
        # Quá nhiều số lẫn chữ (random)
        digits = len(re.findall(r'\d', text))
        if total_letters > 0 and digits > 0 and digits / len(text) > 0.3:
            return True
        
        return False
    
    @staticmethod
    def is_rejection(text: str) -> bool:
        """
        Kiểm tra xem message có phải là từ chối không.
        
        Args:
            text: Nội dung message cần kiểm tra
            
        Returns:
            True nếu là rejection, False nếu không
        """
        rejection_patterns = [
            # Từ chối trực tiếp
            r'\bkhông\s+(cần|muốn|quan tâm)\b',
            r'\bthôi\b',
            r'\bthôi\s+(em|ơi|không)\b',
            
            # Từ chối gián tiếp
            r'nếu\s+(tôi|em|anh|chị)\s+không\s+muốn',
            r'(tôi|em|anh|chị)\s+không\s+muốn',
            r'để\s+(sau|tôi nghĩ|xem xét)',
            r'(tôi|em|anh|chị)\s+(đang\s+)?bận',
            
            # Từ chối đơn giản
            r'^\s*không\s*$',
            r'^\s*thôi\s*$',
        ]
        
        text_lower = text.lower().strip()
        
        # Kiểm tra patterns
        for pattern in rejection_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
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
            
            # Xác nhận không có nhu cầu
            r'(em hiểu|em cảm ơn).*(không có nhu cầu|đã lắng nghe)',
            
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
        return f"Dạ, {self.customer_title} còn nghe em không ạ?"
    
    def get_goodbye_message(self) -> str:
        """Lấy message tạm biệt lần 2"""
        return f"Dạ, có vẻ đường dây không ổn định. Em xin phép kết thúc cuộc gọi. Chúc {self.customer_title} một ngày tốt lành ạ!"
    
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
            
            # Kiểm tra nếu call không còn initiated (đã reset) thì không làm gì
            if not self.call_initiated:
                logger.info("[Timeout] Call not initiated - timer cancelled")
                return
            
            # Kiểm tra nếu đang kết thúc thì không làm gì
            if self.is_ending:
                return
            
            self.silence_count += 1
            logger.info(f"[Timeout] Silence detected (count: {self.silence_count})")
            
            if self.silence_count == 1:
                # Lần 1: Hỏi lại
                reminder = self.get_reminder_message()
                logger.info("[Timeout] Sending reminder (1/2)...")
                await on_reminder(reminder)
                
            elif self.silence_count >= 2:
                # Lần 2: Ngắt máy
                self.is_ending = True
                goodbye = self.get_goodbye_message()
                logger.info("[Timeout] Sending goodbye (2/2) and closing...")
                await on_goodbye(goodbye)
                
        except asyncio.CancelledError:
            # Timer bị cancel - đây là hành vi bình thường
            logger.debug("[Timeout] Timer cancelled")
            pass
        except Exception as e:
            logger.error(f"[Timeout] Error: {e}", exc_info=True)
    
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
        # Không start timer nếu đang kết thúc
        if self.is_ending:
            logger.info("[Timeout] Not starting timer - call is ending")
            return
        
        # Cancel timer cũ nếu có
        if self.silence_timer_task and not self.silence_timer_task.done():
            self.silence_timer_task.cancel()
        
        # Chỉ start timer nếu call đã initiated và chưa đến lần 2
        if self.call_initiated and self.silence_count < 2:
            self.silence_timer_task = asyncio.create_task(
                self.handle_silence_timeout(on_reminder, on_goodbye)
            )
            logger.info(f"[Timeout] Timer started ({self.silence_timeout}s, count: {self.silence_count}/2)")
        else:
            logger.debug(f"[Timeout] Timer not started - initiated: {self.call_initiated}, count: {self.silence_count}")
    
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
    
    def reset(self):
        """Reset toàn bộ state"""
        self.stop_silence_timer()
        self.call_initiated = False
        self.silence_count = 0
        self.last_agent_response = ""
        self.is_ending = False
        self.rejection_count = 0
        self.unclear_count = 0
        logger.info("[CallHandler] State reset")
