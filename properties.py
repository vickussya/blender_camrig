import bpy

from .camera_utils import (
    AXIS_ITEMS,
    PRESET_ITEMS,
    SHOT_ENUM_ITEMS,
    THIRDS_H_ITEMS,
    THIRDS_V_ITEMS,
    TRANSITION_TYPES,
    TURNTABLE_TYPES,
)


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
    use_camera_control_empty: bpy.props.BoolProperty(
        name="Use Control Empty",
        description="Parent cameras to a circle empty for easier manual adjustments",
        default=False,
    )
    use_camera_circle_parent: bpy.props.BoolProperty(
        name="Use Camera Circle Parent",
        description="Add a visible circle empty as a camera parent for manual control",
        default=False,
    )
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


CLASSES = (
    CAMRIG_ShotLibraryItem,
    CAMRIG_SuggestionItem,
    CAMRIG_Settings,
)
