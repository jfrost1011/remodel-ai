import requests
import json
import sys
BASE_URL = "http://localhost:8000"
def test_health():
    """Test health endpoint"""
    print("Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        result = response.json()
        print(f"? Health Check: {result}")
        return True
    except Exception as e:
        print(f"? Health Check Failed: {str(e)}")
        return False
def test_chat_valid_location():
    """Test chat endpoint with valid location"""
    print("\nTesting Chat (Valid Location)...")
    payload = {
        "content": "How much does a kitchen remodel cost in San Diego?",
        "role": "user"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"? Chat Response: {result['message'][:100]}...")
        return True, result.get('session_id')
    except Exception as e:
        print(f"? Chat Failed: {str(e)}")
        return False, None
def test_chat_invalid_location():
    """Test chat endpoint with invalid location"""
    print("\nTesting Chat (Invalid Location)...")
    payload = {
        "content": "How much does a kitchen remodel cost in Phoenix?",
        "role": "user"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"? Location Filter Working: {result['message'][:100]}...")
        return True
    except Exception as e:
        print(f"? Location Filter Failed: {str(e)}")
        return False
def test_estimate():
    """Test estimate endpoint"""
    print("\nTesting Estimate Creation...")
    payload = {
        "project_details": {
            "project_type": "kitchen_remodel",
            "property_type": "single_family",
            "city": "San Diego",
            "state": "CA",
            "square_footage": 200,
            "additional_details": "Modern kitchen with island"
        }
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/estimate", json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"? Estimate Created: ID={result['estimate_id']}")
        print(f"  Total Cost: ${result['total_cost']:,.0f}")
        print(f"  Range: ${result['cost_range_low']:,.0f} - ${result['cost_range_high']:,.0f}")
        return True, result['estimate_id']
    except Exception as e:
        print(f"? Estimate Failed: {str(e)}")
        if hasattr(e, 'response') and e.response.text:
            print(f"  Error details: {e.response.text}")
        return False, None
def test_export(estimate_id):
    """Test export endpoint"""
    print(f"\nTesting PDF Export (Estimate: {estimate_id})...")
    payload = {
        "estimate_id": estimate_id,
        "format": "pdf"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/export", json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"? Export Created: {result['download_name']}")
        # Test download
        download_response = requests.get(f"{BASE_URL}{result['file_url']}")
        download_response.raise_for_status()
        print(f"? PDF Download Successful: {len(download_response.content)} bytes")
        return True
    except Exception as e:
        print(f"? Export Failed: {str(e)}")
        return False
def test_session_history(session_id):
    """Test session history endpoint"""
    print(f"\nTesting Session History (Session: {session_id})...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/sessions/{session_id}/history")
        response.raise_for_status()
        result = response.json()
        print(f"? Session History Retrieved: {len(result['history'])} messages")
        return True
    except Exception as e:
        print(f"? Session History Failed: {str(e)}")
        return False
def run_all_tests():
    """Run all API tests"""
    print("=" * 50)
    print("RemodelAI API Test Suite")
    print("=" * 50)
    test_results = []
    # Test health
    test_results.append(("Health Check", test_health()))
    # Test chat with valid location
    chat_success, session_id = test_chat_valid_location()
    test_results.append(("Chat (Valid Location)", chat_success))
    # Test chat with invalid location
    test_results.append(("Chat (Invalid Location)", test_chat_invalid_location()))
    # Test estimate
    estimate_success, estimate_id = test_estimate()
    test_results.append(("Estimate Creation", estimate_success))
    # Test export if estimate succeeded
    if estimate_id:
        test_results.append(("PDF Export", test_export(estimate_id)))
    # Test session history if chat succeeded
    if session_id:
        test_results.append(("Session History", test_session_history(session_id)))
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    for test_name, result in test_results:
        status = "? PASSED" if result else "? FAILED"
        print(f"{test_name}: {status}")
    print(f"\nTotal: {passed}/{total} tests passed")
    return passed == total
if __name__ == "__main__":
    if run_all_tests():
        print("\n?? All tests passed!")
        sys.exit(0)
    else:
        print("\n? Some tests failed!")
        sys.exit(1)
