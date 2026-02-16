# Cam Rig Generator

Cam Rig Generator is a Blender add-on for quick, cinematic camera blocking. It builds a set of shot cameras around your selection and keeps them aimed at a LookAt target, so animators and previs artists can iterate on framing fast.

## Features
- Shot camera set: Extreme Close-Up, Close-Up (Head), Medium (Waist), Medium Full, Full Body, Wide Establishing
- Auto subject detection (character height) with proportion-based framing
- Axis selection (+X, -X, +Y, -Y, +Z, -Z) for where cameras spawn
- Look-at target Empty (EMPTY_LOOKAT) with tracking constraints
- CAM_RIG collection organization
- Quick Shot Switching buttons for the shot cameras
- Numpad 0: snap view to selected camera (and set it as scene camera)

## Planned (not in the current build)
- Eye-level positioning option toggle
- Dialogue Mode (2 characters -> OTS A/B, Singles A/B, Two-shot)
- Turntable Mode (camera/path or rotating empty, configurable frames)
- Presets (Cinematic, Animation Blocking, etc.)
- Shot Library (save/recall named shots)
- Extra Quick Switch buttons (Close/Med/Wide group)
- Additional N-sidebar panels (Setup / Shot Types / Quick Switch / Dialogue / Turntable / Presets / Height & Composition / Shot Library)

## Installation
1) In Blender, go to `Edit -> Preferences -> Add-ons`.
2) Click **Install...** and select the `.py` or `.zip` file.
3) Enable the add-on by ticking the checkbox.

## Where to find it
- 3D Viewport -> Sidebar (N) -> **Cam Rig** tab -> **Cam Rig Generator**

## Quick Start
1) Select a character/object.
2) Choose axis and height offset.
3) Click **Create/Update Shot Cameras**.
4) Use the Quick Switch buttons to set the active camera.
5) Select any camera and press Numpad 0 to snap the view.

## Panels (N-sidebar)
- **Cam Rig Generator**: Create/update shots, choose axis/height offset, and switch active cameras.

## Naming and Non-Destructive Behavior
- Cameras are named like: `CAM_ECU`, `CAM_CU_HEAD`, `CAM_MED_WAIST`, `CAM_MED_FULL`, `CAM_FULL_BODY`, `CAM_WIDE_EST`
- LookAt target is named: `EMPTY_LOOKAT`
- All add-on objects are placed in: `CAM_RIG`
- The add-on does not modify or delete user objects/cameras unless they were created by the add-on (tagged with a custom property).

## Troubleshooting
- **Cameras spawn inside object** -> Increase distance multiplier (future option) or apply scale: `Ctrl+A` -> **Scale**.
- **Numpad 0 doesn't snap** -> Check keymap conflicts or enable **Emulate Numpad** for laptops.
- **Nothing happens** -> Make sure at least one object is selected.

## Roadmap / Changelog (Optional)
- **Version 2.0**: Axis selection + shot types + dialogue + turntable + shot library systems (planned).
