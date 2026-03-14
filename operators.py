import bpy

from .camera_utils import (
    SHOT_DEFS,
    SHOT_ENUM_ITEMS,
    create_shot_camera,
    create_turntable,
    apply_composition_to_active,
    analyze_scene_for_shots,
    compute_camera_transform,
    get_active_camera,
    get_settings,
    ensure_lookat,
    ensure_collection,
    ensure_root,
    switch_active_camera,
)
from .dialogue import create_dialogue_setup
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
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        settings = get_settings(context)
        err = create_shot_camera(context, settings.selected_shot, index=0)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Rig created for selected shot.")
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
        if settings.preset_mode == "OVERRIDE":
            cam_obj = get_active_camera(context)
            if cam_obj is None:
                return "No active camera."
            subjects = [ob for ob in context.selected_objects if ob.type in {"MESH", "ARMATURE", "EMPTY"}]
            if not subjects:
                return "Select a subject."
            cam_loc, target, lens = compute_camera_transform(
                context,
                subjects,
                cam_obj.get("cam_rig_shot", settings.selected_shot),
                settings.axis,
                settings.eye_level,
            )
            if cam_loc is None or target is None:
                return "Unable to compute preset framing."
            cam_obj.location = cam_loc
            if lens:
                cam_obj.data.lens = lens
            rig_col = ensure_collection(context.scene)
            root = ensure_root(context.scene, rig_col)
            lookat_obj, _ = ensure_lookat(context.scene, rig_col, root, settings)
            lookat_obj.location = target
            return None
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


class CAMRIG_OT_orbit_left(bpy.types.Operator):
    bl_idname = "camrig.orbit_left"
    bl_label = "Orbit Left"

    def execute(self, context):
        err = move_orbit_left(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_orbit_right(bpy.types.Operator):
    bl_idname = "camrig.orbit_right"
    bl_label = "Orbit Right"

    def execute(self, context):
        err = move_orbit_right(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_raise_camera(bpy.types.Operator):
    bl_idname = "camrig.raise_camera"
    bl_label = "Raise Camera"

    def execute(self, context):
        err = raise_camera_orbit(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_lower_camera(bpy.types.Operator):
    bl_idname = "camrig.lower_camera"
    bl_label = "Lower Camera"

    def execute(self, context):
        err = lower_camera_orbit(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_move_closer(bpy.types.Operator):
    bl_idname = "camrig.move_closer"
    bl_label = "Move Closer"

    def execute(self, context):
        err = move_orbit_closer(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_move_farther(bpy.types.Operator):
    bl_idname = "camrig.move_farther"
    bl_label = "Move Farther"

    def execute(self, context):
        err = move_orbit_farther(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_start_auto_orbit(bpy.types.Operator):
    bl_idname = "camrig.start_auto_orbit"
    bl_label = "Start Auto Orbit"

    def execute(self, context):
        err = start_auto_orbit(context)
        if err:
            self.report({"WARNING"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class CAMRIG_OT_stop_auto_orbit(bpy.types.Operator):
    bl_idname = "camrig.stop_auto_orbit"
    bl_label = "Stop Auto Orbit"

    def execute(self, context):
        err = stop_auto_orbit(context)
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
    CAMRIG_OT_analyze_scene,
    CAMRIG_OT_generate_suggestion,
    CAMRIG_OT_generate_coverage,
    CAMRIG_OT_shot_save,
    CAMRIG_OT_shot_load,
    CAMRIG_OT_shot_delete,
    CAMRIG_OT_dialogue,
    CAMRIG_OT_orbit_left,
    CAMRIG_OT_orbit_right,
    CAMRIG_OT_raise_camera,
    CAMRIG_OT_lower_camera,
    CAMRIG_OT_move_closer,
    CAMRIG_OT_move_farther,
    CAMRIG_OT_start_auto_orbit,
    CAMRIG_OT_stop_auto_orbit,
)
