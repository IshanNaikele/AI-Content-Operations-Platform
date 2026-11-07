
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TAVILY_API_KEY")

URL = "https://api.tavily.com/search"

if not API_KEY:
    print("✗ TAVILY_API_KEY not found in .env")
    exit()

print("=" * 55)
print("         TAVILY API TEST")
print("=" * 55)

payload = {
    "query": "Latest advancements in LLM agents, RAG systems, and agentic AI in 2026",
    "topic": "general",
    "search_depth": "advanced",
    "max_results": 5,
    "include_answer": "advanced",
    "include_raw_content": True
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

try:
    print("\nTesting Tavily Advanced Search...\n")

    response = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=90
    )

    print("HTTP Status:", response.status_code)

    if response.status_code == 200:
        data = response.json()

        print("\n✓ API KEY WORKING")
        print("✓ ADVANCED SEARCH WORKING")

        print("\n" + "=" * 55)
        print("SEARCH ANSWER")
        print("=" * 55)

        print(data.get("answer", "No answer returned"))

        results = data.get("results", [])

        print("\n" + "=" * 55)
        print(f"SEARCH RESULTS: {len(results)}")
        print("=" * 55)

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result.get('title')}")
            print("URL:", result.get("url"))
            print("Score:", result.get("score"))
            print("Content:", result.get("content", "")[:500])

            raw = result.get("raw_content")
            if raw:
                print("Raw Content:", raw[:300])

        print("\n" + "=" * 55)
        print("USAGE INFORMATION")
        print("=" * 55)

        print("Usage:", data.get("usage"))
        print("Response Time:", data.get("response_time"))

        print("\n✓ TAVILY ADVANCED SEARCH TEST PASSED")

    else:
        print("\n✗ API REQUEST FAILED")
        print("Response:", response.text[:1500])

        if response.status_code == 401:
            print("Reason: Invalid API key")

        elif response.status_code == 403:
            print("Reason: Access forbidden")

        elif response.status_code == 429:
            print("Reason: Rate limit or quota exceeded")

except requests.exceptions.Timeout:
    print("✗ Request timed out")

except requests.exceptions.RequestException as e:
    print("✗ Network error:", e)

except Exception as e:
    print("✗ Unexpected error:", e)
