"""Liquid-chrome hero loop for the portfolio site (Cycles, 3840x2160 production master, 12 s seamless loop).

Builds the scene from scratch, saves hero.blend next to this file and optionally renders.
  Add --finish matte (default) or --finish mirror to any command; each saves its own hero-<finish>.blend.
  blender -b -P hero.py -- --save                       # build + save .blend only
  blender -b -P hero.py -- --still 0 out.png [--half] [--fast]   # one frame (--half: 50% res, --fast: preview sampling)
  blender -b -P hero.py -- --frames out_dir/            # render the whole loop as 16-bit PNGs
  --web: 1920x1080, 32 samples, 2.4M-vertex mesh, no motion blur -- the website loop. Without it: 4K production master.

Everything that moves is periodic over FRAMES, so frame FRAMES == frame 0:
  - surface noise is sampled along circles in noise space (Scene Time in Geometry Nodes)
  - faster layers cycle a whole number of times per loop; camera and studio are locked, only the liquid moves
"""
import bpy, math, os, sys

FRAMES = 360  # 12 s at 30 fps
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FINISH = args[args.index("--finish") + 1] if "--finish" in args else "matte"
# Per-finish look. matte: satin metal, darker room so the soft highlights keep contrast.
# mirror: polished metal + clear coat for crisp white "wet" reflections.
LOOK = {
    "matte": dict(rough=0.2, rim_rough=0.28, coat=0.0, room=0.15, ceiling=0.2, fstop=16),
    "mirror": dict(rough=0.06, rim_rough=0.12, coat=1.0, room=0.35, ceiling=0.45, fstop=8),
}[FINISH]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 0, FRAMES - 1
scene.render.fps = 30
WEB = "--web" in args
scene.render.resolution_x, scene.render.resolution_y = (1920, 1080) if WEB else (3840, 2160)
scene.render.resolution_percentage = 50 if "--half" in args else 100

# --- Cycles on the GPU (Metal on Apple Silicon) ---
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type != "CPU"  # GPU only: the CPU as an extra device just slows Metal down
scene.cycles.device = "GPU"
FAST = "--fast" in args
scene.cycles.samples = 64 if FAST else 32 if WEB else 512
scene.cycles.adaptive_min_samples = 0 if FAST or WEB else 64
scene.cycles.adaptive_threshold = 0.02 if FAST else 0.03 if WEB else 0.005
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.denoising_use_gpu = True
scene.cycles.max_bounces = 8
scene.cycles.glossy_bounces = 8
scene.cycles.diffuse_bounces = 1
# Deformation blur (GN surface keeps its topology). Off for web loops: ~3x geometry cost, invisible at this speed
scene.render.use_motion_blur = not WEB
scene.render.motion_blur_shutter = 0.5
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"


def math_node(nodes, op, a=None, b=None):
    n = nodes.new("ShaderNodeMath")
    n.operation = op
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


# --- liquid surface: dense grid, two looping noise layers (swells + ripples) ---
bpy.ops.mesh.primitive_plane_add(size=1)
surf = bpy.context.object
surf.name = "LiquidChrome"
ng = bpy.data.node_groups.new("LiquidChrome", "GeometryNodeTree")
surf.modifiers.new("Liquid", "NODES").node_group = ng
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = ng.nodes, ng.links
out = N.new("NodeGroupOutput")
grid = N.new("GeometryNodeMeshGrid")
grid.inputs["Size X"].default_value, grid.inputs["Size Y"].default_value = 22, 13
# ~9.6M verts keeps micro-ripples smooth at 4K; ~2.4M is plenty at 1080p
grid.inputs["Vertices X"].default_value, grid.inputs["Vertices Y"].default_value = (2000, 1200) if WEB else (4000, 2400)

time = N.new("GeometryNodeInputSceneTime")
ang = math_node(N, "MULTIPLY", b=2 * math.pi / FRAMES)
L.new(time.outputs["Frame"], ang.inputs[0])
pos = N.new("GeometryNodeInputPosition")


def layer(scale, radius, phase, detail, distortion, amp, seed_offset, cycles=1):
    """One periodic noise layer: position + circle(cycles * angle + phase) * radius -> centred, scaled height.
    cycles must be a whole number so the layer still closes the loop."""
    speed = math_node(N, "MULTIPLY", b=cycles)
    L.new(ang.outputs[0], speed.inputs[0])
    a = math_node(N, "ADD", b=phase)
    L.new(speed.outputs[0], a.inputs[0])
    c, s = math_node(N, "COSINE"), math_node(N, "SINE")
    L.new(a.outputs[0], c.inputs[0]); L.new(a.outputs[0], s.inputs[0])
    circle = N.new("ShaderNodeCombineXYZ")
    L.new(c.outputs[0], circle.inputs["X"]); L.new(s.outputs[0], circle.inputs["Y"])
    circle.inputs["Z"].default_value = seed_offset
    r = N.new("ShaderNodeVectorMath"); r.operation = "SCALE"; r.inputs["Scale"].default_value = radius
    L.new(circle.outputs[0], r.inputs[0])
    v = N.new("ShaderNodeVectorMath"); v.operation = "ADD"
    L.new(pos.outputs[0], v.inputs[0]); L.new(r.outputs[0], v.inputs[1])
    n = N.new("ShaderNodeTexNoise")
    n.noise_dimensions = "3D"
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = 0.45
    n.inputs["Distortion"].default_value = distortion
    L.new(v.outputs[0], n.inputs["Vector"])
    centred = math_node(N, "SUBTRACT", b=0.5); L.new(n.outputs["Fac"], centred.inputs[0])
    scaled = math_node(N, "MULTIPLY", b=amp); L.new(centred.outputs[0], scaled.inputs[0])
    return scaled


swell = layer(scale=0.13, radius=0.45, phase=0.0, detail=1.5, distortion=1.1, amp=3.8, seed_offset=0.0)
ripple = layer(scale=0.5, radius=0.2, phase=2.1, detail=1.0, distortion=0.5, amp=0.22, seed_offset=7.3, cycles=1)
micro = layer(scale=1.6, radius=0.1, phase=4.2, detail=0.0, distortion=0.2, amp=0.02, seed_offset=13.1, cycles=1)
h1 = math_node(N, "ADD"); L.new(swell.outputs[0], h1.inputs[0]); L.new(ripple.outputs[0], h1.inputs[1])
h = math_node(N, "ADD"); L.new(h1.outputs[0], h.inputs[0]); L.new(micro.outputs[0], h.inputs[1])
offset = N.new("ShaderNodeCombineXYZ"); L.new(h.outputs[0], offset.inputs["Z"])

setpos = N.new("GeometryNodeSetPosition")
L.new(grid.outputs["Mesh"], setpos.inputs["Geometry"]); L.new(offset.outputs[0], setpos.inputs["Offset"])
smooth = N.new("GeometryNodeSetShadeSmooth"); L.new(setpos.outputs[0], smooth.inputs["Geometry"])
setmat = N.new("GeometryNodeSetMaterial"); L.new(smooth.outputs[0], setmat.inputs["Geometry"])
L.new(setmat.outputs[0], out.inputs[0])

# --- chrome: metal (+ clear coat on mirror) with a darker rim where the surface turns away (Layer Weight)
#     to define the curves. Coat/rim approach from https://blender.stackexchange.com/questions/302043 ---
mat = bpy.data.materials.new("Chrome")
mat.use_nodes = True
mt = mat.node_tree; mn, ml = mt.nodes, mt.links
bsdf = mn["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.92, 1)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = LOOK["rough"]
bsdf.inputs["Coat Weight"].default_value = LOOK["coat"]
bsdf.inputs["Coat Roughness"].default_value = 0.01
dark = mn.new("ShaderNodeBsdfPrincipled")
dark.inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
dark.inputs["Metallic"].default_value = 1.0
dark.inputs["Roughness"].default_value = LOOK["rim_rough"]
dark.inputs["Coat Weight"].default_value = LOOK["coat"]
dark.inputs["Coat Roughness"].default_value = 0.01
lw = mn.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
rim = mn.new("ShaderNodeValToRGB")
rim.color_ramp.elements[0].position = 0.55; rim.color_ramp.elements[1].position = 0.95
ml.new(lw.outputs["Facing"], rim.inputs["Fac"])
mix = mn.new("ShaderNodeMixShader")
ml.new(rim.outputs["Color"], mix.inputs["Fac"]); ml.new(bsdf.outputs[0], mix.inputs[1]); ml.new(dark.outputs[0], mix.inputs[2])
ml.new(mix.outputs[0], mn["Material Output"].inputs["Surface"])
setmat.inputs["Material"].default_value = mat

# --- photo studio: near-black world + real, camera-invisible softboxes. Cycles traces them, so the chrome
#     shows crisp mirror reflections of shapes and edges instead of a gradient. ---
world = bpy.data.worlds.new("Studio"); scene.world = world
world.use_nodes = True
wt = world.node_tree; wn, wl = wt.nodes, wt.links
env = wn.new("ShaderNodeTexEnvironment")  # Blender's bundled studio HDRI, dimmed: room detail in the dark reflections
env.image = bpy.data.images.load(os.path.join(bpy.utils.system_resource("DATAFILES"), "studiolights", "world", "studio.exr"))
env.image.pack()  # embed it so the .blend opens on any machine
wl.new(env.outputs["Color"], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = LOOK["room"]


def softbox(name, loc, rot_deg, size, strength, gradient=False):
    """Emissive panel visible only to reflections/lighting. gradient=True fades it along its length (strip-light falloff)."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[math.radians(r) for r in rot_deg])
    o = bpy.context.object; o.name = name; o.scale = (*size, 1)
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = strength
    if gradient:
        tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (0.03, 0.03, 0.03, 1); ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(tc.outputs["Generated"], gr.inputs["Vector"]); nt.links.new(gr.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    o.data.materials.append(m)
    o.visible_camera = False
    o.visible_shadow = False
    return o


# Overhead key panel and strip lights; angles chosen so their mirror images land across the visible surface
# Gradients everywhere so reflections roll off like real softboxes instead of clipping to flat white
softbox("Ceiling", (0.0, 2.0, 14), (0, 0, 10), (36, 24), LOOK["ceiling"], gradient=True)  # dim mid-tones
softbox("KeyPanel", (-3.0, 3.5, 11), (-20, -15, 25), (9, 5), 2.6, gradient=True)
softbox("StripA", (4.5, 1.0, 10), (10, 20, -35), (16, 0.7), 4.5, gradient=True)
softbox("StripB", (-6.0, -1.5, 9), (-10, -25, 60), (14, 0.45), 3.5, gradient=True)
softbox("StripC", (1.0, 7.0, 7), (-50, 0, 5), (20, 0.35), 6.0, gradient=True)
softbox("FillLow", (0.0, 9.0, 3.0), (-80, 0, 0), (30, 1.6), 1.2, gradient=True)  # low wide fill -> reads as a horizon line

# Ring light above the camera axis: shows up as circular highlights travelling through the liquid
bpy.ops.mesh.primitive_torus_add(major_radius=2.6, minor_radius=0.07, location=(0.0, -1.0, 12.5), rotation=(math.radians(-12), 0, 0))
rl = bpy.context.object; rl.name = "RingLight"
rlm = bpy.data.materials.new("RingLight"); rlm.use_nodes = True
rlt = rlm.node_tree; rlt.nodes.remove(rlt.nodes["Principled BSDF"])
rle = rlt.nodes.new("ShaderNodeEmission"); rle.inputs["Strength"].default_value = 18.0
rlt.links.new(rle.outputs[0], rlt.nodes["Material Output"].inputs["Surface"])
rl.data.materials.append(rlm); rl.visible_camera = False; rl.visible_shadow = False

# Horizon ring: thin bright band all around at camera-ish height, the classic chrome horizon in reflections
bpy.ops.mesh.primitive_torus_add(major_radius=18, minor_radius=0.12, location=(0, 0, 1.2))
ring = bpy.context.object; ring.name = "HorizonRing"
rm = bpy.data.materials.new("HorizonRing"); rm.use_nodes = True
rnt = rm.node_tree; rnt.nodes.remove(rnt.nodes["Principled BSDF"])
rem = rnt.nodes.new("ShaderNodeEmission"); rem.inputs["Strength"].default_value = 1.6
rnt.links.new(rem.outputs[0], rnt.nodes["Material Output"].inputs["Surface"])
ring.data.materials.append(rm); ring.visible_camera = False; ring.visible_shadow = False

# --- camera: locked, tilted for perspective depth ---
cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 45
cam_data.dof.use_dof = True; cam_data.dof.aperture_fstop = LOOK["fstop"]; cam_data.dof.focus_distance = 9.5
cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (0, -6.2, 7.4)
cam.rotation_euler = (math.radians(40), 0, 0)

# Output baked into the .blend: Render > Render Animation writes 16-bit PNGs to render/<finish>/ next to the file
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "16"
scene.render.image_settings.color_mode = "RGB"
scene.render.filepath = f"//render/{FINISH}/f"

if not WEB:  # the saved .blend files stay at production settings
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"hero-{FINISH}.blend"))

if "--still" in args:
    i = args.index("--still")
    scene.frame_set(int(args[i + 1]))
    scene.render.filepath = args[i + 2]
    bpy.ops.render.render(write_still=True)
elif "--frames" in args:
    scene.render.filepath = os.path.join(args[args.index("--frames") + 1], "f")
    bpy.ops.render.render(animation=True)
