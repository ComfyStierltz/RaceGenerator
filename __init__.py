from .race_clothes.nodes import NODE_CLASS_MAPPINGS as RACE_NODES
from .race_clothes.nodes import NODE_DISPLAY_NAME_MAPPINGS as RACE_NAMES
from .pose_pick.nodes import NODE_CLASS_MAPPINGS as POSE_NODES
from .pose_pick.nodes import NODE_DISPLAY_NAME_MAPPINGS as POSE_NAMES

NODE_CLASS_MAPPINGS = {**RACE_NODES, **POSE_NODES}
NODE_DISPLAY_NAME_MAPPINGS = {**RACE_NAMES, **POSE_NAMES}
WEB_DIRECTORY = "./web"
print("[RaceGenerator] 0.6.4 nodes split by folder")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
