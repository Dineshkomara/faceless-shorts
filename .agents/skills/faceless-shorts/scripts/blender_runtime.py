#!/usr/bin/env python3
"""Blender 5.2 EEVEE Next 3D Cinematic Animation Runtime.

Executed inside Blender headless mode:
  blender -b -P blender_runtime.py -- --spec <spec.json> --output-dir <frames_dir> [--samples 8] [--fps 30]

Constructs 9:16 vertical 3D scenes, stylized rigged characters (Kings, Pandits, Betal, Science props),
3-point studio lighting, cinematic camera choreography with Depth of Field,
and renders using Apple Silicon Metal GPU acceleration.
"""

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Euler


def parse_args():
    parser = argparse.ArgumentParser(description="Blender 3D Shorts Runtime")
    parser.add_argument("--spec", required=True, help="Path to production spec JSON")
    parser.add_argument("--output-dir", required=True, help="Directory to save rendered PNG frames")
    parser.add_argument("--samples", type=int, default=8, help="EEVEE Next TAA samples (8-16)")
    parser.add_argument("--fps", type=int, default=30, help="Framerate")
    parser.add_argument("--start-frame", type=int, default=None)
    parser.add_argument("--end-frame", type=int, default=None)

    # Extract args after '--'
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = []
    return parser.parse_args(argv)


def clear_scene():
    """Wipes all default objects, collections, and orphan datablocks."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures,
                  bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
        for item in list(block):
            block.remove(item)


def hex_to_rgba(hex_str, alpha=1.0):
    """Converts #RRGGBB hex string to 0.0-1.0 linear RGBA tuple."""
    hex_str = str(hex_str).lstrip('#')
    if len(hex_str) == 6:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        # Convert sRGB to linear approx for Blender
        return (r ** 2.2, g ** 2.2, b ** 2.2, alpha)
    return (0.8, 0.8, 0.8, alpha)


def setup_render_settings(width=1080, height=1920, fps=30, samples=8):
    """Configures Blender 5.2 EEVEE Next engine for ultra-fast Metal GPU rendering."""
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.fps = fps
    scene.render.engine = 'BLENDER_EEVEE'

    # EEVEE Next optimizations (Metal GPU accelerated)
    if hasattr(scene, 'eevee'):
        scene.eevee.taa_render_samples = max(4, min(32, samples))
        if hasattr(scene.eevee, 'shadow_ray_count'):
            scene.eevee.shadow_ray_count = 2
        if hasattr(scene.eevee, 'fast_gi_ray_count'):
            scene.eevee.fast_gi_ray_count = 2

    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.compression = 15  # Fast write
    return scene


def make_material(name, color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0,
                  emission=(0, 0, 0, 1.0), emission_strength=0.0, transmission=0.0):
    """Creates a Principled BSDF PBR material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    if bsdf:
        if 'Base Color' in bsdf.inputs:
            bsdf.inputs['Base Color'].default_value = color
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = roughness
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = metallic
        if emission_strength > 0 and 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emission
            bsdf.inputs['Emission Strength'].default_value = emission_strength
        if transmission > 0 and 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = transmission
    return mat


def build_3d_character(char_id, config, base_loc=(0, 0, 0), base_rot=(0, 0, 0)):
    """Procedurally constructs a stylized 3D rigged character with expressive face, attire, and limbs."""
    # Color parsing
    raw_skin = config.get('skin', config.get('look', {}).get('head', '#D4A373'))
    raw_attire = config.get('attire', config.get('look', {}).get('body', '#B83B5E'))
    skin_col = hex_to_rgba(raw_skin) if isinstance(raw_skin, str) else tuple(raw_skin)
    attire_col = hex_to_rgba(raw_attire) if isinstance(raw_attire, str) else tuple(raw_attire)

    look = config.get('look', {})
    deity_opts = look.get('deityOpts', {})
    char_type = config.get('type', 'human')

    has_crown = config.get('crown', deity_opts.get('crown') in ('mukut', 'crown', True))
    has_tilak = config.get('tilak', bool(deity_opts.get('tilak')))
    has_jewels = config.get('jewels', deity_opts.get('jewellery', True))
    is_betal = 'betal' in char_id.lower() or char_type == 'betal'
    is_sage = 'pandit' in char_id.lower() or 'brother' in char_id.lower() or char_type == 'sage'

    if is_betal:
        skin_col = (0.28, 0.42, 0.65, 1.0)  # Ethereal ghoul blue
        attire_col = (0.12, 0.15, 0.22, 1.0)

    char_group = bpy.data.objects.new(f"Char_{char_id}", None)
    bpy.context.scene.collection.objects.link(char_group)
    char_group.location = base_loc
    char_group.rotation_euler = base_rot

    # 1. Armature Skeleton
    arm_data = bpy.data.armatures.new(f"Arm_{char_id}")
    rig = bpy.data.objects.new(f"Rig_{char_id}", arm_data)
    bpy.context.scene.collection.objects.link(rig)
    rig.parent = char_group
    bpy.context.view_layer.objects.active = rig

    bpy.ops.object.mode_set(mode='EDIT')
    # Root & Spine
    b_root = arm_data.edit_bones.new('Root')
    b_root.head = (0, 0, 0)
    b_root.tail = (0, 0, 0.35)

    b_spine = arm_data.edit_bones.new('Spine')
    b_spine.parent = b_root
    b_spine.head = (0, 0, 0.35)
    b_spine.tail = (0, 0, 1.35)

    b_neck = arm_data.edit_bones.new('Neck')
    b_neck.parent = b_spine
    b_neck.head = (0, 0, 1.35)
    b_neck.tail = (0, 0, 1.50)

    b_head = arm_data.edit_bones.new('Head')
    b_head.parent = b_neck
    b_head.head = (0, 0, 1.50)
    b_head.tail = (0, 0, 1.95)

    # Left Arm Chain
    b_arm_l = arm_data.edit_bones.new('Arm_L')
    b_arm_l.parent = b_spine
    b_arm_l.head = (-0.34, 0, 1.28)
    b_arm_l.tail = (-0.68, 0, 0.95)

    b_forearm_l = arm_data.edit_bones.new('Forearm_L')
    b_forearm_l.parent = b_arm_l
    b_forearm_l.head = (-0.68, 0, 0.95)
    b_forearm_l.tail = (-0.92, 0, 0.65)

    # Right Arm Chain (Gesturing Arm)
    b_arm_r = arm_data.edit_bones.new('Arm_R')
    b_arm_r.parent = b_spine
    b_arm_r.head = (0.34, 0, 1.28)
    b_arm_r.tail = (0.68, 0, 0.95)

    b_forearm_r = arm_data.edit_bones.new('Forearm_R')
    b_forearm_r.parent = b_arm_r
    b_forearm_r.head = (0.68, 0, 0.95)
    b_forearm_r.tail = (0.92, 0, 0.65)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Materials
    mat_skin = make_material(f"Skin_{char_id}", color=skin_col, roughness=0.55)
    mat_attire = make_material(f"Attire_{char_id}", color=attire_col, roughness=0.75)
    mat_gold = make_material(f"Gold_{char_id}", color=(1.0, 0.82, 0.22, 1.0), roughness=0.22, metallic=0.95)
    mat_white = make_material(f"White_{char_id}", color=(0.95, 0.95, 0.95, 1.0), roughness=0.2)
    mat_dark = make_material(f"Dark_{char_id}", color=(0.06, 0.04, 0.03, 1.0), roughness=0.4)
    mat_red = make_material(f"Red_{char_id}", color=(0.88, 0.10, 0.10, 1.0), roughness=0.4)
    mat_rudraksha = make_material(f"Rudraksha_{char_id}", color=(0.38, 0.18, 0.08, 1.0), roughness=0.9)

    # 2. Head Mesh (Sculpted UV Sphere)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(0, 0, 1.62))
    m_head = bpy.context.active_object
    m_head.name = f"Mesh_Head_{char_id}"
    m_head.scale = (0.88, 0.90, 1.05)
    m_head.data.materials.append(mat_skin)
    m_head.parent = rig
    m_head.parent_type = 'BONE'
    m_head.parent_bone = 'Head'

    # Eyes, Pupils, and Eyelids for Blinking
    eyelids = []
    for side, x in [('L', -0.15), ('R', 0.15)]:
        # Sclera (White)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, location=(x, -0.36, 1.66))
        m_eye = bpy.context.active_object
        m_eye.scale = (1.0, 0.45, 1.0)
        m_eye.data.materials.append(mat_white)
        m_eye.parent = rig
        m_eye.parent_type = 'BONE'
        m_eye.parent_bone = 'Head'

        # Pupil / Iris
        if is_betal:
            # Glowing mystical eye for Betal
            mat_glow_eye = make_material(f"GlowEye_{char_id}", color=(0.2, 0.9, 1.0, 1.0),
                                         emission=(0.2, 0.9, 1.0, 1.0), emission_strength=4.0)
            pupil_mat = mat_glow_eye
        else:
            pupil_mat = mat_dark

        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.042, location=(x, -0.39, 1.66))
        m_pupil = bpy.context.active_object
        m_pupil.data.materials.append(pupil_mat)
        m_pupil.parent = rig
        m_pupil.parent_type = 'BONE'
        m_pupil.parent_bone = 'Head'

        # Eyelid (Upper lid used for blinking animation)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.088, location=(x, -0.36, 1.67))
        m_lid = bpy.context.active_object
        m_lid.name = f"Lid_{side}_{char_id}"
        m_lid.scale = (1.02, 0.46, 0.55)
        m_lid.data.materials.append(mat_skin)
        m_lid.parent = rig
        m_lid.parent_type = 'BONE'
        m_lid.parent_bone = 'Head'
        eyelids.append(m_lid)

        # Eyebrow
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.022, depth=0.17,
            location=(x, -0.38, 1.78),
            rotation=(0, 1.57 if side == 'L' else -1.57, 0.08 if side == 'L' else -0.08)
        )
        m_brow = bpy.context.active_object
        m_brow.data.materials.append(mat_dark)
        m_brow.parent = rig
        m_brow.parent_type = 'BONE'
        m_brow.parent_bone = 'Head'

    # Animated Speaking Mouth (Lower Jaw / Lip Bar)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.035, depth=0.16,
        location=(0, -0.37, 1.48),
        rotation=(0, 1.57, 0)
    )
    m_mouth = bpy.context.active_object
    m_mouth.name = f"Mouth_{char_id}"
    m_mouth.scale = (1.0, 0.6, 0.5)
    m_mouth.data.materials.append(mat_dark)
    m_mouth.parent = rig
    m_mouth.parent_type = 'BONE'
    m_mouth.parent_bone = 'Head'

    # Tilak Forehead Mark
    if has_tilak or is_sage:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.016, depth=0.13,
            location=(0, -0.39, 1.78),
            rotation=(1.57, 0, 0)
        )
        m_tilak = bpy.context.active_object
        m_tilak.data.materials.append(mat_red)
        m_tilak.parent = rig
        m_tilak.parent_type = 'BONE'
        m_tilak.parent_bone = 'Head'

    # Headwear: Mukut (Crown) for King / Topknot (Shikha) for Sage
    if has_crown:
        # Layered Ornate Golden Crown
        bpy.ops.mesh.primitive_cone_add(radius1=0.46, radius2=0.22, depth=0.42, location=(0, 0, 2.06))
        m_crown = bpy.context.active_object
        m_crown.data.materials.append(mat_gold)
        m_crown.parent = rig
        m_crown.parent_type = 'BONE'
        m_crown.parent_bone = 'Head'

        # Gemstone Crest on Crown
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.065, location=(0, -0.32, 2.02))
        m_gem = bpy.context.active_object
        m_gem.data.materials.append(mat_red)
        m_gem.parent = rig
        m_gem.parent_type = 'BONE'
        m_gem.parent_bone = 'Head'
    elif is_sage:
        # Traditional Rishi / Pandit Topknot (Shikha Bun)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(0, 0.08, 2.08))
        m_bun = bpy.context.active_object
        m_bun.scale = (0.9, 0.9, 1.1)
        m_bun.data.materials.append(mat_dark)
        m_bun.parent = rig
        m_bun.parent_type = 'BONE'
        m_bun.parent_bone = 'Head'

    # 3. Torso & Regal Robe / Dhoti
    bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=0.95, location=(0, 0, 0.88))
    m_torso = bpy.context.active_object
    m_torso.scale = (1.0, 0.65, 1.0)
    m_torso.data.materials.append(mat_attire)
    m_torso.parent = rig
    m_torso.parent_type = 'BONE'
    m_torso.parent_bone = 'Spine'

    # Golden Necklace / Garland (Haar or Rudraksha)
    if has_jewels and not is_sage:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.035, location=(0, 0, 1.28), rotation=(0.35, 0, 0))
        m_necklace = bpy.context.active_object
        m_necklace.scale = (1.0, 0.75, 1.0)
        m_necklace.data.materials.append(mat_gold)
        m_necklace.parent = rig
        m_necklace.parent_type = 'BONE'
        m_necklace.parent_bone = 'Spine'
    elif is_sage:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.035, location=(0, 0, 1.28), rotation=(0.35, 0, 0))
        m_rudra = bpy.context.active_object
        m_rudra.scale = (1.0, 0.75, 1.0)
        m_rudra.data.materials.append(mat_rudraksha)
        m_rudra.parent = rig
        m_rudra.parent_type = 'BONE'
        m_rudra.parent_bone = 'Spine'

    # 4. Arms & Forearms
    for side, x in [('L', -0.52), ('R', 0.52)]:
        # Upper Arm
        bpy.ops.mesh.primitive_cylinder_add(radius=0.095, depth=0.55, location=(x, 0, 1.10))
        m_upper = bpy.context.active_object
        m_upper.data.materials.append(mat_attire)
        m_upper.parent = rig
        m_upper.parent_type = 'BONE'
        m_upper.parent_bone = f"Arm_{side}"

        # Forearm / Hand (Skin)
        fx = -0.76 if side == 'L' else 0.76
        bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.48, location=(fx, 0, 0.72))
        m_fore = bpy.context.active_object
        m_fore.data.materials.append(mat_skin)
        m_fore.parent = rig
        m_fore.parent_type = 'BONE'
        m_fore.parent_bone = f"Forearm_{side}"

        # Armband (Bajuband) for royalty
        if has_jewels and not is_sage and not is_betal:
            bpy.ops.mesh.primitive_torus_add(major_radius=0.10, minor_radius=0.02, location=(x, 0, 1.15))
            m_band = bpy.context.active_object
            m_band.data.materials.append(mat_gold)
            m_band.parent = rig
            m_band.parent_type = 'BONE'
            m_band.parent_bone = f"Arm_{side}"

    return {
        'group': char_group,
        'rig': rig,
        'head': m_head,
        'mouth': m_mouth,
        'eyelids': eyelids,
        'char_id': char_id,
        'is_betal': is_betal,
        'head_loc': (base_loc[0], base_loc[1], base_loc[2] + 1.65)
    }


def build_3d_environment(env_type='palace'):
    """Creates a grand atmospheric setting matching the script's visual narrative."""
    env_type = str(env_type).lower()

    if 'cemetery' in env_type or 'charnel' in env_type or 'betal' in env_type:
        # === 1. MYTHOLOGICAL CHARNEL GROUND (Vikram & Betal Night Set) ===
        # Dark misty ground plane
        bpy.ops.mesh.primitive_plane_add(size=35, location=(0, 0, 0))
        floor = bpy.context.active_object
        floor.name = 'Env_Ground_Mist'
        mat_mist_ground = make_material('Ground_Ash', color=(0.08, 0.10, 0.12, 1.0), roughness=0.85)
        floor.data.materials.append(mat_mist_ground)

        # Ancient Gnarled Banyan Tree Trunk
        bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=7.0, location=(-2.6, 2.2, 3.5))
        tree = bpy.context.active_object
        tree.scale = (1.1, 0.9, 1.0)
        mat_bark = make_material('Tree_Bark', color=(0.14, 0.11, 0.09, 1.0), roughness=0.95)
        tree.data.materials.append(mat_bark)

        # Hanging Aerial Roots
        for rx, ry, rz in [(-1.8, 1.6, 2.5), (-2.2, 1.0, 2.2), (-1.4, 2.0, 2.8)]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=3.5, location=(rx, ry, rz))
            root = bpy.context.active_object
            root.data.materials.append(mat_bark)

        # Ancient Stone Shrine / Monolith
        bpy.ops.mesh.primitive_cube_add(size=1.2, location=(2.4, 1.8, 0.6))
        shrine = bpy.context.active_object
        shrine.scale = (1.0, 0.7, 1.4)
        mat_ancient_stone = make_material('Ancient_Stone', color=(0.16, 0.17, 0.19, 1.0), roughness=0.9)
        shrine.data.materials.append(mat_ancient_stone)

        # Eerie Warm Brass Lantern on Tree
        mat_lantern_glow = make_material('Lantern_Glow', color=(1.0, 0.6, 0.15, 1.0),
                                         emission=(1.0, 0.6, 0.15, 1.0), emission_strength=7.0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(-1.8, 1.0, 2.1))
        lantern = bpy.context.active_object
        lantern.data.materials.append(mat_lantern_glow)

        bpy.ops.object.light_add(type='POINT', location=(-1.8, 1.0, 2.1))
        pl = bpy.context.active_object
        pl.data.color = (1.0, 0.55, 0.18)
        pl.data.energy = 95

    elif 'science' in env_type or 'zack' in env_type or 'lab' in env_type:
        # === 2. SCIENCE / ZACK D. FILMS ANATOMICAL STUDIO ===
        # Dark clean floor with reflective tech sheen
        bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
        floor = bpy.context.active_object
        mat_tech_floor = make_material('Tech_Floor', color=(0.04, 0.05, 0.07, 1.0), roughness=0.2, metallic=0.3)
        floor.data.materials.append(mat_tech_floor)

        # Glowing Neon Circular Pedestal
        bpy.ops.mesh.primitive_cylinder_add(radius=2.2, depth=0.15, location=(0, 0, 0.08))
        pedestal = bpy.context.active_object
        mat_pedestal = make_material('Tech_Pedestal', color=(0.1, 0.12, 0.16, 1.0), roughness=0.3)
        pedestal.data.materials.append(mat_pedestal)

        # Neon Cyan Ring Trim
        mat_cyan_neon = make_material('Neon_Cyan', color=(0.1, 0.85, 1.0, 1.0),
                                      emission=(0.1, 0.85, 1.0, 1.0), emission_strength=6.0)
        bpy.ops.mesh.primitive_torus_add(major_radius=2.22, minor_radius=0.035, location=(0, 0, 0.15))
        neon_ring = bpy.context.active_object
        neon_ring.data.materials.append(mat_cyan_neon)

        # Procedural Zack D. Films Layered Anatomical Cross-Section Prop
        mat_outer_tissue = make_material('Tissue_Outer', color=(0.88, 0.38, 0.35, 1.0), roughness=0.45)
        mat_inner_core   = make_material('Tissue_Core', color=(0.95, 0.82, 0.42, 1.0), roughness=0.3)
        mat_vessels      = make_material('Vessels_Red', color=(0.95, 0.08, 0.08, 1.0), roughness=0.25)

        # Outer Organ/Tissue Sphere
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.85, location=(0, 0, 1.45))
        organ = bpy.context.active_object
        organ.name = "Anatomy_Outer"
        organ.data.materials.append(mat_outer_tissue)

        # Inner Anatomical Core
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.52, location=(0, 0, 1.45))
        core = bpy.context.active_object
        core.name = "Anatomy_Core"
        core.data.materials.append(mat_inner_core)

        # Procedural Blood Vessels / Nerve Fibers
        for vx, vy, vz in [(0.2, 0.1, 1.5), (-0.25, 0.15, 1.35), (0.1, -0.2, 1.6)]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.7, location=(vx, vy, vz), rotation=(0.4, 0.6, 0.2))
            vessel = bpy.context.active_object
            vessel.data.materials.append(mat_vessels)

        # Animated Slicing Boolean Cutter Plane
        bpy.ops.mesh.primitive_cube_add(size=2.2, location=(1.15, 0, 1.45))
        cutter = bpy.context.active_object
        cutter.name = "Anatomy_Cutter"
        cutter.display_type = 'WIRE'
        cutter.hide_render = True

        # Apply Boolean Difference to Outer Organ
        bool_mod = organ.modifiers.new(name="CrossSectionCut", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cutter

        # Animate Slicing Action: Slices open smoothly over frames
        cutter.location = (2.2, 0, 1.45)  # Start closed
        cutter.keyframe_insert(data_path="location", frame=1)
        cutter.location = (0.2, 0, 1.45)  # Cut open to reveal interior
        cutter.keyframe_insert(data_path="location", frame=60)

    else:
        # === 3. GRAND ROYAL PALACE & TEMPLE COURT (Default) ===
        # Highly Reflective Polished Stone Ground
        bpy.ops.mesh.primitive_plane_add(size=35, location=(0, 0, 0))
        floor = bpy.context.active_object
        floor.name = 'Env_Floor'
        mat_floor = make_material('Floor_Marble', color=(0.08, 0.09, 0.12, 1.0), roughness=0.25, metallic=0.15)
        floor.data.materials.append(mat_floor)

        # Monolithic Carved Temple Pillars with Golden Capitals
        mat_pillar = make_material('Pillar_Stone', color=(0.20, 0.19, 0.18, 1.0), roughness=0.82)
        mat_gold_trim = make_material('Pillar_Gold', color=(0.95, 0.80, 0.25, 1.0), roughness=0.25, metallic=0.92)

        for px in [-2.6, 2.6]:
            for py in [-2.2, 1.4, 5.2]:
                bpy.ops.mesh.primitive_cylinder_add(radius=0.34, depth=6.2, location=(px, py, 3.1))
                pillar = bpy.context.active_object
                pillar.data.materials.append(mat_pillar)

                # Gold Ring Capital
                bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.045, location=(px, py, 2.3))
                ring = bpy.context.active_object
                ring.data.materials.append(mat_gold_trim)

        # Royal Backdrop Archway
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 5.8, 2.5))
        arch = bpy.context.active_object
        arch.scale = (3.5, 0.2, 3.0)
        arch.data.materials.append(mat_pillar)

        # Flaming Oil Lamps (Diya Stands)
        mat_flame = make_material('Flame_Emissive', color=(1.0, 0.5, 0.1, 1.0),
                                  emission=(1.0, 0.55, 0.12, 1.0), emission_strength=8.5)
        for lx in [-1.8, 1.8]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=1.4, location=(lx, -1.0, 0.7))
            stand = bpy.context.active_object
            stand.data.materials.append(mat_gold_trim)

            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(lx, -1.0, 1.46))
            flame = bpy.context.active_object
            flame.scale = (0.7, 0.7, 1.5)
            flame.data.materials.append(mat_flame)

            # Warm flickering point light
            bpy.ops.object.light_add(type='POINT', location=(lx, -1.0, 1.58))
            pl = bpy.context.active_object
            pl.data.color = (1.0, 0.65, 0.22)
            pl.data.energy = 90


def setup_3point_lighting(env_type='palace'):
    """Sets up dramatic 3-point studio lighting with razor-sharp rim separation."""
    is_night = 'cemetery' in env_type or 'charnel' in env_type or 'betal' in env_type

    if is_night:
        # Moonlight Key Light (Cool Slate Blue)
        bpy.ops.object.light_add(type='SPOT', location=(3.4, -4.0, 4.5), rotation=(0.85, 0, 0.6))
        key = bpy.context.active_object
        key.name = "Light_Key"
        key.data.energy = 750
        key.data.spot_size = 1.15
        key.data.color = (0.70, 0.82, 1.0)
        key.data.shadow_soft_size = 0.25

        # Fill Light (Subtle Indigo)
        bpy.ops.object.light_add(type='AREA', location=(-3.2, -3.0, 2.5), rotation=(0.7, 0, -0.7))
        fill = bpy.context.active_object
        fill.name = "Light_Fill"
        fill.data.energy = 180
        fill.data.color = (0.45, 0.55, 0.85)

        # Rim Backlight (Vibrant Cyan Moonlit Edge)
        bpy.ops.object.light_add(type='SPOT', location=(0, 3.6, 3.8), rotation=(-0.95, 0, 3.14))
        rim = bpy.context.active_object
        rim.name = "Light_Rim"
        rim.data.energy = 1200
        rim.data.spot_size = 1.2
        rim.data.color = (0.6, 0.9, 1.0)
    else:
        # Key Light (Warm Amber Sunlight)
        bpy.ops.object.light_add(type='SPOT', location=(3.2, -4.0, 4.5), rotation=(0.85, 0, 0.6))
        key = bpy.context.active_object
        key.name = "Light_Key"
        key.data.energy = 880
        key.data.spot_size = 1.15
        key.data.color = (1.0, 0.92, 0.82)
        key.data.shadow_soft_size = 0.25

        # Fill Light (Cool Sky Blue)
        bpy.ops.object.light_add(type='AREA', location=(-3.2, -3.0, 2.5), rotation=(0.7, 0, -0.7))
        fill = bpy.context.active_object
        fill.name = "Light_Fill"
        fill.data.energy = 230
        fill.data.color = (0.65, 0.82, 1.0)

        # Rim Backlight (Intense Golden Halo for edge separation)
        bpy.ops.object.light_add(type='SPOT', location=(0, 3.5, 3.8), rotation=(-0.95, 0, 3.14))
        rim = bpy.context.active_object
        rim.name = "Light_Rim"
        rim.data.energy = 1150
        rim.data.spot_size = 1.2
        rim.data.color = (1.0, 0.82, 0.45)


def animate_characters_acting(chars, shots, total_frames, fps=30):
    """Animates continuous breathing, eye blinks, speech mouth articulation, and arm gestures."""
    for char_id, char_obj in chars.items():
        rig = char_obj['rig']
        m_mouth = char_obj.get('mouth')
        eyelids = char_obj.get('eyelids', [])
        is_betal = char_obj.get('is_betal', False)

        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='POSE')

        p_root = rig.pose.bones.get('Root')
        p_spine = rig.pose.bones.get('Spine')
        p_head = rig.pose.bones.get('Head')
        p_arm_r = rig.pose.bones.get('Arm_R')
        p_forearm_r = rig.pose.bones.get('Forearm_R')

        # 1. Idle Breathing (Continuous subtle sinusoidal cycle on Spine)
        breath_period = int(fps * 2.2)  # ~2.2s per breath cycle
        for f in range(1, total_frames + 1, breath_period):
            if p_spine:
                p_spine.scale = (1.0, 1.0, 1.0)
                p_spine.keyframe_insert(data_path='scale', frame=f)
                mid_f = min(total_frames, f + breath_period // 2)
                p_spine.scale = (1.025, 1.035, 1.015)
                p_spine.keyframe_insert(data_path='scale', frame=mid_f)

        # 2. Betal Floating Hover Motion (If ghostly entity)
        if is_betal and p_root:
            float_period = int(fps * 2.5)
            for f in range(1, total_frames + 1, float_period):
                p_root.location = (0, 0, 0.25)
                p_root.keyframe_insert(data_path='location', frame=f)
                mid_f = min(total_frames, f + float_period // 2)
                p_root.location = (0, 0, 0.42)
                p_root.keyframe_insert(data_path='location', frame=mid_f)

        # 3. Eye Blinking (Every ~3 to 4 seconds)
        for lid in eyelids:
            blink_interval = int(fps * 3.5)
            for f in range(int(fps * 1.5), total_frames + 1, blink_interval):
                lid.scale = (1.02, 0.46, 0.55)
                lid.keyframe_insert(data_path='scale', frame=f)
                # Closed lid
                lid.scale = (1.05, 0.48, 1.15)
                lid.keyframe_insert(data_path='scale', frame=f + 3)
                # Reopen
                lid.scale = (1.02, 0.46, 0.55)
                lid.keyframe_insert(data_path='scale', frame=f + 6)

        # 4. Acting, Speaking Gestures & Lip-Sync per Shot
        for sh in shots:
            sf = sh.get('start_frame', 1)
            ef = sh.get('end_frame', total_frames)
            speaker = sh.get('speaker', '')

            if speaker == char_id:
                # Active Speaker: Dynamic speech gestures
                if p_arm_r:
                    p_arm_r.rotation_mode = 'XYZ'
                    p_arm_r.rotation_euler = (0, 0, 0)
                    p_arm_r.keyframe_insert(data_path='rotation_euler', frame=max(1, sf - 4))

                    # Raise into speaking posture
                    p_arm_r.rotation_euler = (math.radians(48), math.radians(-12), math.radians(28))
                    p_arm_r.keyframe_insert(data_path='rotation_euler', frame=sf + int(fps * 0.4))

                    # Conversational beat movement
                    p_arm_r.rotation_euler = (math.radians(38), math.radians(-6), math.radians(18))
                    p_arm_r.keyframe_insert(data_path='rotation_euler', frame=sf + int(fps * 1.2))

                    # Hold and return smoothly
                    p_arm_r.rotation_euler = (0, 0, 0)
                    p_arm_r.keyframe_insert(data_path='rotation_euler', frame=ef)

                if p_forearm_r:
                    p_forearm_r.rotation_mode = 'XYZ'
                    p_forearm_r.rotation_euler = (0, 0, 0)
                    p_forearm_r.keyframe_insert(data_path='rotation_euler', frame=max(1, sf - 4))
                    p_forearm_r.rotation_euler = (math.radians(35), math.radians(15), 0)
                    p_forearm_r.keyframe_insert(data_path='rotation_euler', frame=sf + int(fps * 0.5))
                    p_forearm_r.rotation_euler = (0, 0, 0)
                    p_forearm_r.keyframe_insert(data_path='rotation_euler', frame=ef)

                if p_head:
                    p_head.rotation_mode = 'XYZ'
                    p_head.rotation_euler = (0, 0, 0)
                    p_head.keyframe_insert(data_path='rotation_euler', frame=sf)
                    p_head.rotation_euler = (math.radians(8), math.radians(-5), 0)
                    p_head.keyframe_insert(data_path='rotation_euler', frame=sf + int(fps * 0.6))
                    p_head.rotation_euler = (0, 0, 0)
                    p_head.keyframe_insert(data_path='rotation_euler', frame=ef)

                # Mouth speech articulation (vowel cadence pulses)
                if m_mouth:
                    cadence = 5  # Frames per mouth flap (~6 flaps/sec)
                    for mf in range(sf, ef, cadence * 2):
                        m_mouth.scale = (1.0, 0.6, 0.5)
                        m_mouth.keyframe_insert(data_path='scale', frame=mf)
                        open_f = min(ef, mf + cadence)
                        m_mouth.scale = (1.1, 0.8, 1.4)
                        m_mouth.keyframe_insert(data_path='scale', frame=open_f)
                    m_mouth.scale = (1.0, 0.6, 0.5)
                    m_mouth.keyframe_insert(data_path='scale', frame=ef)
            else:
                # Attentive Listener: Slight head tilt and nod
                if p_head and (sf % 2 == 0):
                    p_head.rotation_mode = 'XYZ'
                    p_head.rotation_euler = (0, math.radians(6), math.radians(-3))
                    p_head.keyframe_insert(data_path='rotation_euler', frame=sf)

        bpy.ops.object.mode_set(mode='OBJECT')


def build_camera_choreography(shots, total_frames, chars, fps=30):
    """Sets up camera cutting, continuous push-ins, tracking, and Depth of Field bokeh."""
    scene = bpy.context.scene

    # Target Empty for Depth of Field & Tracking Focus
    target_empty = bpy.data.objects.new("Camera_Target", None)
    bpy.context.scene.collection.objects.link(target_empty)
    target_empty.location = (0, 0, 1.62)

    # Cinema Camera (50mm Portrait Lens)
    cam_data = bpy.data.cameras.new("CinemaCamera")
    cam_data.lens = 50
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = target_empty
    cam_data.dof.aperture_fstop = 2.4  # Dreamy soft background bokeh

    cam_obj = bpy.data.objects.new("CinemaCameraObj", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Smooth Track To constraint
    track = cam_obj.constraints.new(type='TRACK_TO')
    track.target = target_empty
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    for sh in shots:
        sf = sh.get('start_frame', 1)
        ef = sh.get('end_frame', total_frames)
        cam_info = sh.get('camera', {})
        scale = cam_info.get('scale', 'M2S')
        speaker = sh.get('speaker', '')
        target_char = chars.get(speaker) or next(iter(chars.values()))

        tx, ty, tz = target_char['head_loc']

        # Move target to speaker's head
        target_empty.location = (tx, ty, tz)
        target_empty.keyframe_insert(data_path='location', frame=sf)

        # Position Camera with Continuous Slow Dolly Push-In
        if scale == 'CU':  # Dramatic Close-Up
            start_pos = (tx + 0.12, ty - 1.85, tz + 0.05)
            end_pos   = (tx + 0.04, ty - 1.48, tz + 0.02)
        elif scale == 'OTS':  # Over-The-Shoulder
            start_pos = (tx - 0.75, ty - 2.7, tz + 0.28)
            end_pos   = (tx - 0.52, ty - 2.3, tz + 0.22)
        elif scale == 'EWS':  # Establishing Wide Shot
            start_pos = (0, -5.6, 2.3)
            end_pos   = (0, -4.9, 1.9)
        else:  # Medium Two-Shot (M2S)
            start_pos = (0.22, -3.5, 1.65)
            end_pos   = (0.05, -2.9, 1.58)

        cam_obj.location = start_pos
        cam_obj.keyframe_insert(data_path='location', frame=sf)
        cam_obj.location = end_pos
        cam_obj.keyframe_insert(data_path='location', frame=ef)


def render_project(output_dir, start_frame=1, end_frame=30):
    """Executes background render and writes PNG frame sequence."""
    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_end = end_frame

    prefix = Path(output_dir) / "f_"
    scene.render.filepath = str(prefix)

    print(f"\n🎬 [BLENDER 5.2 EEVEE NEXT] Rendering frames {start_frame} -> {end_frame}...")
    bpy.ops.render.render(animation=True)
    print(f"✨ [BLENDER] Render complete! Frames saved in: {output_dir}")


def main():
    args = parse_args()
    spec_path = Path(args.spec)
    if not spec_path.is_file():
        raise SystemExit(f"Missing spec file: {spec_path}")

    spec = json.loads(spec_path.read_text())
    fps = args.fps or spec.get('fps', 30)
    samples = args.samples or spec.get('samples', 8)
    total_frames = spec.get('total_frames', 90)
    shots = spec.get('shots', [])
    env_type = spec.get('environment', {}).get('type', 'palace')
    characters_cfg = spec.get('characters', {
        'protagonist': {'skin': '#D4A373', 'attire': '#B83B5E', 'crown': True}
    })

    clear_scene()
    setup_render_settings(width=1080, height=1920, fps=fps, samples=samples)
    build_3d_environment(env_type)
    setup_3point_lighting(env_type)

    # Position characters spatially in 3D scene
    chars = {}
    char_keys = list(characters_cfg.keys())
    for idx, (cid, ccfg) in enumerate(characters_cfg.items()):
        if len(char_keys) > 1:
            x_offset = (idx - (len(char_keys) - 1) / 2.0) * 1.45
            rot_z = -0.25 if x_offset < 0 else 0.25
        else:
            x_offset = 0.0
            rot_z = 0.0
        chars[cid] = build_3d_character(cid, ccfg, base_loc=(x_offset, 0, 0), base_rot=(0, 0, rot_z))

    animate_characters_acting(chars, shots, total_frames, fps=fps)
    build_camera_choreography(shots, total_frames, chars, fps=fps)

    sf = args.start_frame or 1
    ef = args.end_frame or total_frames
    render_project(args.output_dir, start_frame=sf, end_frame=ef)


if __name__ == '__main__':
    main()
