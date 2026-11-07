
import os
import requests
from dotenv import load_dotenv

load_dotenv()

QUESTION = "Explain what a banana is in one simple sentence."

API_KEYS = [
    ("Research", os.getenv("OPENROUTER_API_KEY_STAGE_RESEARCH")),
    ("Image Prompt", os.getenv("OPENROUTER_API_KEY_STAGE_IMAGE_PROMPT")),
    ("Blog Prompt", os.getenv("OPENROUTER_API_KEY_STAGE_BLOG_PROMPT")),
    ("Video Pipeline 1", os.getenv("OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_1")),
    ("Video Pipeline 2", os.getenv("OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_2")),
]

MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
]

URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_response():

    successful_keys = []
    failed_keys = []

    for key_name, api_key in API_KEYS:

        print(f"\n{'=' * 55}")
        print(f"TESTING API KEY: {key_name}")
        print(f"{'=' * 55}")

        if not api_key:
            print("Key missing. Skipping.")
            failed_keys.append(key_name)
            continue

        key_worked = False

        # Try every model with the CURRENT API key
        for model in MODELS:

            print(f"\nTrying model: {model}")

            try:
                response = requests.post(
                    URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": QUESTION}
                        ],
                        "max_tokens": 100,
                    },
                    timeout=60,
                )

                try:
                    data = response.json()
                except ValueError:
                    data = {}

                error = data.get("error")

                # Classify authentication/key-related failures
                if response.status_code in (401, 403):
                    reason = (
                        error.get("message", str(error))
                        if isinstance(error, dict)
                        else response.text[:300]
                    )

                    print(f"API KEY FAILURE: {reason}")
                    print("Moving to the next API key.")
                    break

                # Handle provider/model failures
                if response.status_code != 200 or error:

                    reason = (
                        error.get("message", str(error))
                        if isinstance(error, dict)
                        else response.text[:300]
                    )

                    print(f"MODEL/PROVIDER FAILURE: {reason}")
                    print("Trying the next model with the same key.")
                    continue

                choices = data.get("choices", [])

                if not choices:
                    print("No choices returned. Trying next model.")
                    continue

                message = choices[0].get("message", {})
                content = message.get("content")

                if not isinstance(content, str) or not content.strip():
                    print("No text output. Trying next model.")
                    continue

                # Successful API key
                print("\nSUCCESS!")
                print(f"API Key: {key_name}")
                print(f"Model: {model}")
                print(f"Output: {content.strip()}")

                successful_keys.append(key_name)
                key_worked = True

                # Stop testing models for this key.
                # Move to the next API key.
                break

            except requests.exceptions.RequestException as e:
                print(f"REQUEST FAILURE: {e}")
                print("Trying the next model with the same key.")
                continue

        if not key_worked:
            failed_keys.append(key_name)
            print(f"\nNo model worked for API key: {key_name}")

    # Final report
    print(f"\n{'=' * 55}")
    print("FINAL API KEY TEST REPORT")
    print(f"{'=' * 55}")

    print(f"\nSuccessful keys: {len(successful_keys)}")
    for name in successful_keys:
        print(f"  ✓ {name}")

    print(f"\nFailed keys: {len(failed_keys)}")
    for name in failed_keys:
        print(f"  ✗ {name}")

    if not successful_keys:
        raise RuntimeError(
            "All five API keys failed across all available models."
        )

    return successful_keys


if __name__ == "__main__":
    results = generate_response()
