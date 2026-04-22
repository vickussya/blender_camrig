import bpy

from .camera_utils import AXIS_ITEMS, SHOT_ENUM_ITEMS, TURNTABLE_TYPES


def _camrig_update_shot_library_name(self, context):
    # Sync Shot Library item name -> camera object name (user-facing rename).
    if getattr(self, "get", None) and self.get("_camrig_renaming"):
        return
    if context is None or getattr(context, "screen", None) is None:
        return

    cam_name = (getattr(self, "camera_name", "") or "").strip()
    if not cam_name:
        return
    cam_obj = bpy.data.objects.get(cam_name)
    if cam_obj is None or cam_obj.type != "CAMERA":
        return

    desired = (getattr(self, "name", "") or "").strip()
    if not desired:
        if getattr(self, "get", None) is None:
            return
        self["_camrig_renaming"] = True
        try:
            self.name = cam_obj.name
            self.camera_name = cam_obj.name
        finally:
            if "_camrig_renaming" in self:
                del self["_camrig_renaming"]
        return

    if cam_obj.name == desired and self.camera_name == cam_obj.name:
        return

    if getattr(self, "get", None) is None:
        return
    self["_camrig_renaming"] = True
    try:
        cam_obj.name = desired
        final_name = cam_obj.name
        self.camera_name = final_name
        self.name = final_name
    finally:
        if "_camrig_renaming" in self:
            del self["_camrig_renaming"]


class CAMRIG_ShotLibraryItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", update=_camrig_update_shot_library_name)
    shot_id: bpy.props.EnumProperty(name="Shot Type", items=SHOT_ENUM_ITEMS)
    camera_name: bpy.props.StringProperty(name="Camera")
    location: bpy.props.FloatVectorProperty(name="Location", size=3, subtype="TRANSLATION")
    rotation: bpy.props.FloatVectorProperty(name="Rotation", size=3, subtype="EULER")
    lens: bpy.props.FloatProperty(name="Lens")
    target_name: bpy.props.StringProperty(name="Target")
    target_location: bpy.props.FloatVectorProperty(name="Target Location", size=3, subtype="TRANSLATION")
    axis: bpy.props.StringProperty(name="Axis")
    eye_level: bpy.props.BoolProperty(name="Eye Level")
    tracking_enabled: bpy.props.BoolProperty(name="Tracking")

    # Extended rig restore (v2): independent rig objects + animation data.
    library_version: bpy.props.IntProperty(name="Library Version", default=2)
    use_camera_circle_parent: bpy.props.BoolProperty(name="Use Camera Circle Parent", default=False)

    rig_collection_name: bpy.props.StringProperty(name="Rig Collection")
    root_name: bpy.props.StringProperty(name="Root")
    root_location: bpy.props.FloatVectorProperty(name="Root Location", size=3, subtype="TRANSLATION")
    root_rotation: bpy.props.FloatVectorProperty(name="Root Rotation", size=3, subtype="EULER")
    root_scale: bpy.props.FloatVectorProperty(name="Root Scale", size=3, subtype="XYZ", default=(1.0, 1.0, 1.0))

    lookat_name: bpy.props.StringProperty(name="LookAt")
    lookat_location: bpy.props.FloatVectorProperty(name="LookAt Location", size=3, subtype="TRANSLATION")
    lookat_rotation: bpy.props.FloatVectorProperty(name="LookAt Rotation", size=3, subtype="EULER")
    lookat_scale: bpy.props.FloatVectorProperty(name="LookAt Scale", size=3, subtype="XYZ", default=(1.0, 1.0, 1.0))

    control_name: bpy.props.StringProperty(name="Control")
    control_location: bpy.props.FloatVectorProperty(name="Control Location", size=3, subtype="TRANSLATION")
    control_rotation: bpy.props.FloatVectorProperty(name="Control Rotation", size=3, subtype="EULER")
    control_scale: bpy.props.FloatVectorProperty(name="Control Scale", size=3, subtype="XYZ", default=(1.0, 1.0, 1.0))

    camera_action: bpy.props.StringProperty(name="Camera Action")
    camera_data_action: bpy.props.StringProperty(name="Camera Data Action")
    root_action: bpy.props.StringProperty(name="Root Action")
    lookat_action: bpy.props.StringProperty(name="LookAt Action")
    control_action: bpy.props.StringProperty(name="Control Action")
    control_driver_expression: bpy.props.StringProperty(name="Control Driver Expression")


class CAMRIG_SuggestionItem(bpy.types.PropertyGroup):
    shot_id: bpy.props.StringProperty(name="Shot ID")
    label: bpy.props.StringProperty(name="Label")
    reason: bpy.props.StringProperty(name="Reason")


class CAMRIG_Settings(bpy.types.PropertyGroup):
    camera_name: bpy.props.StringProperty(
        name="Camera Name",
        description="Optional custom name for newly created shot cameras (leave empty to use defaults)",
        default="",
    )
    axis: bpy.props.EnumProperty(
        name="Axis",
        items=AXIS_ITEMS,
        description="Direction the camera approaches the subject from",
        default="-Y",
    )
    selected_shot: bpy.props.EnumProperty(
        name="Shot Type",
        items=SHOT_ENUM_ITEMS,
        description="Shot type to create when using Setup",
        default="MED_FULL",
    )
    eye_level: bpy.props.BoolProperty(
        name="Eye Level",
        description="Bias framing toward the subject's eye height",
        default=False,
    )
    tracking_enabled: bpy.props.BoolProperty(
        name="Tracking",
        description="Aim the camera at the subject or look-at target",
        default=True,
    )
    use_camera_circle_parent: bpy.props.BoolProperty(
        name="Use Camera Circle Parent",
        description="Add a visible circle empty as a camera parent for manual control",
        default=False,
    )
    look_at_target: bpy.props.PointerProperty(
        name="Look-at Target",
        description="Optional target object the camera should aim at",
        type=bpy.types.Object,
    )
    height_offset: bpy.props.FloatProperty(
        name="Height Offset",
        description="Additional height added to shot target points",
        default=0.0,
        step=1.0,
    )

    turntable_frames: bpy.props.IntProperty(
        name="Frames",
        description="Number of frames for the turntable animation",
        default=120,
        min=1,
    )
    turntable_type: bpy.props.EnumProperty(
        name="Rotation Type",
        items=TURNTABLE_TYPES,
        description="Rotate the camera around the subject",
        default="ROTATE_CAMERA",
    )

    orbit_step: bpy.props.FloatProperty(
        name="Orbit Step",
        description="Degrees to rotate per orbit step",
        default=10.0,
        min=1.0,
    )
    orbit_height_step: bpy.props.FloatProperty(
        name="Height Step",
        description="Vertical distance per orbit height step",
        default=0.2,
        min=0.01,
    )
    orbit_distance_step: bpy.props.FloatProperty(
        name="Distance Step",
        description="Distance change per orbit step",
        default=0.2,
        min=0.01,
    )
    auto_orbit_speed: bpy.props.FloatProperty(
        name="Auto Orbit Speed",
        description="Auto-orbit speed in degrees per frame",
        default=2.0,
        min=0.01,
    )

    shot_library: bpy.props.CollectionProperty(type=CAMRIG_ShotLibraryItem)
    shot_library_index: bpy.props.IntProperty(
        name="Shot Index",
        description="Active shot library index",
        default=0,
    )

    suggestions: bpy.props.CollectionProperty(type=CAMRIG_SuggestionItem)
    suggestion_index: bpy.props.IntProperty(
        name="Suggestion Index",
        description="Active suggestion index",
        default=0,
    )


CLASSES = (
    CAMRIG_ShotLibraryItem,
    CAMRIG_SuggestionItem,
    CAMRIG_Settings,
)
