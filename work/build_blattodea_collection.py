"""Original teaching models of a cockroach and a soldier termite.

Run with Blender --background --factory-startup --python this_file.py.
Uses no external image assets. +Z up, head toward -Y, centered origin and
maximum export dimension 1m; this normalization is not a life-size claim.
The models illustrate group features and are not identified museum specimens.

Taxonomy and morphology:
https://www.nhm.ac.uk/our-science/services/collections/entomology/small-orders.html
https://ask.ifas.ufl.edu/publication/in278
https://ask.ifas.ufl.edu/publication/in369
"""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'blender/scenes/collections/blattodea.blend'
PREVIEW=ROOT/'blender/previews/collections/blattodea.png'
EXPORT=ROOT/'unity/VirtualMuseum/Assets/Museum/Models/Collections'
if bpy.data.filepath and Path(bpy.data.filepath).resolve()!=SOURCE.resolve():
    raise RuntimeError('Use a fresh background Blender process')
for p in (SOURCE.parent,PREVIEW.parent,EXPORT):p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='Blattodea | cockroach and termite comparison'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
asset='';parts=[];assets={}

def material(name,color,roughness=.5):
    mat=bpy.data.materials.new('Collection_'+name);mat.use_nodes=True
    mat.diffuse_color=(*color,1);mat.roughness=roughness
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Roughness'].default_value=roughness
    return mat

roach=material('RoachChestnut',(.105,.035,.015),.34)
roach_wing=material('RoachWingBrown',(.19,.064,.023),.30)
roach_edge=material('RoachAmberEdge',(.36,.17,.045),.43)
roach_vein=material('RoachWingVeins',(.07,.023,.009),.48)
black=material('BlattodeaDarkCuticle',(.014,.010,.006),.30)
pale=material('TermiteSoftIvory',(.78,.70,.51),.62)
pale_joint=material('TermiteJointMembrane',(.46,.36,.22),.76)
head=material('TermiteAmberHead',(.38,.16,.025),.33)
legs=material('TermiteLegIvory',(.66,.53,.32),.53)

def finish(obj,name,mat,smooth=False):
    obj.name=asset+' | '+name;obj['generator']='museum_blattodea_v1'
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:p.use_smooth=True
    parts.append(obj);return obj

def mesh(name,vertices,faces,mat,smooth=False):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
    return finish(obj,name,mat,smooth)

def ellipsoid(name,center,size,mat,n=24,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=n,ring_count=rings,location=center)
    obj=bpy.context.object;obj.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(obj,name,mat,True)

def tube(name,points,radii,mat,n=8,flatten=1):
    points=[Vector(p) for p in points];vertices=[];faces=[]
    for i,p in enumerate(points):
        tangent=points[min(i+1,len(points)-1)]-points[max(0,i-1)]
        rotation=tangent.to_track_quat('Z','Y')
        r=radii[i] if isinstance(radii,list) else radii
        for j in range(n):
            a=j*math.tau/n;v=rotation@Vector((r*math.cos(a),r*math.sin(a),0))
            v.z*=flatten;vertices.append(tuple(p+v))
    for i in range(len(points)-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
    faces.extend([tuple(range(n-1,-1,-1)),tuple((len(points)-1)*n+j for j in range(n))])
    return mesh(name,vertices,faces,mat,True)

def line(name,start,end,radius,mat,tip=None,n=6):
    return tube(name,[start,end],[radius,radius if tip is None else tip],mat,n)

def antenna_path(sign,t):
    return Vector((sign*(.043+.21*t+.05*math.sin(t*math.pi)), -.245-.37*t, .09+.10*math.sin(t*math.pi*.85)))

def begin(name):
    global asset,parts
    asset=name;parts=[]

def end():
    bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get()
    points=[obj.matrix_world@v.co for obj in parts for v in obj.evaluated_get(depsgraph).data.vertices]
    lo=Vector([min(v[k] for v in points) for k in range(3)])
    hi=Vector([max(v[k] for v in points) for k in range(3)])
    midpoint=(lo+hi)*.5;factor=1/max(hi-lo)
    root=bpy.data.objects.new(asset,None);scene.collection.objects.link(root)
    root['generator']='museum_blattodea_v1'
    root['taxonomy']='Blattodea: cockroaches and termites'
    root['interpretation']='Illustrative educational model, species unspecified'
    for obj in parts:
        transform=Matrix.Scale(factor,4)@obj.matrix_world
        transform.translation=(obj.matrix_world.translation-midpoint)*factor
        obj.matrix_world=transform;obj.parent=root
    assets[asset]=(root,list(parts))

begin('Cockroach')
ellipsoid('flattened abdomen',(0,.055,.065),(.122,.222,.053),roach)
# Lateral abdominal tergite margins remain visible beside the closed wings.
for i in range(7):
    y=-.015+i*.039
    radius=.115*math.sqrt(max(.05,1-((y-.055)/.225)**2))
    for sign in (-1,1):
        ellipsoid('abdominal plate edge',(sign*radius,y,.061),(.017,.025,.013),roach_edge,16,8)
ellipsoid('concealed head',(0,-.206,.065),(.069,.068,.044),roach)
ellipsoid('shield pronotum',(0,-.137,.113),(.121,.096,.036),roach_edge)
ellipsoid('pronotum central dark patch',(0,-.136,.130),(.097,.075,.023),roach)
for sign in (-1,1):
    ellipsoid('compound eye',(sign*.052,-.227,.079),(.016,.023,.019),black,18,10)
    tube('labial palp',[(sign*.025,-.246,.053),(sign*.055,-.278,.035),(sign*.042,-.300,.037)],[.006,.004,.0025],roach_edge,8)
    tube('maxillary palp',[(sign*.038,-.238,.045),(sign*.077,-.257,.041),(sign*.090,-.279,.038)],[.007,.004,.0025],roach,8)
    points=[antenna_path(sign,i/44) for i in range(45)]
    tube('long filiform antenna',points,[.0045*(1-i/50) for i in range(45)],roach_vein,6)
    for i in range(1,24):
        t=i/26;p=antenna_path(sign,t)
        ellipsoid('antennal annulation',p,(.0032*(1-t*.65),)*3,roach_edge,8,4)

def wing_surface(sign,t,u):
    width=.117*(math.sin(math.pi*t)**.43)
    y=-.106+.387*t
    x=sign*(.002+width*u)
    z=.077+.045*(math.sin(math.pi*t)**.65)*(1-u*u)
    return Vector((x,y,z))

for sign in (-1,1):
    vertices=[];faces=[];rows=26;columns=9
    for i in range(rows+1):
        for j in range(columns+1):vertices.append(tuple(wing_surface(sign,i/rows,j/columns)))
    for i in range(rows):
        for j in range(columns):
            a=i*(columns+1)+j
            faces.append((a,a+1,a+columns+2,a+columns+1) if sign>0 else (a+columns+1,a+columns+2,a+1,a))
    obj=mesh('closed leathery forewing',vertices,faces,roach_wing,True)
    mod=obj.modifiers.new('Wing thickness','SOLIDIFY');mod.thickness=.0015
    for vein in range(7):
        path=[]
        for i in range(18):
            t=.09+i*.85/17
            u=.06+(vein+.5)/8*(.3+.7*t)
            p=wing_surface(sign,t,u);p.z+=.0015;path.append(p)
        tube('longitudinal wing vein',path,.0009,roach_vein,5)
    for i in range(7):
        t=.31+i*.08
        path=[wing_surface(sign,t+.022*u,u)+Vector((0,0,.0016)) for u in (.18,.35,.52,.69,.84)]
        tube('cross wing vein',path,.00065,roach_edge,5)
    for i,(y,dx,dy) in enumerate([(-.135,.22,-.13),(-.025,.285,.025),(.105,.29,.16)]):
        origin=(sign*.088,y,.066)
        knee=(sign*(dx*.64),y+dy*.38,.045)
        ankle=(sign*dx,y+dy,.019)
        foot=(sign*(dx+.045),y+dy+.04,.013)
        tube('coxa and femur',[origin,knee],[.019,.014],roach,10)
        tube('long tibia',[knee,ankle],[.010,.006],roach_edge,8)
        tube('segmented tarsus',[ankle,foot,(foot[0]+sign*.018,foot[1]+.026,.014)],[.0055,.0035,.0015],roach,8)
        for j in range(8):
            p=Vector(knee).lerp(Vector(ankle),(j+1)/9)
            for side in (-1,1):
                tip=p+Vector((sign*.013,side*.018,-.004))
                line('tibial spine',p,tip,.0025,black,tip=.0002,n=5)
        for j in range(4):
            p=Vector(ankle).lerp(Vector(foot),(j+1)/5)
            ellipsoid('tarsal joint',p,(.005,.006,.004),roach_edge,10,5)
    tube('segmented cercus',[(sign*.041,.251,.056),(sign*.059,.289,.059),(sign*.074,.326,.055)],[.012,.007,.0015],roach_edge,10)
end()

begin('Termite')
# One soft body surface, with gentle segment furrows and no ant-like petiole.
vertices=[];faces=[];rings=65;sides=24
for i in range(rings+1):
    t=i/rings;y=.015+.345*t
    width=.102*(math.sin(math.pi*(.10+.90*t))**.48)
    width=max(.003,width)
    segment=1-.045*(.5+.5*math.cos(t*math.tau*8))
    for j in range(sides):
        a=j*math.tau/sides
        vertices.append((width*math.cos(a)*segment,y,.079+width*.64*math.sin(a)*segment))
for i in range(rings):
    for j in range(sides):
        a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,a+sides,b+sides,b))
faces.extend([tuple(range(sides)),tuple(rings*sides+j for j in range(sides-1,-1,-1))])
body=mesh('soft segmented abdomen',vertices,faces,pale,True)
body.data.materials.append(pale_joint)
for p in body.data.polygons:
    t=(p.index//sides)/rings
    if math.cos(t*math.tau*8)>.985:p.material_index=1
for y,width in [(-.073,.064),(-.019,.066),(.028,.071)]:
    ellipsoid('broad thoracic segment',(0,y,.076),(width,.041,.045),pale)
ellipsoid('small saddle pronotum',(0,-.099,.105),(.071,.037,.025),pale_joint)
ellipsoid('large soldier head',(0,-.222,.090),(.105,.143,.068),head,32,16)
ellipsoid('clypeus',(0,-.340,.079),(.047,.039,.025),head,20,10)
for sign in (-1,1):
    length=1 if sign<0 else .95
    tube('sclerotized soldier mandible',[(sign*.062,-.333,.098),(sign*.078,-.386,.098),(sign*.067,-.434*length,.097),(sign*.023,-.470*length,.093),(-sign*.008,-.477*length,.091)],
        [.020,.018,.013,.007,.0007],black,12,flatten=.60)
    line('mandible tooth',(sign*.061,-.400,.096),(sign*.034,-.407,.098),.009,black,tip=.0006,n=6)
    for i in range(16):
        t=i/15
        p=Vector((sign*(.087+.116*t+.018*math.sin(t*math.pi)), -.265-.143*t,.092+.026*math.sin(t*math.pi)))
        r=.0085-.0036*t
        ellipsoid('beadlike antenna segment',p,(r,r*1.07,r),legs,12,6)
        if i:
            line('antennal membrane',previous,p,r*.50,pale_joint,n=6)
        previous=p
    for i,y in enumerate([-.080,-.021,.037]):
        origin=(sign*.048,y,.073)
        knee=(sign*(.10+i*.006),y-.027+i*.018,.044)
        ankle=(sign*(.168+i*.012),y-.051+i*.053,.014)
        foot=(sign*(.205+i*.014),ankle[1]+.013,.009)
        tube('six delicate articulated legs',[origin,knee,ankle,foot],[.010,.008,.0045,.002],legs,9)
        ellipsoid('leg joint',knee,(.009,.010,.008),pale_joint,12,6)
        line('paired tarsal claw',foot,(foot[0]+sign*.016,foot[1]+.012,.007),.0018,black,tip=.0003,n=5)
        line('paired tarsal claw',foot,(foot[0]+sign*.014,foot[1]-.006,.006),.0018,black,tip=.0003,n=5)
    tube('short terminal cercus',[(sign*.025,.345,.061),(sign*.037,.371,.060)],[.005,.001],legs,8)
end()

def export(name,root,originals):
    depsgraph=bpy.context.evaluated_depsgraph_get();grouped={}
    for obj in originals:
        evaluated=obj.evaluated_get(depsgraph)
        data=bpy.data.meshes.new_from_object(evaluated,depsgraph=depsgraph)
        copy=bpy.data.objects.new('export part',data);scene.collection.objects.link(copy)
        copy.matrix_world=obj.matrix_world.copy()
        grouped.setdefault(tuple(m.name for m in data.materials),[]).append(copy)
    exported=[]
    for materials,objects in grouped.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        if len(objects)>1:bpy.ops.object.join()
        obj=bpy.context.object;obj.name=name+'_'+materials[0].replace('Collection_','');exported.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in exported:obj.select_set(True)
    bpy.context.view_layer.objects.active=exported[0]
    pending=EXPORT/('.'+name+'.pending')
    bpy.ops.export_scene.fbx(filepath=str(pending),use_selection=True,object_types={'MESH'},apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',bake_space_transform=False,
        use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='STRIP')
    pending.replace(EXPORT/(name+'.fbx'))
    points=[obj.matrix_world@v.co for obj in exported for v in obj.data.vertices]
    dimensions=[max(p[k] for p in points)-min(p[k] for p in points) for k in range(3)]
    triangles=sum(len(p.vertices)-2 for obj in exported for p in obj.data.polygons)
    print('BLATTODEA_ASSET '+json.dumps({'name':name,'triangles':triangles,'meshes':len(exported),
        'materials':sorted({m.name for obj in exported for m in obj.data.materials}),'dimensions':dimensions}))
    assert triangles<20000
    for obj in exported:
        data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
        if data.users==0:bpy.data.meshes.remove(data)

for name,(root,objects) in assets.items():export(name,root,objects)
for name,(root,objects) in assets.items():
    root.location.x=-.62 if name=='Cockroach' else .62
    bpy.context.view_layer.update()
    minimum=min((obj.matrix_world@v.co).z for obj in objects for v in obj.data.vertices)
    root.location.z+=.045-minimum

# Preview supports and labels are not exported into the specimens.
preview=material('BlattodeaPreviewStone',(.20,.23,.22),.88)
labelmat=material('BlattodeaPreviewLabel',(.88,.86,.75),.82)
for name,(root,objects) in assets.items():
    bpy.ops.mesh.primitive_cube_add(size=1,location=(root.location.x,0,.015))
    plate=bpy.context.object;plate.name=name+' | preview-only plinth';plate.scale=(1.05,1.15,.045)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);plate.data.materials.append(preview)
    bevel=plate.modifiers.new('Plinth bevel','BEVEL');bevel.width=.018;bevel.segments=3
    bpy.ops.object.text_add(location=(root.location.x-.46,-.535,.043))
    text=bpy.context.object;text.data.body='COCKROACH / BLATTODEA' if name=='Cockroach' else 'TERMITE / SOLDIER'
    text.data.size=.042;text.data.extrude=.0002;text.data.materials.append(labelmat)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));bpy.context.object.data.materials.append(preview)
scene.world=bpy.data.worlds.new('Blattodea studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.28,.31,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.43
for position,power,size in [((-2,-2,4),500,3),((3,1,3),650,2),((0,3,4),500,3)]:
    bpy.ops.object.light_add(type='AREA',location=position);light=bpy.context.object
    light.data.energy=power;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.8,-2.5,3.6));camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,.03))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=2.75;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.render.filepath=str(PREVIEW)
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),check_existing=False)
bpy.ops.render.render(write_still=True)
print('BLATTODEA_COMPLETE')
