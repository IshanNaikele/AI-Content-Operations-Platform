
import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = "@cf/black-forest-labs/flux-1-schnell"
PROMPT = "A realistic traffic light on a city street, high quality, daylight"

for i in range(1, 5):
    account_id = os.getenv(f"CLOUDFLARE_ACCOUNT_ID_{i}")
    api_token = os.getenv(f"CLOUDFLARE_API_TOKEN_{i}")

    if not account_id or not api_token:
        print(f"Key {i}: ✗ Not set in .env")
        continue

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{MODEL}"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {"prompt": PROMPT}

    try:
        print(f"\nKey {i}: Generating image...")

        r = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=120,
        )

        if not r.ok:
            print(f"Key {i}: ✗ HTTP {r.status_code}")
            print(r.text[:500])
            continue

        content_type = r.headers.get("Content-Type", "")

        # Case 1: API returns image bytes directly
        if content_type.startswith("image/"):
            image_bytes = r.content

        # Case 2: API returns JSON containing a base64 image
        else:
            data = r.json()

            if not data.get("success"):
                print(f"Key {i}: ✗ API failed")
                print(data.get("errors", data))
                continue

            result = data.get("result", {})
            image_base64 = result.get("image")

            if not image_base64:
                print(f"Key {i}: ✗ No image found in response")
                print(str(data)[:500])
                continue

            image_bytes = base64.b64decode(image_base64)

        # Save the generated image in the current directory
        filename = f"traffic_light_key_{i}.png"

        with open(filename, "wb") as f:
            f.write(image_bytes)

        print(f"Key {i}: ✓ Image generated successfully!")
        print(f"Saved to: {os.path.abspath(filename)}")

    except Exception as e:
        print(f"Key {i}: ✗ Error — {e}")
