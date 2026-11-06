"""Refine the V1 Aimonite in the saved open asset workshop and export its FBX.

The shell's depth and reverse side are an interpretation of the front reference.
Only objects under the Aimonite root are replaced. Other assets are not exported.
"""
import bpy, math
from pathlib import Path
from mathutils import Vector

path=Path(bpy.data.filepath)
if path.name!='museum_v1_assets.blend' or bpy.data.is_dirty:
    raise RuntimeError('Open the saved V1 asset file with no unsaved changes first')
root=bpy.data.objects.get('Aimonite')
if not root or root.type!='EMPTY': raise RuntimeError('Aimonite root missing')
repo=path.resolve().parents[2]
fbx=repo/'unity/VirtualMuseum/Assets/Museum/Models/Aimonite.fbx'
if not fbx.is_file(): raise RuntimeError('Expected Unity FBX is missing')
scene=bpy.data.scenes['Museum V1 | Asset workshop']
if bpy.context.scene!=scene: raise RuntimeError('Open the V1 workshop scene')

def material(name,color,rough=.48):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m
blue=material('Aimonite shell | pale blue',(.52,.65,.80),.43)
gold=material('Aimonite body | soft yellow',(1,.76,.34),.51)
white=material('Aimonite eyes and boots',(.96,.95,.91))
ink=material('Aimonite outlines',(.025,.033,.045))
grey=material('Aimonite seal',(.47,.52,.54))
colors=[material('Aimonite emblem | '+n,c) for n,c in [
 ('insect',(.33,.48,.26)),('artifact',(.69,.37,.31)),('plant',(.13,.32,.22)),
 ('fossil',(.43,.37,.35)),('people pink',(.95,.66,.70)),('people blue',(.28,.72,.74)),
 ('stone',(.35,.34,.35)),('fossil brown',(.55,.45,.41)),('red mineral',(.60,.29,.32)),
 ('planet',(.24,.28,.41)),('wave',(.16,.39,.62)),('map',(.72,.49,.25))]]
created=[]
def add(o,name,mat):
    o.name=name;o.data.materials.append(mat);created.append(o);return o
def ball(name,pos,size,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=pos)
    o=bpy.context.object;o.scale=size
    for f in o.data.polygons:f.use_smooth=True
    return add(o,name,mat)
def rod(name,a,b,r,mat):
    a,b=Vector(a),Vector(b);d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)*.5)
    o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y');return add(o,name,mat)

# A widening continuous spiral tube. The flattened depth is inferred, not measured.
verts=[];faces=[];steps=220;sides=28;end=math.tau*2+4.05
for i in range(steps+1):
    q=i/steps;t=q*end;r=.012+.53*q;thick=.035+.245*q
    center=Vector((.06+r*math.cos(t),.06,1.46+r*math.sin(t)))
    derivative=Vector((.53/end*math.cos(t)-r*math.sin(t),0,.53/end*math.sin(t)+r*math.cos(t))).normalized()
    outward=Vector((-derivative.z,0,derivative.x))
    for j in range(sides):
        angle=math.tau*j/sides
        p=center+outward*(thick*math.cos(angle))+Vector((0,thick*.83*math.sin(angle),0))
        verts.append(tuple(p))
for i in range(steps):
    for j in range(sides):
        a=i*sides+j;b=i*sides+(j+1)%sides
        faces.append((a,b,b+sides,a+sides))
faces.append(tuple(range(sides-1,-1,-1)))
faces.append(tuple(steps*sides+j for j in range(sides)))
mesh=bpy.data.meshes.new('Continuous ammonite spiral mesh');mesh.from_pydata(verts,[],faces);mesh.update()
shell=bpy.data.objects.new('Shell | widening spiral tube',mesh);scene.collection.objects.link(shell);add(shell,shell.name,blue)
for f in mesh.polygons:f.use_smooth=True

def surface(x,z,offset=.009):
    hit,point,normal,_=shell.ray_cast(Vector((x,-3,z)),Vector((0,1,0)))
    if not hit:return None
    return (x,point.y-offset,z)

def patch(name,cx,cz,sx,sz,poly,mat):
    # Project every point onto the shell, so the emblem lies on the curved tube.
    area=sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
    if area<0:poly=list(reversed(poly))
    coords=[surface(cx+x*sx,cz+z*sz) for x,z in poly]
    # Fit the emblem inside the visible curved face without turning it into a dot.
    for _ in range(14):
        if all(v is not None for v in coords): break
        cx=cx*.96+.06*.04;cz=cz*.96+1.46*.04;sx*=.94;sz*=.94
        coords=[surface(cx+x*sx,cz+z*sz) for x,z in poly]
    if any(v is None for v in coords):
        print('Skipped out-of-shell emblem:',name);return
    me=bpy.data.meshes.new(name+' mesh');me.from_pydata(coords,[],[tuple(range(len(coords)))]);me.update()
    obj=bpy.data.objects.new(name,me);scene.collection.objects.link(obj);add(obj,name,mat)
    # Narrow drawn outline follows the relief rather than floating as round dots.
    for i in range(len(coords)):
        p=Vector(coords[i]);q=Vector(coords[(i+1)%len(coords)]);p.y-=.003;q.y-=.003
        rod(name+' outline',p,q,.0035,ink)

circle=[(math.cos(math.tau*i/32),math.sin(math.tau*i/32)) for i in range(32)]
wave=[(-1,-.25),(-.8,-.05),(-.62,.4),(-.4,.8),(-.1,1),(.18,.9),(.3,.65),(.18,.58),(.03,.72),(-.12,.6),(-.23,.35),(-.18,.02),(.05,-.08),(.32,.02),(.42,.23),(.56,.25),(.56,.0),(.7,-.08),(1,.05),(.8,-.45),(.48,-.60),(.12,-.51),(-.2,-.62),(-.55,-.58),(-.9,-.5)]
leaf=[(-.12,-1),(.08,-.65),(.32,-.34),(.6,.3),(.95,1),(.52,.68),(.56,1),(.22,.68),(.10,.92),(-.02,.48),(-.15,.12),(-.3,-.42)]
person=[(-.28,.40),(-.38,.6),(-.30,.86),(0,1),(.29,.86),(.38,.6),(.27,.4),(.45,.2),(.8,-.08),(.74,-.23),(.45,-.15),(.34,-.08),(.37,-.57),(.20,-.96),(.07,-.94),(0,-.53),(-.10,-.94),(-.27,-.95),(-.37,-.53),(-.35,-.04),(-.62,-.35),(-.76,-.25),(-.51,.12)]
artifact=[(-.72,1),(.55,1),(.8,.7),(.68,.38),(.35,.33),(.25,.05),(.36,-.25),(.8,-.45),(.7,-1),(-.7,-1),(-.8,-.55),(-.5,-.12),(-.46,.18),(-.8,.4)]
rock=[(-.9,-.7),(-1,-.1),(-.72,.18),(-.8,.7),(-.3,.9),(.02,.65),(.38,.85),(.57,.56),(1,.48),(.82,.05),(1,-.4),(.42,-.52),(.24,-.95),(-.2,-.78),(-.48,-1)]
mapshape=[(-.4,-1),(-.2,-.5),(-.55,-.3),(-.47,.12),(-.63,.38),(-.48,.9),(-.1,.7),(.16,.82),(.5,1),(.65,.93),(.38,.57),(.17,.45),(.26,.1),(.02,-.06),(.25,-.48),(.1,-.8)]
for args in [
 ('Insect emblem',-.17,1.99,.125,.125,circle,colors[0]),
 ('Artifact emblem',.23,2.02,.12,.14,artifact,colors[1]),
 ('Plant emblem',.48,1.86,.11,.19,leaf,colors[2]),
 ('Fossil emblem',.62,1.51,.13,.12,rock,colors[3]),
 ('Pink people',.43,1.18,.09,.14,person,colors[4]),
 ('Blue people',.60,1.23,.085,.14,person,colors[5]),
 ('Stone emblem',.27,.99,.13,.12,rock,colors[6]),
 ('Brown fossil',.10,1.12,.11,.11,circle,colors[7]),
 ('Red mineral',.35,1.52,.105,.105,circle,colors[8]),
 ('Planet',-.12,1.56,.13,.13,circle,colors[9]),
 ('Wave',-.32,1.30,.17,.10,wave,colors[10]),
 ('Map',-.48,1.75,.12,.18,mapshape,colors[11]),
]: patch(*args)

def stroke(name,points):
    projected=[surface(x,z,.019) for x,z in points]
    for a,b in zip(projected,projected[1:]):
        if a and b: rod(name,a,b,.003,ink)
stroke('Insect wing markings',[(-.27,2.01),(-.18,2.01),(-.08,2.03)])
stroke('Insect dividing line',[(-.18,2.01),(-.16,1.91)])

# Body and small props follow the reference; proportions at the rear are inferred.
ball('Face',(-.27,-.13,.74),(.255,.20,.27),gold)
for x in [-.46,-.08]:
    ball('Eye white',(x,-.305,.78),(.051,.025,.073),white)
    ball('Pupil',(x,-.328,.78),(.021,.012,.041),ink)
for x in [-.34,-.20]:
    rod('Leg',(x,-.13,.55),(x,-.13,.17),.023,gold)
    rod('White boot',(x,-.13,.17),(x,-.16,.07),.027,white)
    ball('Boot',(x,-.20,.055),(.05,.085,.045),white)
rod('Left arm',(-.49,-.12,.64),(-.52,-.18,.24),.021,gold)
ball('Left hand',(-.52,-.18,.22),(.038,.033,.044),gold)
rod('Right arm',(-.06,-.12,.62),(.06,-.17,.44),.023,gold)
rod('Right forearm',(.06,-.17,.44),(-.02,-.23,.35),.023,gold)
ball('Right hand',(-.02,-.23,.35),(.038,.035,.04),gold)
rod('Brush handle',(-.52,-.20,.25),(-.52,-.20,.07),.009,grey)
ball('Brush tip',(-.52,-.20,.052),(.016,.017,.037),ink)
ball('Seal body',(-.035,-.17,.40),(.12,.075,.07),grey)
ball('Seal head',(-.13,-.22,.43),(.06,.05,.045),grey)
for x in [-.15,-.11]:ball('Seal eye',(x,-.265,.45),(.006,.004,.006),ink)
ball('Seal flipper',(.07,-.16,.36),(.055,.035,.025),grey)

if len(created)<80: raise RuntimeError('Unexpectedly few components; old model retained')
old=list(root.children)
for obj in old:bpy.data.objects.remove(obj,do_unlink=True)
for obj in created:obj.parent=root
bpy.ops.object.select_all(action='DESELECT')
for obj in created:obj.select_set(True)
bpy.context.view_layer.objects.active=shell
workshop_position=root.location.copy()
try:
    # The workshop displays the character four metres aside; Unity needs its
    # local origin at the feet, not that workshop display offset.
    root.location=(0,0,0)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_anim=False)
finally:
    root.location=workshop_position
    bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
result={'objects':len(created),'fbx':str(fbx),'source':str(path),'shell_vertices':len(verts)}
