"""Refine the V1 Aimonite using the front, side and back reference views.

The shell follows the multi-view reference, with the requested deeper ammonite
whorls sculpted into both sides. Parameters below keep the relief editable.
Only objects under the Aimonite root are replaced. Other assets are not exported.
"""
import bpy, math, runpy, bmesh
import numpy as np
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
blue=material('Aimonite shell | pale blue',(.57,.69,.85),.53)
gold=material('Aimonite body | soft yellow',(1,.59,.16),.51)
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

# A true expanding spiral replaces the old isolated circular rear dimple.
# Each side has a valley and a broad rounded shoulder; the rear relief is
# stronger, and the front still carries the painted symbols. Units: metres.
SHELL_RADIUS=.72
SPIRAL_TURNS=2.0
GROOVE_BACK_DEPTH=.17
GROOVE_FRONT_DEPTH=.095
spiral=[]
for i in range(1025):
    t=i/1024
    radius=SHELL_RADIUS*.045*20**t
    angle=-2.05+math.tau*SPIRAL_TURNS*(t-1)
    spiral.append(Vector((.06+radius*math.cos(angle),0,1.50+radius*math.sin(angle))))
samples=np.array([tuple(p) for p in spiral])
midpoints=(samples[:-1]+samples[1:])*.5
segment_lengths=np.linalg.norm(samples[1:]-samples[:-1],axis=1)
along=np.linalg.norm(midpoints-np.array((.06,0,1.50)),axis=1)/SHELL_RADIUS
widths=.016+.045*along
core=np.clip(along/.18,0,1)
core=core*core*(3-2*core)
valley_weights=segment_lengths/(math.sqrt(math.pi)*widths)
shoulder_weights=segment_lengths/(math.sqrt(math.pi)*widths*4.0)

def shell_relief(x,z,depth):
    # Integrate smooth kernels along the curve. A nearest-turn field would
    # jump at the boundary between two turns and create visible serrations.
    distances=(midpoints[:,0]-x)**2+(midpoints[:,2]-z)**2
    rear=depth>0
    amount=((.110+GROOVE_BACK_DEPTH*along) if rear else (.047+GROOVE_FRONT_DEPTH*along))*core
    shoulder=float(np.sum((.105 if rear else .040)*core*shoulder_weights*np.exp(-distances/(widths*4.0)**2)))
    groove_kernel=valley_weights*np.exp(-distances/widths**2)
    valley=float(np.sum(amount*groove_kernel))
    # Fade before the outer rim where the closed shell becomes thin.
    radius=math.hypot(x-.06,z-1.50)/SHELL_RADIUS
    edge=max(0,min(1,(1-radius)/.16));edge=edge*edge*(3-2*edge)
    # Rounded transverse ribs on the undecorated back recall ammonite shell
    # sculpture. They fade toward the central curl and outer silhouette.
    angle=math.atan2(z-1.50,x-.06)
    rib_mask=max(0,min(1,(radius-.28)/.30))
    groove_mask=1-min(1,float(np.sum(groove_kernel)))**.5
    ribs=(.025 if rear else .003)*rib_mask*groove_mask*(.5+.5*math.cos(34*angle+5*radius))**4
    relief=(shoulder-valley+ribs)*edge
    half_thickness=abs(depth)*(.34 if rear else .30)
    return max(-half_thickness*.82,relief)

# One welded closed surface with shared poles and outward normals.
verts=[(.06,.37+shell_relief(.06,1.50,1),1.50)];faces=[];rings=192;sides=288
for i in range(1,rings):
    theta=math.pi*i/rings
    for j in range(sides):
        phi=math.tau*j/sides
        u=math.sin(theta)*math.cos(phi);v=math.sin(theta)*math.sin(phi)
        depth=math.cos(theta)
        x=.06+.72*u;z=1.50+.72*v
        y=.03+depth*(.30 if depth<0 else .34)
        y+=(1 if depth>0 else -1)*shell_relief(x,z,depth)
        verts.append((x,y,z))
south=len(verts);verts.append((.06,-.27-shell_relief(.06,1.50,-1),1.50))
for j in range(sides):faces.append((0,1+j,1+(j+1)%sides))
for i in range(rings-2):
    for j in range(sides):
        a=1+i*sides+j;b=1+i*sides+(j+1)%sides
        faces.append((a,a+sides,b+sides,b))
for j in range(sides):
    a=1+(rings-2)*sides+j;b=1+(rings-2)*sides+(j+1)%sides
    faces.append((a,south,b))
mesh=bpy.data.meshes.new('Rounded coiled shell mesh');mesh.from_pydata(verts,[],faces);mesh.update()
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
if any(not e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:
    raise RuntimeError('Shell must be a closed outward-facing volume')
bm.to_mesh(mesh);bm.free()
shell=bpy.data.objects.new('Shell | rounded continuous whorl',mesh);scene.collection.objects.link(shell);add(shell,shell.name,blue)
for f in mesh.polygons:f.use_smooth=True

aperture=runpy.run_path(str(Path(__file__).with_name('aimonite_aperture.py')))
aperture_details=aperture['carve_aperture'](shell,blue)

def surface(x,z,offset=.009):
    hit,point,normal,_=shell.ray_cast(Vector((x,-3,z)),Vector((0,1,0)))
    if not hit:return None
    return (x,point.y-offset,z)

def drawline(name,coords,mat,width=.0022):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=width;curve.bevel_resolution=2
    spline=curve.splines.new('POLY');spline.points.add(len(coords)-1)
    for p,co in zip(spline.points,coords):p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve);scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target='MESH');obj=bpy.context.object;add(obj,name,mat);obj.select_set(False)

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
    # Triangulate and subdivide before projection so the fill hugs the shell
    # instead of forming large planar facets that cut through its surface.
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    # Adapt to the actual edge length so decals cannot bridge a deep valley.
    for _ in range(8):
        long=[e for e in bm.edges if math.hypot(e.verts[0].co.x-e.verts[1].co.x,e.verts[0].co.z-e.verts[1].co.z)>.009]
        if not long:break
        bmesh.ops.subdivide_edges(bm,edges=long,cuts=1,use_grid_fill=True)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
    for v in bm.verts:
        point=surface(v.co.x,v.co.z)
        if point:v.co=point
    bm.to_mesh(me);bm.free();me.update()
    for face in me.polygons:face.use_smooth=True
    obj=bpy.data.objects.new(name,me);scene.collection.objects.link(obj);add(obj,name,mat)
    # Subdivide each outline segment on the surface, then combine it into one mesh.
    border=[]
    for i in range(len(coords)):
        a=Vector(coords[i]);b=Vector(coords[(i+1)%len(coords)])
        for j in range(max(1,math.ceil((b-a).length/.012))):
            p=a.lerp(b,j/max(1,math.ceil((b-a).length/.012)))
            hit=surface(p.x,p.z,.013)
            if hit:border.append(hit)
    if border:drawline(name+' outline',border+[border[0]],ink)

def stroke(name,points):
    projected=[surface(x,z,.019) for x,z in points]
    valid=[p for p in projected if p is not None]
    if len(valid)>=2:drawline(name,valid,ink,.002)

symbols=runpy.run_path(str(Path(__file__).with_name('aimonite_symbols.py')))
symbols['add_symbols'](patch,stroke,colors,center=(.06,1.50))

# Body and small props follow the reference; proportions at the rear are inferred.
ball('Face',(-.27,-.16,.80),(.255,.21,.29),gold)
for x in [-.46,-.08]:
    ball('Eye white',(x,-.335,.84),(.051,.025,.073),white)
    ball('Pupil',(x,-.358,.84),(.021,.012,.041),ink)
for x in [-.34,-.20]:
    rod('Leg',(x,-.13,.55),(x,-.13,.28),.023,gold)
    rod('White boot',(x,-.13,.28),(x,-.16,.07),.027,white)
    rod('Boot lace', (x-.018,-.163,.25),(x+.018,-.163,.25),.003,ink)
    rod('Boot lace', (x,-.164,.25),(x-.012,-.164,.23),.003,ink)
    rod('Boot lace', (x,-.164,.25),(x+.012,-.164,.23),.003,ink)
    ball('Boot',(x,-.20,.055),(.05,.085,.045),white)
    ball('Boot outer toe',(x-.022,-.257,.043),(.025,.035,.027),white)
    ball('Boot inner toe',(x+.022,-.257,.043),(.025,.035,.027),white)
rod('Left arm',(-.49,-.15,.70),(-.52,-.18,.24),.021,gold)
ball('Left hand',(-.52,-.18,.22),(.038,.033,.044),gold)
rod('Right arm',(-.06,-.15,.68),(.06,-.17,.44),.023,gold)
rod('Right forearm',(.06,-.17,.44),(-.02,-.23,.35),.023,gold)
ball('Right hand',(-.02,-.23,.35),(.038,.035,.04),gold)
rod('Brush handle',(-.52,-.20,.25),(-.52,-.20,.07),.009,grey)
rod('Brush light ferrule',(-.52,-.20,.10),(-.52,-.20,.075),.010,white)
ball('Brush tip',(-.52,-.20,.052),(.016,.017,.037),ink)
ball('Seal body',(-.035,-.17,.40),(.12,.075,.07),grey)
ball('Seal head',(-.13,-.22,.43),(.06,.05,.045),grey)
for x in [-.15,-.11]:ball('Seal eye',(x,-.265,.45),(.006,.004,.006),ink)
ball('Seal flipper',(.07,-.16,.36),(.055,.035,.025),grey)

if len(created)<40: raise RuntimeError('Unexpectedly few components; old model retained')
old=list(root.children_recursive)
for obj in old:bpy.data.objects.remove(obj,do_unlink=True)
for obj in created:obj.parent=root
rigging=runpy.run_path(str(Path(__file__).with_name('rig_aimonite.py')))
rig=rigging['rig_character'](root,created)
bpy.ops.object.select_all(action='DESELECT')
for obj in created:obj.select_set(True)
bpy.context.view_layer.objects.active=shell
workshop_position=root.location.copy()
try:
    # The workshop displays the character four metres aside; Unity needs its
    # local origin at the feet, not that workshop display offset.
    root.location=(0,0,0)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH','ARMATURE'},apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False)
finally:
    root.location=workshop_position
    bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
result={'objects':len(created),'fbx':str(fbx),'source':str(path),'shell_vertices':len(verts)}
