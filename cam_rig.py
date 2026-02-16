import bpy
from mathutils import Vector

TOOL_PROP = "cam_rig_tool"
SHOT_PROP = "cam_rig_shot"
TARGET_PROP = "cam_rig_target"
COLLECTION_NAME = "CAM_RIG"
EMPTY_NAME = "EMPTY_LOOKAT"

SHOT_DEFS = (
    {"id": "ECU", "name": "CAM_ECU", "target_factor": 0.92, "lens": 85.0},
    {"id": "CU", "name": "CAM_CU_HEAD", "target_factor": 0.92, "lens": 70.0},
    {"id": "MED_WAIST", "name": "CAM_MED_WAIST", "target_factor": 0.55, "lens": 50.0},
    {"id": "MED_FULL", "name": "CAM_MED_FULL", "target_factor": 0.70, "lens": 40.0},
    {"id": "FULL", "name": "CAM_FULL_BODY", "target_factor": "CENTER", "lens": 35.0},
    {"id": "WIDE", "name": "CAM_WIDE_EST", "target_factor": "CENTER", "lens": 24.0},
)


def ensure_collection(scene, name=COLLECTION_NAME):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
    return col


def _find_tagged_object(obj_type, name=None, shot_id=None):
    for ob in bpy.data.objects:
        if not ob.get(TOOL_PROP):
            continue
        if ob.type != obj_type:
            continue
        if name and ob.name == name:
            return ob
        if shot_id and ob.get(SHOT_PROP) == shot_id:
            return ob
    return None


def get_or_create_empty(scene, rig_col):
    empty = _find_tagged_object("EMPTY", name=EMPTY_NAME)
    if empty is None:
        empty = bpy.data.objects.new(EMPTY_NAME, None)
        empty.empty_display_type = "ARROWS"
        empty[TOOL_PROP] = True
        scene.collection.objects.link(empty)
    if empty.name not in rig_col.objects:
        rig_col.objects.link(empty)
    return empty


def get_or_create_camera(scene, rig_col, name, shot_id):
    cam_obj = _find_tagged_object("CAMERA", shot_id=shot_id)
    if cam_obj is None:
        cam_data = bpy.data.cameras.new(name=name)
        cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
        cam_obj[TOOL_PROP] = True
        cam_obj[SHOT_PROP] = shot_id
        scene.collection.objects.link(cam_obj)
    if cam_obj.name not in rig_col.objects:
        rig_col.objects.link(cam_obj)
    return cam_obj


def selection_world_bounds(context):
    objs = context.selected_objects
    if not objs:
        return None

    depsgraph = context.evaluated_depsgraph_get()
    corners_world = []
    for ob in objs:
        ob_eval = ob.evaluated_get(depsgraph)
        if not hasattr(ob_eval, "bound_box") or ob_eval.bound_box is None:
            continue
        mw = ob_eval.matrix_world
        for corner in ob_eval.bound_box:
            corners_world.append(mw @ Vector(corner))

    if not corners_world:
        return None

    min_v = Vector((min(v.x for v in corners_world),
                    min(v.y for v in corners_world),
                    min(v.z for v in corners_world)))
    max_v = Vector((max(v.x for v in corners_world),
                    max(v.y for v in corners_world),
                    max(v.z for v in corners_world)))

    center = (min_v + max_v) * 0.5
    size = (max_v - min_v)
    height = size.z
    max_dim = max(size.x, size.y, size.z)

    return {"min": min_v, "max": max_v, "center": center, "size": size, "height": height, "max_dim": max_dim}


def axis_vector(axis):
    if axis == "+X":
        return Vector((1.0, 0.0, 0.0))
    if axis == "-X":
        return Vector((-1.0, 0.0, 0.0))
    if axis == "+Y":
        return Vector((0.0, 1.0, 0.0))
    if axis == "-Y":
        return Vector((0.0, -1.0, 0.0))
    if axis == "+Z":
        return Vector((0.0, 0.0, 1.0))
    return Vector((0.0, 0.0, -1.0))


def ensure_track_to(cam_obj, empty):
    for con in [c for c in cam_obj.constraints if c.type == "TRACK_TO"]:
        cam_obj.constraints.remove(con)
    con = cam_obj.constraints.new(type="TRACK_TO")
    con.target = empty
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"


class CAMRIG_OT_create(bpy.types.Operator):
    bl_idname = "camrig.create"
    bl_label = "Create/Update Shot Cameras"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bounds = selection_world_bounds(context)
        if bounds is None:
            self.report({"ERROR"}, "Select at least one object.")
            return {"CANCELLED"}

        scene = context.scene
        rig_col = ensure_collection(scene)
        empty = get_or_create_empty(scene, rig_col)

        min_v = bounds["min"]
        center = bounds["center"]
        height = bounds["height"]
        max_dim = bounds["max_dim"]

        base_distance = max(max_dim * 2.0, 1.0)
        spacing = 0.5 * max_dim

        axis = axis_vector(scene.camrig_axis)
        height_offset = scene.camrig_height_offset

        for index, shot in enumerate(SHOT_DEFS):
            cam_obj = get_or_create_camera(scene, rig_col, shot["name"], shot["id"])

            if shot["target_factor"] == "CENTER":
                target = Vector((center.x, center.y, center.z))
            else:
                target_z = min_v.z + height * shot["target_factor"]
                target = Vector((center.x, center.y, target_z))

            target.z += height_offset

            distance = base_distance + spacing * index
            cam_obj.location = target + axis * distance
            cam_obj.data.lens = shot["lens"]
            cam_obj[TARGET_PROP] = (target.x, target.y, target.z)
            ensure_track_to(cam_obj, empty)

        empty.location = center
        scene.camera = _find_tagged_object("CAMERA", shot_id="MED_FULL") or scene.camera

        return {"FINISHED"}


class CAMRIG_OT_set_active(bpy.types.Operator):
    bl_idname = "camrig.set_active"
    bl_label = "Set Active Shot"

    shot_id: bpy.props.StringProperty()

    def execute(self, context):
        cam_obj = _find_tagged_object("CAMERA", shot_id=self.shot_id)
        if cam_obj is None:
            self.report({"ERROR"}, "Shot camera not found. Create the rig first.")
            return {"CANCELLED"}

        scene = context.scene
        scene.camera = cam_obj

        empty = _find_tagged_object("EMPTY", name=EMPTY_NAME)
        if empty and cam_obj.get(TARGET_PROP):
            target = cam_obj.get(TARGET_PROP)
            empty.location = Vector((target[0], target[1], target[2]))

        return {"FINISHED"}


class CAMRIG_PT_panel(bpy.types.Panel):
    bl_label = "Cam Rig Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="Shot Cameras")
        box.prop(scene, "camrig_axis", text="Axis")
        box.prop(scene, "camrig_height_offset", text="Height Offset")
        box.operator("camrig.create", text="Create/Update Shot Cameras", icon="CAMERA_DATA")

        box = layout.box()
        box.label(text="Set Active")
        row = box.row(align=True)
        row.operator("camrig.set_active", text="ECU").shot_id = "ECU"
        row.operator("camrig.set_active", text="CU").shot_id = "CU"
        row = box.row(align=True)
        row.operator("camrig.set_active", text="MED_WAIST").shot_id = "MED_WAIST"
        row.operator("camrig.set_active", text="MED_FULL").shot_id = "MED_FULL"
        row = box.row(align=True)
        row.operator("camrig.set_active", text="FULL").shot_id = "FULL"
        row.operator("camrig.set_active", text="WIDE").shot_id = "WIDE"


class CAMRIG_OT_view_selected_camera(bpy.types.Operator):
    bl_idname = "camrig.view_selected_camera"
    bl_label = "View Selected Camera"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if obj and obj.type == "CAMERA":
            context.scene.camera = obj
        bpy.ops.view3d.view_camera()
        return {"FINISHED"}


classes = (
    CAMRIG_OT_create,
    CAMRIG_OT_set_active,
    CAMRIG_PT_panel,
    CAMRIG_OT_view_selected_camera,
)


addon_keymaps = []


def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new("camrig.view_selected_camera", type="NUMPAD_0", value="PRESS")
        addon_keymaps.append((km, kmi))


def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    bpy.types.Scene.camrig_axis = bpy.props.EnumProperty(
        name="Axis",
        items=[
            ("+X", "+X", "Place cameras along +X"),
            ("-X", "-X", "Place cameras along -X"),
            ("+Y", "+Y", "Place cameras along +Y"),
            ("-Y", "-Y", "Place cameras along -Y"),
            ("+Z", "+Z", "Place cameras along +Z"),
            ("-Z", "-Z", "Place cameras along -Z"),
        ],
        default="-Y",
    )
    bpy.types.Scene.camrig_height_offset = bpy.props.FloatProperty(
        name="Height Offset",
        description="Additional height added to shot target points",
        default=0.0,
        step=1.0,
    )

    for c in classes:
        bpy.utils.register_class(c)
    register_keymap()


def unregister():
    unregister_keymap()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.camrig_height_offset
    del bpy.types.Scene.camrig_axis
