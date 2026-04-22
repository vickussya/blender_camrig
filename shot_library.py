import bpy
from mathutils import Euler, Matrix, Vector

from .camera_utils import (
    IS_ROOT_PROP,
    RIG_COLLECTION_PROP,
    ROOT_OBJ_PROP,
    SHOT_PROP,
    TARGET_OBJ_PROP,
    TARGET_PROP,
    TOOL_PROP,
    ensure_collection,
    ensure_shot_collection,
    ensure_shot_root,
    ensure_root,
    ensure_circle_orbit_control,
    ensure_track_to,
    get_or_create_camera_target,
    get_control_empty_name,
    get_rig_collection_for_camera,
    get_rig_root_for_camera,
    get_settings,
    parent_keep_world,
)


def _get_action(datablock):
    if datablock is None:
        return None
    anim = getattr(datablock, "animation_data", None)
    if anim and anim.action:
        return anim.action
    return None


def _copy_action(action, name_prefix):
    if action is None:
        return ""
    new_action = action.copy()
    new_action.name = f"{name_prefix}_{action.name}"
    return new_action.name


def _assign_action(datablock, action_name):
    if not datablock or not action_name:
        return
    action = bpy.data.actions.get(action_name)
    if action is None:
        return
    datablock.animation_data_create()
    datablock.animation_data.action = action


def _find_addon_parent_empty(obj):
    parent = obj.parent if obj else None
    while parent is not None:
        if parent.type == "EMPTY" and parent.get(TOOL_PROP):
            return parent
        parent = parent.parent
    return None


def _best_rig_root_for_camera(cam_obj):
    if cam_obj is None:
        return None

    root = get_rig_root_for_camera(None, cam_obj)
    if root is not None:
        return root

    parent = cam_obj.parent
    last_tool_empty = None
    while parent is not None:
        if parent.type == "EMPTY" and parent.get(TOOL_PROP):
            last_tool_empty = parent
        parent = parent.parent
    return last_tool_empty


def _apply_saved_shot_to_camera(context, cam_obj, item):
    settings = get_settings(context)
    settings.axis = item.axis or settings.axis
    settings.eye_level = item.eye_level
    settings.tracking_enabled = item.tracking_enabled
    if hasattr(item, "use_camera_circle_parent"):
        settings.use_camera_circle_parent = item.use_camera_circle_parent

    cam_obj[SHOT_PROP] = item.shot_id
    cam_obj[TOOL_PROP] = True

    rot = Euler((item.rotation[0], item.rotation[1], item.rotation[2]), "XYZ")
    cam_obj.matrix_world = Matrix.Translation(Vector(item.location)) @ rot.to_matrix().to_4x4()
    cam_obj.data.lens = item.lens

    scene = context.scene
    rig_col = ensure_collection(scene)

    # Prefer stored per-shot container when available; fall back to name-based creation.
    shot_col = None
    if cam_obj.get(RIG_COLLECTION_PROP):
        shot_col = bpy.data.collections.get(cam_obj.get(RIG_COLLECTION_PROP))
    if shot_col is None and getattr(item, "rig_collection_name", ""):
        shot_col = bpy.data.collections.get(item.rig_collection_name)
    if shot_col is None:
        shot_col = ensure_shot_collection(scene, cam_obj.name)
    if cam_obj.name not in shot_col.objects:
        shot_col.objects.link(cam_obj)
    cam_obj[RIG_COLLECTION_PROP] = shot_col.name

    root = None
    if getattr(item, "root_name", ""):
        candidate = bpy.data.objects.get(item.root_name)
        if candidate and candidate.type == "EMPTY" and candidate.get(TOOL_PROP):
            root = candidate
    if root is None:
        root = get_rig_root_for_camera(scene, cam_obj)
    if root is None and getattr(item, "root_location", None):
        root = ensure_shot_root(scene, shot_col, item.shot_id, cam_obj.name)
    if root is None:
        root = ensure_root(scene, rig_col)

    if root and root.get(TOOL_PROP):
        cam_obj[ROOT_OBJ_PROP] = root.name
        if root.name not in shot_col.objects:
            shot_col.objects.link(root)

    # Restore saved root transform (if present).
    if root and getattr(item, "root_location", None) and len(item.root_location) == 3:
        root.location = Vector(item.root_location)
    if root and getattr(item, "root_rotation", None) and len(item.root_rotation) == 3:
        root.rotation_euler = Euler(item.root_rotation, "XYZ")
    if root and getattr(item, "root_scale", None) and len(item.root_scale) == 3:
        root.scale = Vector(item.root_scale)

    target_obj = None
    if getattr(item, "lookat_name", ""):
        candidate = bpy.data.objects.get(item.lookat_name)
        if candidate is not None:
            target_obj = candidate
    if target_obj is None and item.target_name:
        target_obj = bpy.data.objects.get(item.target_name)
    if target_obj is None:
        target_obj, _ = get_or_create_camera_target(scene, shot_col, root, settings, cam_obj)
    if item.target_location and len(item.target_location) == 3:
        target_obj.location = Vector(item.target_location)
    if target_obj and getattr(item, "lookat_location", None) and len(item.lookat_location) == 3:
        target_obj.location = Vector(item.lookat_location)
    if target_obj and getattr(item, "lookat_rotation", None) and len(item.lookat_rotation) == 3:
        target_obj.rotation_euler = Euler(item.lookat_rotation, "XYZ")
    if target_obj and getattr(item, "lookat_scale", None) and len(item.lookat_scale) == 3:
        target_obj.scale = Vector(item.lookat_scale)
    cam_obj[TARGET_OBJ_PROP] = target_obj.name
    cam_obj[TARGET_PROP] = (target_obj.location.x, target_obj.location.y, target_obj.location.z)
    ensure_track_to(cam_obj, target_obj, settings.tracking_enabled)

    # Restore orbit/control parenting if used.
    control_obj = None
    if getattr(item, "use_camera_circle_parent", False) or getattr(item, "control_action", ""):
        control_obj = ensure_circle_orbit_control(scene, shot_col, root, cam_obj, target_obj.location, settings)
        if control_obj:
            item.control_name = control_obj.name
            if getattr(item, "control_location", None) and len(item.control_location) == 3:
                control_obj.location = Vector(item.control_location)
            if getattr(item, "control_rotation", None) and len(item.control_rotation) == 3:
                control_obj.rotation_euler = Euler(item.control_rotation, "XYZ")
            if getattr(item, "control_scale", None) and len(item.control_scale) == 3:
                control_obj.scale = Vector(item.control_scale)
            if getattr(item, "control_driver_expression", ""):
                if control_obj.animation_data:
                    control_obj.driver_remove("rotation_euler", 2)
                fcurve = control_obj.driver_add("rotation_euler", 2)
                fcurve.driver.expression = item.control_driver_expression
    else:
        # Ensure camera is parented to the shot root (keep world transform).
        if root and cam_obj.parent != root:
            parent_keep_world(cam_obj, root)

    if cam_obj.name not in shot_col.objects:
        shot_col.objects.link(cam_obj)
    context.scene.camera = cam_obj

    # Assign saved animation actions (if present).
    _assign_action(cam_obj, getattr(item, "camera_action", ""))
    _assign_action(cam_obj.data, getattr(item, "camera_data_action", ""))
    if root and root.get(TOOL_PROP):
        _assign_action(root, getattr(item, "root_action", ""))
    # Only reassign look-at animation if it is an add-on-owned object.
    if target_obj and target_obj.get(TOOL_PROP):
        _assign_action(target_obj, getattr(item, "lookat_action", ""))
    if control_obj and control_obj.get(TOOL_PROP):
        _assign_action(control_obj, getattr(item, "control_action", ""))


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
    if hasattr(item, "use_camera_circle_parent"):
        item.use_camera_circle_parent = settings.use_camera_circle_parent

    scene = context.scene
    rig_col = get_rig_collection_for_camera(scene, cam_obj)
    if hasattr(item, "rig_collection_name"):
        item.rig_collection_name = rig_col.name if rig_col else ""

    # Store rig object references and transforms (best-effort, backward-safe).
    root = _best_rig_root_for_camera(cam_obj)
    if root:
        item.root_name = root.name
        item.root_location = root.location
        item.root_rotation = root.rotation_euler
        item.root_scale = root.scale

    target_obj = bpy.data.objects.get(item.target_name) if item.target_name else None
    if target_obj:
        item.lookat_name = target_obj.name
        item.lookat_location = target_obj.location
        item.lookat_rotation = target_obj.rotation_euler
        item.lookat_scale = target_obj.scale

    control_obj = None
    if cam_obj.parent and cam_obj.parent.type == "EMPTY" and cam_obj.parent.get("cam_rig_camera") == cam_obj.name:
        control_obj = cam_obj.parent
    else:
        ctrl_name = get_control_empty_name(cam_obj.name)
        candidate = bpy.data.objects.get(ctrl_name)
        if candidate and candidate.type == "EMPTY" and candidate.get("cam_rig_camera") == cam_obj.name:
            control_obj = candidate
    if control_obj:
        item.control_name = control_obj.name
        item.control_location = control_obj.location
        item.control_rotation = control_obj.rotation_euler
        item.control_scale = control_obj.scale
        if hasattr(item, "control_driver_expression"):
            expr = ""
            if control_obj.animation_data:
                for drv in control_obj.animation_data.drivers:
                    if drv.data_path == "rotation_euler" and drv.array_index == 2:
                        expr = drv.driver.expression
                        break
            item.control_driver_expression = expr

    # Copy and store animation actions for reliable restore.
    prefix = f"CamRigShot_{cam_obj.name}"
    item.camera_action = _copy_action(_get_action(cam_obj), f"{prefix}_CAM")
    item.camera_data_action = _copy_action(_get_action(cam_obj.data), f"{prefix}_CAMDATA")
    if root and root.get(TOOL_PROP):
        item.root_action = _copy_action(_get_action(root), f"{prefix}_ROOT")
    if target_obj and target_obj.get(TOOL_PROP):
        item.lookat_action = _copy_action(_get_action(target_obj), f"{prefix}_LOOKAT")
    if control_obj and control_obj.get(TOOL_PROP):
        item.control_action = _copy_action(_get_action(control_obj), f"{prefix}_CTRL")

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
        item.camera_name = cam_obj.name
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
