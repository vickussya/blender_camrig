from .camera_utils import (
    apply_tracking,
    apply_camera_parenting,
    compute_camera_transform,
    create_or_get_camera,
    ensure_collection,
    ensure_lookat,
    ensure_root,
    ensure_track_to,
    get_dialogue_subjects,
    get_primary_subject,
    TARGET_PROP,
)


def create_dialogue_camera(scene, rig_col, root, settings, shot_id, name, camera_location, target_location, lookat_obj):
    cam_obj = create_or_get_camera(scene, rig_col, name, shot_id)
    cam_obj.location = camera_location
    apply_camera_parenting(scene, rig_col, root, cam_obj, settings)
    ensure_track_to(cam_obj, lookat_obj)
    cam_obj[TARGET_PROP] = (target_location.x, target_location.y, target_location.z)
    lookat_obj.location = target_location
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

    root.location = (a.matrix_world.translation + b.matrix_world.translation) * 0.5
    lookat_obj, auto_target = ensure_lookat(scene, rig_col, root, settings)

    def camera_and_target(subject_for_camera, subject_for_target, shot_id, name):
        camera_location, _ = compute_camera_transform(
            context,
            subject_for_camera,
            shot_id,
            settings.axis,
            settings.eye_level,
        )
        _, target_location = compute_camera_transform(
            context,
            subject_for_target,
            shot_id,
            settings.axis,
            settings.eye_level,
        )
        if camera_location is None or target_location is None:
            return "Unable to compute camera placement."
        create_dialogue_camera(
            scene,
            rig_col,
            root,
            settings,
            shot_id,
            name,
            camera_location,
            target_location,
            lookat_obj,
        )
        return None

    if mode in {"OTS_A", "SINGLES"}:
        err = camera_and_target(a, b, "OTS_A", "CAM_OTS_A")
        if err:
            return err
    if mode in {"OTS_B", "SINGLES"}:
        err = camera_and_target(b, a, "OTS_B", "CAM_OTS_B")
        if err:
            return err
    if mode == "SINGLES":
        err = camera_and_target(a, a, "SINGLE_A", "CAM_SINGLE_A")
        if err:
            return err
        err = camera_and_target(b, b, "SINGLE_B", "CAM_SINGLE_B")
        if err:
            return err
    if mode == "TWO_SHOT":
        err = camera_and_target([a, b], [a, b], "TWO_SHOT", "CAM_TWO_SHOT")
        if err:
            return err

    return None
