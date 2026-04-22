import math

import bpy
from mathutils import Vector, Matrix


DEBUG_CAM_RIG = False

TOOL_PROP = "cam_rig_tool"
SHOT_PROP = "cam_rig_shot"
TARGET_PROP = "cam_rig_target"
SUBJECT_PROP = "cam_rig_subject"
ROOT_OBJ_PROP = "cam_rig_root_obj"
RIG_COLLECTION_PROP = "cam_rig_shot_collection"
IS_ROOT_PROP = "cam_rig_is_root"

COLLECTION_NAME = "CAM_RIG"
ROOT_NAME = "CAM_RIG_ROOT"
LOOKAT_NAME = "CAM_LOOKAT"
TARGET_OBJ_PROP = "cam_rig_target_obj"

SHOT_DEFS = (
    {"id": "ECU", "name": "CAM_ECU", "label": "Extreme Close-up", "target_factor": 0.92, "lens": 85.0},
    {"id": "CU", "name": "CAM_CU_HEAD", "label": "Closeup", "target_factor": 0.92, "lens": 70.0},
    {"id": "MED_WAIST", "name": "CAM_MED_WAIST", "label": "Medium", "target_factor": 0.55, "lens": 50.0},
    {"id": "MED_FULL", "name": "CAM_MED_FULL", "label": "Medium Full", "target_factor": 0.70, "lens": 40.0},
    {"id": "FULL", "name": "CAM_FULL_BODY", "label": "Full", "target_factor": "CENTER", "lens": 35.0},
    {"id": "WIDE", "name": "CAM_WIDE_EST", "label": "Wide", "target_factor": "CENTER", "lens": 24.0},
)

SHOT_ENUM_ITEMS = [
    ("ECU", "ECU", "Extreme close-up"),
    ("CU", "CU", "Closeup"),
    ("MED_WAIST", "Medium", "Medium (waist framing)"),
    ("MED_FULL", "Medium Full", "Knees / 3/4 framing"),
    ("FULL", "Full", "Full body"),
    ("WIDE", "Wide", "Wide / establishing"),
]

AXIS_ITEMS = [
    ("+X", "+X", "Place cameras along +X"),
    ("-X", "-X", "Place cameras along -X"),
    ("+Y", "+Y", "Place cameras along +Y"),
    ("-Y", "-Y", "Place cameras along -Y"),
    ("+Z", "+Z", "Place cameras along +Z"),
    ("-Z", "-Z", "Place cameras along -Z"),
]

TURNTABLE_TYPES = [
    ("ROTATE_CAMERA", "Rotate Camera Around Subject", "Spin camera around subject"),
]


def get_settings(context):
    return context.scene.camrig_settings


def _tag_object(obj):
    obj[TOOL_PROP] = True


def _find_tagged_object(obj_type, name=None, shot_id=None):
    for ob in bpy.data.objects:
        if not ob.get(TOOL_PROP):
            continue
        if ob.type != obj_type:
            continue
        if name and ob.name == name:
            return ob
        if shot_id and ob.get(SHOT_PROP) == shot_id:
            return ob
    return None


def get_selected_subjects(context):
    return [
        ob
        for ob in context.selected_objects
        if ob.type in {"MESH", "ARMATURE", "EMPTY"} and not ob.get(TOOL_PROP)
    ]


def _bounds_subjects(subjects):
    # Production scenes often select an ARMATURE/EMPTY "asset root" while geometry lives in children.
    # Use child geometry for bounds when available, otherwise fall back to the selected object itself.
    bounds_sources = []
    for ob in subjects or []:
        if ob is None:
            continue
        if ob.type == "MESH":
            bounds_sources.append(ob)
            continue

        child_meshes = []
        for child in getattr(ob, "children_recursive", []) or []:
            if child is None or child.get(TOOL_PROP):
                continue
            if child.type == "MESH":
                child_meshes.append(child)
        if child_meshes:
            bounds_sources.extend(child_meshes)
        else:
            bounds_sources.append(ob)
    return bounds_sources


def get_primary_subject(context):
    active = context.view_layer.objects.active
    if active in context.selected_objects and active is not None and not active.get(TOOL_PROP):
        return active
    subjects = get_selected_subjects(context)
    return subjects[0] if subjects else None


def get_dialogue_subjects(context):
    subjects = get_selected_subjects(context)
    if len(subjects) < 2:
        return None, None
    active = context.view_layer.objects.active
    if active in subjects and active is not None and not active.get(TOOL_PROP):
        a = active
        b = next((ob for ob in subjects if ob != a), None)
        return a, b
    return subjects[0], subjects[1]


def ensure_collection(scene, name=COLLECTION_NAME):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
    return col


def ensure_shot_collection(scene, base_name):
    rig_col = ensure_collection(scene)
    col_name = f"{base_name}_Rig"
    shot_col = bpy.data.collections.get(col_name)
    if shot_col is None:
        shot_col = bpy.data.collections.new(col_name)
    # bpy_prop_collection membership expects names (strings), not collection objects.
    if rig_col.children.get(shot_col.name) is None:
        rig_col.children.link(shot_col)
    return shot_col


def get_rig_collection_for_camera(scene, cam_obj):
    if cam_obj and cam_obj.get(RIG_COLLECTION_PROP):
        col = bpy.data.collections.get(cam_obj.get(RIG_COLLECTION_PROP))
        if col is not None:
            return col
    return ensure_collection(scene)


def ensure_shot_root(scene, rig_col, shot_id, base_name):
    root_name = f"{base_name}_Root"
    root = bpy.data.objects.get(root_name)
    if root is None or root.type != "EMPTY" or not root.get(TOOL_PROP) or not root.get(IS_ROOT_PROP):
        root = bpy.data.objects.new(root_name, None)
        root.empty_display_type = "PLAIN_AXES"
        _tag_object(root)
        root[IS_ROOT_PROP] = True
        scene.collection.objects.link(root)
    root[SHOT_PROP] = shot_id
    if root.name not in rig_col.objects:
        rig_col.objects.link(root)
    return root


def get_rig_root_for_camera(scene, cam_obj):
    if cam_obj and cam_obj.get(ROOT_OBJ_PROP):
        root = bpy.data.objects.get(cam_obj.get(ROOT_OBJ_PROP))
        if root is not None and root.type == "EMPTY":
            return root
    parent = cam_obj.parent if cam_obj else None
    while parent is not None:
        if parent.type == "EMPTY" and parent.get(IS_ROOT_PROP):
            return parent
        parent = parent.parent
    return None


def ensure_root(scene, rig_col):
    root = _find_tagged_object("EMPTY", name=ROOT_NAME)
    if root is None:
        root = bpy.data.objects.new(ROOT_NAME, None)
        root.empty_display_type = "PLAIN_AXES"
        _tag_object(root)
        scene.collection.objects.link(root)
    if root.name not in rig_col.objects:
        rig_col.objects.link(root)
    return root


def get_or_create_camera_target(scene, rig_col, root, settings, cam_obj):
    if settings.look_at_target:
        return settings.look_at_target, False
    name = f"{LOOKAT_NAME}_{cam_obj.name}"
    empty = _find_tagged_object("EMPTY", name=name)
    if empty is None:
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = "ARROWS"
        _tag_object(empty)
        scene.collection.objects.link(empty)
    if empty.name not in rig_col.objects:
        rig_col.objects.link(empty)
    parent_keep_world(empty, root)
    return empty, True


def parent_keep_world(obj, parent):
    mw = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted() @ mw
    obj.matrix_world = mw


def set_world_location(obj, location):
    if obj is None or location is None:
        return
    mw = obj.matrix_world.copy()
    mw.translation = location
    obj.matrix_world = mw


def ensure_track_to(cam_obj, target_obj, enabled):
    for con in [c for c in cam_obj.constraints if c.type in {"TRACK_TO", "DAMPED_TRACK"}]:
        cam_obj.constraints.remove(con)
    if not enabled:
        return
    con = cam_obj.constraints.new(type="TRACK_TO")
    con.target = target_obj
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"


def apply_tracking(root, subject, enabled):
    # Tracking is aim-only; do not move the rig root.
    if SUBJECT_PROP in root:
        del root[SUBJECT_PROP]
    if enabled and subject:
        root[SUBJECT_PROP] = subject.name


def axis_vector(axis):
    if axis == "+X":
        return Vector((1.0, 0.0, 0.0))
    if axis == "-X":
        return Vector((-1.0, 0.0, 0.0))
    if axis == "+Y":
        return Vector((0.0, 1.0, 0.0))
    if axis == "-Y":
        return Vector((0.0, -1.0, 0.0))
    if axis == "+Z":
        return Vector((0.0, 0.0, 1.0))
    return Vector((0.0, 0.0, -1.0))


def selection_world_bounds(objects, depsgraph):
    if not objects:
        return None

    corners_world = []
    for ob in objects:
        ob_eval = ob.evaluated_get(depsgraph)
        if not hasattr(ob_eval, "bound_box") or ob_eval.bound_box is None:
            continue
        mw = ob_eval.matrix_world
        for corner in ob_eval.bound_box:
            corners_world.append(mw @ Vector(corner))

    if not corners_world:
        return None

    min_v = Vector((
        min(v.x for v in corners_world),
        min(v.y for v in corners_world),
        min(v.z for v in corners_world),
    ))
    max_v = Vector((
        max(v.x for v in corners_world),
        max(v.y for v in corners_world),
        max(v.z for v in corners_world),
    ))

    center = (min_v + max_v) * 0.5
    size = (max_v - min_v)
    height = size.z
    max_dim = max(size.x, size.y, size.z)

    return {"min": min_v, "max": max_v, "center": center, "size": size, "height": height, "max_dim": max_dim}


def compute_subject_anchors(bounds):
    # Use world-space bounding box to derive stable framing anchors.
    min_v = bounds["min"]
    max_v = bounds["max"]
    center = bounds["center"]
    height = bounds["height"]

    neutral_z = min_v.z + height * 0.55
    eye_z = min_v.z + height * 0.85
    return {
        "center": center,
        "bottom": Vector((center.x, center.y, min_v.z)),
        "top": Vector((center.x, center.y, max_v.z)),
        "eye": Vector((center.x, center.y, eye_z)),
        "neutral": Vector((center.x, center.y, neutral_z)),
    }


def compute_target_height(bounds, shot_type, eye_level):
    min_z = bounds["min"].z
    height = bounds["height"]
    eye_z = min_z + height * 0.88
    base_z = {
        "ECU": min_z + height * 0.88,
        "CU": min_z + height * 0.84,
        "MED_WAIST": min_z + height * 0.76,
        "MED_FULL": min_z + height * 0.66,
        "FULL": min_z + height * 0.52,
        "WIDE": min_z + height * 0.50,
    }.get(shot_type, min_z + height * 0.68)

    if not eye_level:
        return base_z

    width = bounds["size"].x
    depth = bounds["size"].y
    upright = height > max(width, depth) * 1.2
    weights = {
        "ECU": 1.0,
        "CU": 0.9,
        "MED_WAIST": 0.7,
        "MED_FULL": 0.5,
        "FULL": 0.2,
        "WIDE": 0.1,
    }
    weight = weights.get(shot_type, 0.5)
    if upright:
        weight = min(weight + 0.1, 1.0)
    return base_z * (1.0 - weight) + eye_z * weight


def get_shot_def(shot_id):
    for shot in SHOT_DEFS:
        if shot["id"] == shot_id:
            return shot
    return None


def compute_eye_height(bounds):
    return bounds["min"].z + bounds["height"] * 0.85


def compute_camera_transform(context, subject, shot_type, axis, eye_level):
    if isinstance(subject, (list, tuple, set)):
        objects = list(subject)
    else:
        objects = [subject] if subject else []

    if not objects:
        return None, None, None

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds(objects, depsgraph)
    if bounds is None:
        return None, None, None

    settings = get_settings(context)
    anchors = compute_subject_anchors(bounds)
    target_height = compute_target_height(bounds, shot_type, eye_level)
    target = Vector((anchors["center"].x, anchors["center"].y, target_height))
    axis_dir = axis_vector(axis)
    target.z += settings.height_offset

    width = bounds["size"].x
    depth = bounds["size"].y
    height = bounds["height"]
    base = max(width, depth, height, 0.1)
    multipliers = {
        "ECU": 1.0,
        "CU": 1.5,
        "MED_WAIST": 2.5,
        "MED_FULL": 3.5,
        "FULL": 5.0,
        "WIDE": 7.5,
    }
    shot_offset = max(base * multipliers.get(shot_type, 2.5), base * 1.0)
    margin = max(base * 0.1, 0.05)
    half_extent = {
        "+X": width * 0.5,
        "-X": width * 0.5,
        "+Y": depth * 0.5,
        "-Y": depth * 0.5,
        "+Z": height * 0.5,
        "-Z": height * 0.5,
    }.get(axis, depth * 0.5)
    distance = half_extent + shot_offset + margin

    # Guardrail: ensure camera is beyond the bbox along the chosen axis.
    if axis == "+X":
        distance = max(distance, (bounds["max"].x - anchors["center"].x) + margin + shot_offset)
    elif axis == "-X":
        distance = max(distance, (anchors["center"].x - bounds["min"].x) + margin + shot_offset)
    elif axis == "+Y":
        distance = max(distance, (bounds["max"].y - anchors["center"].y) + margin + shot_offset)
    elif axis == "-Y":
        distance = max(distance, (anchors["center"].y - bounds["min"].y) + margin + shot_offset)
    elif axis == "+Z":
        distance = max(distance, (bounds["max"].z - anchors["center"].z) + margin + shot_offset)
    elif axis == "-Z":
        distance = max(distance, (anchors["center"].z - bounds["min"].z) + margin + shot_offset)
    camera_location = target + axis_dir * distance

    if axis in {"+Z", "-Z"}:
        camera_location.x = anchors["center"].x
        camera_location.y = anchors["center"].y

    # Final safety: push camera outside bbox if still too close on the axis.
    if axis == "+X" and camera_location.x <= bounds["max"].x + margin:
        camera_location.x = bounds["max"].x + margin
    elif axis == "-X" and camera_location.x >= bounds["min"].x - margin:
        camera_location.x = bounds["min"].x - margin
    elif axis == "+Y" and camera_location.y <= bounds["max"].y + margin:
        camera_location.y = bounds["max"].y + margin
    elif axis == "-Y" and camera_location.y >= bounds["min"].y - margin:
        camera_location.y = bounds["min"].y - margin
    elif axis == "+Z" and camera_location.z <= bounds["max"].z + margin:
        camera_location.z = bounds["max"].z + margin
    elif axis == "-Z" and camera_location.z >= bounds["min"].z - margin:
        camera_location.z = bounds["min"].z - margin

    lens_map = {
        "ECU": 85.0,
        "CU": 70.0,
        "MED_WAIST": 50.0,
        "MED_FULL": 40.0,
        "FULL": 35.0,
        "WIDE": 24.0,
    }

    if DEBUG_CAM_RIG:
        print("Shot type:", shot_type)
        print("BBox min:", bounds["min"], "max:", bounds["max"])
        print("BBox center:", bounds["center"])
        print("Target height:", target_height)
        print("Target location:", target)
        print("Axis vector:", axis_dir)
        print("Half extent:", half_extent)
        print("Shot offset:", shot_offset)
        print("Margin:", margin)
        print("Distance:", distance)
        print("Camera location:", camera_location)
        print("Lens:", lens_map.get(shot_type))

    return camera_location, target, lens_map.get(shot_type)


def create_or_get_camera(scene, rig_col, name, shot_id):
    cam_obj = _find_tagged_object("CAMERA", shot_id=shot_id)
    if cam_obj is None:
        cam_data = bpy.data.cameras.new(name=name)
        cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
        cam_obj[SHOT_PROP] = shot_id
        _tag_object(cam_obj)
        scene.collection.objects.link(cam_obj)
    if cam_obj.name not in rig_col.objects:
        rig_col.objects.link(cam_obj)
    return cam_obj


def place_shot_camera(cam_obj, lookat_obj, target, axis_dir, distance, tracking_enabled):
    # Set world-space placement defensively (camera may already be parented).
    cam_world = cam_obj.matrix_world.copy()
    cam_world.translation = target + axis_dir * distance
    cam_obj.matrix_world = cam_world
    if lookat_obj:
        ensure_track_to(cam_obj, lookat_obj, tracking_enabled)
        cam_obj[TARGET_OBJ_PROP] = lookat_obj.name
    cam_obj[TARGET_PROP] = (target.x, target.y, target.z)


def get_control_empty_name(camera_name):
    if camera_name.startswith("CAM_"):
        return camera_name.replace("CAM_", "CTRL_CAM_", 1)
    return f"CTRL_{camera_name}"


def ensure_camera_control_empty(camera_obj, rig_root, rig_col, enabled, name_override=None):
    if not enabled:
        return None

    name = name_override or get_control_empty_name(camera_obj.name)
    empty = _find_tagged_object("EMPTY", name=name)
    if empty is not None and empty.get("cam_rig_camera") != camera_obj.name:
        empty.name = f"{name}_OLD"
        empty = None
    if empty is None:
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = "CIRCLE"
        empty.empty_display_size = 1.5
        empty.hide_viewport = False
        empty.hide_render = True
        empty.hide_set(False)
        _tag_object(empty)
        rig_col.objects.link(empty)
    if empty.name not in rig_col.objects:
        rig_col.objects.link(empty)

    cam_world = camera_obj.matrix_world.copy()
    empty.matrix_world = cam_world
    empty["cam_rig_camera"] = camera_obj.name

    if rig_root:
        parent_keep_world(empty, rig_root)

    camera_obj.parent = empty
    camera_obj.matrix_parent_inverse = empty.matrix_world.inverted()
    camera_obj.matrix_world = cam_world

    if DEBUG_CAM_RIG:
        print("use_circle_parent:", enabled)
        print("control empty:", empty.name)
        print("control empty linked:", empty.name in rig_col.objects)
        print("camera parent:", camera_obj.parent.name if camera_obj.parent else None)
        print("camera world:", camera_obj.matrix_world.translation)
        print("ctrl cams:", [ob.name for ob in bpy.data.objects if ob.name.startswith("CTRL_CAM")])
    return empty


def apply_camera_parenting(scene, rig_col, parent_obj, camera_obj, settings):
    if parent_obj:
        parent_keep_world(camera_obj, parent_obj)


def get_active_camera(context):
    cam = context.scene.camera
    if cam and cam.type == "CAMERA":
        return cam
    obj = context.view_layer.objects.active
    if obj and obj.type == "CAMERA":
        return obj
    return None


def lock_camera_transforms(cam_obj, locked):
    cam_obj.lock_location = (locked, locked, locked)
    cam_obj.lock_rotation = (locked, locked, locked)
    cam_obj.lock_scale = (locked, locked, locked)


def ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target_location, settings):
    name = get_control_empty_name(cam_obj.name)
    empty = _find_tagged_object("EMPTY", name=name)
    if empty is None or empty.get("cam_rig_camera") != cam_obj.name:
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = "CIRCLE"
        empty.empty_display_size = 1.5
        empty.hide_viewport = False
        empty.hide_render = True
        empty.hide_set(False)
        _tag_object(empty)
        rig_col.objects.link(empty)
    if empty.name not in rig_col.objects:
        rig_col.objects.link(empty)

    empty["cam_rig_camera"] = cam_obj.name
    empty["cam_rig_orbit_target"] = (target_location.x, target_location.y, target_location.z)

    # Place empty at orbit center and camera on the circle circumference.
    set_world_location(empty, target_location)
    if rig_root:
        parent_keep_world(empty, rig_root)

    cam_world = cam_obj.matrix_world.copy()
    radius_vec = cam_world.translation - target_location
    if radius_vec.length == 0.0:
        radius_vec = Vector((1.0, 0.0, 0.0))
    radius = max(radius_vec.length, 0.1)
    empty.empty_display_size = max(radius, 1.5)
    cam_obj.parent = empty
    cam_obj.matrix_parent_inverse = empty.matrix_world.inverted()
    cam_obj.matrix_world = cam_world
    lock_camera_transforms(cam_obj, True)
    return empty


def apply_orbit_controls(scene, rig_col, rig_root, cam_obj, target_location, settings):
    if settings.use_camera_circle_parent:
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target_location, settings)
        return
    lock_camera_transforms(cam_obj, False)


def _orbit_control_empty_for_camera(cam_obj):
    return _find_tagged_object("EMPTY", name=get_control_empty_name(cam_obj.name))


def _orbit_target_location(context, empty):
    if empty and empty.get("cam_rig_orbit_target"):
        tgt = empty.get("cam_rig_orbit_target")
        return Vector((tgt[0], tgt[1], tgt[2]))
    settings = get_settings(context)
    if settings.look_at_target:
        return settings.look_at_target.matrix_world.translation.copy()
    cam_obj = get_active_camera(context)
    if cam_obj and cam_obj.get(TARGET_OBJ_PROP):
        target_obj = bpy.data.objects.get(cam_obj[TARGET_OBJ_PROP])
        if target_obj:
            return target_obj.matrix_world.translation.copy()
    return cam_obj.matrix_world.translation.copy() if cam_obj else Vector((0.0, 0.0, 0.0))


def _orbit_min_radius(context, target_location):
    subjects = get_selected_subjects(context)
    if not subjects:
        return 0.1
    bounds = selection_world_bounds(subjects, context.evaluated_depsgraph_get())
    if not bounds:
        return 0.1
    return max(bounds["max_dim"] * 0.6, 0.1)


def enforce_final_camera_outside_bounds(cam_obj, bounds, axis, shot_offset, margin):
    if cam_obj is None or bounds is None:
        return False, Vector((0.0, 0.0, 0.0))
    cam_matrix = cam_obj.matrix_world.copy()
    cam_world = cam_matrix.translation.copy()
    correction = Vector((0.0, 0.0, 0.0))
    if axis == "+X":
        min_pos = bounds["max"].x + margin + shot_offset
        if cam_world.x <= min_pos:
            correction.x = min_pos - cam_world.x
    elif axis == "-X":
        max_pos = bounds["min"].x - margin - shot_offset
        if cam_world.x >= max_pos:
            correction.x = max_pos - cam_world.x
    elif axis == "+Y":
        min_pos = bounds["max"].y + margin + shot_offset
        if cam_world.y <= min_pos:
            correction.y = min_pos - cam_world.y
    elif axis == "-Y":
        max_pos = bounds["min"].y - margin - shot_offset
        if cam_world.y >= max_pos:
            correction.y = max_pos - cam_world.y
    elif axis == "+Z":
        min_pos = bounds["max"].z + margin + shot_offset
        if cam_world.z <= min_pos:
            correction.z = min_pos - cam_world.z
    elif axis == "-Z":
        max_pos = bounds["min"].z - margin - shot_offset
        if cam_world.z >= max_pos:
            correction.z = max_pos - cam_world.z

    if correction.length > 0.0:
        cam_matrix.translation = cam_world + correction
        cam_obj.matrix_world = cam_matrix
        cam_world = cam_obj.matrix_world.translation.copy()
        return True, cam_world
    return False, cam_world


def move_orbit_left(context):
    settings = get_settings(context)
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    step = settings.orbit_step
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty is None:
        target = _orbit_target_location(context, None)
        scene = context.scene
        rig_col = get_rig_collection_for_camera(scene, cam_obj)
        rig_root = get_rig_root_for_camera(scene, cam_obj) or ensure_root(scene, rig_col)
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target, settings)
        empty = _orbit_control_empty_for_camera(cam_obj)
        if empty is None:
            return "Circle control not found."
    empty.rotation_euler.z += math.radians(step)
    return None


def move_orbit_right(context):
    settings = get_settings(context)
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    step = settings.orbit_step
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty is None:
        target = _orbit_target_location(context, None)
        scene = context.scene
        rig_col = get_rig_collection_for_camera(scene, cam_obj)
        rig_root = get_rig_root_for_camera(scene, cam_obj) or ensure_root(scene, rig_col)
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target, settings)
        empty = _orbit_control_empty_for_camera(cam_obj)
        if empty is None:
            return "Circle control not found."
    empty.rotation_euler.z -= math.radians(step)
    return None


def raise_camera_orbit(context):
    settings = get_settings(context)
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty is None:
        target = _orbit_target_location(context, None)
        scene = context.scene
        rig_col = get_rig_collection_for_camera(scene, cam_obj)
        rig_root = get_rig_root_for_camera(scene, cam_obj) or ensure_root(scene, rig_col)
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target, settings)
        empty = _orbit_control_empty_for_camera(cam_obj)
        if empty is None:
            return "Circle control not found."
    empty.location.z += settings.orbit_height_step
    return None


def lower_camera_orbit(context):
    settings = get_settings(context)
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty is None:
        target = _orbit_target_location(context, None)
        scene = context.scene
        rig_col = get_rig_collection_for_camera(scene, cam_obj)
        rig_root = get_rig_root_for_camera(scene, cam_obj) or ensure_root(scene, rig_col)
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target, settings)
        empty = _orbit_control_empty_for_camera(cam_obj)
        if empty is None:
            return "Circle control not found."
    empty.location.z -= settings.orbit_height_step
    return None


def move_orbit_closer(context):
    settings = get_settings(context)
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty is None:
        target = _orbit_target_location(context, None)
        scene = context.scene
        rig_col = get_rig_collection_for_camera(scene, cam_obj)
        rig_root = get_rig_root_for_camera(scene, cam_obj) or ensure_root(scene, rig_col)
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target, settings)
        empty = _orbit_control_empty_for_camera(cam_obj)
        if empty is None:
            return "Circle control not found."
    target = _orbit_target_location(context, empty)
    cam_world = cam_obj.matrix_world.copy()
    vec = cam_world.translation - target
    if vec.length == 0.0:
        vec = Vector((1.0, 0.0, 0.0))
    min_radius = _orbit_min_radius(context, target)
    new_radius = max(vec.length - settings.orbit_distance_step, min_radius)
    cam_world.translation = target + vec.normalized() * new_radius
    cam_obj.matrix_world = cam_world
    empty.empty_display_size = new_radius
    return None


def move_orbit_farther(context):
    settings = get_settings(context)
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty is None:
        target = _orbit_target_location(context, None)
        scene = context.scene
        rig_col = get_rig_collection_for_camera(scene, cam_obj)
        rig_root = get_rig_root_for_camera(scene, cam_obj) or ensure_root(scene, rig_col)
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target, settings)
        empty = _orbit_control_empty_for_camera(cam_obj)
        if empty is None:
            return "Circle control not found."
    target = _orbit_target_location(context, empty)
    cam_world = cam_obj.matrix_world.copy()
    vec = cam_world.translation - target
    if vec.length == 0.0:
        vec = Vector((1.0, 0.0, 0.0))
    new_radius = vec.length + settings.orbit_distance_step
    cam_world.translation = target + vec.normalized() * new_radius
    cam_obj.matrix_world = cam_world
    empty.empty_display_size = new_radius
    return None


def start_auto_orbit(context):
    settings = get_settings(context)
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    speed = settings.auto_orbit_speed
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty is None:
        target = _orbit_target_location(context, None)
        scene = context.scene
        rig_col = get_rig_collection_for_camera(scene, cam_obj)
        rig_root = get_rig_root_for_camera(scene, cam_obj) or ensure_root(scene, rig_col)
        ensure_circle_orbit_control(scene, rig_col, rig_root, cam_obj, target, settings)
        empty = _orbit_control_empty_for_camera(cam_obj)
        if empty is None:
            return "Circle control not found."
    fcurve = empty.driver_add("rotation_euler", 2)
    fcurve.driver.expression = f"frame*{speed}*0.0174533"
    return None


def stop_auto_orbit(context):
    cam_obj = get_active_camera(context)
    if cam_obj is None:
        return "No active camera."
    empty = _orbit_control_empty_for_camera(cam_obj)
    if empty and empty.animation_data:
        empty.driver_remove("rotation_euler", 2)
    return None


def create_shot_camera(context, shot_id, index=0):
    settings = get_settings(context)
    scene = context.scene
    subjects = get_selected_subjects(context)
    if not subjects:
        return None, "Select at least one object."
    if DEBUG_CAM_RIG:
        print("Subjects:", [ob.name for ob in subjects])
        active = context.view_layer.objects.active
        print("Active:", active.name if active else None)
        print("Shot type:", shot_id, "Axis:", settings.axis)
        print(
            "Settings:",
            {
                "eye_level": settings.eye_level,
                "tracking_enabled": settings.tracking_enabled,
                "use_camera_circle_parent": settings.use_camera_circle_parent,
                "look_at_target": settings.look_at_target.name if settings.look_at_target else None,
                "height_offset": settings.height_offset,
            },
        )

    shot_def = get_shot_def(shot_id)
    if shot_def is None:
        return None, "Unknown shot type."

    desired_name = shot_def["name"]

    rig_col = ensure_collection(scene)
    depsgraph = context.evaluated_depsgraph_get()
    bounds_subjects = _bounds_subjects(subjects)
    bounds = selection_world_bounds(bounds_subjects, depsgraph)
    if DEBUG_CAM_RIG:
        print("Bounds sources:", [ob.name for ob in bounds_subjects])
        if bounds:
            print(
                "Bounds:",
                {
                    "min": tuple(bounds["min"]),
                    "max": tuple(bounds["max"]),
                    "center": tuple(bounds["center"]),
                    "size": tuple(bounds["size"]),
                    "height": bounds["height"],
                    "max_dim": bounds["max_dim"],
                },
            )

    camera_location, target, lens = compute_camera_transform(
        context,
        bounds_subjects,
        shot_id,
        settings.axis,
        settings.eye_level,
    )
    if camera_location is None or target is None:
        return None, "Unable to compute camera placement."
    if DEBUG_CAM_RIG:
        print("Computed target:", tuple(target))
        print("Computed camera_location:", tuple(camera_location))

    cam_obj = create_or_get_camera(scene, rig_col, desired_name, shot_id)

    shot_col = None
    if cam_obj.get(RIG_COLLECTION_PROP):
        shot_col = bpy.data.collections.get(cam_obj.get(RIG_COLLECTION_PROP))
    if shot_col is None:
        shot_col = ensure_shot_collection(scene, cam_obj.name)
    if cam_obj.name not in shot_col.objects:
        shot_col.objects.link(cam_obj)

    root = get_rig_root_for_camera(scene, cam_obj)
    if root is None:
        root = ensure_shot_root(scene, shot_col, shot_id, cam_obj.name)
    cam_obj[ROOT_OBJ_PROP] = root.name
    cam_obj[RIG_COLLECTION_PROP] = shot_col.name
    if DEBUG_CAM_RIG:
        print("Rig root:", root.name, "world:", tuple(root.matrix_world.translation))

    if bounds:
        set_world_location(root, bounds["center"])
    apply_tracking(root, get_primary_subject(context), settings.tracking_enabled)
    if DEBUG_CAM_RIG:
        print("Root after placement:", root.name, "world:", tuple(root.matrix_world.translation))

    lookat_obj, auto_target = get_or_create_camera_target(scene, shot_col, root, settings, cam_obj)
    if DEBUG_CAM_RIG and lookat_obj is not None:
        print("LookAt:", lookat_obj.name, "auto_target:", auto_target, "world(before):", tuple(lookat_obj.matrix_world.translation))

    computed_target = target
    computed_camera_location = camera_location
    if not auto_target and lookat_obj is not None:
        # Respect user-provided look-at target: do not move it; instead use it as the placement target.
        target = lookat_obj.matrix_world.translation.copy()
    elif lookat_obj is not None:
        # Auto-created target is placed in world space at the computed target position.
        set_world_location(lookat_obj, target)
    if DEBUG_CAM_RIG:
        print("Placement target(world):", tuple(target), "auto_target:", auto_target)
    cam_obj.data.lens = lens if lens else shot_def["lens"]
    if DEBUG_CAM_RIG:
        print("use_circle_parent:", settings.use_camera_circle_parent)
    axis_dir = axis_vector(settings.axis)
    distance = (computed_camera_location - computed_target).length
    if DEBUG_CAM_RIG:
        print("Axis dir:", tuple(axis_dir), "distance:", distance)
    place_shot_camera(cam_obj, lookat_obj, target, axis_dir, distance, settings.tracking_enabled)
    if DEBUG_CAM_RIG:
        print("Camera world (before parenting):", tuple(cam_obj.matrix_world.translation), "parent:", cam_obj.parent.name if cam_obj.parent else None)
    apply_camera_parenting(scene, shot_col, root, cam_obj, settings)
    if DEBUG_CAM_RIG:
        print("Camera world (after parenting):", tuple(cam_obj.matrix_world.translation), "parent:", cam_obj.parent.name if cam_obj.parent else None)
    apply_orbit_controls(scene, shot_col, root, cam_obj, target, settings)
    if DEBUG_CAM_RIG:
        print("Camera world (after orbit):", tuple(cam_obj.matrix_world.translation), "parent:", cam_obj.parent.name if cam_obj.parent else None)
    if DEBUG_CAM_RIG:
        print("camera parent:", cam_obj.parent.name if cam_obj.parent else None)
        print("camera lens:", cam_obj.data.lens)
        print("ctrl cams:", [ob.name for ob in bpy.data.objects if ob.name.startswith("CTRL_CAM")])
    if bounds:
        cam_world = cam_obj.matrix_world.translation
        if DEBUG_CAM_RIG:
            print("Initial camera world:", cam_world)
        base = max(bounds["size"].x, bounds["size"].y, bounds["height"], 0.1)
        shot_offset = max(base * {"ECU": 1.0, "CU": 1.5, "MED_WAIST": 2.5, "MED_FULL": 3.5, "FULL": 5.0, "WIDE": 7.5, "OTS_A": 2.5, "OTS_B": 2.5, "SINGLE_A": 2.5, "SINGLE_B": 2.5, "TWO_SHOT": 4.0, "TURNTABLE": 4.0}.get(shot_id, 2.5), base * 1.0)
        margin = max(base * 0.1, 0.05)
        corrected, final_world = enforce_final_camera_outside_bounds(cam_obj, bounds, settings.axis, shot_offset, margin)
        if DEBUG_CAM_RIG:
            print("Final camera world:", final_world)
            print("Final correction applied:", corrected)
        inside = False
        if settings.axis == "+X":
            inside = final_world.x <= bounds["max"].x + margin
        elif settings.axis == "-X":
            inside = final_world.x >= bounds["min"].x - margin
        elif settings.axis == "+Y":
            inside = final_world.y <= bounds["max"].y + margin
        elif settings.axis == "-Y":
            inside = final_world.y >= bounds["min"].y - margin
        elif settings.axis == "+Z":
            inside = final_world.z <= bounds["max"].z + margin
        elif settings.axis == "-Z":
            inside = final_world.z >= bounds["min"].z - margin
        if DEBUG_CAM_RIG:
            print("INSIDE_BBOX_CHECK:", inside)

    return cam_obj, None


def switch_active_camera(context, shot_id):
    cam_obj = _find_tagged_object("CAMERA", shot_id=shot_id)
    if cam_obj is None:
        return False
    scene = context.scene
    scene.camera = cam_obj
    if cam_obj.get(TARGET_OBJ_PROP) and cam_obj.get(TARGET_PROP):
        target_obj = bpy.data.objects.get(cam_obj[TARGET_OBJ_PROP])
        if target_obj:
            target = cam_obj[TARGET_PROP]
            set_world_location(target_obj, Vector((target[0], target[1], target[2])))
    return True


def ensure_rig_for_selection(context):
    settings = get_settings(context)
    scene = context.scene
    subjects = get_selected_subjects(context)
    if not subjects:
        return None, "Select at least one object."

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds(_bounds_subjects(subjects), depsgraph)
    if bounds is None:
        return None, "Unable to compute bounds for selection."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)

    set_world_location(root, bounds["center"])
    subject = get_primary_subject(context)
    apply_tracking(root, subject, settings.tracking_enabled)

    return bounds, None


def create_shot_set(context):
    bounds, err = ensure_rig_for_selection(context)
    if err:
        return err

    settings = get_settings(context)
    subjects = get_selected_subjects(context)
    bounds_subjects = _bounds_subjects(subjects)
    scene = context.scene
    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    for index, shot in enumerate(SHOT_DEFS):
        camera_location, target, lens = compute_camera_transform(
            context,
            bounds_subjects,
            shot["id"],
            settings.axis,
            settings.eye_level,
        )
        if camera_location is None or target is None:
            continue
        cam_obj = create_or_get_camera(scene, rig_col, shot["name"], shot["id"])
        lookat_obj, auto_target = get_or_create_camera_target(scene, rig_col, root, settings, cam_obj)
        computed_target = target
        computed_camera_location = camera_location
        if not auto_target and lookat_obj is not None:
            target = lookat_obj.matrix_world.translation.copy()
        elif lookat_obj is not None:
            set_world_location(lookat_obj, target)
        cam_obj.data.lens = lens if lens else shot["lens"]
        if DEBUG_CAM_RIG:
            print("use_circle_parent:", settings.use_camera_circle_parent)
        axis_dir = axis_vector(settings.axis)
        distance = (computed_camera_location - computed_target).length
        place_shot_camera(cam_obj, lookat_obj, target, axis_dir, distance, settings.tracking_enabled)
        apply_camera_parenting(scene, rig_col, root, cam_obj, settings)
        apply_orbit_controls(scene, rig_col, root, cam_obj, target, settings)
        if DEBUG_CAM_RIG:
            print("camera parent:", cam_obj.parent.name if cam_obj.parent else None)
            print("camera lens:", cam_obj.data.lens)
            print("ctrl cams:", [ob.name for ob in bpy.data.objects if ob.name.startswith("CTRL_CAM")])

    scene.camera = _find_tagged_object("CAMERA", shot_id="MED_FULL") or scene.camera
    return None


def create_turntable(context):
    settings = get_settings(context)
    scene = context.scene
    subjects = get_selected_subjects(context)
    if not subjects:
        return "Select a subject to turntable."

    depsgraph = context.evaluated_depsgraph_get()
    bounds_subjects = _bounds_subjects(subjects)
    bounds = selection_world_bounds(bounds_subjects, depsgraph)
    if bounds is None:
        return "Unable to compute bounds for turntable."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    set_world_location(root, bounds["center"])
    apply_tracking(root, get_primary_subject(context), settings.tracking_enabled)

    start = scene.frame_start
    end = start + max(settings.turntable_frames, 1)

    pivot = _find_tagged_object("EMPTY", name="CAM_TURNTABLE_PIVOT")
    if pivot is None:
        pivot = bpy.data.objects.new("CAM_TURNTABLE_PIVOT", None)
        pivot.empty_display_type = "PLAIN_AXES"
        _tag_object(pivot)
        scene.collection.objects.link(pivot)
    if pivot.name not in rig_col.objects:
        rig_col.objects.link(pivot)
    set_world_location(pivot, bounds["center"])
    parent_keep_world(pivot, root)

    cam_obj = _find_tagged_object("CAMERA", shot_id="TURNTABLE")
    if cam_obj is None:
        cam_data = bpy.data.cameras.new(name="CAM_TURNTABLE")
        cam_obj = bpy.data.objects.new(name="CAM_TURNTABLE", object_data=cam_data)
        cam_obj[SHOT_PROP] = "TURNTABLE"
        _tag_object(cam_obj)
        scene.collection.objects.link(cam_obj)
    if cam_obj.name not in rig_col.objects:
        rig_col.objects.link(cam_obj)

    camera_location, target, lens = compute_camera_transform(
        context,
        bounds_subjects,
        "TURNTABLE",
        settings.axis,
        settings.eye_level,
    )
    if camera_location is None or target is None:
        return "Unable to compute camera placement."

    lookat_obj, auto_target = get_or_create_camera_target(scene, rig_col, root, settings, cam_obj)
    computed_target = target
    computed_camera_location = camera_location
    if not auto_target and lookat_obj is not None:
        target = lookat_obj.matrix_world.translation.copy()
    elif lookat_obj is not None:
        set_world_location(lookat_obj, target)

    axis_dir = axis_vector(settings.axis)
    distance = (computed_camera_location - computed_target).length
    set_world_location(cam_obj, target + axis_dir * distance)
    if lens:
        cam_obj.data.lens = lens
    apply_camera_parenting(scene, rig_col, pivot, cam_obj, settings)
    lock_camera_transforms(cam_obj, True)
    ensure_track_to(cam_obj, lookat_obj, settings.tracking_enabled)

    base = max(bounds["size"].x, bounds["size"].y, bounds["height"], 0.1)
    shot_offset = max(base * 4.0, base * 1.0)
    margin = max(base * 0.1, 0.05)
    corrected, final_world = enforce_final_camera_outside_bounds(cam_obj, bounds, settings.axis, shot_offset, margin)
    if DEBUG_CAM_RIG:
        print("Turntable initial camera:", camera_location)
        print("Turntable final camera:", final_world)
        print("Turntable correction applied:", corrected)

    pivot.rotation_euler = Vector((0.0, 0.0, 0.0))
    pivot.keyframe_insert(data_path="rotation_euler", frame=start)
    pivot.rotation_euler = Vector((0.0, 0.0, 6.283185))
    pivot.keyframe_insert(data_path="rotation_euler", frame=end)
    return None


def analyze_scene_for_shots(context):
    settings = get_settings(context)
    subjects = get_selected_subjects(context)
    depsgraph = context.evaluated_depsgraph_get()

    suggestions = []
    if not subjects:
        return suggestions

    bounds = selection_world_bounds(subjects, depsgraph)
    if bounds is None:
        return suggestions

    max_dim = bounds["max_dim"]
    height = bounds["height"]
    if max_dim < 0.5:
        suggestions.append({"id": "ECU", "label": "ECU", "reason": "Small subject suggests extreme close-up."})
    suggestions.append({"id": "CU", "label": "CU", "reason": "Close-up for detail framing."})
    suggestions.append({"id": "MED_WAIST", "label": "Medium", "reason": "Standard cinematic framing."})
    if height >= 1.0:
        suggestions.append({"id": "FULL", "label": "Full", "reason": "Show full subject silhouette."})
    suggestions.append({"id": "WIDE", "label": "Wide", "reason": "Establishing shot with space."})

    # Ensure at least three suggestions.
    if len(suggestions) < 3:
        suggestions.extend(
            [
                {"id": "CU", "label": "CU", "reason": "Default close-up suggestion."},
                {"id": "MED_WAIST", "label": "Medium", "reason": "Default medium framing."},
                {"id": "WIDE", "label": "Wide", "reason": "Default wide framing."},
            ]
        )
        suggestions = suggestions[:3]

    return suggestions
