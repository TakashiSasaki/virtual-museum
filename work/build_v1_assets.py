"""Run inside interactive Blender. Creates a NEW scene and exports V1 FBX assets.

Set MUSEUM_ROOT to the repository directory before exec(), or run using --python.
Existing scenes and shared assets are not changed.
"""
import bpy, math
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(globals().get('MUSEUM_ROOT', Path(__file__).resolve().parents[1]))
DEST = ROOT / 'unity/VirtualMuseum/Assets/Museum/Models'
DEST.mkdir(parents=True, exist_ok=True)
SAVE = ROOT / 'blender/scenes/museum_v1_assets.blend'
if SAVE.exists():
    raise RuntimeError('V1 source already exists; inspect before rebuilding')
scene = bpy.data.scenes.new('Museum V1 | Asset workshop')
bpy.context.window.scene = scene

def mat(name, rgb, metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Roughness'].default_value=.46; p.inputs['Metallic'].default_value=metallic
    return m
ivory=mat('Warm porcelain',(.78,.81,.76)); wood=mat('Walnut specimen boxes',(.19,.09,.04))
teal=mat('Museum green',(.025,.25,.20)); brass=mat('Brass',(.65,.40,.10),.5)
ink=mat('Graphite',(.035,.055,.065)); blue=mat('Aimo blue shell',(.07,.32,.67))
yellow=mat('Aimo golden body',(1,.65,.07)); white=mat('Labels',(.95,.93,.84))
orange=mat('Butterfly amber',(.88,.28,.055)); green=mat('Beetle emerald',(.06,.39,.19),.3)
pink=mat('Symbol coral',(.89,.24,.32)); objects=[]

def finish(o,name,material):
    o.name=name; o.data.materials.append(material); objects.append(o); return o
def cube(name,loc,scale,m,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,m)
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL'); mod.width=bevel; mod.segments=2
        o.modifiers.new('Corner normals','WEIGHTED_NORMAL')
    return o
def ball(name,loc,scale,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc)
    o=bpy.context.object; o.scale=scale; finish(o,name,m)
    for p in o.data.polygons:p.use_smooth=True
    return o
def rod(name,a,b,r,m):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)/2)
    o=bpy.context.object; o.rotation_mode='QUATERNION'; o.rotation_quaternion=d.to_track_quat('Z','Y')
    return finish(o,name,m)
def begin():
    global objects
    objects=[]
def export(name,display):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(DEST/(name+'.fbx')),use_selection=True,object_types={'MESH'},
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_anim=False)
    parent=bpy.data.objects.new(name,None); scene.collection.objects.link(parent)
    for o in objects:o.parent=parent
    parent.location=display

begin()
for x in [-.91,.91]:
    for y in [-.38,.38]:cube('Shelf upright',(x,y,1.4),(.055,.055,2.8),ivory)
cube('Storage base',(0,0,.36),(1.85,.8,.72),ivory)
for x in [-.46,.46]:
    cube('Door',(x,-.413,.37),(.88,.035,.62),white)
    rod('Door handle',(x+.30,-.455,.3),(x+.30,-.455,.5),.012,ink)
for h in [1.45,1.64,1.83,2.02,2.21,2.4,2.59]:
    for x in [-.46,.46]:
        cube('Specimen drawer',(x,0,h),(.85,.72,.13),wood)
        cube('Drawer label',(x-.2,-.367,h),(.19,.008,.04),white,0)
        cube('Drawer pull',(x+.2,-.39,h),(.12,.04,.02),brass,.006)
for x in [-.46,.46]:
    tray=cube('Inclined display',(x,-.03,1.03),(.84,.7,.06),wood)
    tray.rotation_euler.x=math.radians(18)
    pad=cube('Tray lining',(x,-.035,1.07),(.77,.62,.015),white,0); pad.rotation_euler.x=math.radians(18)
    for j in range(3):
        for k in range(2):
            ball('Pinned dummy insect',(x+(j-1)*.22,-.18+k*.25,1.065+(-.18+k*.25)*.32),(.035,.07,.018),ink)
export('SpecimenShelf',(-3,0,0))

begin()
cube('Bench top',(0,0,.84),(3,.85,.08),white)
for x in [-1.4,1.4]:
    for y in [-.33,.33]:cube('Bench leg',(x,y,.4),(.06,.06,.8),ivory)
cube('Observation mat',(0,-.04,.888),(1.1,.65,.016),teal,0)
for x in [-1,0,1]:cube('Wall cabinet',(x,.18,2.15),(.96,.45,.75),ivory)
export('ObservationBench',(0,0,0))

begin()
cube('Microscope base',(0,0,.04),(.32,.38,.08),ivory,.06)
rod('Stand',(0,.1,.05),(0,.1,.50),.038,ivory)
ball('Optical body',(0,-.035,.43),(.10,.10,.13),ivory)
for x in [-.055,.055]:rod('Eyepiece',(x,-.08,.49),(x,-.19,.60),.025,ink)
rod('Objective',(0,-.04,.4),(0,-.04,.28),.045,ink)
for x in [-.17,.17]:
    rod('Lamp arm',(x,.07,.07),(x,-.03,.29),.014,ink)
    ball('LED light',(x,-.03,.29),(.04,.05,.025),ink)
export('Microscope',(2.4,0,0))

begin()
ball('Blue shell',(0,.13,1.25),(.64,.20,.69),blue)
# Raised symbols suggest the reference's range of disciplines.
for i,m in enumerate([green,orange,teal,pink,brass,white,ink]):
    a=i*math.tau/7
    ball('Discipline symbol',(math.sin(a)*.45,-.07,1.3+math.cos(a)*.45),(.10,.035,.10),m)
ball('Face',(0,-.22,.77),(.27,.23,.29),yellow)
for x in [-.19,.19]:
    ball('Eye white',(x,-.412,.83),(.064,.03,.088),white)
    ball('Pupil',(x,-.438,.83),(.027,.013,.046),ink)
for x in [-.11,.11]:
    rod('Leg',(x,-.16,.57),(x,-.16,.14),.026,yellow)
    ball('Boot',(x,-.21,.08),(.06,.12,.09),white)
for side in [-1,1]:
    rod('Arm',(side*.23,-.20,.72),(side*.35,-.23,.47),.026,yellow)
    ball('Hand',(side*.35,-.23,.47),(.047,.04,.055),yellow)
# Small magnifying glass in right hand.
rod('Loupe handle',(.35,-.24,.47),(.43,-.24,.63),.014,ink)
bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,location=(.46,-.24,.69),major_radius=.065,minor_radius=.012,rotation=(math.pi/2,0,0))
finish(bpy.context.object,'Magnifier ring',brass)
export('Aimonite',(4,0,0))

begin()
ball('Beetle body',(0,0,.07),(.12,.20,.075),green)
ball('Beetle thorax',(0,-.18,.07),(.09,.08,.065),green)
ball('Beetle head',(0,-.26,.065),(.065,.065,.05),ink)
rod('Wing seam',(0,-.12,.143),(0,.17,.11),.004,brass)
for side in [-1,1]:
    for y in [-.13,0,.12]:
        rod('Leg',(side*.07,y,.05),(side*.20,y+.07,.025),.01,ink)
        rod('Foot',(side*.20,y+.07,.025),(side*.26,y+.02,.015),.008,ink)
    rod('Antenna',(side*.04,-.27,.07),(side*.11,-.39,.09),.006,ink)
export('DummyBeetle',(-2,-2,1))

begin()
ball('Butterfly body',(0,0,.025),(.025,.16,.03),ink)
for s in [-1,1]:
    wing=ball('Forewing',(s*.15,-.07,.025),(.17,.14,.016),orange);wing.rotation_euler.z=s*.4
    ball('Hindwing',(s*.12,.11,.023),(.11,.11,.015),yellow)
    ball('Wing eyespot',(s*.20,-.075,.043),(.048,.045,.007),ink)
    ball('Eyespot center',(s*.20,-.075,.051),(.022,.023,.004),white)
    rod('Antenna',(s*.012,-.13,.03),(s*.055,-.23,.05),.004,ink)
export('DummyButterfly',(0,-2,1))

begin()
for i in range(95):
    t=i/94*math.pi*4.6; r=.018+.015*t
    ball('Spiral chamber',(math.cos(t)*r,math.sin(t)*r,0),(.019+i*.0005,.019+i*.0005,.035+i*.00035),brass)
export('DummyAmmonite',(2,-2,1))

# A separate workshop scene for reviewing the source models.
objects=[]
cube('Workshop floor',(0,0,-.08),(12,8,.1),mat('Workshop floor',(.12,.16,.18)),0)
bpy.ops.object.camera_add(location=(8,-12,8)); camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=12;scene.camera=camera
for loc,power,size in [((0,-4,8),1800,8),((4,4,6),1400,6)]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Workshop world');scene.world.color=(.25,.25,.25)
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1400;scene.render.resolution_y=850;scene.render.resolution_percentage=100
scene.render.filepath='//../previews/museum_v1_assets.png'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.color_type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(SAVE))
result={'blend':str(SAVE),'models':7,'scene':scene.name,'objects':len(scene.objects)}
