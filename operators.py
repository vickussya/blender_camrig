import bpy

from .camera_utils import (
    SHOT_DEFS,
    SHOT_ENUM_ITEMS,
    create_shot_camera,
    create_shot_set,
    create_turntable,
    apply_composition_to_active,
    analyze_scene_for_shots,
    get_settings,
    switch_active_camera,
)
from .dialogue import create_dialogue_setup
from .transitions import create_transition
from .shot_library import delete_shot, load_shot, save_shot


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
        err = save_shot(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Shot saved.")
        return {"FINISHED"}


class CAMRIG_OT_shot_load(bpy.types.Operator):
    bl_idname = "camrig.shot_load"
    bl_label = "Load Shot"
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

    def execute(self, context):
        err = delete_shot(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
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


CLASSES = (
    CAMRIG_OT_create_rig,
    CAMRIG_OT_create_shot,
    CAMRIG_OT_set_active,
    CAMRIG_OT_view_selected_camera,
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
    CAMRIG_OT_dialogue,
)
