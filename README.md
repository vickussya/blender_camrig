# Cam Rig Generator

Cam Rig Generator is a Blender add-on for cinematic camera blocking and previs. It builds shot camera sets around your selection, keeps them aimed at a LookAt target, and adds dialogue, turntable, composition, and orbit tools.

## Features
- Shot camera set: Extreme Close-Up, Close-Up, Medium, Medium Full, Full Body, Wide
- Rig tracking: rig root follows a selected subject with a toggle
- Look-at target: auto LookAt empty or user-defined target object
- Rule of Thirds composition tool with horizontal/vertical placement
- Orbit controls: circle empty or curve path helpers
- Dialogue setup: OTS A/B, Singles A/B, Two Shot
- Turntable creation (rotate camera or subject)
- Cinematic presets: Kubrick framing, Wes Anderson symmetry, Hollywood dialogue
- Intelligent framing analysis with shot suggestions
- Shot library saved in the .blend file
- CAM_RIG collection organization + Numpad 0 quick view

## Installation
1) In Blender, go to `Edit -> Preferences -> Add-ons`.
2) Click **Install...** and select the `.py` or `.zip` file.
3) Enable the add-on by ticking the checkbox.

## Where to find it
- 3D Viewport -> Sidebar (N) -> **Cam Rig** tab

## Quick Start
1) Select a character/object.
2) Use **Setup** to set axis, eye level, tracking, and target.
3) Click **Create/Update Shot Cameras**.
4) Use **Shot Types** or **Quick Switch** to change cameras.
5) Use **Composition** for Rule of Thirds framing.

## Panels (N-sidebar)
- **Setup**: Create rig, axis selection, eye level toggle, tracking, look-at target
- **Shot Types**: Create specific shot types
- **Quick Switch**: CU / Medium / Wide switches
- **Create Dialogue Setup**: OTS A/B, Singles, Two Shot
- **Turntable**: Create turntable animation and set rotation type
- **Shot Library**: Save / Load / Delete saved shots
- **Composition**: Rule of Thirds toggle and placement
- **Circle / Path Controls**: orbit helpers and controls
- **Cinematic Presets**: Kubrick / Wes Anderson / Hollywood dialogue
- **Intelligent Framing**: Analyze scene and generate suggested shots

## Naming and Non-Destructive Behavior
- Cameras are named like: `CAM_ECU`, `CAM_CU_HEAD`, `CAM_MED_WAIST`, `CAM_MED_FULL`, `CAM_FULL_BODY`, `CAM_WIDE_EST`
- Dialogue cameras: `CAM_OTS_A`, `CAM_OTS_B`, `CAM_SINGLE_A`, `CAM_SINGLE_B`, `CAM_TWO_SHOT`
- LookAt target: `CAM_LOOKAT`
- Rig root: `CAM_RIG_ROOT`
- All add-on objects are placed in: `CAM_RIG`
- The add-on avoids touching user cameras unless they are created by the add-on

## Notes
- Tracking uses a Copy Location constraint on `CAM_RIG_ROOT`.
- Rule of Thirds offsets the look-at target, not the subject.
- Shot library data is stored in the scene and saved with the .blend file.

## Troubleshooting
- **Cameras spawn inside object** -> Apply scale (`Ctrl+A` -> Scale) or increase distance by moving the subject scale.
- **Numpad 0 doesn't snap** -> Check keymap conflicts or enable **Emulate Numpad**.
- **Nothing happens** -> Make sure at least one object is selected and you are in Object Mode.

## License
This add-on is licensed under the GPL-3.0. See `LICENSE` for details.
