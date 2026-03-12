from .camera_utils import _find_tagged_object, get_settings


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
