# test_context_rating.py
import asyncio
import re
from services.rag_service import RAGService

async def test_conversation_quality():
    """Test the quality of conversation with 10 questions and rate each response."""
    service = RAGService()
    session_id = "test_rating_session"
    total_score = 0
    
    # Questions designed to test context awareness
    questions = [
        "I'm planning to remodel my kitchen in San Diego. What would it cost?",
        "What material options do I have for countertops?",
        "I'm thinking about installing an island. How much extra would that cost?",
        "What's the typical timeline for a kitchen remodel?",
        "Are permits required for kitchen remodels in San Diego?",
        "I want to stay under $40,000 total. Is that realistic?",
        "What kind of appliances would you recommend for that budget?",
        "Can I keep my existing cabinets to save money?",
        "How much would it cost to just replace the countertops and sink?",
        "What would you suggest as the best way to divide my budget between cabinets, countertops, and appliances?"
    ]
    
    # Evaluation criteria for each question
    criteria = [
        "Provided specific San Diego cost info (not generic)",
        "Remembered kitchen context without being told again",
        "Referenced kitchen & remembered San Diego",
        "Provided timeline specific to kitchen remodels",
        "Provided San Diego-specific permit info for kitchens",
        "Referred back to previously mentioned costs vs. new budget",
        "Made recommendations within the stated $40k budget",
        "Discussed cabinet refinishing in context of budget",
        "Provided specific costs for just these items",
        "Gave budget breakdown consistent with $40k total"
    ]
    
    print("\n===== CONTEXT AWARENESS EVALUATION =====\n")
    
    for i, (question, criterion) in enumerate(zip(questions, criteria), 1):
        print(f"\n----- QUESTION {i}/10 -----")
        print(f"Q: {question}")
        
        # Get response
        response = await service.get_chat_response(question, [], session_id)
        message = response.get('message', '')
        
        # Print truncated response
        print(f"A: {message[:10000]}...")
        
        # Rate this response (1-10)
        print(f"\nCriterion: {criterion}")
        rating = int(input("Rate this response (1-10): "))
        total_score += rating
        
        # Optional: Add comments
        comment = input("Comments (optional): ")
        if comment:
            print(f"Comment: {comment}")
    
    # Calculate and display final score
    final_score = total_score / len(questions)
    print(f"\n===== FINAL SCORE: {final_score:.1f}/10 =====")
    print(f"Previous score: 7/10")
    print(f"Improvement: {final_score - 7:.1f}")
    
    return final_score

if __name__ == "__main__":
    asyncio.run(test_conversation_quality())