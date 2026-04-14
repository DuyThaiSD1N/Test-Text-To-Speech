# -*- coding: utf-8 -*-
"""
Redis Store for Conversation Memory
"""
import redis.asyncio as redis
import json
import os
import logging
from typing import List, Optional, Tuple, Dict

logger = logging.getLogger(__name__)


# Simple message classes to replace langchain
class Message:
    """Base message class"""
    def __init__(self, content: str):
        self.content = content


class HumanMessage(Message):
    """Human message"""
    pass


class AIMessage(Message):
    """AI message"""
    pass


class RedisConversationStore:
    """Redis-based conversation storage"""
    
    def __init__(self, redis_url: str = None):
        """
        Initialize Redis connection
        
        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
            logger.info(f"[Redis] ✅ Connected to {self.redis_url}")
        except Exception as e:
            logger.error(f"[Redis] ❌ Connection failed: {e}")
            raise
    
    async def save_message(
        self, 
        session_id: str, 
        message: Message,
        ttl: int = 3600
    ):
        """
        Save a message to Redis
        
        Args:
            session_id: Unique session identifier
            message: HumanMessage or AIMessage
            ttl: Time to live in seconds (default: 1 hour)
        """
        if not self.redis:
            await self.connect()
        
        key = f"session:{session_id}:messages"
        
        # Serialize message
        msg_dict = {
            "type": "human" if isinstance(message, HumanMessage) else "ai",
            "content": message.content
        }
        
        # Append to list
        await self.redis.rpush(key, json.dumps(msg_dict, ensure_ascii=False))
        
        # Set/update TTL
        await self.redis.expire(key, ttl)
        
        logger.debug(f"[Redis] Saved message to {key}")
    
    async def get_history(
        self, 
        session_id: str,
        max_messages: Optional[int] = None
    ) -> List[Message]:
        """
        Get conversation history from Redis
        
        Args:
            session_id: Unique session identifier
            max_messages: Maximum number of messages to retrieve (None = all)
        
        Returns:
            List of HumanMessage/AIMessage
        """
        if not self.redis:
            await self.connect()
        
        key = f"session:{session_id}:messages"
        
        # Get messages
        if max_messages:
            # Get last N messages
            messages = await self.redis.lrange(key, -max_messages, -1)
        else:
            # Get all messages
            messages = await self.redis.lrange(key, 0, -1)
        
        # Deserialize
        history = []
        for msg_json in messages:
            try:
                msg_dict = json.loads(msg_json)
                if msg_dict["type"] == "human":
                    history.append(HumanMessage(content=msg_dict["content"]))
                else:
                    history.append(AIMessage(content=msg_dict["content"]))
            except Exception as e:
                logger.error(f"[Redis] Failed to parse message: {e}")
                continue
        
        logger.debug(f"[Redis] Retrieved {len(history)} messages from {key}")
        return history
    
    async def save_context(
        self,
        session_id: str,
        context: str,
        title: str,
        ttl: int = 3600
    ):
        """
        Save customer context
        
        Args:
            session_id: Unique session identifier
            context: Customer context string
            title: Customer title (Anh/Chị/Cô/Chú)
            ttl: Time to live in seconds
        """
        if not self.redis:
            await self.connect()
        
        key = f"session:{session_id}:context"
        data = {
            "context": context,
            "title": title
        }
        
        await self.redis.setex(
            key, 
            ttl, 
            json.dumps(data, ensure_ascii=False)
        )
        
        logger.debug(f"[Redis] Saved context to {key}")
    
    async def get_context(self, session_id: str) -> Tuple[str, str]:
        """
        Get customer context
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Tuple of (context, title)
        """
        if not self.redis:
            await self.connect()
        
        key = f"session:{session_id}:context"
        data = await self.redis.get(key)
        
        if data:
            try:
                parsed = json.loads(data)
                return parsed["context"], parsed["title"]
            except Exception as e:
                logger.error(f"[Redis] Failed to parse context: {e}")
        
        return "", "Quý khách"
    
    async def clear_session(self, session_id: str):
        """
        Clear all data for a session
        
        Args:
            session_id: Unique session identifier
        """
        if not self.redis:
            await self.connect()
        
        await self.redis.delete(
            f"session:{session_id}:messages",
            f"session:{session_id}:context"
        )
        
        logger.info(f"[Redis] Cleared session {session_id}")
    
    async def extend_ttl(self, session_id: str, ttl: int = 3600):
        """
        Extend TTL for a session
        
        Args:
            session_id: Unique session identifier
            ttl: New TTL in seconds
        """
        if not self.redis:
            await self.connect()
        
        await self.redis.expire(f"session:{session_id}:messages", ttl)
        await self.redis.expire(f"session:{session_id}:context", ttl)
        
        logger.debug(f"[Redis] Extended TTL for session {session_id}")
    
    async def get_session_info(self, session_id: str) -> dict:
        """
        Get session information
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Dict with session info
        """
        if not self.redis:
            await self.connect()
        
        history = await self.get_history(session_id)
        context, title = await self.get_context(session_id)
        
        # Get TTL
        ttl = await self.redis.ttl(f"session:{session_id}:messages")
        
        return {
            "session_id": session_id,
            "message_count": len(history),
            "customer_title": title,
            "customer_context": context,
            "ttl_seconds": ttl if ttl > 0 else 0
        }
    
    async def list_active_sessions(self) -> List[str]:
        """
        List all active session IDs
        
        Returns:
            List of session IDs
        """
        if not self.redis:
            await self.connect()
        
        keys = await self.redis.keys("session:*:messages")
        session_ids = [key.split(":")[1] for key in keys]
        
        return session_ids
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("[Redis] Connection closed")
