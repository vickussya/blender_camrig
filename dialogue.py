from mathutils import Vector

from .camera_utils import (
    apply_camera_parenting,
    apply_orbit_controls,
    apply_tracking,
    compute_camera_transform,
    create_or_get_camera,
    DEBUG_CAM_RIG,
    enforce_final_camera_outside_bounds,
    ensure_collection,
    ensure_root,
    ensure_track_to,
    get_dialogue_subjects,
    get_or_create_camera_target,
    get_primary_subject,
    selection_world_bounds,
    SHOT_OFFSET_MULTIPLIERS,
    TARGET_OBJ_PROP,
    TARGET_PROP,
)


def _place_dialogue_cam(context, scene, rig_col, root, settings, shot_id, cam_name, camera_loc, target_loc, target_subjects):
    """Create and fully configure one dialogue camera with its own lookat target."""
    cam_obj = create_or_get_camera(scene, rig_col, cam_name, shot_id)
    cam_obj.location = camera_loc
    apply_camera_parenting(scene, rig_col, root, cam_obj, settings)

    lookat_obj, _ = get_or_create_camera_target(scene, rig_col, root, settings, cam_obj)
    lookat_obj.location = target_loc

    apply_orbit_controls(scene, rig_col, root, cam_obj, target_loc, settings)
    ensure_track_to(cam_obj, lookat_obj, settings.tracking_enabled)
    cam_obj[TARGET_PROP] = (target_loc.x, target_loc.y, target_loc.z)
    cam_obj[TARGET_OBJ_PROP] = lookat_obj.name

    depsgraph = context.evaluated_depsgraph_get()
    bounds = selection_world_bounds(target_subjects, depsgraph)
    if bounds:
        base = max(bounds["size"].x, bounds["size"].y, bounds["height"], 0.1)
        shot_offset = max(base * SHOT_OFFSET_MULTIPLIERS.get(shot_id, 2.5), base * 1.0)
        margin = max(base * 0.1, 0.05)
        enforce_final_camera_outside_bounds(cam_obj, bounds, settings.axis, shot_offset, margin)

    if DEBUG_CAM_RIG:
        print(f"Dialogue {cam_name}: world={tuple(cam_obj.matrix_world.translation)}")

    return cam_obj


def create_dialogue_setup(context):
    """Create all four dialogue cameras: OTS_A, OTS_B, SINGLE_A, SINGLE_B."""
    settings = context.scene.camrig_settings
    scene = context.scene

    a, b = get_dialogue_subjects(context)
    if not a or not b:
        return "Select exactly two dialogue participants."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    apply_tracking(root, get_primary_subject(context), settings.tracking_enabled)
    root.location = (a.matrix_world.translation + b.matrix_world.translation) * 0.5

    ab = b.matrix_world.translation - a.matrix_world.translation
    if ab.length < 0.001:
        ab = Vector((1.0, 0.0, 0.0))
    ab_dir = ab.normalized()
    right = ab_dir.cross(Vector((0.0, 0.0, 1.0))).normalized()
    if right.length < 0.001:
        right = Vector((1.0, 0.0, 0.0))

    shoulder_offset = right * (max(ab.length, 1.0) * 0.15)

    def resolve_placement(cam_subjects, tgt_subjects, shot_id, lateral=None):
        cam_loc, _, lens = compute_camera_transform(
            context, cam_subjects, shot_id, settings.axis, settings.eye_level,
        )
        _, tgt_loc, _ = compute_camera_transform(
            context, tgt_subjects, shot_id, settings.axis, settings.eye_level,
        )
        if cam_loc is None or tgt_loc is None:
            return None, None, None
        if lateral is not None:
            cam_loc = cam_loc + lateral
        return cam_loc, tgt_loc, lens

    # OTS_A — camera on A's side, targeting B
    cam_loc, tgt_loc, lens = resolve_placement([a, b], [b], "OTS_A", shoulder_offset)
    if cam_loc is None:
        return "Unable to compute OTS_A placement."
    cam = _place_dialogue_cam(context, scene, rig_col, root, settings, "OTS_A", "CAM_OTS_A", cam_loc, tgt_loc, [b])
    if lens:
        cam.data.lens = lens

    # OTS_B — camera on B's side, targeting A
    cam_loc, tgt_loc, lens = resolve_placement([a, b], [a], "OTS_B", -shoulder_offset)
    if cam_loc is None:
        return "Unable to compute OTS_B placement."
    cam = _place_dialogue_cam(context, scene, rig_col, root, settings, "OTS_B", "CAM_OTS_B", cam_loc, tgt_loc, [a])
    if lens:
        cam.data.lens = lens

    # SINGLE_A — standalone close-up of A
    cam_loc, tgt_loc, lens = resolve_placement([a], [a], "SINGLE_A")
    if cam_loc is None:
        return "Unable to compute SINGLE_A placement."
    cam = _place_dialogue_cam(context, scene, rig_col, root, settings, "SINGLE_A", "CAM_SINGLE_A", cam_loc, tgt_loc, [a])
    if lens:
        cam.data.lens = lens

    # SINGLE_B — standalone close-up of B
    cam_loc, tgt_loc, lens = resolve_placement([b], [b], "SINGLE_B")
    if cam_loc is None:
        return "Unable to compute SINGLE_B placement."
    cam = _place_dialogue_cam(context, scene, rig_col, root, settings, "SINGLE_B", "CAM_SINGLE_B", cam_loc, tgt_loc, [b])
    if lens:
        cam.data.lens = lens

    return None
