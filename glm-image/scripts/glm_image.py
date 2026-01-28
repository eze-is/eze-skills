#!/usr/bin/env python3
"""
GLM-Image API Client

A Python client for calling the GLM-Image text-to-image API from BigModel.
Supports both synchronous and asynchronous image generation.
"""

import argparse
import json
import sys
import time
from urllib.parse import urlparse

# Check if requests is available
try:
    import requests
except ImportError:
    print("Error: requests library is required. Install it with: pip3 install requests", file=sys.stderr)
    sys.exit(1)


class GLMImageClient:
    """Client for GLM-Image API."""

    # API endpoints
    SYNC_URL = "https://open.bigmodel.cn/api/paas/v4/images/generations"
    ASYNC_URL = "https://open.bigmodel.cn/api/paas/v4/async/images/generations"
    RESULT_URL_TEMPLATE = "https://open.bigmodel.cn/api/paas/v4/async-result/{}"

    # Recommended sizes
    RECOMMENDED_SIZES = [
        "1280x1280",
        "1568x1056",
        "1056x1568",
        "1472x1088",
        "1088x1472",
        "1728x960",
        "960x1728",
    ]

    def __init__(self, api_key: str):
        """Initialize client with API key.

        Args:
            api_key: BigModel API key in format 'id.secret'
        """
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def generate_sync(self, prompt: str, quality: str = "hd", size: str = None,
                      watermark_enabled: bool = True, user_id: str = None) -> dict:
        """Generate image synchronously.

        Args:
            prompt: Text description of the image to generate
            quality: Image quality ('hd' for high quality)
            size: Image size (e.g., '1024x1024'), must be 32-aligned and within 512-2048px
            watermark_enabled: Whether to add watermark
            user_id: End user unique ID

        Returns:
            API response dict with image URLs
        """
        payload = {
            "model": "glm-image",
            "prompt": prompt,
            "quality": quality,
        }

        if size:
            payload["size"] = size
        if watermark_enabled is not None:
            payload["watermark_enabled"] = str(watermark_enabled).lower()
        if user_id:
            payload["user_id"] = user_id

        response = requests.post(self.SYNC_URL, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def generate_async(self, prompt: str, quality: str = "hd", size: str = None,
                       watermark_enabled: bool = True, user_id: str = None) -> dict:
        """Generate image asynchronously.

        Args:
            prompt: Text description of the image to generate
            quality: Image quality ('hd' for high quality)
            size: Image size (e.g., '1024x1024')
            watermark_enabled: Whether to add watermark
            user_id: End user unique ID

        Returns:
            API response dict with task ID and status
        """
        payload = {
            "model": "glm-image",
            "prompt": prompt,
            "quality": quality,
        }

        if size:
            payload["size"] = size
        if watermark_enabled is not None:
            payload["watermark_enabled"] = str(watermark_enabled).lower()
        if user_id:
            payload["user_id"] = user_id

        response = requests.post(self.ASYNC_URL, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_result(self, task_id: str) -> dict:
        """Get async task result.

        Args:
            task_id: Task ID from async generation

        Returns:
            API response dict with task status and result
        """
        url = self.RESULT_URL_TEMPLATE.format(task_id)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def wait_for_result(self, task_id: str, timeout: int = 300, interval: int = 2) -> dict:
        """Wait for async task to complete.

        Args:
            task_id: Task ID from async generation
            timeout: Maximum wait time in seconds
            interval: Polling interval in seconds

        Returns:
            Final API response dict with image URLs

        Raises:
            TimeoutError: If task doesn't complete within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get_result(task_id)
            status = result.get("task_status")

            if status == "SUCCESS":
                return result
            elif status == "FAIL":
                raise RuntimeError(f"Image generation failed: {result}")

            time.sleep(interval)

        raise TimeoutError(f"Image generation timed out after {timeout} seconds")

    def extract_image_urls(self, response: dict) -> list:
        """Extract image URLs from API response.

        Args:
            response: API response dict

        Returns:
            List of image URLs
        """
        if "image_result" in response:
            return [item["url"] for item in response["image_result"]]
        elif "data" in response:
            return [item["url"] for item in response["data"]]
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using GLM-Image API"
    )
    parser.add_argument("prompt", help="Text description of the image")
    parser.add_argument("--api-key", required=True, help="BigModel API key")
    parser.add_argument("--async", dest="async_mode", action="store_true",
                        help="Use async mode")
    parser.add_argument("--quality", default="hd", choices=["hd"],
                        help="Image quality (default: hd)")
    parser.add_argument("--size", help="Image size (e.g., 1024x1024)")
    parser.add_argument("--no-watermark", action="store_true",
                        help="Disable watermark")
    parser.add_argument("--user-id", help="End user ID")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Timeout for async mode in seconds (default: 300)")
    parser.add_argument("--output", "-o", help="Output file for JSON result")

    args = parser.parse_args()

    client = GLMImageClient(args.api_key)

    if args.async_mode:
        # Async mode
        submit_result = client.generate_async(
            prompt=args.prompt,
            quality=args.quality,
            size=args.size,
            watermark_enabled=not args.no_watermark,
            user_id=args.user_id
        )
        task_id = submit_result.get("id")
        print(f"Task submitted. ID: {task_id}", file=sys.stderr)

        final_result = client.wait_for_result(task_id, timeout=args.timeout)
    else:
        # Sync mode
        final_result = client.generate_sync(
            prompt=args.prompt,
            quality=args.quality,
            size=args.size,
            watermark_enabled=not args.no_watermark,
            user_id=args.user_id
        )

    # Output image URLs
    urls = client.extract_image_urls(final_result)
    for url in urls:
        print(url)

    # Save JSON result if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(final_result, f, indent=2)
        print(f"\nResult saved to: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
