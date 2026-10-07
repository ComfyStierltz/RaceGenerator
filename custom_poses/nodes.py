import json
import os

import torch
from aiohttp import web
from nodes import ConditioningConcat, common_ksampler
import comfy.samplers

try:
    from server import PromptServer
except Exception:
    PromptServer = None

PACK_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSE_FILE = os.path.join(PACK_DIR, "custom_poses", "poses.json")


def load_store():
    if not os.path.isfile(POSE_FILE):
        return {"poses": []}
    with open(POSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_store(store):
    os.makedirs(os.path.dirname(POSE_FILE), exist_ok=True)
    with open(POSE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def pose_names():
    names = [item.get("name") for item in load_store().get("poses", []) if item.get("name")]
    return names or ["08 squat"]


def as_image(image):
    while image.ndim > 4 and image.shape[1] == 1:
        image = image[:, 0]
    if image.ndim == 5:
        image = image[:, 0]
    if image.ndim == 4 and image.shape[1] in (1, 3, 4) and image.shape[-1] not in (1, 3, 4):
        image = image.permute(0, 2, 3, 1)
    if image.ndim == 3:
        image = image.unsqueeze(0)
    if image.shape[-1] > 3:
        image = image[:, :, :, :3]
    return image.clamp(0, 1)


def encode(clip, text):
    return clip.encode_from_tokens_scheduled(clip.tokenize(text or ""))


def pose_latent(vae, shared, image, width, height):
    if image is None and not width and not height:
        return shared
    if image is None:
        canvas = torch.zeros((1, height or 3120, width or 2080, 3))
        canvas[:, :, :, 1] = 1
        image = canvas
    else:
        image = as_image(image)
        if width and height:
            scaled = torch.nn.functional.interpolate(image.permute(0, 3, 1, 2), size=(height, width), mode="area")
            image = scaled.permute(0, 2, 3, 1)
    return {"samples": vae.encode(image[:, :, :, :3])}


class SpriteCustomPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "latent": ("LATENT",),
                "anatomy": ("STRING", {"forceInput": True}),
                "clothes": ("STRING", {"forceInput": True}),
                "selected_pose": ("STRING", {"forceInput": True}),
                "shared_negative": ("STRING", {"forceInput": True}),
                "editing_pose": (pose_names(), {"default": pose_names()[0]}),
                "positive": ("STRING", {"multiline": True, "default": ""}),
                "pose_negative": ("STRING", {"multiline": True, "default": ""}),
                "width": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 16}),
                "height": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 16}),
                "denoise": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0}),
                "reference_name": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "steps": ("INT", {"default": 10, "min": 1, "max": 40}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 20.0}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS, {"default": "euler_ancestral"}),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS, {"default": "beta"}),
            },
            "optional": {"reference_image": ("IMAGE",)},
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "sprite"
    OUTPUT_NODE = True

    def run(self, model, clip, vae, latent, anatomy, clothes, selected_pose, shared_negative, editing_pose, positive, pose_negative, width, height, denoise, reference_name, seed, steps, cfg, sampler_name, scheduler, reference_image=None):
        import folder_paths
        from pathlib import Path
        from PIL import Image
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item.update({"positive": positive, "negative": pose_negative, "width": width, "height": height, "denoise": denoise, "reference": reference_name})
        save_store(store)
        if selected_pose == "all":
            chosen = poses
        else:
            chosen = [item for item in poses if item.get("name") == selected_pose or selected_pose.startswith(item.get("name", "")[:2])]
        if not chosen:
            print(f"[RaceGenerator] custom poses skipped for {selected_pose}")
            return (torch.zeros((1, 64, 64, 3)),)
        anatomy_cond = encode(clip, " ".join(part for part in (anatomy, clothes) if part and part.strip()))
        frames = []
        out = Path(folder_paths.get_output_directory()) / "sprites"
        out.mkdir(parents=True, exist_ok=True)
        for index, item in enumerate(chosen):
            ref = reference_image if item.get("reference") else None
            pose_width = int(item.get("width") or 0)
            pose_height = int(item.get("height") or 0)
            current = pose_latent(vae, latent, ref, pose_width, pose_height)
            negative_text = ", ".join(part for part in (shared_negative, item.get("negative") or "") if part and part.strip())
            positive_cond = ConditioningConcat().concat(anatomy_cond, encode(clip, item.get("positive") or positive))[0]
            sampled = common_ksampler(model, seed + index, steps, cfg, sampler_name, scheduler, positive_cond, encode(clip, negative_text), current, denoise=float(item.get("denoise") or denoise))[0]
            image = as_image(vae.decode(sampled["samples"]))
            frame = image[0]
            frames.append(frame)
            arr = (frame.clamp(0, 1).cpu().numpy() * 255).astype("uint8")
            safe = f"custom_{index + 1:02d}_{item.get('name', 'pose').replace(' ', '_')}.png"
            Image.fromarray(arr).save(out / safe)
            print(f"[RaceGenerator] saved {out / safe} {tuple(frame.shape)}")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        small = []
        for frame in frames:
            scale = min(1040 / frame.shape[1], 1560 / frame.shape[0], 1)
            preview = torch.nn.functional.interpolate(frame.permute(2, 0, 1).unsqueeze(0), scale_factor=scale, mode="area")
            small.append(preview[0].permute(1, 2, 0).cpu())
        height = max(frame.shape[0] for frame in small)
        width = max(frame.shape[1] for frame in small)
        batch = []
        for frame in small:
            canvas = torch.zeros((height, width, frame.shape[2]))
            canvas[:frame.shape[0], :frame.shape[1]] = frame
            batch.append(canvas)
        return (torch.stack(batch, dim=0),)


if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/custom_poses")
    async def sprite_custom_poses(request):
        return web.json_response(load_store())

    @PromptServer.instance.routes.post("/sprite_preset/save_custom_pose")
    async def sprite_save_custom_pose(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "bad name"}, status=400)
        store = load_store()
        poses = store.setdefault("poses", [])
        payload = {
            "name": name,
            "positive": data.get("positive") or "",
            "negative": data.get("negative") or "",
            "width": int(data.get("width") or 0),
            "height": int(data.get("height") or 0),
            "denoise": float(data.get("denoise") or 0.8),
            "reference": data.get("reference") or "",
        }
        item = next((pose for pose in poses if pose.get("name") == name), None)
        if item is None:
            poses.append(payload)
        else:
            item.update(payload)
        save_store(store)
        return web.json_response({"ok": True, "names": [pose["name"] for pose in poses]})


NODE_CLASS_MAPPINGS = {"SpriteCustomPoses": SpriteCustomPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteCustomPoses": "Custom poses"}
