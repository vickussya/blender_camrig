bl_info = {
    "name": "Cam Rig Generator (Close/Med/Wide + LookAt)",
    "author": "vickussya",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Cam Rig",
    "description": "Creates 3 cameras (close/med/wide) that frame selection and track a LookAt empty.",
    "category": "Camera",
}

from . import cam_rig

register = cam_rig.register
unregister = cam_rig.unregister
