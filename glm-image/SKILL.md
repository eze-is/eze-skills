---
name: glm-image
description: Text-to-image generation using GLM-Image API from BigModel (智谱AI). Use when users ask to generate, create, or make images from text descriptions, prompts, or ideas. Supports Chinese and English prompts with configurable image sizes and quality. Requires API key.
---

# GLM-Image

Text-to-image generation using the GLM-Image API from BigModel (智谱AI).

## Quick Start

Use the bundled Python script to generate images:

```bash
python3 scripts/glm_image.py "a beautiful sunset over mountains" --api-key YOUR_API_KEY
```

For Chinese prompts:

```bash
python3 scripts/glm_image.py "蓝天白云下的美丽山景" --api-key YOUR_API_KEY
```

## Usage

### Script Syntax

```bash
python3 scripts/glm_image.py <prompt> --api-key <API_KEY> [options]
```

**Required Arguments:**
- `prompt`: Text description of the image to generate
- `--api-key`: BigModel API key (format: `id.secret`)

**Optional Arguments:**
| Option | Description |
|--------|-------------|
| `--async` | Use async mode (polling for result) |
| `--quality` | Image quality, default: `hd` |
| `--size` | Image size (e.g., `1024x1024`) |
| `--no-watermark` | Disable watermark |
| `--user-id` | End user unique ID |
| `--timeout` | Async timeout in seconds (default: 300) |
| `--output`, `-o` | Save JSON result to file |

### Image Sizes

Recommended sizes (32-aligned, within 512-2048px):
- `1280x1280`
- `1568x1056`, `1056x1568`
- `1472x1088`, `1088x1472`
- `1728x960`, `960x1728`

Custom sizes must:
- Be within 512-2048px range
- Be multiples of 32
- Have max pixels ≤ 2^22

### Examples

Generate with custom size:

```bash
python3 scripts/glm_image.py "一只可爱的小猫" --api-key YOUR_KEY --size 1024x1024
```

Async mode with JSON output:

```bash
python3 scripts/glm_image.py "futuristic cityscape" --api-key YOUR_KEY --async --output result.json
```

No watermark (requires signed disclaimer):

```bash
python3 scripts/glm_image.py "山水画" --api-key YOUR_KEY --no-watermark
```

## API Authentication

API key format: `{id}.{secret}`

Example header:
```
Authorization: Bearer {api_key}
```

## Resources

### scripts/glm_image.py

Python client for GLM-Image API. Supports:
- Synchronous generation (direct result)
- Asynchronous generation (polling)
- Configurable size, quality, watermark
- Result extraction and JSON output

Can be imported as a module:

```python
from scripts.glm_image import GLMImageClient

client = GLMImageClient("your_api_key")
result = client.generate_sync("a sunset at the beach")
urls = client.extract_image_urls(result)
```
