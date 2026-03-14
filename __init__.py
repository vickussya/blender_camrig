bl_info = {
    "name": "Cam Rig Generator (Cinematic Toolkit)",
    "author": "vickussya",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Cam Rig",
    "description": "Cinematic camera rig with tracking, dialogue, turntable, presets, and shot library tools.",
    "category": "Camera",
}

import importlib

import bpy

from . import camera_utils, dialogue, operators, panels, properties, shot_library


if "bpy" in locals():
    importlib.reload(camera_utils)
    importlib.reload(dialogue)
    importlib.reload(shot_library)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)


CLASSES = (
    *properties.CLASSES,
    *operators.CLASSES,
    *panels.CLASSES,
)

addon_keymaps = []


def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new("camrig.view_selected_camera", type="NUMPAD_0", value="PRESS")
        addon_keymaps.append((km, kmi))


def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    # Property groups must be registered before attaching to bpy.types.Scene.
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.camrig_settings = bpy.props.PointerProperty(type=properties.CAMRIG_Settings)
    register_keymap()


def unregister():
    unregister_keymap()
    del bpy.types.Scene.camrig_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
