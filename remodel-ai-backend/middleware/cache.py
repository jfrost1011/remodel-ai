from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import time
from typing import Dict, Optional, Tuple

# Simple in-memory cache
cache: Dict[str, Tuple[float, Response]] = {}
CACHE_EXPIRY = 3600  # 1 hour in seconds

class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests or specific POST endpoints
        if request.method == "GET" or (
            request.method == "POST" and 
            request.url.path == "/api/v1/chat" and 
            not await self._is_dynamic_content(request)
        ):
            cache_key = await self._generate_cache_key(request)
            cached_response = self._get_cached_response(cache_key)
            
            if cached_response:
                return cached_response
            
            # Process the request
            response = await call_next(request)
            
            # Cache the response
            if 200 <= response.status_code < 400:
                try:
                    # Try to read the response body
                    response_body = [chunk async for chunk in response.body_iterator]
                    response.body_iterator = self._iterate_in_threadpool(iter(response_body))
                    
                    # Create a new response with the same data
                    content = b"".join(response_body)
                    cached_resp = Response(
                        content=content,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
                    
                    # Store in cache
                    cache[cache_key] = (time.time(), cached_resp)
                except:
                    # If we can't cache the response, just return it
                    pass
            
            return response
        
        # For non-cacheable requests, just pass through
        return await call_next(request)
    
    async def _is_dynamic_content(self, request: Request) -> bool:
        """Check if the request is for dynamic content that shouldn't be cached"""
        if request.url.path != "/api/v1/chat":
            return False
            
        # Don't cache cost estimate requests
        try:
            body_bytes = await request.body()
            body_str = body_bytes.decode("utf-8")
            import json
            body = json.loads(body_str)
            content = body.get("content", "").lower()
            return "cost" in content or "estimate" in content or "price" in content
        except:
            return True
    
    async def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique key for the request"""
        url = str(request.url)
        
        # For POST requests, include the body in the cache key
        if request.method == "POST":
            body = await request.body()
            return hashlib.md5(f"{url}:{body}".encode()).hexdigest()
        
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cached_response(self, key: str) -> Optional[Response]:
        """Retrieve a cached response if it exists and is not expired"""
        if key in cache:
            timestamp, response = cache[key]
            if time.time() - timestamp < CACHE_EXPIRY:
                return response
            # Remove expired cache entry
            del cache[key]
        return None
    
    def _iterate_in_threadpool(self, iterator):
        """Return iterator that can be used in async context."""
        
        async def _iterate():
            for item in iterator:
                yield item
        
        return _iterate()