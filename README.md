# RaceGenerator

Только пресеты расы и одежды. Код ноды — `nodes.py`, рядом с папками JSON.

- `races/<имя>.json` — раса.
- `clothes/<имя>.json` — одежда.
- `SpritePromptPreset` пишет в эти папки.
- `SpritePresetSelect` выбирает. `apply` выключен: берутся поля редактора. `naked`: одежда не мержится.

Клонировать в `ComfyUI/custom_nodes/RaceGenerator` и перезапустить ComfyUI.
