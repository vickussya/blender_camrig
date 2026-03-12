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


def get_settings(context):
    return context.scene.camrig_settings


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


def get_shot_def(shot_id):
    for shot in SHOT_DEFS:
        if shot["id"] == shot_id:
            return shot
    return None


def compute_eye_height(bounds):
    return bounds["min"].z + bounds["height"] * 0.9


def compute_target(bounds, shot_def, settings):
    center = bounds["center"]
    min_v = bounds["min"]
    height = bounds["height"]

    if shot_def["target_factor"] == "CENTER":
        target = Vector((center.x, center.y, center.z))
    else:
        if settings.eye_level:
            target_z = compute_eye_height(bounds)
        else:
            target_z = min_v.z + height * shot_def["target_factor"]
        target = Vector((center.x, center.y, target_z))

    target.z += settings.height_offset
    return target


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
    if root:
        parent_keep_world(cam_obj, root)
    if lookat_obj:
        ensure_track_to(cam_obj, lookat_obj)
    cam_obj[TARGET_PROP] = (target.x, target.y, target.z)


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

    max_dim = bounds["max_dim"]
    base_distance = max(max_dim * 2.0, 1.0)
    spacing = 0.5 * max_dim
    distance = base_distance + spacing * index

    cam_obj = create_or_get_camera(scene, rig_col, shot_def["name"], shot_id)
    cam_obj.data.lens = shot_def["lens"]
    place_shot_camera(cam_obj, root, lookat_obj, target, axis_dir, distance)

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
    max_dim = bounds["max_dim"]
    base_distance = max(max_dim * 2.0, 1.0)
    spacing = 0.5 * max_dim

    scene = context.scene
    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    lookat_obj, auto_target = ensure_lookat(scene, rig_col, root, settings)

    for index, shot in enumerate(SHOT_DEFS):
        target = compute_target(bounds, shot, settings)
        target = apply_thirds_offset(target, bounds, settings, axis_dir)
        distance = base_distance + spacing * index
        cam_obj = create_or_get_camera(scene, rig_col, shot["name"], shot["id"])
        cam_obj.data.lens = shot["lens"]
        place_shot_camera(cam_obj, root, lookat_obj, target, axis_dir, distance)

    if auto_target:
        lookat_obj.location = bounds["center"]

    scene.camera = _find_tagged_object("CAMERA", shot_id="MED_FULL") or scene.camera
    return None


def create_dialogue_camera(scene, rig_col, root, shot_id, name, position, target_obj):
    cam_obj = create_or_get_camera(scene, rig_col, name, shot_id)
    cam_obj.location = position
    parent_keep_world(cam_obj, root)
    ensure_track_to(cam_obj, target_obj)
    return cam_obj


def create_dialogue_setup(context, mode):
    settings = get_settings(context)
    scene = context.scene
    a, b = get_dialogue_subjects(context)
    if not a or not b:
        return "Select two dialogue participants."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    apply_tracking(root, get_primary_subject(context), settings.tracking_enabled)

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds([a, b], depsgraph)
    if bounds is None:
        return "Unable to compute bounds for dialogue setup."

    center = bounds["center"]
    root.location = center

    ab = (b.matrix_world.translation - a.matrix_world.translation)
    if ab.length == 0.0:
        ab = Vector((1.0, 0.0, 0.0))
    ab_dir = ab.normalized()
    up = Vector((0.0, 0.0, 1.0))
    right = ab_dir.cross(up).normalized()
    if right.length == 0.0:
        right = Vector((1.0, 0.0, 0.0))

    distance = max(bounds["max_dim"] * 2.0, 1.5)
    shoulder = bounds["max_dim"] * 0.25
    eye = compute_eye_height(bounds) if settings.eye_level else center.z

    if mode in {"OTS_A", "SINGLES"}:
        pos = a.matrix_world.translation + (-ab_dir * distance) + (right * shoulder)
        pos.z = eye
        create_dialogue_camera(scene, rig_col, root, "OTS_A", "CAM_OTS_A", pos, b)
    if mode in {"OTS_B", "SINGLES"}:
        pos = b.matrix_world.translation + (ab_dir * distance) + (-right * shoulder)
        pos.z = eye
        create_dialogue_camera(scene, rig_col, root, "OTS_B", "CAM_OTS_B", pos, a)
    if mode == "SINGLES":
        pos = a.matrix_world.translation + (-ab_dir * distance)
        pos.z = eye
        create_dialogue_camera(scene, rig_col, root, "SINGLE_A", "CAM_SINGLE_A", pos, a)
        pos = b.matrix_world.translation + (ab_dir * distance)
        pos.z = eye
        create_dialogue_camera(scene, rig_col, root, "SINGLE_B", "CAM_SINGLE_B", pos, b)
    if mode == "TWO_SHOT":
        pos = center + (right * distance)
        pos.z = eye
        create_dialogue_camera(scene, rig_col, root, "TWO_SHOT", "CAM_TWO_SHOT", pos, b)

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
    parent_keep_world(cam_obj, pivot)

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


def apply_preset(context, preset):
    settings = get_settings(context)
    if preset in {"KUBRICK", "WES"}:
        settings.rule_of_thirds = False
        settings.thirds_h = "CENTER"
        settings.thirds_v = "MID"
        settings.eye_level = True
        return apply_composition_to_active(context)
    if preset == "HOLLYWOOD":
        return create_dialogue_setup(context, "SINGLES")
    return None


def create_transition(context):
    settings = get_settings(context)
    scene = context.scene
    src = _find_tagged_object("CAMERA", shot_id=settings.transition_source)
    dst = _find_tagged_object("CAMERA", shot_id=settings.transition_target)
    if src is None or dst is None:
        return "Source or target camera not found."

    start = settings.transition_start
    end = settings.transition_end
    if end <= start:
        return "End frame must be after start frame."

    if settings.transition_type == "CUT":
        scene.camera = dst
        marker = scene.timeline_markers.new(f"CAM_{settings.transition_target}", frame=start)
        marker.camera = dst
        return None

    if settings.transition_type == "DOLLY":
        scene.camera = src
        scene.frame_set(start)
        src.keyframe_insert(data_path="location", frame=start)
        src.keyframe_insert(data_path="rotation_euler", frame=start)
        scene.frame_set(end)
        src.location = dst.location
        src.rotation_euler = dst.rotation_euler
        src.keyframe_insert(data_path="location", frame=end)
        src.keyframe_insert(data_path="rotation_euler", frame=end)
        return None

    if settings.transition_type == "ZOOM":
        scene.camera = src
        scene.frame_set(start)
        src.data.keyframe_insert(data_path="lens", frame=start)
        scene.frame_set(end)
        src.data.lens = dst.data.lens
        src.data.keyframe_insert(data_path="lens", frame=end)
        return None

    return None


class CAMRIG_ShotLibraryItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    shot_id: bpy.props.EnumProperty(name="Shot Type", items=SHOT_ENUM_ITEMS)
    camera_name: bpy.props.StringProperty(name="Camera")
    location: bpy.props.FloatVectorProperty(name="Location", size=3, subtype="TRANSLATION")
    rotation: bpy.props.FloatVectorProperty(name="Rotation", size=3, subtype="EULER")
    lens: bpy.props.FloatProperty(name="Lens")
    target_name: bpy.props.StringProperty(name="Target")
    axis: bpy.props.StringProperty(name="Axis")
    eye_level: bpy.props.BoolProperty(name="Eye Level")
    rule_of_thirds: bpy.props.BoolProperty(name="Rule of Thirds")
    thirds_h: bpy.props.StringProperty(name="Thirds H")
    thirds_v: bpy.props.StringProperty(name="Thirds V")


class CAMRIG_SuggestionItem(bpy.types.PropertyGroup):
    shot_id: bpy.props.StringProperty(name="Shot ID")
    label: bpy.props.StringProperty(name="Label")
    reason: bpy.props.StringProperty(name="Reason")


class CAMRIG_Settings(bpy.types.PropertyGroup):
    axis: bpy.props.EnumProperty(name="Axis", items=AXIS_ITEMS, default="-Y")
    eye_level: bpy.props.BoolProperty(name="Eye Level", default=False)
    tracking_enabled: bpy.props.BoolProperty(name="Tracking", default=True)
    look_at_target: bpy.props.PointerProperty(name="Look-at Target", type=bpy.types.Object)
    height_offset: bpy.props.FloatProperty(
        name="Height Offset",
        description="Additional height added to shot target points",
        default=0.0,
        step=1.0,
    )

    rule_of_thirds: bpy.props.BoolProperty(name="Rule of Thirds", default=False)
    thirds_h: bpy.props.EnumProperty(name="Horizontal", items=THIRDS_H_ITEMS, default="CENTER")
    thirds_v: bpy.props.EnumProperty(name="Vertical", items=THIRDS_V_ITEMS, default="MID")

    transition_type: bpy.props.EnumProperty(name="Transition", items=TRANSITION_TYPES, default="CUT")
    transition_source: bpy.props.EnumProperty(name="Source", items=SHOT_ENUM_ITEMS, default="CU")
    transition_target: bpy.props.EnumProperty(name="Target", items=SHOT_ENUM_ITEMS, default="MED_FULL")
    transition_start: bpy.props.IntProperty(name="Start Frame", default=1, min=1)
    transition_end: bpy.props.IntProperty(name="End Frame", default=24, min=2)

    turntable_frames: bpy.props.IntProperty(name="Frames", default=120, min=1)
    turntable_type: bpy.props.EnumProperty(name="Rotation Type", items=TURNTABLE_TYPES, default="ROTATE_CAMERA")

    preset: bpy.props.EnumProperty(name="Preset", items=PRESET_ITEMS, default="KUBRICK")

    shot_library: bpy.props.CollectionProperty(type=CAMRIG_ShotLibraryItem)
    shot_library_index: bpy.props.IntProperty(name="Shot Index", default=0)

    suggestions: bpy.props.CollectionProperty(type=CAMRIG_SuggestionItem)
    suggestion_index: bpy.props.IntProperty(name="Suggestion Index", default=0)


class CAMRIG_UL_shot_library(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name or "Shot", icon="CAMERA_DATA")


class CAMRIG_UL_suggestions(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        label = f"{item.label} - {item.reason}" if item.reason else item.label
        layout.label(text=label, icon="INFO")


class CAMRIG_OT_create_rig(bpy.types.Operator):
    bl_idname = "camrig.create_rig"
    bl_label = "Create/Update Shot Cameras"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        err = create_shot_set(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Shot cameras updated.")
        return {"FINISHED"}


class CAMRIG_OT_create_shot(bpy.types.Operator):
    bl_idname = "camrig.create_shot"
    bl_label = "Create Shot"
    bl_options = {"REGISTER", "UNDO"}

    shot_id: bpy.props.EnumProperty(items=SHOT_ENUM_ITEMS)

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        index = 0
        for idx, shot in enumerate(SHOT_DEFS):
            if shot["id"] == self.shot_id:
                index = idx
                break
        cam_obj, err = create_shot_camera(context, self.shot_id, index=index)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        context.scene.camera = cam_obj
        return {"FINISHED"}


class CAMRIG_OT_set_active(bpy.types.Operator):
    bl_idname = "camrig.set_active"
    bl_label = "Set Active Shot"

    shot_id: bpy.props.EnumProperty(items=SHOT_ENUM_ITEMS)

    def execute(self, context):
        if not switch_active_camera(context, self.shot_id):
            self.report({"WARNING"}, "Shot camera not found. Create the rig first.")
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_view_selected_camera(bpy.types.Operator):
    bl_idname = "camrig.view_selected_camera"
    bl_label = "View Selected Camera"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if obj and obj.type == "CAMERA":
            context.scene.camera = obj
        bpy.ops.view3d.view_camera()
        return {"FINISHED"}


class CAMRIG_OT_dialogue(bpy.types.Operator):
    bl_idname = "camrig.dialogue"
    bl_label = "Create Dialogue Setup"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        items=[
            ("OTS_A", "OTS A", "Create OTS A"),
            ("OTS_B", "OTS B", "Create OTS B"),
            ("SINGLES", "Singles", "Create singles and OTS"),
            ("TWO_SHOT", "Two Shot", "Create two shot"),
        ]
    )

    def execute(self, context):
        err = create_dialogue_setup(context, self.mode)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_turntable(bpy.types.Operator):
    bl_idname = "camrig.turntable"
    bl_label = "Create Turntable"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        err = create_turntable(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_apply_composition(bpy.types.Operator):
    bl_idname = "camrig.apply_composition"
    bl_label = "Apply Composition"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        err = apply_composition_to_active(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_apply_preset(bpy.types.Operator):
    bl_idname = "camrig.apply_preset"
    bl_label = "Apply Preset"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        err = apply_preset(context, settings.preset)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_transition(bpy.types.Operator):
    bl_idname = "camrig.transition"
    bl_label = "Create Transition"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        err = create_transition(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_analyze_scene(bpy.types.Operator):
    bl_idname = "camrig.analyze_scene"
    bl_label = "Analyze Scene"

    def execute(self, context):
        settings = get_settings(context)
        settings.suggestions.clear()
        suggestions = analyze_scene_for_shots(context)
        for entry in suggestions:
            item = settings.suggestions.add()
            item.shot_id = entry["id"]
            item.label = entry["label"]
            item.reason = entry["reason"]
        settings.suggestion_index = 0
        if not suggestions:
            self.report({"INFO"}, "No suggestions generated.")
        return {"FINISHED"}


class CAMRIG_OT_generate_suggestion(bpy.types.Operator):
    bl_idname = "camrig.generate_suggestion"
    bl_label = "Generate Suggested Shot"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        if not settings.suggestions:
            self.report({"WARNING"}, "No suggestions available.")
            return {"CANCELLED"}
        idx = settings.suggestion_index
        item = settings.suggestions[idx]
        if item.shot_id in {"OTS_A", "OTS_B", "TWO_SHOT", "SINGLES"}:
            mode = "SINGLES" if item.shot_id == "SINGLES" else item.shot_id
            err = create_dialogue_setup(context, mode)
            if err:
                self.report({"WARNING"}, err)
                return {"CANCELLED"}
            return {"FINISHED"}
        cam_obj, err = create_shot_camera(context, item.shot_id, index=0)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        context.scene.camera = cam_obj
        return {"FINISHED"}


class CAMRIG_OT_generate_coverage(bpy.types.Operator):
    bl_idname = "camrig.generate_coverage"
    bl_label = "Generate Coverage Set"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        if not settings.suggestions:
            self.report({"WARNING"}, "No suggestions available.")
            return {"CANCELLED"}
        for item in settings.suggestions:
            if item.shot_id == "SINGLES":
                create_dialogue_setup(context, "SINGLES")
            elif item.shot_id in {"OTS_A", "OTS_B", "TWO_SHOT"}:
                create_dialogue_setup(context, item.shot_id)
            else:
                create_shot_camera(context, item.shot_id, index=0)
        return {"FINISHED"}


class CAMRIG_OT_shot_save(bpy.types.Operator):
    bl_idname = "camrig.shot_save"
    bl_label = "Save Shot"

    def execute(self, context):
        settings = get_settings(context)
        cam_obj = context.scene.camera
        if cam_obj is None:
            self.report({"WARNING"}, "No active camera to save.")
            return {"CANCELLED"}
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
        self.report({"INFO"}, "Shot saved.")
        return {"FINISHED"}


class CAMRIG_OT_shot_load(bpy.types.Operator):
    bl_idname = "camrig.shot_load"
    bl_label = "Load Shot"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        if not settings.shot_library:
            self.report({"WARNING"}, "Shot library is empty.")
            return {"CANCELLED"}
        item = settings.shot_library[settings.shot_library_index]
        cam_obj = bpy.data.objects.get(item.camera_name)
        if cam_obj is None or cam_obj.type != "CAMERA":
            self.report({"WARNING"}, "Camera for this shot not found.")
            return {"CANCELLED"}
        cam_obj.location = item.location
        cam_obj.rotation_euler = item.rotation
        cam_obj.data.lens = item.lens
        settings.axis = item.axis or settings.axis
        settings.eye_level = item.eye_level
        settings.rule_of_thirds = item.rule_of_thirds
        settings.thirds_h = item.thirds_h or settings.thirds_h
        settings.thirds_v = item.thirds_v or settings.thirds_v
        context.scene.camera = cam_obj
        return {"FINISHED"}


class CAMRIG_OT_shot_delete(bpy.types.Operator):
    bl_idname = "camrig.shot_delete"
    bl_label = "Delete Shot"

    def execute(self, context):
        settings = get_settings(context)
        if not settings.shot_library:
            return {"CANCELLED"}
        idx = settings.shot_library_index
        settings.shot_library.remove(idx)
        settings.shot_library_index = max(0, idx - 1)
        return {"FINISHED"}


class CAMRIG_PT_setup(bpy.types.Panel):
    bl_label = "Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.operator("camrig.create_rig", icon="CAMERA_DATA")
        layout.prop(settings, "axis")
        layout.prop(settings, "eye_level")
        layout.prop(settings, "tracking_enabled")
        layout.prop(settings, "look_at_target")
        layout.prop(settings, "height_offset")


class CAMRIG_PT_shot_types(bpy.types.Panel):
    bl_label = "Shot Types"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        layout = self.layout
        layout.operator("camrig.create_shot", text="Extreme Close-up").shot_id = "ECU"
        layout.operator("camrig.create_shot", text="Closeup").shot_id = "CU"
        layout.operator("camrig.create_shot", text="Medium").shot_id = "MED_WAIST"
        layout.operator("camrig.create_shot", text="Medium Full").shot_id = "MED_FULL"
        layout.operator("camrig.create_shot", text="Full").shot_id = "FULL"
        layout.operator("camrig.create_shot", text="Wide").shot_id = "WIDE"


class CAMRIG_PT_quick_switch(bpy.types.Panel):
    bl_label = "Quick Switch"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("camrig.set_active", text="Switch to CU").shot_id = "CU"
        row.operator("camrig.set_active", text="Switch to Medium").shot_id = "MED_WAIST"
        row.operator("camrig.set_active", text="Switch to Wide").shot_id = "WIDE"


class CAMRIG_PT_dialogue(bpy.types.Panel):
    bl_label = "Create Dialogue Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("camrig.dialogue", text="OTS A").mode = "OTS_A"
        row.operator("camrig.dialogue", text="OTS B").mode = "OTS_B"
        row = layout.row(align=True)
        row.operator("camrig.dialogue", text="Singles").mode = "SINGLES"
        row.operator("camrig.dialogue", text="Two Shot").mode = "TWO_SHOT"


class CAMRIG_PT_turntable(bpy.types.Panel):
    bl_label = "Turntable"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.operator("camrig.turntable", icon="DRIVER_ROTATIONAL_DIFFERENCE")
        layout.prop(settings, "turntable_frames")
        layout.prop(settings, "turntable_type")


class CAMRIG_PT_shot_library(bpy.types.Panel):
    bl_label = "Shot Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.template_list("CAMRIG_UL_shot_library", "", settings, "shot_library", settings, "shot_library_index")
        row = layout.row(align=True)
        row.operator("camrig.shot_save", text="Save Shot")
        row.operator("camrig.shot_load", text="Load Shot")
        row.operator("camrig.shot_delete", text="Delete Shot")


class CAMRIG_PT_composition(bpy.types.Panel):
    bl_label = "Composition"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.prop(settings, "rule_of_thirds")
        layout.prop(settings, "thirds_h")
        layout.prop(settings, "thirds_v")
        layout.operator("camrig.apply_composition", icon="ORIENTATION_VIEW")


class CAMRIG_PT_transition(bpy.types.Panel):
    bl_label = "Shot Transition"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.prop(settings, "transition_type")
        layout.prop(settings, "transition_source")
        layout.prop(settings, "transition_target")
        layout.prop(settings, "transition_start")
        layout.prop(settings, "transition_end")
        layout.operator("camrig.transition", icon="ANIM")


class CAMRIG_PT_presets(bpy.types.Panel):
    bl_label = "Cinematic Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.prop(settings, "preset")
        layout.operator("camrig.apply_preset", icon="PRESET")


class CAMRIG_PT_intelligent_framing(bpy.types.Panel):
    bl_label = "Intelligent Framing"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.operator("camrig.analyze_scene", icon="VIEWZOOM")
        layout.template_list("CAMRIG_UL_suggestions", "", settings, "suggestions", settings, "suggestion_index")
        row = layout.row(align=True)
        row.operator("camrig.generate_suggestion", text="Generate Suggested Shot")
        row.operator("camrig.generate_coverage", text="Generate Coverage Set")


classes = (
    CAMRIG_ShotLibraryItem,
    CAMRIG_SuggestionItem,
    CAMRIG_Settings,
    CAMRIG_UL_shot_library,
    CAMRIG_UL_suggestions,
    CAMRIG_OT_create_rig,
    CAMRIG_OT_create_shot,
    CAMRIG_OT_set_active,
    CAMRIG_OT_view_selected_camera,
    CAMRIG_OT_dialogue,
    CAMRIG_OT_turntable,
    CAMRIG_OT_apply_composition,
    CAMRIG_OT_apply_preset,
    CAMRIG_OT_transition,
    CAMRIG_OT_analyze_scene,
    CAMRIG_OT_generate_suggestion,
    CAMRIG_OT_generate_coverage,
    CAMRIG_OT_shot_save,
    CAMRIG_OT_shot_load,
    CAMRIG_OT_shot_delete,
    CAMRIG_PT_setup,
    CAMRIG_PT_shot_types,
    CAMRIG_PT_quick_switch,
    CAMRIG_PT_dialogue,
    CAMRIG_PT_turntable,
    CAMRIG_PT_shot_library,
    CAMRIG_PT_composition,
    CAMRIG_PT_transition,
    CAMRIG_PT_presets,
    CAMRIG_PT_intelligent_framing,
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
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.camrig_settings = bpy.props.PointerProperty(type=CAMRIG_Settings)
    register_keymap()


def unregister():
    unregister_keymap()
    del bpy.types.Scene.camrig_settings
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
