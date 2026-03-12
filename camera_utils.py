import bpy
from mathutils import Vector


TOOL_PROP = "cam_rig_tool"
SHOT_PROP = "cam_rig_shot"
TARGET_PROP = "cam_rig_target"
SUBJECT_PROP = "cam_rig_subject"

COLLECTION_NAME = "CAM_RIG"
ROOT_NAME = "CAM_RIG_ROOT"
LOOKAT_NAME = "CAM_LOOKAT"

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
    ("OTS_A", "OTS A", "Over-the-shoulder A"),
    ("OTS_B", "OTS B", "Over-the-shoulder B"),
    ("SINGLE_A", "Single A", "Single A"),
    ("SINGLE_B", "Single B", "Single B"),
    ("TWO_SHOT", "Two Shot", "Two shot"),
    ("TURNTABLE", "Turntable", "Turntable camera"),
]

AXIS_ITEMS = [
    ("+X", "+X", "Place cameras along +X"),
    ("-X", "-X", "Place cameras along -X"),
    ("+Y", "+Y", "Place cameras along +Y"),
    ("-Y", "-Y", "Place cameras along -Y"),
    ("+Z", "+Z", "Place cameras along +Z"),
    ("-Z", "-Z", "Place cameras along -Z"),
]

THIRDS_H_ITEMS = [
    ("LEFT", "Left Third", "Place subject near left third"),
    ("CENTER", "Center", "Keep subject centered"),
    ("RIGHT", "Right Third", "Place subject near right third"),
]

THIRDS_V_ITEMS = [
    ("UPPER", "Upper Third", "Place subject near upper third"),
    ("MID", "Midline", "Keep subject centered vertically"),
    ("LOWER", "Lower Third", "Place subject near lower third"),
]

TRANSITION_TYPES = [
    ("CUT", "Cut", "Instant switch"),
    ("DOLLY", "Dolly", "Move camera between shots"),
    ("ZOOM", "Zoom", "Animate lens between shots"),
]

TURNTABLE_TYPES = [
    ("ROTATE_CAMERA", "Rotate Camera Around Subject", "Spin camera around subject"),
    ("ROTATE_SUBJECT", "Rotate Subject", "Rotate subject/root"),
]

PRESET_ITEMS = [
    ("KUBRICK", "Kubrick Framing", "Centered symmetry / one-point feel"),
    ("WES", "Wes Anderson Symmetry", "Balanced, frontal symmetry"),
    ("HOLLYWOOD", "Hollywood Dialogue", "Shot-reverse-shot coverage"),
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
    return [ob for ob in context.selected_objects if ob.type in {"MESH", "ARMATURE", "EMPTY"}]


def get_primary_subject(context):
    active = context.view_layer.objects.active
    if active in context.selected_objects:
        return active
    subjects = get_selected_subjects(context)
    return subjects[0] if subjects else None


def get_dialogue_subjects(context):
    subjects = get_selected_subjects(context)
    if len(subjects) < 2:
        return None, None
    active = context.view_layer.objects.active
    if active in subjects:
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


def ensure_lookat(scene, rig_col, root, settings):
    if settings.look_at_target:
        return settings.look_at_target, False
    empty = _find_tagged_object("EMPTY", name=LOOKAT_NAME)
    if empty is None:
        empty = bpy.data.objects.new(LOOKAT_NAME, None)
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


def ensure_track_to(cam_obj, target_obj):
    for con in [c for c in cam_obj.constraints if c.type in {"TRACK_TO", "DAMPED_TRACK"}]:
        cam_obj.constraints.remove(con)
    con = cam_obj.constraints.new(type="DAMPED_TRACK")
    con.target = target_obj
    con.track_axis = "TRACK_NEGATIVE_Z"


def apply_tracking(root, subject, enabled):
    for con in [c for c in root.constraints if c.type == "COPY_LOCATION"]:
        if con.name.startswith("CAMRIG_TRACK"):
            root.constraints.remove(con)
    if enabled and subject:
        con = root.constraints.new(type="COPY_LOCATION")
        con.name = "CAMRIG_TRACK"
        con.target = subject
        root[SUBJECT_PROP] = subject.name
    elif SUBJECT_PROP in root:
        del root[SUBJECT_PROP]


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

    eye_z = min_v.z + height * 0.85
    neutral_z = min_v.z + height * 0.55
    return {
        "center": center,
        "bottom": Vector((center.x, center.y, min_v.z)),
        "top": Vector((center.x, center.y, max_v.z)),
        "eye": Vector((center.x, center.y, eye_z)),
        "neutral": Vector((center.x, center.y, neutral_z)),
    }


def get_shot_def(shot_id):
    for shot in SHOT_DEFS:
        if shot["id"] == shot_id:
            return shot
    return None


def compute_eye_height(bounds):
    return bounds["min"].z + bounds["height"] * 0.85


def compute_target(bounds, shot_def, settings):
    anchors = compute_subject_anchors(bounds)
    if settings.eye_level:
        target = anchors["eye"].copy()
    else:
        if shot_def["target_factor"] == "CENTER":
            target = anchors["center"].copy()
        else:
            target = anchors["neutral"].copy()
            target.z = bounds["min"].z + bounds["height"] * shot_def["target_factor"]

    target.z = max(target.z, anchors["neutral"].z)
    target.z += settings.height_offset
    return target


def compute_shot_distance(shot_id, bounds):
    size = bounds["size"]
    base_size = max(size.x, size.y, size.z * 0.75, 0.1)
    multipliers = {
        "ECU": 1.2,
        "CU": 1.6,
        "MED_WAIST": 2.2,
        "MED_FULL": 2.8,
        "FULL": 3.4,
        "WIDE": 5.0,
        "OTS_A": 2.4,
        "OTS_B": 2.4,
        "SINGLE_A": 2.2,
        "SINGLE_B": 2.2,
        "TWO_SHOT": 3.2,
        "TURNTABLE": 3.8,
    }
    return max(base_size * multipliers.get(shot_id, 2.5), 0.5)


def apply_thirds_offset(target, bounds, settings, axis_dir):
    if not settings.rule_of_thirds:
        return target

    max_dim = bounds["max_dim"]
    height = bounds["height"]
    up = Vector((0.0, 0.0, 1.0))
    if abs(axis_dir.dot(up)) > 0.95:
        up = Vector((0.0, 1.0, 0.0))
    right = axis_dir.cross(up).normalized()

    h_factor = {"LEFT": -0.25, "CENTER": 0.0, "RIGHT": 0.25}.get(settings.thirds_h, 0.0)
    v_factor = {"UPPER": 0.25, "MID": 0.0, "LOWER": -0.25}.get(settings.thirds_v, 0.0)

    h_offset = right * (max_dim * h_factor)
    v_offset = up * (height * v_factor)
    return target + h_offset + v_offset


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


def place_shot_camera(cam_obj, root, lookat_obj, target, axis_dir, distance):
    cam_obj.location = target + axis_dir * distance
    if lookat_obj:
        ensure_track_to(cam_obj, lookat_obj)
    cam_obj[TARGET_PROP] = (target.x, target.y, target.z)


def get_control_empty_name(camera_name):
    if camera_name.startswith("CAM_"):
        return camera_name.replace("CAM_", "CTRL_CAM_", 1)
    return f"CTRL_{camera_name}"


def get_or_create_camera_control_empty(scene, rig_col, parent_obj, camera_obj, name):
    empty = _find_tagged_object("EMPTY", name=name)
    if empty is None:
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = "CIRCLE"
        empty.empty_display_size = 0.5
        _tag_object(empty)
        scene.collection.objects.link(empty)
    if empty.name not in rig_col.objects:
        rig_col.objects.link(empty)
    empty.matrix_world = camera_obj.matrix_world.copy()
    parent_keep_world(empty, parent_obj)
    parent_keep_world(camera_obj, empty)
    return empty


def apply_camera_parenting(scene, rig_col, parent_obj, camera_obj, settings):
    if settings.use_camera_control_empty:
        control_name = get_control_empty_name(camera_obj.name)
        get_or_create_camera_control_empty(scene, rig_col, parent_obj, camera_obj, control_name)
        return
    if parent_obj:
        parent_keep_world(camera_obj, parent_obj)


def create_shot_camera(context, shot_id, index=0):
    settings = get_settings(context)
    scene = context.scene
    subjects = get_selected_subjects(context)
    if not subjects:
        return None, "Select at least one object."

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds(subjects, depsgraph)
    if bounds is None:
        return None, "Unable to compute bounds for selection."

    shot_def = get_shot_def(shot_id)
    if shot_def is None:
        return None, "Unknown shot type."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    lookat_obj, auto_target = ensure_lookat(scene, rig_col, root, settings)

    axis_dir = axis_vector(settings.axis)
    target = compute_target(bounds, shot_def, settings)
    target = apply_thirds_offset(target, bounds, settings, axis_dir)

    distance = compute_shot_distance(shot_id, bounds)

    cam_obj = create_or_get_camera(scene, rig_col, shot_def["name"], shot_id)
    cam_obj.data.lens = shot_def["lens"]
    place_shot_camera(cam_obj, root, lookat_obj, target, axis_dir, distance)
    apply_camera_parenting(scene, rig_col, root, cam_obj, settings)

    if auto_target:
        lookat_obj.location = target

    return cam_obj, None


def switch_active_camera(context, shot_id):
    cam_obj = _find_tagged_object("CAMERA", shot_id=shot_id)
    if cam_obj is None:
        return False
    scene = context.scene
    scene.camera = cam_obj
    lookat = _find_tagged_object("EMPTY", name=LOOKAT_NAME)
    if lookat and cam_obj.get(TARGET_PROP):
        target = cam_obj[TARGET_PROP]
        lookat.location = Vector((target[0], target[1], target[2]))
    return True


def ensure_rig_for_selection(context):
    settings = get_settings(context)
    scene = context.scene
    subjects = get_selected_subjects(context)
    if not subjects:
        return None, "Select at least one object."

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds(subjects, depsgraph)
    if bounds is None:
        return None, "Unable to compute bounds for selection."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    lookat_obj, auto_target = ensure_lookat(scene, rig_col, root, settings)

    root.location = bounds["center"]
    subject = get_primary_subject(context)
    apply_tracking(root, subject, settings.tracking_enabled)

    if auto_target:
        lookat_obj.location = bounds["center"]

    return bounds, None


def create_shot_set(context):
    bounds, err = ensure_rig_for_selection(context)
    if err:
        return err

    settings = get_settings(context)
    axis_dir = axis_vector(settings.axis)

    scene = context.scene
    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    lookat_obj, auto_target = ensure_lookat(scene, rig_col, root, settings)

    for index, shot in enumerate(SHOT_DEFS):
        target = compute_target(bounds, shot, settings)
        target = apply_thirds_offset(target, bounds, settings, axis_dir)
        distance = compute_shot_distance(shot["id"], bounds)
        cam_obj = create_or_get_camera(scene, rig_col, shot["name"], shot["id"])
        cam_obj.data.lens = shot["lens"]
        place_shot_camera(cam_obj, root, lookat_obj, target, axis_dir, distance)
        apply_camera_parenting(scene, rig_col, root, cam_obj, settings)

    if auto_target:
        lookat_obj.location = bounds["center"]

    scene.camera = _find_tagged_object("CAMERA", shot_id="MED_FULL") or scene.camera
    return None


def create_turntable(context):
    settings = get_settings(context)
    scene = context.scene
    subjects = get_selected_subjects(context)
    if not subjects:
        return "Select a subject to turntable."

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds(subjects, depsgraph)
    if bounds is None:
        return "Unable to compute bounds for turntable."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    root.location = bounds["center"]
    apply_tracking(root, get_primary_subject(context), settings.tracking_enabled)

    start = scene.frame_start
    end = start + max(settings.turntable_frames, 1)

    if settings.turntable_type == "ROTATE_SUBJECT":
        root.rotation_euler = Vector((0.0, 0.0, 0.0))
        root.keyframe_insert(data_path="rotation_euler", frame=start)
        root.rotation_euler = Vector((0.0, 0.0, 6.283185))
        root.keyframe_insert(data_path="rotation_euler", frame=end)
        return None

    pivot = _find_tagged_object("EMPTY", name="CAM_TURNTABLE_PIVOT")
    if pivot is None:
        pivot = bpy.data.objects.new("CAM_TURNTABLE_PIVOT", None)
        pivot.empty_display_type = "PLAIN_AXES"
        _tag_object(pivot)
        scene.collection.objects.link(pivot)
    if pivot.name not in rig_col.objects:
        rig_col.objects.link(pivot)
    pivot.location = bounds["center"]
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

    axis_dir = axis_vector(settings.axis)
    distance = max(bounds["max_dim"] * 2.5, 2.0)
    cam_obj.location = bounds["center"] + axis_dir * distance
    apply_camera_parenting(scene, rig_col, pivot, cam_obj, settings)

    lookat_obj, auto_target = ensure_lookat(scene, rig_col, root, settings)
    if auto_target:
        lookat_obj.location = bounds["center"]
    ensure_track_to(cam_obj, lookat_obj)

    pivot.rotation_euler = Vector((0.0, 0.0, 0.0))
    pivot.keyframe_insert(data_path="rotation_euler", frame=start)
    pivot.rotation_euler = Vector((0.0, 0.0, 6.283185))
    pivot.keyframe_insert(data_path="rotation_euler", frame=end)
    return None


def apply_composition_to_active(context):
    settings = get_settings(context)
    scene = context.scene
    cam_obj = scene.camera
    if cam_obj is None:
        return "No active camera to apply composition."

    subjects = get_selected_subjects(context)
    if not subjects:
        return "Select at least one object."

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds(subjects, depsgraph)
    if bounds is None:
        return "Unable to compute bounds for selection."

    axis_dir = axis_vector(settings.axis)
    shot_def = get_shot_def(cam_obj.get(SHOT_PROP, "MED_FULL")) or SHOT_DEFS[3]
    target = compute_target(bounds, shot_def, settings)
    target = apply_thirds_offset(target, bounds, settings, axis_dir)

    lookat_obj, auto_target = ensure_lookat(scene, ensure_collection(scene), ensure_root(scene, ensure_collection(scene)), settings)
    if auto_target:
        lookat_obj.location = target
    cam_obj[TARGET_PROP] = (target.x, target.y, target.z)
    return None


def analyze_scene_for_shots(context):
    settings = get_settings(context)
    subjects = get_selected_subjects(context)
    depsgraph = context.evaluated_depsgraph_get()

    suggestions = []
    if len(subjects) >= 2:
        suggestions.append({"id": "OTS_A", "label": "OTS A", "reason": "Two subjects detected for dialogue coverage."})
        suggestions.append({"id": "OTS_B", "label": "OTS B", "reason": "Reverse angle for dialogue."})
        suggestions.append({"id": "TWO_SHOT", "label": "Two Shot", "reason": "Shared framing for both subjects."})
        suggestions.append({"id": "SINGLES", "label": "Singles", "reason": "Individual close singles for each subject."})
        return suggestions

    if not subjects:
        return suggestions

    bounds = selection_world_bounds(subjects, depsgraph)
    if bounds is None:
        return suggestions

    max_dim = bounds["max_dim"]
    height = bounds["height"]
    if max_dim < 0.5:
        suggestions.append({"id": "ECU", "label": "ECU", "reason": "Small subject suggests extreme close-up."})
    if max_dim < 1.5:
        suggestions.append({"id": "CU", "label": "CU", "reason": "Detail-focused closeup."})
    if height >= 1.0:
        suggestions.append({"id": "MED_WAIST", "label": "Medium", "reason": "Standard character framing."})
        suggestions.append({"id": "MED_FULL", "label": "Medium Full", "reason": "Balanced coverage for body and context."})
    suggestions.append({"id": "FULL", "label": "Full", "reason": "Show full body silhouette."})
    if max_dim > 2.5 or settings.axis in {"+Z", "-Z"}:
        suggestions.append({"id": "WIDE", "label": "Wide", "reason": "Scene scale suggests an establishing shot."})

    return suggestions
