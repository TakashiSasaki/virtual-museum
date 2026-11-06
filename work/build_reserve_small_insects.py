"""Build five editable reserve teaching models; does not edit an open Blender scene.

Run in a separate Blender process with --background --threads 2 --python this file.
Pass -- --overwrite only after reviewing the owned output paths below.
Original generalized morphology studies, not scans or exact species replicas.
Blender axes: +Y anterior, +Z dorsal. FBX bounds centred, max dimension 1 m.
No external images, libraries or texture dependencies. Parts remain editable;
only export copies are joined by material. All materials are opaque.

Primary morphology references consulted 2026-11-07 (no artwork copied):
https://genent.cals.ncsu.edu/insect-identification/order-coleoptera/family-coccinellidae/
https://extension.umn.edu/garden-and-home/yard-and-garden/yard-and-garden-insects/lady-beetles
https://mdc.mo.gov/discover-nature/field-guide/fireflies-lightning-bugs
https://extension.okstate.edu/fact-sheets/an-introduction-to-fireflies
https://australian.museum/learn/animals/insects/botany-bay-weevil/
https://extension.umn.edu/garden-and-home/home-maintenance/household-insects/ants
https://mdc.mo.gov/discover-nature/field-guide/antlion-larvae-doodlebug-larvae
"""
import bpy, bmesh, math, random, runpy, sys, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SAVE=ROOT/'blender/scenes/collections/reserve_small_insects.blend'
PREVIEW=ROOT/'blender/previews/collections/reserve_small_insects.png'
EXPORT=ROOT/'unity/VirtualMuseum/Assets/Museum/Models/Reserve'
NAMES=['Ladybird','Firefly','Weevil','Ant','AntlionLarva']
if '--overwrite' not in sys.argv and any(p.exists() for p in [SAVE,PREVIEW]+[EXPORT/(n+'.fbx') for n in NAMES]):
    raise RuntimeError('Owned outputs exist; inspect before passing --overwrite.')
for p in (SAVE.parent,PREVIEW.parent,EXPORT):p.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
export_groups=runpy.run_path(str(ROOT/'work/export_static_fbx.py'))['export_selected_groups']
random.seed(5117)
parts=[];current=None;reports=[]

def material(name,color,rough=.4,metal=0):
    m=bpy.data.materials.new(current.name+'_'+name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m

def mesh(name,verts,faces,mat):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(current.name+' | '+name,data);current.objects.link(obj)
    data.materials.append(mat);parts.append(obj)
    for p in data.polygons:p.use_smooth=True
    return obj

def ball(name,loc,scale,mat,seg=20,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    obj=bpy.context.object;obj.name=current.name+' | '+name;obj.scale=scale
    for col in list(obj.users_collection):col.objects.unlink(obj)
    current.objects.link(obj);obj.data.materials.append(mat);parts.append(obj)
    for p in obj.data.polygons:p.use_smooth=True
    return obj

def tube(name,points,radii,mat,sides=7):
    pts=[Vector(p) for p in points]
    if isinstance(radii,(int,float)):radii=[radii]*len(pts)
    verts=[];faces=[]
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        a=tangent.cross(Vector((0,0,1)))
        if a.length<.01:a=tangent.cross(Vector((0,1,0)))
        a.normalize();b=tangent.cross(a).normalized()
        for j in range(sides):
            angle=j*math.tau/sides;verts.append(tuple(p+radii[i]*(a*math.cos(angle)+b*math.sin(angle))))
    for i in range(len(pts)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,mat)

def curve(name,controls,r,mat,end=None,sides=6):
    p=[Vector(x) for x in controls];pts=[]
    for i in range(len(p)-1):
        a=p[max(0,i-1)];b=p[i];c=p[i+1];d=p[min(len(p)-1,i+2)]
        for j in range(4):
            t=j/4;pts.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    pts.append(p[-1]);end=r if end is None else end
    return tube(name,pts,[r+(end-r)*i/(len(pts)-1) for i in range(len(pts))],mat,sides)

def mirror(pts,side):return [(side*x,y,z) for x,y,z in pts]

def leg(name,pts,mat,dark,r=.012):
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        a,b=Vector(a),Vector(b);rad=r*(1-i*.20)
        tube(name+' segment '+str(i+1),[a,a.lerp(b,.35),b],[rad*.8,rad,rad*.56],mat)
        if i<len(pts)-2:ball(name+' joint',b,(rad*.72,)*3,dark,10,6)
    p=Vector(pts[-1]);direction=(p-Vector(pts[-2])).normalized()
    for s in (-1,1):
        tube(name+' tarsal claw',[p,p+direction*.017+Vector((s*.004,0,0)),p+direction*.023+Vector((s*.003,0,.006))],[r*.20,r*.14,.0005],dark,5)

def beetle_legs(mat,dark,roots=(.12,.04,-.06),reach=.26,r=.014):
    for s in (-1,1):
        for i,y in enumerate(roots):
            dy=(.14,0,-.16)[i]
            leg('walking leg '+str(s)+' '+str(i+1),mirror([(.08,y,-.015),(reach*.72,y+dy*.6,-.005),(reach,y+dy,-.075),(reach+.035,y+dy*1.25,-.082)],s),mat,dark,r)

def dome(width,length,cy,height,mat):
    for side in (-1,1):
        verts=[];faces=[];ny=22;nx=14
        for i in range(ny+1):
            a=math.pi*i/ny
            for j in range(nx+1):
                b=math.pi*.5*j/nx
                verts.append((side*(.002+width*math.sin(a)*math.sin(b)),cy+length*math.cos(a),.012+height*math.sin(a)*math.cos(b)))
        for i in range(ny):
            for j in range(nx):
                a=i*(nx+1)+j;f=(a,a+1,a+nx+2,a+nx+1);faces.append(f[::-1] if side>0 else f)
        # Close the floor and centre section explicitly. A single cap ngon is
        # nonplanar here and Unity may discard it as self-intersecting.
        base=len(verts)
        for i in range(ny+1):verts.append((side*.002,cy+length*math.cos(math.pi*i/ny),.012))
        for i in range(ny):
            floor=(base+i,i*(nx+1)+nx,(i+1)*(nx+1)+nx,base+i+1)
            centre=(base+i+1,(i+1)*(nx+1),i*(nx+1),base+i)
            faces.extend([floor if side>0 else floor[::-1],centre if side>0 else centre[::-1]])
        obj=mesh('left elytron' if side<0 else 'right elytron',verts,faces,mat)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0000001)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000001)
        bm.to_mesh(obj.data);bm.free();obj.data.update()

def surface(x,y,width,length,cy,height,offset=.002):
    return (x,y,.012+height*math.sqrt(max(.001,1-(x/width)**2-((y-cy)/length)**2))+offset)

def spot(name,x,y,r,width,length,cy,height,mat):
    count=24;rings=4
    verts=[surface(x,y,width,length,cy,height,.004)]
    for k in range(1,rings+1):
        ring=k/rings
        for j in range(count):
            a=math.tau*j/count;verts.append(surface(x+r*ring*math.cos(a),y+r*ring*math.sin(a),width,length,cy,height,.004))
    faces=[(0,1+j,1+(j+1)%count) for j in range(count)]
    for k in range(rings-1):
        base=1+k*count;nextbase=base+count
        faces.extend((base+j,nextbase+j,nextbase+(j+1)%count,base+(j+1)%count) for j in range(count))
    return mesh(name,verts,faces,mat)

def ladybird():
    red=material('Red_elytra',(.64,.025,.012),.25)
    black=material('Dark_cuticle',(.019,.021,.021),.32)
    spots=material('Black_markings',(.009,.009,.008),.30)
    cream=material('Cream_pronotum_marks',(.85,.79,.57),.43)
    eyes=material('Eyes',(.012,.018,.019),.19)
    legmat=material('Legs',(.075,.04,.022),.42)
    ball('ventral abdomen',(0,-.055,-.013),(.205,.265,.061),black,24,12)
    dome(.22,.27,-.045,.175,red)
    for s in (-1,1):
        for x,y,r in [(.09,.085,.043),(.135,-.055,.048),(.078,-.19,.039)]:spot('conforming dark spot',s*x,y,r,.22,.27,-.045,.175,spots)
    spot('central anterior mark',0,.175,.032,.22,.27,-.045,.175,spots)
    ball('pronotum',(0,.213,.035),(.164,.103,.086),black,24,12)
    for s in (-1,1):
        ball('pale lateral pronotum patch',(s*.121,.228,.071),(.036,.062,.016),cream,16,8)
        ball('compound eye',(s*.067,.302,.035),(.018,.027,.024),eyes,14,8)
        curve('short club antenna',mirror([(.038,.322,.017),(.069,.351,.018),(.097,.362,.019)],s),.004,legmat)
        ball('antennal club',(s*.10,.364,.018),(.008,.014,.007),black,12,6)
    ball('head',(0,.286,.018),(.081,.065,.052),black)
    beetle_legs(legmat,black,roots=(.20,.095,-.025),reach=.25,r=.011)
    for y in [-.08,-.14,-.20]:tube('ventral abdominal seam',[(-.13,y,-.055),(0,y-.01,-.073),(.13,y,-.055)],.002,legmat)

def firefly():
    dark=material('Soft_black_elytra',(.025,.033,.028),.48)
    orange=material('Orange_pronotum',(.52,.13,.035),.43)
    cream=material('Pale_elytral_margin',(.65,.50,.22),.49)
    brown=material('Legs_and_antennae',(.11,.065,.028),.42)
    eyes=material('Eyes',(.007,.011,.009),.19)
    lantern=material('Ventral_lantern',(.77,.85,.32),.48)
    for i in range(7):ball('abdomen segment '+str(i),(0,.02-i*.045,-.012),(.093-i*.002,.033,.040),brown,18,8)
    dome(.104,.245,-.06,.047,dark)
    for s in (-1,1):
        curve('pale elytral edge',mirror([(.017,.178,.024),(.077,.12,.046),(.104,-.02,.025),(.079,-.24,.025),(.013,-.301,.017)],s),.004,cream)
        for x in (.029,.055,.078):
            pts=[surface(s*x,y,.104,.245,-.06,.047,.001) for y in [.13,.08,.02,-.05,-.12,-.20]]
            tube('elytral ridge',pts,.0015,brown,5)
    ball('shield pronotum',(0,.225,.026),(.118,.089,.045),orange,24,12)
    ball('dark pronotum centre',(0,.221,.065),(.054,.062,.006),dark,18,8)
    ball('head beneath shield',(0,.291,.003),(.068,.057,.031),dark)
    for s in (-1,1):
        ball('compound eye',(s*.056,.30,.01),(.018,.026,.021),eyes,14,8)
        pts=mirror([(.032,.322,.015),(.078,.36,.024),(.10,.414,.018),(.11,.462,.01)],s)
        curve('segmented antenna',pts,.005,brown,end=.002)
        for i in range(9):
            y=.35+i*.012;x=.068+i*.0045;ball('antenna segment',(s*x,y,.021),(.005,.008,.004),dark,8,6)
        for y in (-.21,-.25):ball('ventral pale lantern plate',(s*.039,y,-.047),(.042,.021,.006),lantern,16,8)
    beetle_legs(brown,dark,roots=(.18,.095,.01),reach=.19,r=.009)

def weevil():
    body=material('Ochre_cuticle',(.22,.155,.072),.55)
    elytra=material('Umber_elytra',(.27,.20,.092),.52)
    dark=material('Dark_joints',(.035,.027,.015),.40)
    gold=material('Pale_scales',(.60,.49,.25),.59)
    eyes=material('Eyes',(.008,.012,.009),.20)
    legmat=material('Leg_cuticle',(.135,.10,.04),.49)
    ball('ventral abdomen',(0,-.14,-.014),(.14,.20,.063),body,22,12)
    dome(.16,.22,-.10,.10,elytra)
    ball('pronotum',(0,.124,.025),(.108,.095,.08),body,22,12)
    ball('head',(0,.225,.029),(.077,.071,.062),body)
    curve('long rostrum',[(0,.25,.025),(0,.32,.020),(0,.40,-.010),(0,.465,-.047)],.026,body,end=.015,sides=12)
    for s in (-1,1):
        ball('compound eye',(s*.066,.245,.045),(.020,.026,.025),eyes,16,10)
        curve('elbowed rostral antenna',mirror([(.02,.368,.002),(.101,.395,.016),(.135,.35,.031),(.168,.329,.036)],s),.004,legmat)
        ball('antenna club',(s*.17,.328,.037),(.014,.010,.009),body,12,8)
        curve('mandible at snout tip',mirror([(.009,.462,-.05),(.016,.478,-.055),(.003,.482,-.056)],s),.003,dark,end=.0008)
        for j in range(1,7):
            a=j*math.pi/15
            pts=[]
            for k in range(21):
                theta=.22+(math.pi-.44)*k/20
                pts.append((s*(.002+.161*math.sin(theta)*math.sin(a)),-.10+.22*math.cos(theta),.014+.101*math.sin(theta)*math.cos(a)))
            tube('longitudinal elytral stria',pts,.0018,dark,5)
        for j in range(24):
            y=-.27+random.random()*.32;x=s*(.025+random.random()*.09)
            z=surface(x,y,.16,.22,-.1,.10,.002)[2]
            ball('scattered pale scale',(x,y,z),(.005,.009,.0018),gold,8,6)
    beetle_legs(legmat,dark,roots=(.13,.055,-.03),reach=.205,r=.012)

def ant():
    head=material('Head_cuticle',(.14,.043,.014),.38)
    thorax=material('Mesosoma_cuticle',(.27,.074,.022),.40)
    gaster=material('Gaster_cuticle',(.045,.027,.019),.30)
    joint=material('Joints_mandibles',(.033,.023,.013),.35)
    eyes=material('Eyes',(.006,.009,.008),.18)
    setae=material('Fine_setae',(.43,.25,.10),.60)
    ball('head capsule',(0,.245,.042),(.112,.115,.083),head,26,14)
    ball('pronotum',(0,.065,.025),(.077,.074,.060),thorax,20,12)
    ball('mesonotum',(0,-.005,.026),(.061,.053,.053),thorax)
    ball('propodeum',(0,-.06,.018),(.058,.053,.049),thorax)
    ball('petiole stalk',(0,-.125,-.004),(.020,.042,.018),head,14,8)
    ball('single petiole node',(0,-.142,.024),(.031,.022,.054),head,16,10)
    ball('gaster',(0,-.285,.027),(.125,.15,.097),gaster,28,16)
    for y,z,w in [(-.23,.112,.112),(-.29,.126,.126),(-.35,.113,.111)]:
        pts=[(w*math.sin(a),y,z-.072*(1-math.cos(a))) for a in [-1.1,-.8,-.4,0,.4,.8,1.1]]
        tube('gaster segment boundary',pts,.002,head,5)
    for s in (-1,1):
        ball('compound eye',(s*.091,.27,.078),(.021,.031,.022),eyes,16,10)
        curve('mandible',mirror([(.045,.335,.018),(.049,.376,.009),(.013,.388,.008)],s),.016,joint,end=.002,sides=8)
        for j in range(3):tube('mandible tooth',mirror([(.04-j*.009,.375+j*.004,.008),(.025-j*.009,.374+j*.004,.008)],s),[.004,.0005],joint,5)
        curve('antenna scape',mirror([(.038,.318,.072),(.095,.371,.092),(.165,.422,.091)],s),.006,head,end=.004)
        curve('antenna funiculus',mirror([(.165,.422,.091),(.203,.374,.090),(.242,.329,.078)],s),.004,head,end=.0025)
        for j in range(8):ball('antennal segment',(s*(.172+j*.01),.414-j*.011,.091-j*.0017),(.0045,.007,.004),joint,8,6)
        plans=[(.08,.28,.32),(.012,.30,-.025),(-.065,.27,-.32)]
        for i,(y,reach,tip) in enumerate(plans):
            pts=mirror([(.048,y,.015),(.12,y+(tip-y)*.25,.065),(reach*.78,y+(tip-y)*.55,.012),(reach,tip,-.10),(reach+.025,tip+(.04 if i==0 else -.025),-.108)],s)
            leg('long worker leg '+str(s)+' '+str(i),pts,thorax,joint,.009)
    for i in range(58):
        a=random.random()*math.tau;u=random.uniform(-.8,.8);v=math.sqrt(1-u*u)
        n=Vector((v*math.cos(a),u,v*math.sin(a)));p=Vector((n.x*.126,-.285+n.y*.151,.027+n.z*.098))
        tube('gaster seta',[p,p+n*.009],[.0008,.0001],setae,4)

def antlion():
    body=material('Sand_abdomen',(.44,.32,.18),.72)
    plates=material('Dorsal_segments',(.53,.41,.25),.70)
    head=material('Head_and_thorax',(.30,.20,.105),.63)
    jaws=material('Sickle_mandibles',(.12,.072,.031),.44)
    bristles=material('Bristles',(.14,.10,.055),.68)
    spots=material('Dark_mottling',(.23,.17,.09),.70)
    eyes=material('Lateral_eye_tubercles',(.018,.018,.012),.36)
    ball('pear shaped abdomen',(0,-.14,.018),(.198,.235,.115),body,26,14)
    for j in range(7):
        y=.006-j*.05;w=.112+math.sin((j+1)*math.pi/8)*.085
        ball('abdominal segment '+str(j),(0,y,.033), (w,.039,.098-j*.003),plates,22,10)
        for s in (-1,1):
            ball('lateral tubercle',(s*w,y,.016),(.032,.027,.030),body,12,8)
            for k in range(6):
                p=Vector((s*(w+.009),y+(k-2.5)*.007,.033));q=p+Vector((s*(.04+random.random()*.025),random.uniform(-.014,.014),.012))
                tube('lateral stiff bristle',[p,q],[.0022,.00025],bristles,4)
    ball('thorax',(0,.104,.015),(.116,.104,.072),head,22,12)
    ball('broad head',(0,.229,.028),(.137,.107,.065),head,26,14)
    for s in (-1,1):
        curve('sickle shaped hollow mandible',mirror([(.090,.29,.034),(.136,.38,.048),(.113,.47,.063),(.044,.535,.069)],s),.023,jaws,end=.0018,sides=10)
        for i in range(3):
            p=(.121-i*.009,.363+i*.040,.048+i*.006)
            tube('mandible inner tooth',mirror([p,(p[0]-.043,p[1]+.011,p[2])],s),[.008,.0007],jaws,6)
        ball('eye tubercle',(s*.129,.253,.046),(.017,.022,.019),head,12,8)
        for i in range(3):ball('small lateral eye',(s*(.139+i*.001),.245+i*.008,.056),(.0045,.0045,.0045),eyes,8,6)
        curve('short antenna',mirror([(.087,.303,.062),(.107,.325,.065),(.123,.340,.064)],s),.0026,head,end=.001)
        for i,y in enumerate([.15,.088,.028]):
            reach=.18+i*.025;tip=y+(.08 if i==0 else -.025-i*.025)
            leg('short thoracic leg '+str(s)+' '+str(i),mirror([(.075,y,-.01),(.13,y,-.026),(reach,tip,-.073),(reach+.021,tip+.008,-.08)],s),head,jaws,.010)
    for j in range(44):
        x=random.uniform(-.12,.12);y=random.uniform(-.28,.015)
        z=.033+.10*math.sqrt(max(.1,1-(x/.20)**2))
        ball('dorsal mottled granule',(x,y,z),(.007,.011,.003),spots,8,6)
        tube('dorsal stiff seta',[(x,y,z+.002),(x+random.uniform(-.01,.01),y+.006,z+.025)],[.0013,.0001],bristles,4)

def bounds(objects):
    bpy.context.view_layer.update();p=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    low=Vector(tuple(min(v[i] for v in p) for i in range(3)));high=Vector(tuple(max(v[i] for v in p) for i in range(3)))
    return low,high

collections=[]
for name,builder in zip(NAMES,[ladybird,firefly,weevil,ant,antlion]):
    current=bpy.data.collections.new(name);scene.collection.children.link(current);parts=[];builder()
    low,high=bounds(parts);centre=(low+high)/2;factor=1/max(high-low)
    for obj in parts:obj.location=(obj.location-centre)*factor;obj.scale*=factor
    bpy.context.view_layer.update();triangles=0
    for obj in parts:obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
    if triangles>25000:raise RuntimeError(name+' exceeds triangle budget: '+str(triangles))
    # Explicit triangulation makes the exact render topology portable to Unity;
    # original source meshes retain their editable faces underneath modifiers.
    for obj in parts:obj.modifiers.new('Portable triangulated export','TRIANGULATE')
    result=export_groups(EXPORT/(name+'.fbx'),parts)
    mats=sorted({o.data.materials[0] for o in parts},key=lambda x:x.name)
    result.update(name=name,triangles=triangles,materials=[{'name':m.name,'rgba':list(m.diffuse_color),'roughness':m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value,'metallic':m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value} for m in mats])
    reports.append(result)
    study=bpy.data.scenes.new('Study | '+name);study.collection.children.link(current)
    scene.collection.children.unlink(current);collections.append(current)

current=bpy.data.collections.new('Gallery');scene.collection.children.link(current)
scene.name='Reserve small insects | gallery';parts=[]
ground=material('Ground',(.027,.044,.046),.82);labelmat=material('Caption',(.74,.82,.77),.7)
for i,(name,col) in enumerate(zip(NAMES,collections)):
    x=((i if i<3 else i-3)-(1 if i<3 else .5))*1.6;y=.82 if i<3 else -.83
    obj=bpy.data.objects.new(name+' preview',None);obj.instance_type='COLLECTION';obj.instance_collection=col;obj.location=(x,y,.20);current.objects.link(obj)
    for suffix,body,dy,size in [('caption',['LADYBIRD','FIREFLY','WEEVIL','WORKER ANT','ANTLION LARVA'][i],-.65,.075),('note','RESERVE MODEL  /  NOT TO SCALE',-.75,.036)]:
        data=bpy.data.curves.new(name+' '+suffix,'FONT');data.body=body;data.align_x='CENTER';data.size=size
        text=bpy.data.objects.new(name+' '+suffix,data);current.objects.link(text);text.location=(x,y+dy,-.03);data.materials.append(labelmat)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.08));bpy.context.object.data.materials.append(ground)
data=bpy.data.cameras.new('Gallery camera');camera=bpy.data.objects.new('Gallery camera',data);scene.collection.objects.link(camera)
camera.location=(0,-1.15,9);camera.rotation_euler=(Vector((0,-.02,0))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=5.15;scene.camera=camera
for name,loc,power,size,color in [('Key',(-3,2,5),450,4,(.92,.97,1)),('Fill',(3,-1,4),280,3,(1,.85,.68)),('Rim',(0,4,3),300,3,(.72,.88,1))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Gallery world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.22,.25,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
bpy.ops.wm.save_as_mainfile(filepath=str(SAVE))
bpy.ops.wm.open_mainfile(filepath=str(SAVE));bpy.ops.render.render(write_still=True)
print('RESERVE_SMALL_REPORT='+json.dumps(reports,ensure_ascii=False))
print('RESERVE_SMALL_COMPLETE')
