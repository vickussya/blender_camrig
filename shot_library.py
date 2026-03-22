import bpy
from mathutils import Euler, Matrix, Vector

from .camera_utils import (
    SHOT_PROP,
    TARGET_OBJ_PROP,
    TARGET_PROP,
    TOOL_PROP,
    ensure_collection,
    ensure_root,
    ensure_track_to,
    get_or_create_camera_target,
    get_settings,
)


def _apply_saved_shot_to_camera(context, cam_obj, item):
    settings = get_settings(context)
    settings.axis = item.axis or settings.axis
    settings.eye_level = item.eye_level
    settings.tracking_enabled = item.tracking_enabled

    cam_obj[SHOT_PROP] = item.shot_id
    cam_obj[TOOL_PROP] = True

    rot = Euler((item.rotation[0], item.rotation[1], item.rotation[2]), "XYZ")
    cam_obj.matrix_world = Matrix.Translation(Vector(item.location)) @ rot.to_matrix().to_4x4()
    cam_obj.data.lens = item.lens

    rig_col = ensure_collection(context.scene)
    root = ensure_root(context.scene, rig_col)

    target_obj = None
    if item.target_name:
        target_obj = bpy.data.objects.get(item.target_name)
    if target_obj is None:
        target_obj, _ = get_or_create_camera_target(context.scene, rig_col, root, settings, cam_obj)
    if item.target_location and len(item.target_location) == 3:
        target_obj.location = Vector(item.target_location)
    cam_obj[TARGET_OBJ_PROP] = target_obj.name
    cam_obj[TARGET_PROP] = (target_obj.location.x, target_obj.location.y, target_obj.location.z)
    ensure_track_to(cam_obj, target_obj, settings.tracking_enabled)

    if cam_obj.name not in rig_col.objects:
        rig_col.objects.link(cam_obj)
    context.scene.camera = cam_obj


def save_shot(context):
    settings = get_settings(context)
    cam_obj = context.scene.camera
    if cam_obj is None:
        return "No active camera to save."
    if cam_obj.get(SHOT_PROP) == "TURNTABLE":
        return "Turntable shots cannot be saved in Shot Library."
    item = settings.shot_library.add()
    item.name = cam_obj.name
    item.shot_id = cam_obj.get(SHOT_PROP, "MED_FULL")
    item.camera_name = cam_obj.name
    item.location = cam_obj.matrix_world.translation
    item.rotation = cam_obj.matrix_world.to_euler()
    item.lens = cam_obj.data.lens
    item.target_name = cam_obj.get(TARGET_OBJ_PROP, "")
    if cam_obj.get(TARGET_PROP):
        target = cam_obj[TARGET_PROP]
        item.target_location = (target[0], target[1], target[2])
    elif item.target_name and bpy.data.objects.get(item.target_name):
        target_obj = bpy.data.objects.get(item.target_name)
        item.target_location = target_obj.location
    item.axis = settings.axis
    item.eye_level = settings.eye_level
    item.tracking_enabled = settings.tracking_enabled
    settings.shot_library_index = len(settings.shot_library) - 1
    return None


def load_shot(context):
    settings = get_settings(context)
    if not settings.shot_library:
        return "Shot library is empty."
    item = settings.shot_library[settings.shot_library_index]
    cam_obj = bpy.data.objects.get(item.camera_name)
    if cam_obj is None or cam_obj.type != "CAMERA":
        base_name = item.name or "CAM_SHOT_RESTORED"
        name = base_name if base_name not in bpy.data.objects else f"{base_name}_RESTORED"
        cam_data = bpy.data.cameras.new(name=name)
        cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
        context.scene.collection.objects.link(cam_obj)
    _apply_saved_shot_to_camera(context, cam_obj, item)
    return None


def delete_shot(context):
    settings = get_settings(context)
    if not settings.shot_library:
        return "Shot library is empty."
    idx = settings.shot_library_index
    settings.shot_library.remove(idx)
    settings.shot_library_index = max(0, idx - 1)
    return None
