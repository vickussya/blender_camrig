import bpy

from .camera_utils import SHOT_PROP, get_settings


def save_shot(context):
    settings = get_settings(context)
    cam_obj = context.scene.camera
    if cam_obj is None:
        return "No active camera to save."
    item = settings.shot_library.add()
    item.name = cam_obj.name
    item.shot_id = cam_obj.get(SHOT_PROP, "MED_FULL")
    item.camera_name = cam_obj.name
    item.location = cam_obj.location
    item.rotation = cam_obj.rotation_euler
    item.lens = cam_obj.data.lens
    item.target_name = getattr(settings.look_at_target, "name", "")
    item.axis = settings.axis
    item.eye_level = settings.eye_level
    item.rule_of_thirds = settings.rule_of_thirds
    item.thirds_h = settings.thirds_h
    item.thirds_v = settings.thirds_v
    settings.shot_library_index = len(settings.shot_library) - 1
    return None


def load_shot(context):
    settings = get_settings(context)
    if not settings.shot_library:
        return "Shot library is empty."
    item = settings.shot_library[settings.shot_library_index]
    cam_obj = bpy.data.objects.get(item.camera_name)
    if cam_obj is None or cam_obj.type != "CAMERA":
        return "Camera for this shot not found."
    cam_obj.location = item.location
    cam_obj.rotation_euler = item.rotation
    cam_obj.data.lens = item.lens
    settings.axis = item.axis or settings.axis
    settings.eye_level = item.eye_level
    settings.rule_of_thirds = item.rule_of_thirds
    settings.thirds_h = item.thirds_h or settings.thirds_h
    settings.thirds_v = item.thirds_v or settings.thirds_v
    context.scene.camera = cam_obj
    return None


def delete_shot(context):
    settings = get_settings(context)
    if not settings.shot_library:
        return "Shot library is empty."
    idx = settings.shot_library_index
    settings.shot_library.remove(idx)
    settings.shot_library_index = max(0, idx - 1)
    return None
