bl_info = {
    "name": "Cam Rig Generator (Close/Med/Wide + LookAt)",
    "author": "ChatGPT",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Cam Rig",
    "description": "Creates 3 cameras (close/med/wide) that frame selection and track a LookAt empty.",
    "category": "Camera",
}

import bpy
from mathutils import Vector, Matrix
from math import atan, tan

TOOL_PROP = "cam_rig_tool"
COLLECTION_NAME = "CAM_RIG"
EMPTY_NAME = "EMPTY_LOOKAT"
CAM_CLOSE = "CAM_CLOSE"
CAM_MED = "CAM_MED"
CAM_WIDE = "CAM_WIDE"

def ensure_collection(scene, name=COLLECTION_NAME):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
    return col

def get_or_create_empty(scene, rig_col):
    empty = bpy.data.objects.get(EMPTY_NAME)
    if empty is None or empty.type != "EMPTY":
        empty = bpy.data.objects.new(EMPTY_NAME, None)
        empty.empty_display_type = "ARROWS"
        empty[TOOL_PROP] = True
        scene.collection.objects.link(empty)
    if empty.name not in rig_col.objects:
        rig_col.objects.link(empty)
    return empty

def get_or_create_camera(scene, rig_col, name):
    cam_obj = bpy.data.objects.get(name)
    if cam_obj is None or cam_obj.type != "CAMERA":
        cam_data = bpy.data.cameras.new(name=name)
        cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
        cam_obj[TOOL_PROP] = True
        scene.collection.objects.link(cam_obj)
    if cam_obj.name not in rig_col.objects:
        rig_col.objects.link(cam_obj)
    return cam_obj

def selection_world_bounds(context):
    objs = context.selected_objects
    if not objs:
        return None

    corners_world = []
    for ob in objs:
        if not hasattr(ob, "bound_box") or ob.bound_box is None:
            continue
        mw = ob.matrix_world
        for corner in ob.bound_box:
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
    radius = 0.5 * max(size.x, size.y, size.z)
    radius = max(radius, 0.05)

    return {"center": center, "radius": radius}

class CAMRIG_OT_create(bpy.types.Operator):
    bl_idname = "camrig.create"
    bl_label = "Create Cam Rig"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bounds = selection_world_bounds(context)
        if bounds is None:
            self.report({"ERROR"}, "Select at least one object.")
            return {"CANCELLED"}

        scene = context.scene
        rig_col = ensure_collection(scene)
        empty = get_or_create_empty(scene, rig_col)
        cam_close = get_or_create_camera(scene, rig_col, CAM_CLOSE)
        cam_med = get_or_create_camera(scene, rig_col, CAM_MED)
        cam_wide = get_or_create_camera(scene, rig_col, CAM_WIDE)

        center = bounds["center"]
        radius = bounds["radius"]

        empty.location = center

        forward = Vector((0.0, 1.0, 0.0))
        up = Vector((0.0, 0.0, 1.0))

        def position_camera(cam_obj, distance):
            cam_obj.location = center - forward * distance
            cam_obj.constraints.clear()
            con = cam_obj.constraints.new(type="TRACK_TO")
            con.target = empty
            con.track_axis = "TRACK_NEGATIVE_Z"
            con.up_axis = "UP_Y"

        position_camera(cam_close, radius * 1.5)
        position_camera(cam_med, radius * 2.5)
        position_camera(cam_wide, radius * 4.0)

        scene.camera = cam_med

        return {"FINISHED"}

class CAMRIG_PT_panel(bpy.types.Panel):
    bl_label = "Cam Rig Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam Rig"

    def draw(self, context):
        layout = self.layout
        layout.operator("camrig.create", icon="CAMERA_DATA")

classes = (CAMRIG_OT_create, CAMRIG_PT_panel)

# --- Numpad 0 Snap to Selected Camera ---

class CAMRIG_OT_view_selected_camera(bpy.types.Operator):
    bl_idname = "camrig.view_selected_camera"
    bl_label = "View Selected Camera"

    def execute(self, context):
        obj = context.view_layer.objects.active
        if obj and obj.type == "CAMERA":
            context.scene.camera = obj
        bpy.ops.view3d.view_camera()
        return {"FINISHED"}

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
    for c in classes:
        bpy.utils.register_class(c)
    bpy.utils.register_class(CAMRIG_OT_view_selected_camera)
    register_keymap()

def unregister():
    unregister_keymap()
    bpy.utils.unregister_class(CAMRIG_OT_view_selected_camera)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
