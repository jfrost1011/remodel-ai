import requests
import time
import concurrent.futures
import statistics
BASE_URL = "http://localhost:8000"
def time_request(endpoint, method="GET", json_data=None):
    """Time a single request"""
    start = time.time()
    if method == "GET":
        response = requests.get(f"{BASE_URL}{endpoint}")
    else:
        response = requests.post(f"{BASE_URL}{endpoint}", json=json_data)
    end = time.time()
    return end - start, response.status_code
def test_endpoint_performance(name, endpoint, method="GET", json_data=None, num_requests=10):
    """Test performance of an endpoint"""
    print(f"\nTesting {name} ({num_requests} requests)...")
    times = []
    errors = 0
    for i in range(num_requests):
        try:
            duration, status = time_request(endpoint, method, json_data)
            if status == 200:
                times.append(duration)
            else:
                errors += 1
        except Exception as e:
            errors += 1
    if times:
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print(f"  Errors: {errors}")
    else:
        print(f"  All requests failed!")
def test_concurrent_load(num_concurrent=5):
    """Test concurrent request handling"""
    print(f"\nTesting Concurrent Load ({num_concurrent} simultaneous requests)...")
    chat_payload = {
        "content": "How much does a kitchen remodel cost in San Diego?",
        "role": "user"
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = []
        start_time = time.time()
        for i in range(num_concurrent):
            future = executor.submit(
                requests.post,
                f"{BASE_URL}/api/v1/chat",
                json=chat_payload
            )
            futures.append(future)
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                response = future.result()
                results.append(response.status_code)
            except Exception as e:
                results.append(None)
        end_time = time.time()
    successful = sum(1 for r in results if r == 200)
    print(f"  Successful: {successful}/{num_concurrent}")
    print(f"  Total time: {end_time - start_time:.3f}s")
    print(f"  Avg per request: {(end_time - start_time) / num_concurrent:.3f}s")
def run_performance_tests():
    """Run all performance tests"""
    print("=" * 50)
    print("RemodelAI Performance Test Suite")
    print("=" * 50)
    # Test individual endpoints
    test_endpoint_performance("Health Check", "/health")
    test_endpoint_performance(
        "Chat Endpoint",
        "/api/v1/chat",
        method="POST",
        json_data={
            "content": "How much does a kitchen remodel cost in San Diego?",
            "role": "user"
        }
    )
    test_endpoint_performance(
        "Estimate Endpoint",
        "/api/v1/estimate",
        method="POST",
        json_data={
            "project_details": {
                "project_type": "kitchen_remodel",
                "property_type": "single_family",
                "city": "San Diego",
                "state": "CA",
                "square_footage": 200
            }
        },
        num_requests=5  # Fewer requests since this is more expensive
    )
    # Test concurrent load
    test_concurrent_load(5)
    test_concurrent_load(10)
if __name__ == "__main__":
    run_performance_tests()
