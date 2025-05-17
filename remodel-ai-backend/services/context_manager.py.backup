from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import redis
from config import settings
import logging

logger = logging.getLogger(__name__)

class ConversationContext:
    """Structured context data model for a conversation"""
    def __init__(self):
        self.session_id: str = ""
        self.location: Optional[str] = None
        self.project_type: Optional[str] = None
        self.budget_range: Dict[str, int] = {}  # {"min": 25000, "max": 50000}
        self.timeline: Optional[str] = None  # "6-8 weeks"
        self.discussed_prices: Dict[str, List[str]] = {}  # {"kitchen": ["25,000", "50,000"]}
        self.specific_features: List[str] = []
        self.conversation_summary: str = ""
        self.last_updated: datetime = datetime.now()
        self.turn_count: int = 0
        self.metadata: Dict[str, Any] = {}  # For storing qa_chain, memory, etc.
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "location": self.location,
            "project_type": self.project_type,
            "budget_range": self.budget_range,
            "timeline": self.timeline,
            "discussed_prices": self.discussed_prices,
            "specific_features": self.specific_features,
            "conversation_summary": self.conversation_summary,
            "last_updated": self.last_updated.isoformat(),
            "turn_count": self.turn_count,
            "metadata": self.metadata
        }
    
    def from_dict(self, data: Dict[str, Any]):
        self.session_id = data.get("session_id", "")
        self.location = data.get("location")
        self.project_type = data.get("project_type")
        self.budget_range = data.get("budget_range", {})
        self.timeline = data.get("timeline")
        self.discussed_prices = data.get("discussed_prices", {})
        self.specific_features = data.get("specific_features", [])
        self.conversation_summary = data.get("conversation_summary", "")
        self.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        self.turn_count = data.get("turn_count", 0)
        self.metadata = data.get("metadata", {})
        return self

class ContextManager:
    """Manages conversation context with Redis persistence"""
    
    def __init__(self):
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            # Fallback to in-memory storage
            self.redis_client = None
            self.memory_store = {}
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one"""
        context = ConversationContext()
        context.session_id = session_id
        
        # Try to get from Redis
        if self.redis_client:
            try:
                data = self.redis_client.get(f"context:{session_id}")
                if data:
                    context.from_dict(json.loads(data))
                    logger.info(f"Loaded context for session {session_id}")
                else:
                    logger.info(f"Created new context for session {session_id}")
            except Exception as e:
                logger.error(f"Redis read error: {str(e)}")
        else:
            # Fallback to memory store
            if session_id in self.memory_store:
                context.from_dict(self.memory_store[session_id])
        
        return context
    
    def save_context(self, session_id: str, context: ConversationContext):
        """Save context to Redis or memory"""
        context.last_updated = datetime.now()
        context_data = context.to_dict()
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"context:{session_id}",
                    settings.session_ttl,  # TTL in seconds
                    json.dumps(context_data)
                )
                logger.info(f"Saved context for session {session_id}")
            except Exception as e:
                logger.error(f"Redis write error: {str(e)}")
                # Fallback to memory
                self.memory_store[session_id] = context_data
        else:
            self.memory_store[session_id] = context_data
    
    def update_context_from_exchange(self, 
                                   session_id: str, 
                                   query: str, 
                                   response: str) -> ConversationContext:
        """Update context based on a query/response exchange"""
        context = self.get_or_create_context(session_id)
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Extract location
        if 'san diego' in query_lower or 'san diego' in response_lower:
            context.location = 'San Diego'
        elif 'los angeles' in query_lower or 'los angeles' in response_lower:
            context.location = 'Los Angeles'
        
        # Extract project type
        project_keywords = {
            'kitchen': ['kitchen'],
            'bathroom': ['bathroom', 'bath'],
            'room_addition': ['room addition', 'addition'],
            'adu': ['adu', 'accessory dwelling'],
            'garage': ['garage']
        }
        
        for ptype, keywords in project_keywords.items():
            for keyword in keywords:
                if keyword in query_lower or keyword in response_lower:
                    context.project_type = ptype
                    break
        
        # Extract prices
        import re
        price_pattern = r'\$(\d{1,3}(?:,\d{3})*)'
        prices = re.findall(price_pattern, response)
        
        if prices and context.project_type:
            # Clean and convert prices
            clean_prices = [p.replace(',', '') for p in prices]
            context.discussed_prices[context.project_type] = prices
            
            # Update budget range if we have at least 2 prices
            if len(clean_prices) >= 2:
                numeric_prices = [int(p) for p in clean_prices]
                context.budget_range = {
                    "min": min(numeric_prices),
                    "max": max(numeric_prices)
                }
        
        # Extract timeline
        timeline_pattern = r'(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?'
        timeline_match = re.search(timeline_pattern, response_lower)
        if timeline_match:
            context.timeline = f"{timeline_match.group(1)}-{timeline_match.group(2)} weeks"
        
        # Extract specific features mentioned
        feature_keywords = ['appliances', 'countertops', 'cabinets', 'flooring', 
                          'backsplash', 'island', 'sink', 'lighting']
        for feature in feature_keywords:
            if feature in query_lower or feature in response_lower:
                if feature not in context.specific_features:
                    context.specific_features.append(feature)
        
        # Update conversation summary
        if context.project_type and context.location:
            context.conversation_summary = (
                f"Discussing {context.project_type} remodel in {context.location}. "
                f"Budget: ${context.budget_range.get('min', 'TBD')}-"
                f"${context.budget_range.get('max', 'TBD')}. "
                f"Timeline: {context.timeline or 'Not discussed'}. "
                f"Features: {', '.join(context.specific_features) or 'None specified'}"
            )
        
        context.turn_count += 1
        # Calculate budget range from discussed prices
        if context.discussed_prices and context.project_type:
            project_prices = context.discussed_prices.get(context.project_type, [])
            if project_prices:
                numeric_prices = []
                for price in project_prices:
                    try:
                        numeric_price = int(price.replace(',', ''))
                        numeric_prices.append(numeric_price)
                    except:
                        continue
                if numeric_prices:
                    context.budget_range = {
                        "min": min(numeric_prices),
                        "max": max(numeric_prices)
                    }
        self.save_context(context)
        
        return context
    
    def get_context_prompt(self, context: ConversationContext) -> str:
        """Generate a context prompt for the LLM"""
        prompt_parts = []
        
        if context.project_type:
            prompt_parts.append(f"We are discussing a {context.project_type} remodel")
        
        if context.location:
            prompt_parts.append(f"in {context.location}")
        
        if context.budget_range:
            prompt_parts.append(
                f"with a budget range of ${context.budget_range['min']:,} to ${context.budget_range['max']:,}"
            )
        
        if context.timeline:
            prompt_parts.append(f"timeline of {context.timeline}")
        
        if context.specific_features:
            prompt_parts.append(f"including features: {', '.join(context.specific_features)}")
        
        if prompt_parts:
            return "Context: " + ". ".join(prompt_parts) + "."
        
        return ""
    
    def validate_response_consistency(self, 
                                    response: str, 
                                    context: ConversationContext) -> Dict[str, Any]:
        """Check if response is consistent with established context"""
        issues = []
        
        # Check price consistency
        if context.budget_range:
            import re
            prices_in_response = re.findall(r'\$(\d{1,3}(?:,\d{3})*)', response)
            for price_str in prices_in_response:
                price = int(price_str.replace(',', ''))
                if price < context.budget_range['min'] * 0.8 or price > context.budget_range['max'] * 1.2:
                    issues.append({
                        "type": "price_inconsistency",
                        "found": price,
                        "expected_range": context.budget_range
                    })
        
        # Check timeline consistency
        if context.timeline:
            timeline_pattern = r'(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?'
            timeline_match = re.search(timeline_pattern, response.lower())
            if timeline_match:
                new_timeline = f"{timeline_match.group(1)}-{timeline_match.group(2)} weeks"
                if new_timeline != context.timeline:
                    issues.append({
                        "type": "timeline_inconsistency",
                        "found": new_timeline,
                        "expected": context.timeline
                    })
        
        return {
            "is_consistent": len(issues) == 0,
            "issues": issues
        }
