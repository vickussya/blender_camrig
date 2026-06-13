from mathutils import Vector

from .camera_utils import (
    apply_camera_parenting,
    apply_orbit_controls,
    apply_tracking,
    create_or_get_camera,
    DEBUG_CAM_RIG,
    ensure_collection,
    ensure_root,
    ensure_track_to,
    get_dialogue_subjects,
    get_or_create_camera_target,
    get_primary_subject,
    selection_world_bounds,
    set_world_location,
    TARGET_OBJ_PROP,
    TARGET_PROP,
)

_OTS_LENS = 50.0
_SINGLE_LENS = 70.0


def _eye_z(bounds):
    return bounds["min"].z + bounds["height"] * 0.85


def _place_dialogue_cam(context, scene, rig_col, root, settings, shot_id, cam_name, camera_loc, target_loc, lens):
    cam_obj = create_or_get_camera(scene, rig_col, cam_name, shot_id)

    # Set world-space position before parenting so parent_keep_world preserves it.
    cam_wm = cam_obj.matrix_world.copy()
    cam_wm.translation = Vector(camera_loc)
    cam_obj.matrix_world = cam_wm

    lookat_obj, _ = get_or_create_camera_target(scene, rig_col, root, settings, cam_obj)
    set_world_location(lookat_obj, target_loc)

    apply_camera_parenting(scene, rig_col, root, cam_obj, settings)
    apply_orbit_controls(scene, rig_col, root, cam_obj, target_loc, settings)
    ensure_track_to(cam_obj, lookat_obj, settings.tracking_enabled)
    cam_obj[TARGET_PROP] = (target_loc.x, target_loc.y, target_loc.z)
    cam_obj[TARGET_OBJ_PROP] = lookat_obj.name

    if lens:
        cam_obj.data.lens = lens

    if DEBUG_CAM_RIG:
        print(f"Dialogue {cam_name}: world={tuple(cam_obj.matrix_world.translation)}")

    return cam_obj


def create_dialogue_setup(context):
    """Create four dialogue cameras: OTS_A, OTS_B, SINGLE_A, SINGLE_B."""
    settings = context.scene.camrig_settings
    scene = context.scene

    a, b = get_dialogue_subjects(context)
    if not a or not b:
        return "Select exactly two dialogue participants."

    depsgraph = context.evaluated_depsgraph_get()
    bounds_a = selection_world_bounds([a], depsgraph)
    bounds_b = selection_world_bounds([b], depsgraph)
    if bounds_a is None or bounds_b is None:
        return "Unable to compute bounding boxes for dialogue subjects."

    rig_col = ensure_collection(scene)
    root = ensure_root(scene, rig_col)
    apply_tracking(root, get_primary_subject(context), settings.tracking_enabled)
    root.location = (a.matrix_world.translation + b.matrix_world.translation) * 0.5

    a_center = bounds_a["center"]
    b_center = bounds_b["center"]
    a_eye_z = _eye_z(bounds_a)
    b_eye_z = _eye_z(bounds_b)
    a_size = bounds_a["max_dim"]
    b_size = bounds_b["max_dim"]

    # Flat AB direction — height difference between characters is irrelevant for lateral placement.
    ab_flat = Vector((b_center.x - a_center.x, b_center.y - a_center.y, 0.0))
    if ab_flat.length < 0.001:
        ab_flat = Vector((1.0, 0.0, 0.0))
    ab_dir = ab_flat.normalized()
    ab_dist = ab_flat.length

    # "right" = direction to the right when looking from A toward B (horizontal plane).
    # Using the cross product with Z-up: right = ab_dir × Z.
    right = ab_dir.cross(Vector((0.0, 0.0, 1.0))).normalized()
    if right.length < 0.001:
        right = Vector((1.0, 0.0, 0.0))

    # OTS distance: max of inter-character distance and the shoulder character's size.
    ots_a_behind = max(ab_dist * 0.6, a_size * 1.0)
    ots_b_behind = max(ab_dist * 0.6, b_size * 1.0)
    # Lateral: 35 % of the behind distance — keeps shoulder/ear in the corner of the frame.
    ots_lateral = ots_a_behind * 0.35

    # Single distance: enough for a CU from the opposing direction.
    single_a_dist = max(ab_dist * 0.5, a_size * 2.0)
    single_b_dist = max(ab_dist * 0.5, b_size * 2.0)

    # ── OTS_A: behind A (−ab_dir from A), over A's LEFT shoulder (−right), looking at B ──────
    # When A faces B (+ab_dir), A's left = −right in world space.
    ots_a_cam = Vector((
        a_center.x - ab_dir.x * ots_a_behind - right.x * ots_lateral,
        a_center.y - ab_dir.y * ots_a_behind - right.y * ots_lateral,
        a_eye_z,
    ))
    _place_dialogue_cam(
        context, scene, rig_col, root, settings,
        "OTS_A", "CAM_OTS_A",
        ots_a_cam,
        Vector((b_center.x, b_center.y, b_eye_z)),
        _OTS_LENS,
    )

    # ── OTS_B: behind B (+ab_dir from B), over B's RIGHT shoulder (also −right), looking at A ─
    # When B faces A (−ab_dir), B's right = −right in world space.
    # Both OTS cameras land on the same side of the AB axis → 180-degree rule satisfied.
    ots_b_cam = Vector((
        b_center.x + ab_dir.x * ots_b_behind - right.x * ots_lateral,
        b_center.y + ab_dir.y * ots_b_behind - right.y * ots_lateral,
        b_eye_z,
    ))
    _place_dialogue_cam(
        context, scene, rig_col, root, settings,
        "OTS_B", "CAM_OTS_B",
        ots_b_cam,
        Vector((a_center.x, a_center.y, a_eye_z)),
        _OTS_LENS,
    )

    # ── SINGLE_A: from B's direction (+ab_dir from A), facing A ──────────────────────────────
    single_a_cam = Vector((
        a_center.x + ab_dir.x * single_a_dist,
        a_center.y + ab_dir.y * single_a_dist,
        a_eye_z,
    ))
    _place_dialogue_cam(
        context, scene, rig_col, root, settings,
        "SINGLE_A", "CAM_SINGLE_A",
        single_a_cam,
        Vector((a_center.x, a_center.y, a_eye_z)),
        _SINGLE_LENS,
    )

    # ── SINGLE_B: from A's direction (−ab_dir from B), facing B ──────────────────────────────
    single_b_cam = Vector((
        b_center.x - ab_dir.x * single_b_dist,
        b_center.y - ab_dir.y * single_b_dist,
        b_eye_z,
    ))
    _place_dialogue_cam(
        context, scene, rig_col, root, settings,
        "SINGLE_B", "CAM_SINGLE_B",
        single_b_cam,
        Vector((b_center.x, b_center.y, b_eye_z)),
        _SINGLE_LENS,
    )

    return None
