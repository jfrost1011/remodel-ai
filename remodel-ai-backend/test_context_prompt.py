# test_context_prompt.py
import asyncio
from services.rag_service import RAGService

async def test_conversation():
    service = RAGService()
    session_id = "test_session_123"
    
    # First message - should have minimal context
    print("\n----- FIRST MESSAGE -----")
    response1 = await service.get_chat_response(
        "I'm thinking about remodeling my kitchen in San Diego. What would it cost?",
        [],
        session_id
    )
    print(f"RESPONSE: {response1['message'][:200]}...")
    
    # Second message - should now have context about kitchen remodel in San Diego
    print("\n----- SECOND MESSAGE -----")
    response2 = await service.get_chat_response(
        "What kind of countertops would you recommend?",
        [],
        session_id
    )
    print(f"RESPONSE: {response2['message'][:200]}...")
    
    # Third message - ask something that would normally trigger a budget question
    print("\n----- THIRD MESSAGE -----")
    response3 = await service.get_chat_response(
        "Would high-end appliances fit in my budget?",
        [],
        session_id
    )
    print(f"RESPONSE: {response3['message'][:200]}...")

if __name__ == "__main__":
    asyncio.run(test_conversation())