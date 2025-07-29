import redis
import json
import logging
from typing import Optional, Any, Dict, List
from app.config import settings
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """Redis caching service for TestPilot AI Backend."""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis instance."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair in cache."""
        if not self.is_connected():
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.redis_client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.is_connected():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    # Specific caching methods for TestPilot AI
    def cache_prompt(self, prompt_hash: str, response: str, expire: int = 3600) -> bool:
        """Cache AI prompt responses."""
        return self.set(f"prompt:{prompt_hash}", response, expire)
    
    def get_cached_prompt(self, prompt_hash: str) -> Optional[str]:
        """Get cached AI prompt response."""
        return self.get(f"prompt:{prompt_hash}")
    
    def cache_session(self, session_id: str, data: Dict[str, Any], expire: int = 1800) -> bool:
        """Cache user session data."""
        return self.set(f"session:{session_id}", data, expire)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data."""
        return self.get(f"session:{session_id}")
    
    def cache_execution_result(self, test_case_id: int, result: Dict[str, Any], expire: int = 7200) -> bool:
        """Cache test execution results."""
        return self.set(f"execution:{test_case_id}", result, expire)
    
    def get_execution_result(self, test_case_id: int) -> Optional[Dict[str, Any]]:
        """Get cached execution result."""
        return self.get(f"execution:{test_case_id}")
    
    def invalidate_test_case_cache(self, test_case_id: int) -> bool:
        """Invalidate all cache entries related to a test case."""
        if not self.is_connected():
            return False
        
        try:
            # Delete execution result cache
            self.delete(f"execution:{test_case_id}")
            # Delete any other related cache entries
            pattern = f"*:{test_case_id}"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache for test case {test_case_id}: {e}")
            return False

# Global cache service instance
cache_service = CacheService() 