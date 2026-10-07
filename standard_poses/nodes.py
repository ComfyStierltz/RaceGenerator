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
    return ["all"] + names if names else ["all"]


def encode(clip, text):
    tokens = clip.tokenize(text or "")
    return clip.encode_from_tokens_scheduled(tokens)


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
                "positive": ("STRING", {"multiline": True, "default": ""}),
                "negative": ("STRING", {"multiline": True, "default": ""}),
                "editing_pose": (pose_names(), {"default": pose_names()[0]}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "steps": ("INT", {"default": 10, "min": 1, "max": 40}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 20.0}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS, {"default": "euler_ancestral"}),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS, {"default": "beta"}),
                "denoise": ("FLOAT", {"default": 0.55, "min": 0.0, "max": 1.0}),
                "clean_denoise": ("FLOAT", {"default": 0.28, "min": 0.0, "max": 1.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "sprite"
    OUTPUT_NODE = True

    def run(self, model, clip, vae, latent, anatomy, clothes, selected_pose, positive, negative, editing_pose, seed, steps, cfg, sampler_name, scheduler, denoise, clean_denoise):
        import folder_paths
        from pathlib import Path
        from PIL import Image
        store = load_store()
        poses = store.get("poses") or []
        shared_negative = negative or store.get("negative") or ""
        if selected_pose == "all":
            chosen = poses
        else:
            chosen = [item for item in poses if item.get("name") == selected_pose]
            if not chosen and selected_pose.startswith("0") and int(selected_pose[:2]) <= 7:
                chosen = [item for item in poses if item.get("name", "").startswith(selected_pose[:2])]
        if not chosen:
            print(f"[RaceGenerator] standard poses skipped for {selected_pose}")
            return (torch.zeros((1, 64, 64, 3)),)
        anatomy_cond = encode(clip, " ".join(part for part in (anatomy, clothes) if part and part.strip()))
        negative_cond = encode(clip, shared_negative)
        frames = []
        out = Path(folder_paths.get_output_directory()) / "sprites"
        out.mkdir(parents=True, exist_ok=True)
        for index, item in enumerate(chosen):
            pose_cond = encode(clip, item.get("positive") or positive)
            positive_cond = ConditioningConcat().concat(anatomy_cond, pose_cond)[0]
            sampled = common_ksampler(model, seed + index, steps, cfg, sampler_name, scheduler, positive_cond, negative_cond, latent, denoise=denoise)[0]
            image = vae.decode(sampled["samples"])
            cleaned = common_ksampler(model, seed + 100 + index, 8, cfg, sampler_name, scheduler, positive_cond, negative_cond, {"samples": vae.encode(image)}, denoise=clean_denoise)[0]
            image = vae.decode(cleaned["samples"])
            frames.append(image[0])
            arr = (image[0].clamp(0, 1).cpu().numpy() * 255).astype("uint8")
            Image.fromarray(arr).save(out / f"{item.get('name', 'pose').replace(' ', '_')}.png")
            print(f"[RaceGenerator] standard pose {item.get('name')}")
        height = max(frame.shape[0] for frame in frames)
        width = max(frame.shape[1] for frame in frames)
        batch = []
        for frame in frames:
            canvas = torch.zeros((height, width, frame.shape[2]), dtype=frame.dtype, device=frame.device)
            canvas[:frame.shape[0], :frame.shape[1]] = frame
            batch.append(canvas)
        return (torch.stack(batch, dim=0),)


if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/standard_poses")
    async def sprite_standard_poses(request):
        return web.json_response(load_store())

    @PromptServer.instance.routes.post("/sprite_preset/save_standard_pose")
    async def sprite_save_standard_pose(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name or name == "all":
            return web.json_response({"error": "bad name"}, status=400)
        store = load_store()
        poses = store.setdefault("poses", [])
        item = next((pose for pose in poses if pose.get("name") == name), None)
        if item is None:
            poses.append({"name": name, "positive": data.get("positive") or ""})
        else:
            item["positive"] = data.get("positive") or ""
        if "negative" in data:
            store["negative"] = data.get("negative") or ""
        save_store(store)
        return web.json_response({"ok": True, "names": ["all"] + [pose["name"] for pose in poses]})


NODE_CLASS_MAPPINGS = {"SpriteStandardPoses": SpriteStandardPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteStandardPoses": "Standard poses"}
