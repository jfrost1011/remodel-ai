from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import redis
import logging
import re

from config import settings
from services.city_mappings import normalize_location   # ← NEW import

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  ConversationContext dataclass-style container
# ─────────────────────────────────────────────────────────────────────────────
class ConversationContext:
    """Structured context data model for a conversation."""

    def __init__(self):
        self.session_id: str = ""
        self.location: Optional[str] = None
        self.project_type: Optional[str] = None
        self.budget_range: Dict[str, int] = {}            # {"min": 25 000, "max": 50 000}
        self.timeline: Optional[str] = None               # "6-8 weeks"
        self.discussed_prices: Dict[str, List[str]] = {}  # {"kitchen": ["25,000", "50,000"]}
        self.specific_features: List[str] = []
        self.conversation_summary: str = ""
        self.last_updated: datetime = datetime.now()
        self.turn_count: int = 0
        self.metadata: Dict[str, Any] = {}

    # ─── serialization helpers ────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id":           self.session_id,
            "location":             self.location,
            "project_type":         self.project_type,
            "budget_range":         self.budget_range,
            "timeline":             self.timeline,
            "discussed_prices":     self.discussed_prices,
            "specific_features":    self.specific_features,
            "conversation_summary": self.conversation_summary,
            "last_updated":         self.last_updated.isoformat(),
            "turn_count":           self.turn_count,
            "metadata":             self.metadata,
        }

    def from_dict(self, data: Dict[str, Any]):
        self.session_id           = data.get("session_id", "")
        self.location             = data.get("location")
        self.project_type         = data.get("project_type")
        self.budget_range         = data.get("budget_range", {})
        self.timeline             = data.get("timeline")
        self.discussed_prices     = data.get("discussed_prices", {})
        self.specific_features    = data.get("specific_features", [])
        self.conversation_summary = data.get("conversation_summary", "")
        self.last_updated         = datetime.fromisoformat(
            data.get("last_updated", datetime.now().isoformat())
        )
        self.turn_count           = data.get("turn_count", 0)
        self.metadata             = data.get("metadata", {})
        return self


# ─────────────────────────────────────────────────────────────────────────────
#  ContextManager
# ─────────────────────────────────────────────────────────────────────────────
class ContextManager:
    """Handles persistence of conversation context (Redis with in-memory fallback)."""

    def __init__(self):
        try:
            self.redis_client = settings.get_redis_connection()
            if self.redis_client:
                self.redis_client.ping()
            logger.info("Redis connection established")
            print("DEBUG: ContextManager – Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            print(f"DEBUG: ContextManager – Redis connection failed: {e}")
            self.redis_client = None

        # Always keep a Python-side fallback
        self.memory_store: Dict[str, Dict[str, Any]] = {}

    # ─── load / save helpers ──────────────────────────────────────────────
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        print(f"DEBUG: Getting context for session {session_id}")
        ctx = ConversationContext()
        ctx.session_id = session_id

        if self.redis_client:
            try:
                raw = self.redis_client.get(f"context:{session_id}")
                if raw:
                    ctx.from_dict(json.loads(raw))
                    print(f"DEBUG: Loaded context from Redis for {session_id}")
            except Exception as ex:
                print(f"DEBUG: Redis read error: {ex}")

        if session_id in self.memory_store:
            ctx.from_dict(self.memory_store[session_id])
            print(f"DEBUG: Loaded context from in-memory store for {session_id}")

        return ctx

    def save_context(self, session_id: str, context: ConversationContext):
        context.last_updated = datetime.now()
        data = context.to_dict()
        print(f"DEBUG: Saving context for {session_id}")

        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"context:{session_id}",
                    settings.session_ttl,
                    json.dumps(data),
                )
                print(f"DEBUG: Saved context to Redis for {session_id}")
                return
            except Exception as ex:
                print(f"DEBUG: Redis write error: {ex}")

        # Fallback to local memory
        self.memory_store[session_id] = data
        print(f"DEBUG: Saved context to in-memory store for {session_id}")

    # ─── main update after each Q/A turn ──────────────────────────────────
    def update_context_from_exchange(
        self, session_id: str, query: str, response: str
    ) -> ConversationContext:
        print(f"DEBUG: Updating context from exchange for {session_id}")
        print(f"DEBUG: Query: {query[:80]} …")
        print(f"DEBUG: Response: {response[:80]} …")

        context = self.get_or_create_context(session_id)
        q_lower = query.lower()
        r_lower = response.lower()

        # ── location extraction (now uses normalize_location) ─────────────
        new_location = normalize_location(q_lower)
        if new_location:
            print(f"DEBUG: normalize_location found → {new_location}")
        else:
            # Fall back to very coarse matching if nothing found
            if "san diego" in q_lower:
                new_location = "San Diego"
            elif "los angeles" in q_lower or (" la " in q_lower and "los angeles" not in q_lower):
                new_location = "Los Angeles"

        # Assistant mention (first-time only)
        if not new_location and not context.location:
            new_location = normalize_location(r_lower)
            if new_location:
                print(f"DEBUG: Assistant response implied location → {new_location}")

        # Apply location switching logic
        if new_location and context.location:
            switch_intent = any(
                kw in q_lower
                for kw in ["instead", "switch", "what about", "how about", "change to"]
            )
            if switch_intent and new_location != context.location:
                print(f"DEBUG: Switching location {context.location} → {new_location}")
                context.location = new_location
        elif new_location and not context.location:
            print(f"DEBUG: Setting initial location → {new_location}")
            context.location = new_location

        # ── project-type extraction ───────────────────────────────────────
        project_map = {
            "kitchen":        ["kitchen"],
            "bathroom":       ["bathroom", "bath"],
            "room_addition":  ["room addition", "addition"],
            "adu":            ["adu", "accessory dwelling"],
            "garage":         ["garage"],
        }
        for ptype, words in project_map.items():
            if any(w in q_lower or w in r_lower for w in words):
                context.project_type = ptype
                print(f"DEBUG: Found project type → {ptype}")
                break

        # ── price extraction (≥ $1 000, ignore $/sq ft) ───────────────────
        price_pat = r"\$(\d{1,3}(?:,\d{3})*)"
        prices = re.findall(price_pat, response)

        is_sqft_context = any(tag in r_lower for tag in ["per square", "per sq", "/sq"])

        filtered_prices = []
        for p in prices:
            try:
                val = int(p.replace(",", ""))
                if val >= 1_000:
                    filtered_prices.append(p)
            except ValueError:
                continue

        if filtered_prices and context.project_type:
            context.discussed_prices[context.project_type] = filtered_prices
            nums = [int(p.replace(",", "")) for p in filtered_prices]
            context.budget_range = {"min": min(nums), "max": max(nums)}
            print(f"DEBUG: Updated budget range → {context.budget_range}")

        # ── timeline extraction ───────────────────────────────────────────
        tl_match = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?", r_lower)
        if tl_match:
            context.timeline = f"{tl_match.group(1)}-{tl_match.group(2)} weeks"
            print(f"DEBUG: Timeline set → {context.timeline}")

        # ── feature extraction ────────────────────────────────────────────
        for feature in [
            "appliances", "countertops", "cabinets", "flooring",
            "backsplash", "island", "sink", "lighting"
        ]:
            if feature in q_lower or feature in r_lower:
                if feature not in context.specific_features:
                    context.specific_features.append(feature)
                    print(f"DEBUG: Added feature → {feature}")

        # ── conversation summary ─────────────────────────────────────────
        if context.project_type and context.location:
            context.conversation_summary = (
                f"Discussing {context.project_type} remodel in {context.location}. "
                f"Budget: ${context.budget_range.get('min', 'TBD')}-"
                f"${context.budget_range.get('max', 'TBD')}. "
                f"Timeline: {context.timeline or 'Not discussed'}. "
                f"Features: {', '.join(context.specific_features) or 'None specified'}"
            )
            print(f"DEBUG: Summary → {context.conversation_summary}")

        context.turn_count += 1
        self.save_context(session_id, context)
        return context

    # ─── helper: produce a one-liner context prompt for the LLM ───────────
    def get_context_prompt(self, context: ConversationContext) -> str:
        parts = []
        if context.project_type:
            parts.append(f"We are discussing a {context.project_type} remodel")
        if context.location:
            parts.append(f"in {context.location}")
        if context.budget_range.get("min") is not None:
            parts.append(
                f"with a budget range of ${context.budget_range['min']:,}"
                f" to ${context.budget_range['max']:,}"
            )
        if context.timeline:
            parts.append(f"with a timeline of {context.timeline}")
        if context.specific_features:
            parts.append(f"including features: {', '.join(context.specific_features)}")

        if parts:
            prompt = "Context: " + ". ".join(parts) + "."
            print(f"DEBUG: Generated context prompt → {prompt}")
            return prompt
        return ""

    # ─── helper: system prompt fed to the LLM at chain creation ───────────
    def get_system_prompt(self, session_id: str) -> str:
        ctx = self.get_or_create_context(session_id)

        base_prompt = (
            "You are an expert construction cost estimator for RemodelAI, "
            "specializing in home remodeling projects in California, especially "
            "San Diego and Los Angeles.\n\n"
            "Your expertise includes:\n"
            "- Providing accurate cost estimates for remodeling projects\n"
            "- Understanding California building codes and regulations\n"
            "- Giving timeline estimates for projects\n"
            "- Recommending materials and design options\n"
            "- Explaining the construction and permitting process\n\n"
            "When providing estimates, always give a range (low-high) and explain "
            "the factors that affect cost. Be specific about San Diego and Los Angeles "
            "market conditions.\n\n"
            "Only provide assistance for projects in San Diego and Los Angeles, "
            "as we don't have accurate data for other locations.\n\n"
            "Always be respectful, professional, and helpful. Avoid asking for "
            "information the user has already provided."
        )

        if ctx.conversation_summary:
            system_prompt = (
                f"{base_prompt}\n\nCONVERSATION CONTEXT:\n{ctx.conversation_summary}\n\n"
                "IMPORTANT: Use this context to avoid re-asking for known details."
            )
        else:
            system_prompt = base_prompt

        print("DEBUG: Generated system prompt (truncated):")
        print(system_prompt[:500] + "…")
        return system_prompt
