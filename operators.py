import bpy

from .camera_utils import (
    SHOT_DEFS,
    SHOT_ENUM_ITEMS,
    create_shot_camera,
    create_turntable,
    analyze_scene_for_shots,
    get_settings,
    switch_active_camera,
)
from .shot_library import delete_shot, load_shot, save_shot
from .camera_utils import (
    move_orbit_left,
    move_orbit_right,
    raise_camera_orbit,
    lower_camera_orbit,
    move_orbit_closer,
    move_orbit_farther,
    start_auto_orbit,
    stop_auto_orbit,
)


class CAMRIG_OT_create_rig(bpy.types.Operator):
    bl_idname = "camrig.create_rig"
    bl_label = "Create/Update Selected Shot"
    bl_description = "Create the base rig and only the currently selected shot camera"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        settings = get_settings(context)
        cam_obj, err = create_shot_camera(context, settings.selected_shot, index=0)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        if cam_obj:
            context.scene.camera = cam_obj
        self.report({"INFO"}, "Rig created for selected shot.")
        return {"FINISHED"}


class CAMRIG_OT_create_shot(bpy.types.Operator):
    bl_idname = "camrig.create_shot"
    bl_label = "Create Shot"
    bl_description = "Create the selected shot type camera and set it active"
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
    bl_description = "Switch the scene camera to the chosen shot"

    shot_id: bpy.props.EnumProperty(items=SHOT_ENUM_ITEMS)

    def execute(self, context):
        if not switch_active_camera(context, self.shot_id):
            self.report({"WARNING"}, "Shot camera not found. Create the rig first.")
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_view_selected_camera(bpy.types.Operator):
    bl_idname = "camrig.view_selected_camera"
    bl_label = "View Selected Camera"
    bl_description = "Set the active camera to the selected camera and view through it"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if obj and obj.type == "CAMERA":
            context.scene.camera = obj
        bpy.ops.view3d.view_camera()
        return {"FINISHED"}


class CAMRIG_OT_turntable(bpy.types.Operator):
    bl_idname = "camrig.turntable"
    bl_label = "Create Turntable"
    bl_description = "Create a turntable animation based on the current settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        scene = context.scene
        err = create_turntable(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        end = scene.frame_start + max(settings.turntable_frames, 1)
        self.report({"INFO"}, f"Turntable animation created from frame {scene.frame_start} to {end}.")
        return {"FINISHED"}


class CAMRIG_OT_orbit_left(bpy.types.Operator):
    bl_idname = "camrig.orbit_left"
    bl_label = "Orbit Left"
    bl_description = "Move the orbit camera counterclockwise around the subject"

    def execute(self, context):
        err = move_orbit_left(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_orbit_right(bpy.types.Operator):
    bl_idname = "camrig.orbit_right"
    bl_label = "Orbit Right"
    bl_description = "Move the orbit camera clockwise around the subject"

    def execute(self, context):
        err = move_orbit_right(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_raise_camera(bpy.types.Operator):
    bl_idname = "camrig.raise_camera"
    bl_label = "Raise Camera"
    bl_description = "Raise the orbit camera upward"

    def execute(self, context):
        err = raise_camera_orbit(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_lower_camera(bpy.types.Operator):
    bl_idname = "camrig.lower_camera"
    bl_label = "Lower Camera"
    bl_description = "Lower the orbit camera downward"

    def execute(self, context):
        err = lower_camera_orbit(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_move_closer(bpy.types.Operator):
    bl_idname = "camrig.move_closer"
    bl_label = "Move Closer"
    bl_description = "Move the orbit camera closer to the subject"

    def execute(self, context):
        err = move_orbit_closer(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_move_farther(bpy.types.Operator):
    bl_idname = "camrig.move_farther"
    bl_label = "Move Farther"
    bl_description = "Move the orbit camera farther from the subject"

    def execute(self, context):
        err = move_orbit_farther(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_start_auto_orbit(bpy.types.Operator):
    bl_idname = "camrig.start_auto_orbit"
    bl_label = "Start Auto Orbit"
    bl_description = "Start automated orbit motion for the current orbit mode"

    def execute(self, context):
        err = start_auto_orbit(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_stop_auto_orbit(bpy.types.Operator):
    bl_idname = "camrig.stop_auto_orbit"
    bl_label = "Stop Auto Orbit"
    bl_description = "Stop automated orbit motion"

    def execute(self, context):
        err = stop_auto_orbit(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_analyze_scene(bpy.types.Operator):
    bl_idname = "camrig.analyze_scene"
    bl_label = "Analyze Scene"
    bl_description = "Analyze the scene and suggest useful shot types"

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
    bl_description = "Create the currently selected suggestion as a camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        if not settings.suggestions:
            self.report({"WARNING"}, "No suggestions available.")
            return {"CANCELLED"}
        idx = settings.suggestion_index
        item = settings.suggestions[idx]
        cam_obj, err = create_shot_camera(context, item.shot_id, index=0)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        context.scene.camera = cam_obj
        return {"FINISHED"}


class CAMRIG_OT_generate_coverage(bpy.types.Operator):
    bl_idname = "camrig.generate_coverage"
    bl_label = "Generate Coverage Set"
    bl_description = "Create cameras for all current suggestions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        if not settings.suggestions:
            self.report({"WARNING"}, "No suggestions available.")
            return {"CANCELLED"}
        for item in settings.suggestions:
            create_shot_camera(context, item.shot_id, index=0)
        return {"FINISHED"}


class CAMRIG_OT_shot_save(bpy.types.Operator):
    bl_idname = "camrig.shot_save"
    bl_label = "Save Shot"
    bl_description = "Save the active camera to the shot library"

    def execute(self, context):
        err = save_shot(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Shot saved.")
        return {"FINISHED"}


class CAMRIG_OT_shot_load(bpy.types.Operator):
    bl_idname = "camrig.shot_load"
    bl_label = "Load Shot"
    bl_description = "Load the selected shot from the library"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        err = load_shot(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_shot_delete(bpy.types.Operator):
    bl_idname = "camrig.shot_delete"
    bl_label = "Delete Shot"
    bl_description = "Delete the selected shot from the library"

    def execute(self, context):
        err = delete_shot(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


CLASSES = (
    CAMRIG_OT_create_rig,
    CAMRIG_OT_create_shot,
    CAMRIG_OT_set_active,
    CAMRIG_OT_view_selected_camera,
    CAMRIG_OT_turntable,
    CAMRIG_OT_analyze_scene,
    CAMRIG_OT_generate_suggestion,
    CAMRIG_OT_generate_coverage,
    CAMRIG_OT_shot_save,
    CAMRIG_OT_shot_load,
    CAMRIG_OT_shot_delete,
    CAMRIG_OT_orbit_left,
    CAMRIG_OT_orbit_right,
    CAMRIG_OT_raise_camera,
    CAMRIG_OT_lower_camera,
    CAMRIG_OT_move_closer,
    CAMRIG_OT_move_farther,
    CAMRIG_OT_start_auto_orbit,
    CAMRIG_OT_stop_auto_orbit,
)
