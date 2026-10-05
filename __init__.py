
import json
import comfy.samplers
import os
import re

from aiohttp import web

try:
    from server import PromptServer
except Exception:
    PromptServer = None

WEB_DIRECTORY = "./web"
NODE_DIR = os.path.dirname(os.path.realpath(__file__))
RACE_DIR = os.path.join(NODE_DIR, "presets")
CLOTHES_DIR = os.path.join(NODE_DIR, "clothes")
NAKED = "naked"


def slug(name):
    clean = re.sub(r"[^0-9A-Za-zА-Яа-я_\- ]+", "", name).strip().replace(" ", "_")
    return clean or "preset"


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def race_files():
    os.makedirs(RACE_DIR, exist_ok=True)
    return sorted(p for p in os.listdir(RACE_DIR) if p.endswith(".json"))


def clothes_files():
    os.makedirs(CLOTHES_DIR, exist_ok=True)
    return sorted(p for p in os.listdir(CLOTHES_DIR) if p.endswith(".json"))


def race_names():
    found = []
    for name in race_files():
        data = read_json(os.path.join(RACE_DIR, name))
        found.append(data.get("name") or name[:-5])
    return found or ["(пусто)"]


def clothes_names():
    found = [NAKED]
    for name in clothes_files():
        data = read_json(os.path.join(CLOTHES_DIR, name))
        found.append(data.get("name") or name[:-5])
    return found


def load_race(name):
    for file_name in race_files():
        data = read_json(os.path.join(RACE_DIR, file_name))
        if data.get("name") == name or file_name[:-5] == name:
            return data.get("anatomy") or "", data.get("negative") or ""
    return "", ""


def load_clothes(name):
    if not name or name == NAKED:
        return ""
    for file_name in clothes_files():
        data = read_json(os.path.join(CLOTHES_DIR, file_name))
        if data.get("name") == name or file_name[:-5] == name:
            return data.get("text") or ""
    return ""


def save_race(name, anatomy, negative):
    os.makedirs(RACE_DIR, exist_ok=True)
    path = os.path.join(RACE_DIR, slug(name) + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "anatomy": anatomy, "negative": negative}, f, ensure_ascii=False, indent=2)


def save_clothes(name, text):
    if name == NAKED:
        return
    os.makedirs(CLOTHES_DIR, exist_ok=True)
    path = os.path.join(CLOTHES_DIR, slug(name) + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "text": text}, f, ensure_ascii=False, indent=2)


class SpritePromptPreset:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "race_preset": (race_names(), {"default": race_names()[0]}),
                "anatomy": ("STRING", {"multiline": True, "default": ""}),
                "negative": ("STRING", {"multiline": True, "default": ""}),
                "clothes_preset": (clothes_names(), {"default": clothes_names()[0]}),
                "clothes": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("anatomy", "negative", "clothes")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, race_preset, anatomy, negative, clothes_preset, clothes):
        return (anatomy, negative, clothes)


class SpritePresetSelect:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "apply": ("BOOLEAN", {"default": True}),
                "race_preset": (race_names(), {"default": race_names()[0]}),
                "clothes_preset": (clothes_names(), {"default": NAKED}),
            },
            "optional": {
                "anatomy_in": ("STRING", {"forceInput": True}),
                "negative_in": ("STRING", {"forceInput": True}),
                "clothes_in": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN")
    RETURN_NAMES = ("anatomy", "negative", "clothes", "use_clothes")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, apply, race_preset, clothes_preset, anatomy_in="", negative_in="", clothes_in=""):
        if not apply:
            text = clothes_in or ""
            return (anatomy_in or "", negative_in or "", text, bool(text.strip()))
        anatomy, negative = load_race(race_preset)
        clothes = load_clothes(clothes_preset)
        return (anatomy, negative, clothes, clothes_preset != NAKED and bool(clothes.strip()))


if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/list")
    async def sprite_preset_list(request):
        return web.json_response({"races": race_names(), "clothes": clothes_names()})

    @PromptServer.instance.routes.post("/sprite_preset/save_body")
    async def sprite_preset_save_body(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "empty name"}, status=400)
        save_race(name, data.get("anatomy") or "", data.get("negative") or "")
        return web.json_response({"ok": True, "names": race_names()})

    @PromptServer.instance.routes.post("/sprite_preset/save_clothes")
    async def sprite_preset_save_clothes(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name or name == NAKED:
            return web.json_response({"error": "bad name"}, status=400)
        save_clothes(name, data.get("clothes") or "")
        return web.json_response({"ok": True, "names": clothes_names()})

    @PromptServer.instance.routes.get("/sprite_preset/poses")
    async def sprite_preset_poses(request):
        return web.json_response(load_poses())

    @PromptServer.instance.routes.post("/sprite_preset/save_pose")
    async def sprite_preset_save_pose(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "empty name"}, status=400)
        store = load_poses()
        poses = store["poses"]
        item = next((p for p in poses if p.get("name") == name), None)
        if item is None:
            poses.append({"name": name, "positive": data.get("positive") or "", "negative": data.get("negative") or "", "denoise": float(data.get("denoise") or 0.6)})
        else:
            item["positive"] = data.get("positive") or ""
            item["negative"] = data.get("negative") or ""
            item["denoise"] = float(data.get("denoise") or item.get("denoise") or 0.6)
        save_poses(store)
        return web.json_response({"ok": True, "names": [p["name"] for p in poses]})

    @PromptServer.instance.routes.get("/sprite_preset/custom_poses")
    async def sprite_preset_custom_poses(request):
        return web.json_response(load_custom_poses())

    @PromptServer.instance.routes.post("/sprite_preset/save_custom_pose")
    async def sprite_preset_save_custom_pose(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "empty name"}, status=400)
        store = load_custom_poses()
        poses = store["poses"]
        item = next((p for p in poses if p.get("name") == name), None)
        payload = {
            "name": name,
            "positive": data.get("positive") or "",
            "negative": data.get("negative") or "",
            "denoise": float(data.get("denoise") or 0.8),
            "use_reference": bool(data.get("use_reference")),
            "width": int(data.get("width") or 1040),
            "height": int(data.get("height") or 1560),
        }
        if item is None:
            poses.append(payload)
        else:
            item.update(payload)
        save_custom_poses(store)
        return web.json_response({"ok": True, "names": [p["name"] for p in poses]})



POSE_DIR = os.path.join(NODE_DIR, "standard_poses")
POSE_FILE = os.path.join(POSE_DIR, "poses.json")


def load_poses():
    os.makedirs(POSE_DIR, exist_ok=True)
    if not os.path.exists(POSE_FILE):
        return {"poses": []}
    data = read_json(POSE_FILE)
    return {"poses": data.get("poses") or []}


def save_poses(store):
    os.makedirs(POSE_DIR, exist_ok=True)
    with open(POSE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def pose_names():
    names = [p.get("name") for p in load_poses()["poses"] if p.get("name")]
    return names or ["(пусто)"]



CUSTOM_DIR = os.path.join(NODE_DIR, "custom_poses")
CUSTOM_FILE = os.path.join(CUSTOM_DIR, "poses.json")


def load_custom_poses():
    os.makedirs(CUSTOM_DIR, exist_ok=True)
    if not os.path.exists(CUSTOM_FILE):
        return {"poses": []}
    return {"poses": read_json(CUSTOM_FILE).get("poses") or []}


def save_custom_poses(store):
    os.makedirs(CUSTOM_DIR, exist_ok=True)
    with open(CUSTOM_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)



def reference_images():
    try:
        import folder_paths
        return folder_paths.get_filename_list("input")
    except Exception:
        return []


def load_reference(name):
    if not name or name == "none":
        return None
    import folder_paths
    from PIL import Image
    import numpy as np
    import torch
    path = folder_paths.get_annotated_filepath(name)
    image = Image.open(path).convert("RGB")
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def pad_batch(images):
    import torch
    import torch.nn.functional as F
    height = max(img.shape[1] for img in images)
    width = max(img.shape[2] for img in images)
    padded = []
    for img in images:
        b, h, w, c = img.shape
        canvas = torch.zeros((b, height, width, c), device=img.device, dtype=img.dtype)
        canvas[:, :h, :w] = img
        padded.append(canvas)
    return torch.cat(padded, dim=0)


def custom_pose_names():
    names = [p.get("name") for p in load_custom_poses()["poses"] if p.get("name")]
    return names or ["(пусто)"]


class SpriteStandardPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "latent": ("LATENT",),
                "shared_positive": ("CONDITIONING",),
                "shared_negative": ("CONDITIONING",),
                "pose": (pose_names(), {"default": pose_names()[0]}),
                "positive": ("STRING", {"multiline": True, "default": ""}),
                "negative": ("STRING", {"multiline": True, "default": ""}),
                "denoise": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),
                "noise_index": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "steps": ("INT", {"default": 10, "min": 1, "max": 40}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "frame": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE",) * 7 + ("IMAGE",)
    RETURN_NAMES = tuple(f"pose_{i:02}" for i in range(1, 8)) + ("all_poses",)
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, model, clip, vae, latent, shared_positive, shared_negative, pose, positive, negative, denoise, noise_index, steps, cfg, sampler_name, scheduler, frame):
        import torch
        import torch.nn.functional as F
        from nodes import common_ksampler

        store = load_poses()
        for item in store["poses"]:
            if item.get("name") == pose:
                item["positive"] = positive
                item["negative"] = negative
                item["denoise"] = denoise
                save_poses(store)
                break
        poses = load_poses()["poses"]

        def encode(text):
            tokens = clip.tokenize(text or "")
            return clip.encode_from_tokens_scheduled(tokens)

        def margin(image):
            while image.ndim > 4:
                image = image.squeeze(1)
            if image.ndim == 3:
                image = image.unsqueeze(0)
            b, h, w, c = image.shape
            nh, nw = max(1, int(h * 0.84)), max(1, int(w * 0.84))
            scaled = F.interpolate(image.permute(0, 3, 1, 2), size=(nh, nw), mode="bicubic", align_corners=False).permute(0, 2, 3, 1)
            canvas = torch.zeros((b, 1560, 1040, c), device=image.device, dtype=image.dtype)
            canvas[:, 110:110 + nh, 80:80 + nw] = scaled[:, :min(nh, 1450), :min(nw, 960)]
            return canvas

        blank = torch.zeros((1, 1560, 1040, 3))
        images = []
        for i, item in enumerate(poses):
            pos = shared_positive + encode((frame or "") + " " + (item.get("positive") or ""))
            neg = shared_negative + encode(item.get("negative") or "")
            sampled = common_ksampler(model, noise_index + i, steps, cfg, sampler_name, scheduler, pos, neg, latent, denoise=float(item.get("denoise") or 0.6))[0]
            images.append(margin(vae.decode(sampled["samples"])))
        singles = [(images[i] if i < len(images) else blank) for i in range(7)]
        batch = pad_batch(images) if images else blank
        return tuple(singles) + (batch,)


class SpriteCustomPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "latent": ("LATENT",),
                "shared_positive": ("CONDITIONING",),
                "shared_negative": ("CONDITIONING",),
                "pose": (custom_pose_names(), {"default": custom_pose_names()[0]}),
                "positive": ("STRING", {"multiline": True, "default": ""}),
                "negative": ("STRING", {"multiline": True, "default": ""}),
                "denoise": ("FLOAT", {"default": 0.86, "min": 0.0, "max": 1.0, "step": 0.01}),
                "use_reference": ("BOOLEAN", {"default": False}),
                "reference_image": (["none"] + reference_images(), {"default": "none"}),
                "width": ("INT", {"default": 1560, "min": 512, "max": 2048, "step": 8}),
                "height": ("INT", {"default": 1560, "min": 512, "max": 2048, "step": 8}),
                "noise_index": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "steps": ("INT", {"default": 10, "min": 1, "max": 40}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "frame": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {"pose_reference": ("IMAGE",)},
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("pose_01", "pose_02", "all_poses")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, model, clip, vae, latent, shared_positive, shared_negative, pose, positive, negative, denoise, use_reference, reference_image, width, height, noise_index, steps, cfg, sampler_name, scheduler, frame, pose_reference=None):
        import torch
        import torch.nn.functional as F
        from nodes import common_ksampler

        store = load_custom_poses()
        for item in store["poses"]:
            if item.get("name") == pose:
                item.update({"positive": positive, "negative": negative, "denoise": denoise, "use_reference": use_reference, "reference_image": reference_image, "width": width, "height": height})
                save_custom_poses(store)
                break
        poses = load_custom_poses()["poses"]

        def encode(text):
            tokens = clip.tokenize(text or "")
            return clip.encode_from_tokens_scheduled(tokens)

        def as_image(image):
            while image.ndim > 4:
                image = image.squeeze(1)
            if image.ndim == 3:
                image = image.unsqueeze(0)
            return image

        def fit(image, tw, th):
            image = as_image(image)
            b, h, w, c = image.shape
            scale = min(tw / w, th / h) * 0.72
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            scaled = F.interpolate(image.permute(0, 3, 1, 2), size=(nh, nw), mode="bicubic", align_corners=False).permute(0, 2, 3, 1)
            canvas = torch.zeros((b, th, tw, c), device=image.device, dtype=image.dtype)
            y = max(0, th - nh - 80)
            x = max(0, (tw - nw) // 2)
            canvas[:, y:y + nh, x:x + nw] = scaled[:, :nh, :nw]
            return canvas

        def plate(image, tw, th):
            image = as_image(image)
            b, h, w, c = image.shape
            nh, nw = max(1, int(h * 0.84)), max(1, int(w * 0.84))
            scaled = F.interpolate(image.permute(0, 3, 1, 2), size=(nh, nw), mode="bicubic", align_corners=False).permute(0, 2, 3, 1)
            canvas = torch.zeros((b, th, tw, c), device=image.device, dtype=image.dtype)
            canvas[:, 80:80 + nh, 80:80 + nw] = scaled[:, :min(nh, th - 80), :min(nw, tw - 80)]
            return canvas

        images = []
        for i, item in enumerate(poses):
            tw, th = int(item.get("width") or 1040), int(item.get("height") or 1560)
            pose_latent = latent
            ref = load_reference(item.get("reference_image"))
            if ref is None and pose_reference is not None and item.get("use_reference"):
                ref = pose_reference
            if ref is not None and item.get("use_reference") and item.get("reference_image") not in (None, "", "none"):
                pose_latent = vae.encode(fit(ref, tw, th))
            elif pose_reference is not None and item.get("use_reference") and ref is not None:
                pose_latent = vae.encode(fit(ref, tw, th))
            pos = shared_positive + encode((frame or "") + " " + (item.get("positive") or ""))
            neg = shared_negative + encode(item.get("negative") or "")
            sampled = common_ksampler(model, noise_index + i, steps, cfg, sampler_name, scheduler, pos, neg, pose_latent, denoise=float(item.get("denoise") or 0.8))[0]
            images.append(plate(vae.decode(sampled["samples"]), tw, th))
        blank = torch.zeros((1, 1560, 1040, 3))
        first = images[0] if images else blank
        second = images[1] if len(images) > 1 else blank
        batch = pad_batch(images) if images else blank
        return (first, second, batch)


NODE_CLASS_MAPPINGS = {
    "SpritePromptPreset": SpritePromptPreset,
    "SpritePresetSelect": SpritePresetSelect,
    "SpriteStandardPoses": SpriteStandardPoses,
    "SpriteCustomPoses": SpriteCustomPoses,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SpritePromptPreset": "пресеты расы и одежды v3",
    "SpritePresetSelect": "выбор расы и одежды",
    "SpriteStandardPoses": "Standard poses",
    "SpriteCustomPoses": "Custom poses",
}
