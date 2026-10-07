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
POSE_FILE = os.path.join(PACK_DIR, "standard_poses", "poses.json")


def load_store():
    if not os.path.isfile(POSE_FILE):
        return {"negative": "", "poses": []}
    with open(POSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_store(store):
    os.makedirs(os.path.dirname(POSE_FILE), exist_ok=True)
    with open(POSE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def pose_names():
    names = [item.get("name") for item in load_store().get("poses", []) if item.get("name")]
    return names or ["01 front"]



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


class SpriteStandardPoses:
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
                "editing_pose": (pose_names(), {"default": pose_names()[0]}),
                "positive": ("STRING", {"multiline": True, "default": ""}),
                "pose_negative": ("STRING", {"multiline": True, "default": ""}),
                "shared_negative": ("STRING", {"multiline": True, "default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "steps": ("INT", {"default": 10, "min": 1, "max": 40}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 20.0}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS, {"default": "euler_ancestral"}),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS, {"default": "beta"}),
                "denoise": ("FLOAT", {"default": 0.55, "min": 0.0, "max": 1.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "sprite"
    OUTPUT_NODE = True

    def run(self, model, clip, vae, latent, anatomy, clothes, selected_pose, editing_pose, positive, pose_negative, shared_negative, seed, steps, cfg, sampler_name, scheduler, denoise):
        import folder_paths
        from pathlib import Path
        from PIL import Image
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose:
                item["positive"] = positive
                item["negative"] = pose_negative
        store["negative"] = shared_negative
        save_store(store)
        if selected_pose == "all":
            chosen = poses
        else:
            chosen = [item for item in poses if item.get("name") == selected_pose or item.get("name", "").startswith(selected_pose[:2])]
            chosen = [item for item in chosen if not item.get("name", "").startswith("08") and not item.get("name", "").startswith("09")]
        if not chosen:
            print(f"[RaceGenerator] standard poses skipped for {selected_pose}")
            return (torch.zeros((1, 64, 64, 3)),)
        anatomy_cond = encode(clip, " ".join(part for part in (anatomy, clothes) if part and part.strip()))
        frames = []
        out = Path(folder_paths.get_output_directory()) / "sprites"
        out.mkdir(parents=True, exist_ok=True)
        for index, item in enumerate(chosen):
            negative_text = ", ".join(part for part in (shared_negative, item.get("negative") or "") if part and part.strip())
            positive_cond = ConditioningConcat().concat(anatomy_cond, encode(clip, item.get("positive") or positive))[0]
            negative_cond = encode(clip, negative_text)
            sampled = common_ksampler(model, seed + index, steps, cfg, sampler_name, scheduler, positive_cond, negative_cond, latent, denoise=denoise)[0]
            image = as_image(vae.decode(sampled["samples"]))
            frames.append(image[0])
            arr = (image[0].clamp(0, 1).cpu().numpy() * 255).astype("uint8")
            Image.fromarray(arr).save(out / f"{item.get('name', 'pose').replace(' ', '_')}.png")
            print(f"[RaceGenerator] standard pose {item.get('name')} {tuple(image.shape)}")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"[RaceGenerator] standard poses saved {len(frames)}, preview is the last frame")
        return (frames[-1].unsqueeze(0).cpu(),)


if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/standard_poses")
    async def sprite_standard_poses(request):
        return web.json_response(load_store())

    @PromptServer.instance.routes.post("/sprite_preset/save_standard_pose")
    async def sprite_save_standard_pose(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "bad name"}, status=400)
        store = load_store()
        poses = store.setdefault("poses", [])
        item = next((pose for pose in poses if pose.get("name") == name), None)
        payload = {"name": name, "positive": data.get("positive") or "", "negative": data.get("negative") or ""}
        if item is None:
            poses.append(payload)
        else:
            item.update(payload)
        if "shared_negative" in data:
            store["negative"] = data.get("shared_negative") or ""
        save_store(store)
        return web.json_response({"ok": True, "names": [pose["name"] for pose in poses]})


NODE_CLASS_MAPPINGS = {"SpriteStandardPoses": SpriteStandardPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteStandardPoses": "Standard poses"}
