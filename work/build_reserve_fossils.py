"""Create five original generalized fossils for future exhibits.

Use a separate Blender background process, --threads 2, and -- --overwrite
only after reviewing this script's owned .blend, gallery and five FBX files.
Editable original geometry; no scans, downloaded textures, named locality,
precise age or species-identification claims. Maximum export dimension 1 m.

Morphological references consulted 2026-11-07:
https://naturalhistory.si.edu/education/teaching-resources/paleontology/information-about-fossil-family-day-trilobite-model
https://collections.st-andrews.ac.uk/item/orthocone-nautiloids/1017569
https://www.app.pan.pl/archive/published/app49/app49-057.pdf
https://www.bgs.ac.uk/discovering-geology/fossils-and-geological-time/crinoids/
https://www.floridamuseum.ufl.edu/discover-fish/sharks/fossil/shark-tooth-id-guide/
https://multilingualmuseum.manchester.ac.uk/object/fossil-fern/
"""
import bpy, math, random, runpy, sys, json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[1]
SAVE=ROOT/'blender/scenes/collections/reserve_fossils.blend'
PREVIEW=ROOT/'blender/previews/collections/reserve_fossils.png'
EXPORT=ROOT/'unity/VirtualMuseum/Assets/Museum/Models/Reserve'
NAMES=['TrilobiteFossil','OrthoconeFossil','CrinoidStemFossil','SharkToothFossil','FernFossil']
if '--overwrite' not in sys.argv and any(p.exists() for p in [SAVE,PREVIEW]+[EXPORT/(n+'.fbx') for n in NAMES]):
    raise RuntimeError('Owned outputs exist; review them before passing --overwrite.')
for folder in (SAVE.parent,PREVIEW.parent,EXPORT):folder.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
export_groups=runpy.run_path(str(ROOT/'work/export_static_fbx.py'))['export_selected_groups']
current=None;parts=[];reports=[]
random.seed(1823)

def mat(label,color,rough=.45,metal=0,alpha=1):
    m=bpy.data.materials.new(current.name+'_'+label);m.use_nodes=True;m.diffuse_color=(*color,alpha)
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,alpha)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Alpha'].default_value=alpha
    if alpha<1:m.surface_render_method='DITHERED';m.use_transparent_shadow=True
    return m

def mesh(name,verts,faces,material,smooth=True):
    data=bpy.data.meshes.new(current.name+' '+name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(data.name,data);current.objects.link(obj);data.materials.append(material)
    for p in data.polygons:p.use_smooth=smooth
    parts.append(obj);return obj

def ball(name,loc,scale,material,seg=20,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    obj=bpy.context.object;obj.name=current.name+' '+name;obj.scale=scale
    for col in list(obj.users_collection):col.objects.unlink(obj)
    current.objects.link(obj);obj.data.materials.append(material)
    for p in obj.data.polygons:p.use_smooth=True
    parts.append(obj);return obj

def tube(name,points,radii,material,sides=7):
    points=[Vector(p) for p in points]
    if isinstance(radii,(float,int)):radii=[radii]*len(points)
    verts=[];faces=[]
    for i,p in enumerate(points):
        tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        cross=tangent.cross(Vector((0,0,1)))
        if cross.length<.01:cross=tangent.cross(Vector((0,1,0)))
        cross.normalize();other=tangent.cross(cross).normalized()
        for j in range(sides):
            a=j*math.tau/sides;verts.append(tuple(p+radii[i]*(cross*math.cos(a)+other*math.sin(a))))
    for i in range(len(points)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,material)

def curve(name,control,radius,material,end=None,steps=5,sides=6):
    p=[Vector(v) for v in control];out=[]
    for i in range(len(p)-1):
        a=p[max(i-1,0)];b=p[i];c=p[i+1];d=p[min(i+2,len(p)-1)]
        for j in range(steps):
            t=j/steps;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(p[-1]);end=radius if end is None else end
    return tube(name,out,[radius+(end-radius)*i/(len(out)-1) for i in range(len(out))],material,sides)

def mirror(points,s):return [(s*p[0],p[1],p[2]) for p in points]



def slab(material,edge,width=.42,length=.49,height=.07):
    n=30;outline=[]
    for j in range(n):
        angle=j*math.tau/n;r=1+random.uniform(-.10,.08)
        outline.append((width*r*math.cos(angle),length*r*math.sin(angle)))
    verts=[(0,0,.0)]+[(x,y,random.uniform(-.002,.002)) for x,y in outline]+[(x*.96,y*.96,-height+random.uniform(-.012,.008)) for x,y in outline]+[(0,0,-height)]
    faces=[(0,1+j,1+(j+1)%n) for j in range(n)]
    faces += [(1+j,1+n+j,1+n+(j+1)%n,1+(j+1)%n) for j in range(n)]
    faces += [(1+2*n,1+n+(j+1)%n,1+n+j) for j in range(n)]
    mesh('broken rock slab',verts,faces,material,False)
    for layer in range(2):
        path=[(x*(.99-layer*.012),y*(.99-layer*.012),-.022-layer*.027) for x,y in outline]
        tube('bedding plane',path+[path[0]],.0015,edge,5)
    return outline

def flecks(material,count=60,width=.4,length=.46):
    for i in range(count):
        x=random.uniform(-width,width);y=random.uniform(-length,length)
        if (x/width)**2+(y/length)**2>.85:continue
        r=random.uniform(.002,.006)
        ball('matrix grain',(x,y,.003),(r,r*.7,.0018),material,8,4)

def polygon_solid(name,outline,material,top=.04,bottom=0):
    if sum(outline[i][0]*outline[(i+1)%len(outline)][1]-outline[(i+1)%len(outline)][0]*outline[i][1] for i in range(len(outline)))<0:outline=list(reversed(outline))
    p=[Vector((x,y,top)) for x,y in outline];n=len(p);lookup={tuple(v):i for i,v in enumerate(p)}
    verts=[tuple(v) for v in p]+[(x,y,bottom) for x,y in outline];faces=[]
    for tri in tessellate_polygon([p]):
        ids=tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in tri)
        if (p[ids[1]]-p[ids[0]]).cross(p[ids[2]]-p[ids[0]]).z<0:ids=ids[::-1]
        faces.extend([ids,tuple(n+i for i in reversed(ids))])
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh(name,verts,faces,material,False)

def trilobite():
    rock=mat('Siltstone',(.31,.255,.18),.9);grain=mat('MatrixGrain',(.43,.36,.25),.92)
    shell=mat('FossilCuticle',(.115,.074,.037),.60);ridge=mat('RidgeHighlights',(.19,.13,.070),.65)
    dark=mat('IncisedSutures',(.045,.034,.023),.8)
    slab(rock,grain);flecks(grain,90)
    # Convex central axial lobe flanked by paired pleural lobes.
    ball('head shield',(0,.24,.024),(.219,.143,.043),shell,32,16)
    ball('glabella',(0,.255,.055),(.074,.112,.052),ridge,24,12)
    curve('cephalon border',[(-.21,.21,.033),(-.19,.30,.043),(0,.376,.04),(.19,.30,.043),(.21,.21,.033)],.007,ridge,steps=7)
    for s in(-1,1):
        ball('lateral eye ridge',(s*.126,.278,.064),(.028,.052,.022),ridge,18,10)
        curve('facial suture',mirror([(.13,.34,.054),(.10,.28,.064),(.15,.21,.055)],s),.0024,dark)
        curve('genal tip',mirror([(.18,.25,.029),(.219,.19,.018),(.226,.13,.009)],s),.009,shell,end=.001,steps=5)
    for i in range(12):
        y=.155-i*.033;w=.205-i*.0065
        ball('axial thoracic ring',(0,y,.055),(.067-i*.0019,.021,.042-i*.0011),ridge,20,10)
        for s in(-1,1):
            curve('pleural rib',mirror([(.058-i*.0013,y,.062),(.12-i*.003,y-.006,.044),(w,y-.03,.020),(w+.007,y-.051,.006)],s),.011-i*.00030,shell,end=.003,steps=4,sides=9)
            curve('pleural furrow',mirror([(.08,y+.006,.052),(.13-i*.003,y-.001,.036),(w-.009,y-.027,.023)],s),.0015,dark,steps=4)
    ball('pygidium',(0,-.285,.021),(.126,.105,.032),shell,28,14)
    for i in range(4):
        y=-.25-i*.023;w=.10-i*.02
        curve('pygidial ring',[(-w,y,.041),(0,y+.015,.058),(w,y,.041)],.0032,ridge,steps=6)
    curve('matrix crack',[(-.39,.06,.004),(-.29,.025,.004),(-.23,.045,.004)],.0017,dark)

def orthocone():
    rock=mat('DarkLimestone',(.092,.105,.099),.77);grain=mat('CalciticMatrix',(.17,.19,.17),.8)
    shell=mat('ShellWall',(.62,.57,.43),.58);fill=mat('ChamberInfill',(.35,.39,.34),.73)
    septum=mat('Septa',(.76,.70,.55),.54);siph=mat('Siphuncle',(.18,.19,.12),.7)
    slab(rock,grain,width=.30);flecks(grain,85,width=.28)
    outline=[(-.014,-.425),(-.17,.355),(-.165,.405),(.165,.405),(.17,.355),(.014,-.425)]
    polygon_solid('longitudinal shell section',outline,shell,.018,.001)
    polygon_solid('exposed chamber infill',[(-.006,-.40),(-.157,.355),(-.151,.386),(.151,.386),(.157,.355),(.006,-.40)],fill,.021,.018)
    # Chamber partitions are curved, and grow farther apart toward the aperture.
    for i in range(13):
        f=(i/14)**1.2;y=-.37+f*.72;w=.012+(y+.425)/.83*.153
        curve('transverse septum',[(-w,y,.029),(-w*.6,y-.025,.03),(0,y-.038,.032),(w*.6,y-.025,.03),(w,y,.029)],.004,septum,steps=6)
    tube('central siphuncle',[(0,-.40,.027),(0,.37,.027)],[.004,.011],siph,10)
    for s in(-1,1):curve('raised shell rim',mirror([(.014,-.42,.024),(.065,-.12,.027),(.118,.14,.03),(.165,.395,.032)],s),.0045,shell,steps=7)
    curve('broken matrix seam',[(-.265,-.19,.006),(-.22,-.13,.004),(-.19,-.10,.004)],.002,siph)

def annulus(name,center,radius,hole,thickness,material,axis='Z',star=False):
    n=50;verts=[]
    for layer in(-1,1):
        for inner in(False,True):
            for j in range(n):
                a=j*math.tau/n;r=hole if inner else radius
                if star:r*=1+(.15 if inner else .10)*math.cos(5*a)
                p=Vector((r*math.cos(a),r*math.sin(a),layer*thickness*.5))
                if axis=='Y':p=Vector((p.x,-p.z,p.y))
                verts.append(tuple(Vector(center)+p))
    faces=[]
    for j in range(n):
        k=(j+1)%n
        faces.extend([(j,k,n+k,n+j),(2*n+j,3*n+j,3*n+k,2*n+k),(j,2*n+j,2*n+k,k),(n+j,n+k,3*n+k,3*n+j)])
    return mesh(name,verts,[tuple(reversed(face)) for face in faces],material,False)

def crinoid():
    rock=mat('Limestone',(.44,.41,.32),.88);grain=mat('LimestoneGrain',(.58,.54,.42),.9)
    calcite=mat('ColumnalCalcite',(.63,.58,.43),.67);edge=mat('ArticulationRidges',(.38,.32,.22),.76)
    dark=mat('BreakFaces',(.22,.20,.15),.9)
    slab(rock,grain);flecks(grain,100)
    # An articulated stem fragment and disarticulated columnals show both the
    # stacking and the central axial canal, rather than resembling a plant stem.
    for i in range(15):
        y=-.30+i*.041;radius=.077+(.009 if i%4==0 else 0)
        annulus('stem columnal',(-.145,y,.079),radius,.019,.034,calcite,'Y')
        if i in(0,14):
            for j in range(24):
                a=j*math.tau/24
                tube('articular radial ridge',[(-.145+.023*math.cos(a),y+(.018 if i==14 else -.018),.079+.023*math.sin(a)),(-.145+radius*.9*math.cos(a),y+(.018 if i==14 else -.018),.079+radius*.9*math.sin(a))],.0018,edge,5)
    for i,(x,y,r) in enumerate([(.13,.25,.082),(.15,.015,.095),(.09,-.245,.070),(.27,-.14,.044)]):
        annulus('loose columnal',(x,y,.025),r,r*.22,.038,calcite,'Z',i==1)
        for j in range(22):
            a=j*math.tau/22
            tube('loose articular ridge',[(x+r*.27*math.cos(a),y+r*.27*math.sin(a),.045),(x+r*.92*math.cos(a),y+r*.92*math.sin(a),.045)],.0016,edge,5)
    curve('stone fissure',[(.24,.36,.004),(.19,.32,.004),(.28,.27,.004)],.002,dark)

def shark():
    enamel=mat('FossilEnamel',(.095,.13,.14),.26)
    rootmat=mat('PorousRoot',(.29,.235,.16),.85);pore=mat('RootGranules',(.16,.145,.11),.93)
    collar=mat('CrownRootBoundary',(.42,.36,.24),.75)
    # A broad triangular serrated crown and bilobed root, generalized rather
    # than attributed to a species or a particular geological occurrence.
    outline=[(0,.45)]
    for s in(1,-1):
        edgepts=[]
        for i in range(1,28):
            f=i/27;x=s*(.245*f);y=.45-.53*f
            if i%2:x+=s*.008
            edgepts.append((x,y))
        if s==1:outline+=edgepts+[(.22,-.135),(-.22,-.135)]
        else:outline+=list(reversed(edgepts))
    p=[Vector((x,y,0)) for x,y in outline];n=len(p)
    verts=[(0,.05,.055),(0,.05,-.031)]+[(v.x,v.y,.002) for v in p]
    faces=[]
    for i in range(n):faces.extend([(0,2+(i+1)%n,2+i),(1,2+i,2+(i+1)%n)])
    mesh('serrated triangular crown',verts,faces,enamel,True)
    rootshape=[(-.25,-.06),(-.31,-.11),(-.32,-.23),(-.22,-.275),(-.10,-.23),(0,-.17),(.10,-.23),(.22,-.275),(.32,-.23),(.31,-.11),(.25,-.06),(.14,-.105),(0,-.12),(-.14,-.105)]
    polygon_solid('bilobed root',rootshape,rootmat,.040,-.045)
    curve('crown root boundary',[(-.24,-.082,.046),(-.13,-.118,.049),(0,-.13,.05),(.13,-.118,.049),(.24,-.082,.046)],.007,collar)
    for i in range(120):
        x=random.uniform(-.30,.30);y=random.uniform(-.22,-.12)
        if abs(x)<.09 and y<-.16:continue
        ball('root porous grain',(x,y,.041),(random.uniform(.002,.006),.003,.0015),pore,8,4)
    tube('root central nutrient groove',[(0,-.125,.045),(0,-.155,.044)],[.003,.004],pore,7)

def fern():
    rock=mat('Shale',(.34,.32,.27),.96);layer=mat('ShaleLayers',(.23,.23,.20),.96)
    carbon=mat('CarbonCompression',(.044,.050,.036),.88);vein=mat('CarbonRachis',(.08,.083,.052),.87)
    grain=mat('FineMatrix',(.42,.39,.32),.97)
    slab(rock,layer,width=.41);flecks(grain,120)
    curve('primary rachis',[(0,-.43,.011),(-.025,-.18,.012),(-.012,.12,.012),(.02,.40,.011)],.006,vein,end=.0015,steps=10)
    for row in range(12):
        y=-.31+row*.059;length=.29*(1-row/14);base=Vector((-.015,y,.012))
        for s in(-1,1):
            tip=base+Vector((s*length,.09,.0));curve('pinna rachis',[base,base.lerp(tip,.55),tip],.0028,vein,end=.0007)
            count=max(3,8-row//2)
            for j in range(count):
                f=.13+j*.76/count;mid=base.lerp(tip,f);remaining=(1-f);leaflen=.045*remaining+.009
                for side in(-1,1):
                    end=mid+Vector((s*leaflen*.30,side*leaflen,.001))
                    direction=(end-mid).normalized();normal=Vector((-direction.y,direction.x,0));w=leaflen*.29
                    points=[mid,mid.lerp(end,.30)+normal*w,mid.lerp(end,.72)+normal*w*.75,end,mid.lerp(end,.72)-normal*w*.75,mid.lerp(end,.30)-normal*w]
                    polygon_solid('pinnule compression',[(v.x,v.y) for v in points],carbon,.013,.010)
                    tube('pinnule midvein',[mid+Vector((0,0,.002)),end+Vector((0,0,.001))],[.0008,.0003],vein,5)
    curve('shale fracture',[(-.34,-.33,.003),(-.25,-.34,.003),(-.18,-.39,.003)],.0012,layer)

def finish(name):
    bpy.context.view_layer.update();points=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box]
    lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
    center=(lo+hi)*.5;factor=1/max(hi-lo)
    for o in parts:o.location=(o.location-center)*factor;o.scale*=factor
    bpy.context.view_layer.update();triangles=0
    for o in parts:o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
    if triangles>25000:raise RuntimeError(name+' exceeds triangle budget: '+str(triangles))
    report=export_groups(EXPORT/(name+'.fbx'),parts)
    report.update(name=name,triangles=triangles,maximum_dimension=1,center=[0,0,0])
    report['materials']=[{'name':m.name,'rgba':list(m.diffuse_color),'roughness':m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value,'metallic':m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value} for m in sorted({o.data.materials[0] for o in parts},key=lambda m:m.name)]
    if report['material_groups']>8:raise RuntimeError('Material budget exceeded')
    reports.append(report)
    study=bpy.data.scenes.new('Study | '+name);study.collection.children.link(current);scene.collection.children.unlink(current)
    return current

collections=[]
for name,builder in zip(NAMES,[trilobite,orthocone,crinoid,shark,fern]):
    current=bpy.data.collections.new(name);scene.collection.children.link(current);parts=[]
    builder();collections.append(finish(name))

current=bpy.data.collections.new('Gallery');scene.collection.children.link(current);parts=[]
scene.name='Reserve fossils | gallery'
bg=mat('Background',(.027,.035,.038),.87);caption=mat('Caption',(.76,.77,.68),.8)
positions=[(-1.25,.75),(0,.75),(1.25,.75),(-.65,-.72),(.65,-.72)]
labels=['01  TRILOBITE','02  ORTHOCONE SECTION','03  CRINOID COLUMNALS','04  SHARK TOOTH','05  FERN COMPRESSION']
for i,(name,col) in enumerate(zip(NAMES,collections)):
    x,y=positions[i]
    inst=bpy.data.objects.new(name+' overview',None);inst.instance_type='COLLECTION';inst.instance_collection=col
    inst.location=(x,y,.11);current.objects.link(inst)
    for line,body,offset,size in [(0,labels[i],-.62,.055),(1,'GENERALIZED FOSSIL STUDY  /  NOT TO SCALE',-.70,.023)]:
        data=bpy.data.curves.new(name+' caption '+str(line),'FONT');data.body=body;data.align_x='CENTER';data.size=size
        obj=bpy.data.objects.new(data.name,data);current.objects.link(obj);obj.location=(x,y+offset,-.05);data.materials.append(caption)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.07));bpy.context.object.name='Gallery ground';bpy.context.object.data.materials.append(bg)
data=bpy.data.cameras.new('Gallery camera');camera=bpy.data.objects.new('Gallery camera',data);scene.collection.objects.link(camera)
camera.location=(0,-1.4,8);camera.rotation_euler=(Vector((0,-.12,0))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=4.04;scene.camera=camera
for name,loc,power,size,color in [('Key',(-3,1,5),520,3,(.95,.97,1)),('Warm fill',(3,-2,4),180,4,(1,.87,.69)),('Rim',(0,4,3),220,3,(.71,.85,1))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Gallery world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.2,.24,.27,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.27
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
bpy.ops.wm.save_as_mainfile(filepath=str(SAVE));bpy.ops.wm.open_mainfile(filepath=str(SAVE));bpy.ops.render.render(write_still=True)
print('RESERVE_FOSSILS_REPORT='+json.dumps(reports,ensure_ascii=False))
print('RESERVE_FOSSILS_COMPLETE')
