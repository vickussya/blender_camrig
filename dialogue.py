from mathutils import Vector

from .camera_utils import (
    apply_tracking,
    compute_eye_height,
    create_or_get_camera,
    ensure_collection,
    ensure_root,
    ensure_track_to,
    get_dialogue_subjects,
    get_primary_subject,
    parent_keep_world,
    selection_world_bounds,
)


def create_dialogue_camera(scene, rig_col, root, shot_id, name, position, target_obj):
    cam_obj = create_or_get_camera(scene, rig_col, name, shot_id)
    cam_obj.location = position
    parent_keep_world(cam_obj, root)
    ensure_track_to(cam_obj, target_obj)
    return cam_obj


def create_dialogue_setup(context, mode):
    settings = context.scene.camrig_settings
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
