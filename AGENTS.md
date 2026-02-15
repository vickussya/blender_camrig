# AGENTS.md

Best practices used so far in this repository:

- Keep the Blender add-on entry point at the zip root (`__init__.py`) for installability.
- Separate add-on logic into modules and keep `__init__.py` minimal.
- Provide a single `register()`/`unregister()` pair and avoid duplicates.
- Use clear, stable `bl_info` metadata (name, author, version, Blender version).
- Use Blender-safe module imports and avoid heavy logic at import time.
- Keep class registration centralized and unregister in reverse order.
- Keep keymap registration isolated and cleaned up on unregister.
- Use consistent naming for objects, collections, and operators.

