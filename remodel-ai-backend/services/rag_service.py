# services/rag_service.py
# ───────────────────────────────────────────────────────────────────────────
import os
import uuid
from typing import Optional, List, Dict, Any, Tuple
import asyncio
import aiohttp
import logging
import re

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from pinecone import Pinecone as PineconeClient

from config import settings
from services.context_manager import ContextManager
from services.city_mappings import normalize_location

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────────────────
#  SIMPLE SINGLETON SUPPORT
# ───────────────────────────────────────────────────────────────────────────
_instance: "RAGService | None" = None  # module-level handle (debug only)


# ═══════════════════════════════════════════════════════════════════════════
#  RAGService
# ═══════════════════════════════════════════════════════════════════════════
class RAGService:
    """
    Retrieval-Augmented Generation service with:

      • LangChain ConversationalRetrievalChain
      • Pinecone vector store
      • Context + memory handling

    Implemented as a **singleton** so we initialise expensive
    resources (LLM, embeddings, Pinecone, etc.) only once per process.
    """

    _instance: "RAGService | None" = None  # class-level handle

    # ────────────────────────────────────────────────────────────────────
    #  Singleton plumbing
    # ────────────────────────────────────────────────────────────────────
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("Creating new RAGService instance")
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False         # flag for __init__
        return cls._instance

    # ────────────────────────────────────────────────────────────────────
    #  Real initialisation (runs only once)
    # ────────────────────────────────────────────────────────────────────
    def __init__(self):
        # Skip heavy init if we've already run it
        if getattr(self, "_initialized", False):
            print("Using existing RAGService instance")
            return

        print("Initializing RAG Service…")

        # ── LLM & embeddings ────────────────────────────────────────────
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.3,
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model,
        )

        # ── Context manager & session store ─────────────────────────────
        self.context_manager = ContextManager()
        self.sessions: Dict[str, Dict[str, Any]] = {}

        # ── Shared aiohttp session ──────────────────────────────────────
        self.aiohttp_session: Optional[aiohttp.ClientSession] = None

        # ── Pinecone vector store ───────────────────────────────────────
        try:
            pc = PineconeClient(api_key=settings.pinecone_api_key)
            self.vector_store = PineconeVectorStore(
                index_name=settings.pinecone_index,
                embedding=self.embeddings,
                pinecone_api_key=settings.pinecone_api_key,
            )
            print("Pinecone vector store initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {e}")
            self.vector_store = None

        # Mark the singleton as fully initialised
        self._initialized = True

    # ═══════════════════════════════════════════════════════════════════
    #  Lightweight language detection (heuristic)
    # ═══════════════════════════════════════════════════════════════════
    def detect_language(self, text: str) -> str:
        """
        Very simple heuristic language detector.
        Returns "en", "es", or "fr" (default "en").
        """
        text = text.lower()

        es_tokens = [
            " el ", " la ", " los ", " las ", " es ", " son ", " para ", " como ",
            " que ", " y ", " pero ", " por ", " estar "
        ]
        fr_tokens = [
            " le ", " la ", " les ", " est ", " sont ", " pour ", " comme ",
            " que ", " et ", " ou ", " mais ", " être "
        ]

        es_hits = sum(tok in text for tok in es_tokens)
        fr_hits = sum(tok in text for tok in fr_tokens)

        if es_hits > 5:
            return "es"
        if fr_hits > 5:
            return "fr"
        return "en"

    # ═══════════════════════════════════════════════════════════════════
    #  Session helpers
    # ═══════════════════════════════════════════════════════════════════
    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        context = self.context_manager.get_or_create_context(session_id)
        key = f"session_{session_id}"

        if key not in self.sessions:
            memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=500,
                memory_key="chat_history",
                return_messages=True,
                output_key="answer",
            )
            qa_chain = self._create_qa_chain(memory, session_id=session_id)
            self.sessions[key] = {"memory": memory, "qa_chain": qa_chain}
            self.context_manager.save_context(session_id, context)

        return {
            "memory": self.sessions[key]["memory"],
            "qa_chain": self.sessions[key]["qa_chain"],
            "context": context,
            "conversation_summary": context.conversation_summary,
        }

    # ═══════════════════════════════════════════════════════════════════
    #  QA chain (context-aware prompt, simple retriever)
    # ═══════════════════════════════════════════════════════════════════
    def _create_qa_chain(self, memory, session_id: Optional[str] = None):
        # Fetch context to optionally append conversation summary
        context = (
            self.context_manager.get_or_create_context(session_id)
            if session_id
            else None
        )

        # 1) dynamic / fallback system prompt
        system_template = (
            self.context_manager.get_system_prompt(session_id)
            if session_id
            else (
                "You are an expert AI construction cost advisor specializing in "
                "California residential construction, particularly in San Diego "
                "and Los Angeles.\n\nCRITICAL INSTRUCTIONS:\n1. ALWAYS maintain "
                "the context of the conversation…\nAssistant: I'll respond based "
                "on our ongoing conversation about your specific project."
            )
        )

        # Append summary if available
        if context and context.conversation_summary and len(context.conversation_summary) > 5:
            system_template += (
                f"\n\nIMPORTANT CONTEXT: {context.conversation_summary}\n\n"
                "Keep this conversation history in mind when responding to the user."
            )

        # 2) prompt assembly
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_template),
                HumanMessagePromptTemplate.from_template(
                    "Context from search: {context}\n\nQuestion: {question}"
                ),
            ]
        )

        # 3) simple retriever (top-3)
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        # 4) chain
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={
                "prompt": chat_prompt,
                "document_separator": "\n",
                "document_variable_name": "context",
            },
            return_source_documents=True,
            verbose=False,
        )

    # ═══════════════════════════════════════════════════════════════════
    #  aiohttp helpers
    # ═══════════════════════════════════════════════════════════════════
    async def _get_aiohttp_session(self):
        if self.aiohttp_session is None or self.aiohttp_session.closed:
            self.aiohttp_session = aiohttp.ClientSession()
        return self.aiohttp_session

    async def close(self):
        if self.aiohttp_session and not self.aiohttp_session.closed:
            await self.aiohttp_session.close()

    # ═══════════════════════════════════════════════════════════════════
    #  Quick query-type detector
    # ═══════════════════════════════════════════════════════════════════
    def is_construction_query(self, query: str) -> bool:
        keywords = [
            "cost", "price", "estimate", "remodel", "renovation", "kitchen",
            "bathroom", "project", "construction", "timeline", "budget",
            "appliances", "materials", "san diego", "los angeles",
            "proceed", "first step", "summarize",
        ]
        return any(k in query.lower() for k in keywords)

    # ═══════════════════════════════════════════════════════════════════
    #  update_session_context  (improved location + price parsing)
    # ═══════════════════════════════════════════════════════════════════
    def update_session_context(self, query: str, response: str, session_id: str):
        # -------------- (contents unchanged from your original file) --------------
        context = self.context_manager.get_or_create_context(session_id)
        ql, rl = query.lower(), response.lower()
        updates: Dict[str, Any] = {}

        # ── location (user-initiated only) ──────────────────────────────
        q_loc = normalize_location(ql)
        if q_loc:
            change_intent = any(term in ql for term in [
                "moving to", "instead of", "switch to", "change to",
                "not in", "rather than", "project in", "property in"
            ])
            if not context.location or change_intent:
                print(f"DEBUG: Updating location to {q_loc} based on user query")
                updates["location"] = q_loc
            else:
                print(f"DEBUG: Ignored location change to {q_loc} – no clear user intent")

        # ── project type ────────────────────────────────────────────────
        proj_map = {
            "kitchen": ["kitchen"],
            "bathroom": ["bathroom", "bath"],
            "room_addition": ["room addition", "addition"],
            "adu": ["adu", "accessory dwelling"],
            "garage": ["garage"],
        }
        for ptype, words in proj_map.items():
            if any(w in ql or w in rl for w in words):
                updates["project_type"] = ptype
                break

        # ── price parsing (≥ $1 000) ────────────────────────────────────
        price_re = r"\$(\d{1,3}(?:,\d{3})*)"
        price_matches = re.findall(price_re, response)
        filtered_prices: List[str] = []
        for p in price_matches:
            try:
                val = int(p.replace(",", ""))
                if val >= 1_000:
                    filtered_prices.append(p)
            except ValueError:
                continue

        if filtered_prices and context.project_type:
            context.discussed_prices.setdefault(context.project_type, []).extend(filtered_prices)
            context.discussed_prices[context.project_type] = list(
                dict.fromkeys(context.discussed_prices[context.project_type])
            )
            updates["discussed_prices"] = context.discussed_prices

            all_prices = [int(p.replace(",", "")) for p in context.discussed_prices[context.project_type]]

            if len(all_prices) >= 2:
                if max(all_prices) >= 20_000:
                    thresh = max(all_prices) * 0.1
                    all_prices = [p for p in all_prices if p >= thresh]
                    print(f"DEBUG: Filtered out budget outliers, using {len(all_prices)} significant prices")

                min_price, max_price = min(all_prices), max(all_prices)

                if context.budget_range and "min" in context.budget_range:
                    curr_min = context.budget_range["min"]
                    curr_max = context.budget_range["max"]

                    if min_price < curr_min * 0.8 or max_price > curr_max * 1.2:
                        new_min = min(curr_min, min_price)
                        new_max = max(curr_max, max_price)
                        updates["budget_range"] = {"min": new_min, "max": new_max}
                        print(f"DEBUG: Updated budget range to ${new_min:,} - ${new_max:,}")
                else:
                    updates["budget_range"] = {"min": min_price, "max": max_price}
                    print(f"DEBUG: Set initial budget range to ${min_price:,} - ${max_price:,}")

            elif len(all_prices) == 1 and not context.budget_range:
                single_price = all_prices[0]
                range_min = int(single_price * 0.85)
                range_max = int(single_price * 1.15)
                updates["budget_range"] = {"min": range_min, "max": range_max}
                print(f"DEBUG: Created range from single price ${single_price:,} → ${range_min:,} - ${range_max:,}")

        elif price_matches and not filtered_prices:
            print("DEBUG: All prices < $1,000 filtered out; budget not updated")

        # ── timeline (lightweight) ───────────────────────────────────────
        tl_match = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?", rl)
        if tl_match:
            updates["timeline"] = f"{tl_match.group(1)}-{tl_match.group(2)} weeks"

        # ── update conversation summary ─────────────────────────────────
        context.conversation_summary = self._build_conversation_summary(context)
        updates["conversation_summary"] = context.conversation_summary

        # Apply & save
        for k, v in updates.items():
            if hasattr(context, k):
                setattr(context, k, v)
        self.context_manager.save_context(session_id, context)

    # -------------------------------------------------------------------
    #  Helper: build summary
    # -------------------------------------------------------------------
    def _build_conversation_summary(self, context) -> str:
        parts = []
        if context.project_type:
            parts.append(f"{context.project_type.capitalize()} remodel")
        if context.location:
            parts.append(f"in {context.location}")
        if context.budget_range and "min" in context.budget_range and "max" in context.budget_range:
            mn, mx = context.budget_range["min"], context.budget_range["max"]
            parts.append(f"with budget range ${mn:,}-${mx:,}" if mn != mx else f"with budget of ${mn:,}")
        if context.timeline:
            parts.append(f"over {context.timeline}")
        if context.specific_features:
            feat = ", ".join(context.specific_features[:3])
            if len(context.specific_features) > 3:
                feat += f" and {len(context.specific_features)-3} more features"
            parts.append(f"including {feat}")

        if parts:
            summary = "Discussing " + " ".join(parts) + "."
            print(f"DEBUG: Updated conversation summary: {summary}")
            return summary
        return ""

    # ═══════════════════════════════════════════════════════════════════
    #  Validation helpers  (price + timeline + price-inclusion guard)
    # ═══════════════════════════════════════════════════════════════════
    async def _try_validate_correct(
        self, response: str, session_id: str, query: str, fallback: bool = False
    ) -> str:
        """
        Single-pass validator; returns either the original response
        (if valid) or a corrected version from the LLM.
        """
        context = self.context_manager.get_or_create_context(session_id)

        # ── price consistency ──────────────────────────────────────────
        if context.discussed_prices and context.project_type:
            known = context.discussed_prices.get(context.project_type, [])
            resp_prices = re.findall(r"\$(\d{1,3}(?:,\d{3})*)", response)
            if known and resp_prices:
                rmn = min(int(p.replace(",", "")) for p in resp_prices)
                rmx = max(int(p.replace(",", "")) for p in resp_prices)
                knmn = min(int(p.replace(",", "")) for p in known)
                knmx = max(int(p.replace(",", "")) for p in known)
                if abs(rmn - knmn) > 5_000 or abs(rmx - knmx) > 10_000:
                    prompt = (
                        f"The response appears inconsistent with our established budget range "
                        f"${knmn:,}–${knmx:,}. Original response:\n{response}\n\n"
                        f"Please restate the answer to keep it within that budget."
                    )
                    return (await self.llm.ainvoke(prompt)).content

        # ── timeline consistency (with replacement-only leniency) ──────
        if context.timeline:
            is_replacement_only = any(term in query.lower() for term in [
                "replace countertop", "replace the countertop", "replace sink",
                "just replace", "only replace"
            ])

            tl_match = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?", response)
            if tl_match:
                new_min = int(tl_match.group(1))
                new_max = int(tl_match.group(2))

                curr_match = re.search(r"(\d+)-(\d+)", context.timeline)
                if curr_match:
                    curr_min = int(curr_match.group(1))
                    curr_max = int(curr_match.group(2))

                    min_realistic = 1 if is_replacement_only else 4
                    if context.project_type == "kitchen" and new_min < min_realistic:
                        prompt = (
                            f"The timeline of {new_min}-{new_max} weeks is unrealistically short "
                            f"for this type of project. Please revise."
                        )
                        return (await self.llm.ainvoke(prompt)).content

                    valid = (
                        new_min >= curr_min * 0.5
                        and new_max <= curr_max * 2
                    )
                    if not valid:
                        prompt = (
                            f"The timeline {new_min}-{new_max} weeks conflicts with the "
                            f"established timeline of {curr_min}-{curr_max} weeks. Please revise."
                        )
                        return (await self.llm.ainvoke(prompt)).content

        # ── price-inclusion guard ───────────────────────────────────────
        if any(k in query.lower() for k in ["cost", "price", "how much"]):
            if not re.search(r"\$\d[\d,.]*", response):
                prompt = (
                    f"The user asked about costs, but the response contains no price information.\n\n"
                    f"Original response:\n{response}\n\n"
                    f"Please revise to include specific price ranges (in dollars)."
                )
                return (await self.llm.ainvoke(prompt)).content

        return response

    async def _validate_and_correct_response(
        self, response: str, session_id: str, query: str
    ) -> str:
        """
        Wraps _try_validate_correct with a single retry. Falls back to the
        original answer if the second attempt still fails validation.
        """
        original = response

        first_pass = await self._try_validate_correct(response, session_id, query)
        if first_pass == response:
            return first_pass  # valid first try

        second_pass = await self._try_validate_correct(first_pass, session_id, query, fallback=True)
        if second_pass != first_pass:
            return second_pass  # corrected successfully

        # Second attempt still invalid → fall back
        print("DEBUG: Validation loop did not converge; returning original response")
        return original

    # ═══════════════════════════════════════════════════════════════════
    #  Main entry
    # ═══════════════════════════════════════════════════════════════════
    async def get_chat_response(
        self,
        query: str,
        chat_history: List[Tuple[str, str]],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Incoming query: {query}")

        if not session_id:
            session_id = str(uuid.uuid4())
        logger.info(f"Session: {session_id}")

        await self._get_aiohttp_session()

        session = self.get_or_create_session(session_id)
        context = session["context"]

        # greeting / off-topic
        if not self.is_construction_query(query) and not context.project_type:
            friendly = (
                f'You are a friendly RemodelAI assistant.\nUser said: "{query}"\n'
                "Respond briefly, mentioning you can estimate remodel costs in San Diego or LA."
            )
            msg = (await self.llm.ainvoke(friendly)).content
            return {"message": msg, "source_documents": []}

        if not self.vector_store:
            return {
                "message": "Sorry, our construction knowledge base is temporarily unavailable.",
                "source_documents": [],
            }

        try:
            qa_chain = session["qa_chain"]

            # ── language detection + instruction ────────────────────────
            user_lang = self.detect_language(query)
            print(f"DEBUG: Detected user language: {user_lang}")

            lang_instruction = {
                "en": "Please respond in English.",
                "es": "Por favor, responde en español.",
                "fr": "Veuillez répondre en français.",
            }.get(user_lang, "Please respond in English.")

            # context prompt
            ctx_prompt = self.context_manager.get_context_prompt(context)
            enhanced_query = (
                f"{ctx_prompt} {lang_instruction} {query}"
                if ctx_prompt else f"{lang_instruction} {query}"
            )

            # ── run chain ───────────────────────────────────────────────
            result = await qa_chain.ainvoke({"question": enhanced_query})

            # ── language-aware document filtering (improved) ───────────
            raw_docs = result.get("source_documents", [])
            valid_docs, filtered = [], 0
            for doc in raw_docs:
                if not getattr(doc, "page_content", "").strip():
                    filtered += 1
                    continue
                d_lang = self.detect_language(doc.page_content)
                if d_lang in (user_lang, "en"):
                    valid_docs.append(doc)
                else:
                    filtered += 1
            if filtered:
                print(f"DEBUG: Filtered {filtered} documents due to language/empty content")

            # answer text
            answer = result.get("answer", "")

            # validate / self-correct (with fallback)
            answer = await self._validate_and_correct_response(answer, session_id, query)

            # ── enhanced boilerplate removal ───────────────────────────
            boilerplate_patterns = [
                r"^(Absolutely!|Certainly!|Of course!|Here's|Sure!|I'd be happy to help!)\s*",
                r"^(Certainly!|Here’s|Sure!)\s*Here’s a revised response that aligns with your established budget.*?\.\s*-*\s*",
                r"^(I understand you're asking about|As you mentioned,|Based on your question about|Regarding your inquiry about|When it comes to)\s*",
                r"\s*(Feel free to ask if you need more specific recommendations|Let me know if you need any further assistance|I hope this information helps|If you have any additional questions, feel free to ask)\.*$",
                r"\s*(It's important to note that|Keep in mind that|Please note that)\s*",
                r"\n+### (In conclusion|Summary|Final thoughts):.+?(?=\n|\Z)",
            ]
            for pattern in boilerplate_patterns:
                answer = re.sub(pattern, "", answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r"\n{3,}", "\n\n", answer).strip()

            # prefix language tag for non-English
            if user_lang == "es":
                answer = f"**(Respuesta en Español)**\n\n{answer}"
            elif user_lang == "fr":
                answer = f"**(Réponse en Français)**\n\n{answer}"

            # update context
            self.update_session_context(query, answer, session_id)

            return {
                "message": answer,
                "source_documents": valid_docs,
                "session_id": session_id,
            }

        except Exception:
            logger.exception("get_chat_response failed")
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": [],
            }

    # ═══════════════════════════════════════════════════════════════════
    #  Destructor – let event-loop handle session cleanup
    # ═══════════════════════════════════════════════════════════════════
    def __del__(self):
        if (
            hasattr(self, "aiohttp_session")
            and self.aiohttp_session
            and not self.aiohttp_session.closed
        ):
            logger.info("RAGService being destroyed with unclosed aiohttp session")
