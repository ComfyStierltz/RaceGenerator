POSES = [
    "all",
    "01 front",
    "02 three-quarter left",
    "03 profile left",
    "04 three-quarter back left",
    "05 back",
    "06 profile right",
    "07 three-quarter right",
    "08 squat",
    "09 rear",
]


class SpritePosePick:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {f"pose_{i:02d}": ("IMAGE",) for i in range(1, 10)}
        return {"required": {"pose": (POSES, {"default": "all"}), "output_folder": ("STRING", {"default": "sprites"})}, "optional": optional}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "sprite"
    OUTPUT_NODE = True

    def run(self, pose, output_folder="sprites", **kwargs):
        import folder_paths
        import torch
        from pathlib import Path
        from PIL import Image
        wanted = list(range(1, 10)) if pose == "all" else [int(pose[:2])]
        names = {i: POSES[i] for i in range(1, 10)}
        out = Path(folder_paths.get_output_directory()) / (output_folder or "sprites")
        out.mkdir(parents=True, exist_ok=True)
        frames = []
        for i in wanted:
            image = kwargs.get(f"pose_{i:02d}")
            if image is None:
                continue
            arr = (image[0].clamp(0, 1).cpu().numpy() * 255).astype("uint8")
            safe = names[i].replace(" ", "_")
            Image.fromarray(arr).save(out / f"{safe}.png")
            frames.append(image[0])
        if not frames:
            return (torch.zeros((1, 64, 64, 4)),)
        height = max(frame.shape[0] for frame in frames)
        width = max(frame.shape[1] for frame in frames)
        channels = max(frame.shape[2] for frame in frames)
        batch = []
        for frame in frames:
            canvas = torch.zeros((height, width, channels), dtype=frame.dtype, device=frame.device)
            canvas[:frame.shape[0], :frame.shape[1], :frame.shape[2]] = frame
            batch.append(canvas)
        print(f"[RaceGenerator] saved {len(batch)} pose(s) to {out}")
        return (torch.stack(batch, dim=0),)

NODE_CLASS_MAPPINGS = {
    "SpritePosePick": SpritePosePick,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SpritePosePick": "Pose pick",
}
