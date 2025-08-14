"""
Cached correction service with Redis integration for improved performance.
"""
import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.core.services.correction_service import CorrectionService
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class CachedCorrectionService(CorrectionService):
    """Enhanced correction service with Redis caching for improved performance."""
    
    def __init__(self):
        """Initialize with Redis caching."""
        super().__init__()
        
        # Initialize Redis connection
        self.redis_client = self._initialize_redis()
        self.cache_ttl = int(os.getenv('CACHE_TTL_SECONDS', '3600'))  # 1 hour default
        self.cache_enabled = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
        
        if self.cache_enabled:
            logger.info("Redis caching enabled for correction service")
        else:
            logger.info("Redis caching disabled for correction service")
    
    def _initialize_redis(self):
        """Initialize Redis connection with fallback."""
        try:
            import redis
            
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_db = int(os.getenv('REDIS_DB', '0'))
            redis_password = os.getenv('REDIS_PASSWORD')
            
            redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            redis_client.ping()
            logger.info("Redis connection established successfully")
            return redis_client
            
        except ImportError:
            logger.warning("Redis package not installed. Caching will be disabled.")
            return None
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
            return None
    
    def _get_cache_key(self, key_type: str, identifier: str) -> str:
        """Generate cache key with type prefix."""
        return f"correction:{key_type}:{identifier}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache with error handling."""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set data in cache with error handling."""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.cache_ttl
            self.redis_client.setex(cache_key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
            return False
    
    def _invalidate_cache(self, pattern: str) -> bool:
        """Invalidate cache entries matching pattern."""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
            return True
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return False
    
    def get_correction_log(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get correction log with caching."""
        cache_key = self._get_cache_key('log', correlation_id)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for correction log: {correlation_id}")
            return cached_data
        
        # Get from database
        result = super().get_correction_log(correlation_id)
        
        # Cache the result
        if result:
            self._set_cache(cache_key, result)
            logger.debug(f"Cached correction log: {correlation_id}")
        
        return result
    
    def create_correction_log(self, correlation_id: str, user_email: str, task_ids: List[str], 
                             email_subject: str = None) -> str:
        """Create correction log and invalidate related cache."""
        result = super().create_correction_log(correlation_id, user_email, task_ids, email_subject)
        
        # Invalidate user-related cache
        if self.cache_enabled:
            self._invalidate_cache(f"correction:user:{user_email}:*")
        
        return result
    
    def update_correction_log_status(self, correlation_id: str, status: str, error_message: str = None):
        """Update correction log status and invalidate cache."""
        result = super().update_correction_log_status(correlation_id, status, error_message)
        
        # Invalidate specific cache entry
        if self.cache_enabled:
            cache_key = self._get_cache_key('log', correlation_id)
            self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for correlation_id: {correlation_id}")
        
        return result
    
    def get_correction_stats(self) -> Dict[str, Any]:
        """Get correction statistics with caching."""
        cache_key = "correction:stats:current"
        
        # Try cache first (shorter TTL for stats)
        cached_stats = self._get_from_cache(cache_key)
        if cached_stats:
            logger.debug("Cache hit for correction stats")
            return cached_stats
        
        # Get from database
        stats = super().get_correction_stats()
        
        # Cache with shorter TTL (5 minutes for stats)
        self._set_cache(cache_key, stats, ttl=300)
        logger.debug("Cached correction stats")
        
        return stats
    
    def get_user_corrections(self, user_email: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's correction history with caching."""
        cache_key = self._get_cache_key('user_history', user_email)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for user corrections: {user_email}")
            return cached_data[:limit]
        
        # Get from database (this would need to be implemented in base class)
        # For now, we'll simulate this
        corrections = self._get_user_corrections_from_db(user_email, limit)
        
        # Cache the result
        if corrections:
            self._set_cache(cache_key, corrections, ttl=1800)  # 30 minutes
            logger.debug(f"Cached user corrections: {user_email}")
        
        return corrections
    
    def _get_user_corrections_from_db(self, user_email: str, limit: int) -> List[Dict[str, Any]]:
        """Get user corrections from database (placeholder implementation)."""
        # This would need to be implemented in the base CorrectionService
        # For now, return empty list
        return []
    
    def get_correction_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get correction analytics with caching."""
        cache_key = f"correction:analytics:{days}days"
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for analytics: {days} days")
            return cached_data
        
        # Calculate analytics
        analytics = self._calculate_correction_analytics(days)
        
        # Cache with longer TTL (1 hour for analytics)
        self._set_cache(cache_key, analytics, ttl=3600)
        logger.debug(f"Cached analytics for {days} days")
        
        return analytics
    
    def _calculate_correction_analytics(self, days: int) -> Dict[str, Any]:
        """Calculate correction analytics (placeholder implementation)."""
        # This would calculate various analytics like:
        # - Corrections per day
        # - Success rate trends
        # - Most common correction types
        # - User engagement metrics
        
        return {
            'period_days': days,
            'total_corrections': 0,
            'success_rate': 0.0,
            'avg_processing_time': 0.0,
            'top_correction_types': [],
            'user_engagement': {}
        }
    
    def warm_cache(self, correlation_ids: List[str]) -> Dict[str, bool]:
        """Pre-warm cache with specific correlation IDs."""
        if not self.cache_enabled or not self.redis_client:
            return {}
        
        results = {}
        for correlation_id in correlation_ids:
            try:
                # Get from database and cache
                log_data = super().get_correction_log(correlation_id)
                if log_data:
                    cache_key = self._get_cache_key('log', correlation_id)
                    success = self._set_cache(cache_key, log_data)
                    results[correlation_id] = success
                else:
                    results[correlation_id] = False
            except Exception as e:
                logger.error(f"Failed to warm cache for {correlation_id}: {e}")
                results[correlation_id] = False
        
        logger.info(f"Cache warming completed: {sum(results.values())}/{len(results)} successful")
        return results
    
    def clear_cache(self, pattern: str = "correction:*") -> bool:
        """Clear all cache entries matching pattern."""
        return self._invalidate_cache(pattern)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {'enabled': False, 'connected': False}
        
        try:
            info = self.redis_client.info()
            keys = self.redis_client.keys("correction:*")
            
            return {
                'enabled': self.cache_enabled,
                'connected': True,
                'total_keys': len(keys),
                'memory_usage': info.get('used_memory_human', 'N/A'),
                'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_misses', 1), 1)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'enabled': self.cache_enabled, 'connected': False, 'error': str(e)}
    
    def close(self):
        """Close database and Redis connections."""
        super().close()
        
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}") 