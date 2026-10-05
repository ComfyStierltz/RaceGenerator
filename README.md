# RaceGenerator

Ноды пресетов для спрайт-графа ComfyUI.

- `SpritePromptPreset` — редактор. Раса пишется в `presets/<имя>.json`, одежда в `clothes/<имя>.json`.
- `SpritePresetSelect` — необязательный выбор. `apply` выключен: берутся поля редактора. `naked`: одежда не мержится.

Клонировать в `ComfyUI/custom_nodes/RaceGenerator` и перезапустить ComfyUI. В пакете должны быть `__init__.py`, `web/preset.js`, `presets/` и `clothes/`.

Граф: `workflows/comfy_sprite_base_v18.json`. Ноды `SpritePromptPreset` и `SpritePresetSelect` помечены пакетом RaceGenerator.
