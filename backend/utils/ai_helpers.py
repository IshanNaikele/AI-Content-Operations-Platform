import os
import requests
from openai import OpenAI
from config import OPENROUTER_BASE_URL, OPENROUTER_FALLBACK_MODELS, LLM_MAX_TOKENS ,OPENROUTER_API_KEY
from config import CLOUDFLARE_MODEL, get_cloudflare_credentials


# ═════════════════════════════════════════════════════════
# SHARED LLM FUNCTION — OpenRouter with fallback list
# ═════════════════════════════════════════════════════════

def openrouter_chat_completion(messages, temperature=0.7, response_format=None, stage=None, **kwargs):
    """
    Tries OpenRouter models one by one from OPENROUTER_FALLBACK_MODELS.
    Skips models that return empty choices or empty content.
    Returns the first successful response. Raises error if all fail.
    """
    last_error = None

    for model in OPENROUTER_FALLBACK_MODELS:
        try:
            client = OpenAI(
                api_key=OPENROUTER_API_KEY or os.getenv("X_API_KEY"),
                base_url=OPENROUTER_BASE_URL,
            )

            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": LLM_MAX_TOKENS,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)

            # ════════════════════════════════════════════════════════════
            # CENTRALIZED GUARD — downstream files never need this check
            # ═════════════════════════════════════════════════════════════
            if not response.choices or response.choices[0] is None:
                last_error = RuntimeError(f"Model {model} returned empty choices")
                continue

            content = response.choices[0].message.content
            if not content or not content.strip():
                last_error = RuntimeError(f"Model {model} returned empty content")
                continue

            return response

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"All OpenRouter fallback models failed. Last error: {last_error}"
    )


# ═════════════════════════════════════════════════════════
# SHARED IMAGE FUNCTION — Cloudflare Flux-1-schnell
# ═════════════════════════════════════════════════════════

def generate_cloudflare_image(prompt, output_path, width=1024, height=1024, key_num=1):
    """
    Generates one image via Cloudflare Flux-1-schnell.
    Saves to output_path. Returns the URL path string.
    """
    account_id, api_token = get_cloudflare_credentials(key_num)

    if not account_id or not api_token:
        raise RuntimeError(f"Cloudflare credentials not found for key #{key_num}")

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{CLOUDFLARE_MODEL}"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=180)

    if not response.ok:
        raise RuntimeError(f"Cloudflare image failed: HTTP {response.status_code} — {response.text[:200]}")

    data = response.json()
    if not data.get("success"):
        raise RuntimeError(f"Cloudflare image failed: {data.get('errors', response.text)}")

    import base64
    image_b64 = data["result"]["image"]
    image_bytes = base64.b64decode(image_b64)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return output_path