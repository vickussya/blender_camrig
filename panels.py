import bpy

from .camera_utils import get_settings


class CAMRIG_UL_shot_library(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name or "Shot", icon="CAMERA_DATA")


class CAMRIG_UL_suggestions(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        label = f"{item.label} - {item.reason}" if item.reason else item.label
        layout.label(text=label, icon="INFO")


class CAMRIG_PT_setup(bpy.types.Panel):
    bl_label = "Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.operator("camrig.create_rig", icon="CAMERA_DATA")
        layout.prop(settings, "selected_shot")
        layout.prop(settings, "axis")
        layout.prop(settings, "eye_level")
        layout.prop(settings, "tracking_enabled")
        layout.prop(settings, "use_camera_circle_parent")
        layout.prop(settings, "use_curve_path")
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


class CAMRIG_PT_orbit_controls(bpy.types.Panel):
    bl_label = "Circle / Path Controls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.prop(settings, "use_camera_circle_parent")
        layout.prop(settings, "use_curve_path")
        controls = layout.column()
        controls.enabled = settings.use_camera_circle_parent or settings.use_curve_path
        controls.prop(settings, "orbit_step")
        controls.prop(settings, "orbit_height_step")
        controls.prop(settings, "orbit_distance_step")
        controls.prop(settings, "auto_orbit_speed")
        row = controls.row(align=True)
        row.operator("camrig.orbit_left", text="Orbit Left")
        row.operator("camrig.orbit_right", text="Orbit Right")
        row = controls.row(align=True)
        row.operator("camrig.raise_camera", text="Raise Camera")
        row.operator("camrig.lower_camera", text="Lower Camera")
        row = controls.row(align=True)
        row.operator("camrig.move_closer", text="Move Closer")
        row.operator("camrig.move_farther", text="Move Farther")
        row = controls.row(align=True)
        row.operator("camrig.start_auto_orbit", text="Start Auto Orbit")
        row.operator("camrig.stop_auto_orbit", text="Stop Auto Orbit")


class CAMRIG_PT_presets(bpy.types.Panel):
    bl_label = "Cinematic Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        settings = get_settings(context)
        layout = self.layout
        layout.prop(settings, "preset")
        layout.prop(settings, "preset_mode")
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


CLASSES = (
    CAMRIG_UL_shot_library,
    CAMRIG_UL_suggestions,
    CAMRIG_PT_setup,
    CAMRIG_PT_shot_types,
    CAMRIG_PT_quick_switch,
    CAMRIG_PT_dialogue,
    CAMRIG_PT_turntable,
    CAMRIG_PT_shot_library,
    CAMRIG_PT_composition,
    CAMRIG_PT_orbit_controls,
    CAMRIG_PT_presets,
    CAMRIG_PT_intelligent_framing,
)
