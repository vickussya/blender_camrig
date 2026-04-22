# Blender CamRig — Cinematic Camera Toolkit

Create cinematic shots in seconds, switch between shot sizes instantly, and keep cameras aimed correctly.
Save and reload shots anytime for fast iteration and previs.

## Blender Version
Compatible with Blender 3.0+.

## Features

### Shot Creation
Create and update cinematic shots based on selected objects.

<img width="371" height="346" alt="shot-creation png" src="https://github.com/user-attachments/assets/54ca38b2-ca38-453c-9cc1-8015944c7d12" />

### Switch Shot
Instantly switch between predefined shot sizes.

<img width="353" height="99" alt="switch-shot png" src="https://github.com/user-attachments/assets/05cd35b2-f92f-485e-8904-0f2290509c0d" />

### Turntable Animation
Create automatic camera rotation around the subject for presentation shots.

<img width="364" height="160" alt="turnable-animation png" src="https://github.com/user-attachments/assets/b4409842-1941-4e5f-9abd-bcf4fc012b91" />

### Shot Library
Save shots and recreate them anytime — even after deleting the original camera.

<img width="358" height="285" alt="shot-library png" src="https://github.com/user-attachments/assets/d640070f-7b49-45c5-8935-121aa3e5b6ee" />

### Circle Controls
Manually orbit, adjust height, and control camera distance around the subject.

<img width="358" height="335" alt="circle-controls png" src="https://github.com/user-attachments/assets/956bfa3b-40e2-4839-bd5a-6961c86b3861" />

### Intelligent Framing
Analyze the scene and get automatic cinematic shot suggestions.

<img width="367" height="319" alt="intelligent-framing png" src="https://github.com/user-attachments/assets/5f688dfc-4e84-424c-83b2-1b5d6c0cda6e" />

## Why Use This Addon
- Fast shot creation
- Consistent cinematic framing
- Easy iteration
- Reusable shot library

## Current Workflow (UI)
All tools live in `View3D > Sidebar (N) > Cam Rig`.

### Shot Creation
1) Select one or more subject objects.
2) In **Shot Creation**, choose **Shot Type** (dropdown).
3) Set options as needed:
   - **Axis** (camera approach direction)
   - **Eye Level** (bias framing toward eye height)
   - **Tracking** (aim camera at the subject / look-at target)
   - **Use Camera Circle Parent** (adds a visible circle control parent)
   - **Look-at Target** (optional target object to aim at; when set, it’s respected and not moved)
   - **Height Offset** (adds vertical offset to the computed target)
4) Click **Create/Update Selected Shot**.

Notes:
- Each generated shot creates its own independent rig container (camera + root + look-at + optional control empty), so shots stay editable and independent.

### Switch Shot
Use **Switch Shot** to quickly set the active scene camera to an existing shot camera (no rig rebuild).

### Turntable Animation
Use **Turntable Animation** to create an automatic rotation shot around the selected subject.

### Shot Library
- **Save Shot** stores the full shot state needed to restore it later:
  - camera transform + lens
  - root + look-at transforms
  - animation actions (camera/root/look-at/control when present)
  - orbit/control driver expression (when used)
- **Load Shot** restores the shot’s animated behavior (not just a static position).
- Rename a library entry in **Shot Library** to rename/sync the linked camera object name in the Outliner (Blender-safe unique naming is applied automatically).

### Circle Controls
When **Use Camera Circle Parent** is enabled, use **Circle Controls** to orbit and adjust height/distance around the subject.

## Limitations
- Turntable shots cannot be saved in Shot Library (by design)
- Curve path / advanced presets planned for future versions

## Installation
1) Download the ZIP.
2) In Blender, go to `Edit -> Preferences -> Add-ons`.
3) Click **Install...** and select the ZIP.
4) Enable the add-on by ticking the checkbox.
5) Requires Blender 3.0+.

## Roadmap
- More presets
- Advanced camera paths
- Improved composition tools

## License
This add-on is licensed under the GPL-3.0. See `LICENSE` for details.
