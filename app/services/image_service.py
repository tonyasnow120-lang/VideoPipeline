from pathlib import Path

from app.models import AppSettings, Series


def generate_images(
    scenes: list,
    series: Series,
    settings: AppSettings,
    workspace_dir: Path,
    log_fn,
) -> list:
    if settings.image_provider == "local_sd":
        return _generate_local_sd(scenes, settings.local_sd_url, workspace_dir, log_fn)
    else:
        return _generate_openai_images(
            scenes, settings.openai_api_key, workspace_dir, log_fn
        )


def _generate_local_sd(scenes, sd_url, workspace_dir, log_fn):
    import base64

    import requests

    paths = []
    for scene in scenes:
        log_fn("info", f"Generating image for scene {scene.scene_number}...")
        payload = {
            "prompt": scene.image_prompt + ", masterpiece, best quality, highly detailed",
            "negative_prompt": (
                "text, watermark, logo, signature, blurry, low quality, "
                "deformed, ugly, worst quality, low resolution, nsfw"
            ),
            "width": 576,
            "height": 1024,
            "steps": 25,
            "cfg_scale": 7.0,
            "sampler_name": "DPM++ 2M Karras",
            "batch_size": 1,
            "n_iter": 1,
        }
        response = requests.post(f"{sd_url}/sdapi/v1/txt2img", json=payload, timeout=300)
        response.raise_for_status()
        img_b64 = response.json()["images"][0]
        out_path = workspace_dir / f"scene_{scene.scene_number}_image.png"
        out_path.write_bytes(base64.b64decode(img_b64))
        paths.append(out_path)
        log_fn("success", f"Image generated for scene {scene.scene_number}")
    return paths


def _generate_openai_images(scenes, api_key, workspace_dir, log_fn):
    import time

    import httpx
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    paths = []
    for scene in scenes:
        log_fn("info", f"Requesting OpenAI image for scene {scene.scene_number}...")
        response = client.images.generate(
            model="gpt-image-1",
            prompt=scene.image_prompt,
            size="1024x1536",
            quality="standard",
            n=1,
        )
        data = response.data[0]
        out_path = workspace_dir / f"scene_{scene.scene_number}_image.png"
        # gpt-image-1 may return a URL or base64 depending on configuration.
        if getattr(data, "url", None):
            img_bytes = httpx.get(data.url).content
            out_path.write_bytes(img_bytes)
        else:
            import base64

            out_path.write_bytes(base64.b64decode(data.b64_json))
        paths.append(out_path)
        log_fn("success", f"Image generated for scene {scene.scene_number}")
        time.sleep(1)
    return paths
