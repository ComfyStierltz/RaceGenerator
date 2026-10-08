from .race_clothes.nodes import NODE_CLASS_MAPPINGS as RACE_NODES
from .race_clothes.nodes import NODE_DISPLAY_NAME_MAPPINGS as RACE_NAMES
from .pose_pick.nodes import NODE_CLASS_MAPPINGS as POSE_NODES
from .pose_pick.nodes import NODE_DISPLAY_NAME_MAPPINGS as POSE_NAMES
from .standard_poses.nodes import NODE_CLASS_MAPPINGS as STANDARD_NODES
from .standard_poses.nodes import NODE_DISPLAY_NAME_MAPPINGS as STANDARD_NAMES
from .custom_poses.nodes import NODE_CLASS_MAPPINGS as CUSTOM_NODES
from .cycle.nodes import NODE_CLASS_MAPPINGS as CYCLE_NODES
from .custom_poses.nodes import NODE_DISPLAY_NAME_MAPPINGS as CUSTOM_NAMES
from .cycle.nodes import NODE_DISPLAY_NAME_MAPPINGS as CYCLE_NAMES

NODE_CLASS_MAPPINGS = {**RACE_NODES, **POSE_NODES, **STANDARD_NODES, **CUSTOM_NODES, **CYCLE_NODES}
NODE_DISPLAY_NAME_MAPPINGS = {**RACE_NAMES, **POSE_NAMES, **STANDARD_NAMES, **CUSTOM_NAMES, **CYCLE_NAMES}
print("[RaceGenerator] 0.9.19 race and pose refs")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
