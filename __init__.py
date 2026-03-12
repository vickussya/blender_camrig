bl_info = {
    "name": "Cam Rig Generator (Cinematic Toolkit)",
    "author": "vickussya",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Cam Rig",
    "description": "Cinematic camera rig with tracking, dialogue, turntable, presets, and shot library tools.",
    "category": "Camera",
}

from . import cam_rig

register = cam_rig.register
unregister = cam_rig.unregister
