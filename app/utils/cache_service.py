import redis
from config import Config
import json

class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.config = Config()
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
        except Exception as e:
            print(f"Redis connection failed: {e}. Caching disabled.")
            self.enabled = False
    
    def get(self, key: str):
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: dict, expiry: int = 3600):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expiry: Expiry time in seconds (default: 1 hour)
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.setex(
                key,
                expiry,
                json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Error deleting from cache: {e}")
            return False
    
    def clear_all(self):
        """Clear all cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
