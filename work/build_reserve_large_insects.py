"""Four original anatomical studies for the future-exhibit reserve.

Run in a separate Blender background process with --threads 2. Existing owned
outputs require -- --overwrite. Does not touch a running Blender or Unity scene.
Editable parts are kept in individual Study scenes; export copies are grouped
by material. Head +Y, dorsal +Z; centered maximum dimension 1 m, not life size.

Generalized teaching models, not exact species replicas or scans. Morphology
consulted 2026-11-07; no reference imagery or text copied into the artwork:
https://australian.museum/learn/animals/insects/cicadas-superfamily-cicadoidea/
https://australian.museum/learn/animals/insects/grasshoppers-crickets-katydids-and-locusts-order-orthoptera/
https://australian.museum/learn/animals/insects/leaf-and-stick-insects-order-phasmatodea/
https://australian.museum/learn/species-identification/ask-an-expert/what-do-earwigs-look-like/
https://mdc.mo.gov/discover-nature/field-guide/earwigs
"""
import bpy, math, random, runpy, sys, json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[1]
SAVE=ROOT/'blender/scenes/collections/reserve_large_insects.blend'
PREVIEW=ROOT/'blender/previews/collections/reserve_large_insects.png'
EXPORT=ROOT/'unity/VirtualMuseum/Assets/Museum/Models/Reserve'
NAMES=['Cicada','Grasshopper','StickInsect','Earwig']
if '--overwrite' not in sys.argv and any(p.exists() for p in [SAVE,PREVIEW]+[EXPORT/(n+'.fbx') for n in NAMES]):
    raise RuntimeError('Owned outputs exist; review them before passing --overwrite.')
for folder in (SAVE.parent,PREVIEW.parent,EXPORT):folder.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
export_groups=runpy.run_path(str(ROOT/'work/export_static_fbx.py'))['export_selected_groups']
Thorax=runpy.run_path(str(ROOT/'work/insect_anatomy.py'))['Thorax']
current=None;parts=[];reports=[]
random.seed(971)

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

def leg(name,points,material,dark,radius=.013):
    p=[Vector(v) for v in points]
    for i in range(len(p)-1):
        r=radius*(1-.2*i)
        tube(name+' segment', [p[i],p[i].lerp(p[i+1],.35),p[i+1]],[r*.75,r,r*.5],material,8)
        if i<len(p)-2:ball(name+' joint',p[i+1],(r*.8,)*3,dark,12,6)
    v=(p[-1]-p[-2]).normalized()
    for s in (-1,1):tube(name+' claw',[p[-1],p[-1]+v*.018+Vector((s*.006,0,0)),p[-1]+v*.023+Vector((s*.003,0,.005))],[.0025,.0015,.0003],dark,5)

def wing(name,outline,material,s,z=.065,thick=.0012):
    points=[Vector((s*x,y,z+.045*abs(x))) for x,y in outline]
    tris=tessellate_polygon([points]);lookup={tuple(p):i for i,p in enumerate(points)};n=len(points)
    verts=[tuple(p) for p in points]+[(p.x,p.y,p.z-thick) for p in points];faces=[]
    for tri in tris:
        ids=tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in tri)
        if (points[ids[1]]-points[ids[0]]).cross(points[ids[2]]-points[ids[0]]).z<0:ids=ids[::-1]
        faces.extend([ids,tuple(n+i for i in reversed(ids))])
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh(name,verts,faces,material,False)

def antenna(name,points,material,segments=15,radius=.004):
    controls=[Vector(v) for v in points]
    for i in range(segments):
        t=i/segments;u=(i+1)/segments
        def at(f):
            f=f*(len(controls)-1);j=min(int(f),len(controls)-2);return controls[j].lerp(controls[j+1],f-j)
        a=at(t);b=at(u);r=radius*(1-.7*t)
        tube(name+' antennomere',[a,a.lerp(b,.4),b],[r*.75,r,r*.55],material,7)

def cicada():
    shell=mat('OliveCuticle',(.21,.29,.07),.4);dark=mat('DarkSutures',(.038,.057,.026),.5)
    amber=mat('OchreEdge',(.40,.24,.055),.45);eye=mat('CompoundEye',(.105,.025,.014),.24)
    vein=mat('WingVein',(.12,.13,.062),.46);membrane=mat('WingMembrane',(.64,.70,.57),.29,alpha=.35)
    abdomen=mat('Abdomen',(.16,.12,.055),.51)
    ball('abdomen',(0,-.207,.004),(.128,.192,.085),abdomen,24,14)
    for i in range(7):
        y=-.055-i*.050;section=math.sqrt(1-((y+.207)/.192)**2)
        curve('abdominal tergite edge',[(.128*section*math.cos(a),y,.004+.085*section*math.sin(a))
            for a in (0,.52,1.04,1.57,2.10,2.62,3.14)],.0026,amber,steps=2)
    chest=Thorax(mesh,ball,[(.290,.200,.141,-.030,.098),
        (.200,.095,.145,-.054,.143),(.095,-.036,.138,-.057,.117)],shell)
    ball('pronotum collar',(0,.255,.045),(.174,.055,.070),shell,24,12)
    ball('broad head',(0,.34,.040),(.184,.083,.069),shell,24,12)
    for s in (-1,1):
        ball('widely spaced compound eye',(s*.169,.349,.064),(.045,.05,.05),eye)
        curve('mesonotum dark stripe',mirror([(.035,.217,.107),(.077,.133,.134),(.056,.026,.115)],s),.008,dark)
        antenna('short bristle',mirror([(.09,.40,.06),(.11,.435,.075),(.125,.47,.08)],s),dark,8,.004)
        fore=[(.10,.175),(.225,.135),(.36,-.005),(.40,-.205),(.335,-.405),(.25,-.48),(.18,-.45),(.12,-.20)]
        hind=[(.11,.08),(.21,.015),(.28,-.12),(.245,-.31),(.17,-.36),(.105,-.19)]
        wing('short hind wing',hind,membrane,s,.057);wing('long fore wing',fore,membrane,s,.079)
        def wp(x,y):return (s*x,y,.083+.045*x)
        curve('wing leading margin',[wp(x,y) for x,y in fore[:6]],.0035,vein,steps=3)
        curve('wing trailing margin',[wp(x,y) for x,y in [fore[0]]+list(reversed(fore[4:]))],.0025,vein,steps=3)
        for j in range(6):
            a=(.11,.16-j*.018);b=(.19+j*.018,-.05-j*.035);c=(.23+j*.025,-.43+j*.045)
            curve('longitudinal wing vein',[wp(*a),wp(*b),wp(*c)],.0019,vein,steps=4)
        for row in range(4):
            y=-.04-row*.09
            curve('cross vein row',[wp(.15,y+.018),wp(.23,y),wp(.32+(row==1)*.03,y-.028)],.00125,vein,steps=3)
        for i in range(3):
            root=chest.coxa(i,s,.018,shell)
            y=root.y
            pts=[root,(s*.20,y+(.06 if i==0 else -.03),-.038),
                 (s*.25,y+(.15-i*.14),-.12),(s*.28,y+(.19-i*.16),-.13)]
            leg('leg '+str(i+1),pts,shell,dark,.018 if i==0 else .012)
            if i==0:
                for k in range(3):tube('fore femur spine',[(s*(.145+k*.014),y+.03,-.022),(s*(.142+k*.014),y+.025,-.055)],[.005,.0005],dark,5)
    for x,y in [(-.024,.332),(.024,.332),(0,.366)]:ball('dorsal ocellus',(x,y,.106),(.009,.009,.006),eye,12,8)
    tube('ventral piercing rostrum',[(0,.37,-.015),(0,.16,-.065),(0,.015,-.06)],[.009,.008,.002],dark,8)

def grasshopper():
    green=mat('LeafGreen',(.17,.32,.065),.55);light=mat('PaleCuticle',(.34,.43,.12),.57)
    dark=mat('DarkJoints',(.055,.075,.023),.48);wingmat=mat('FoldedTegmina',(.22,.26,.07),.48)
    stripe=mat('WingStriae',(.39,.38,.15),.6);eye=mat('CompoundEye',(.22,.15,.055),.25)
    ball('long tapered abdomen',(0,-.233,.035),(.075,.20,.067),green,24,12)
    for i in range(8):
        y=-.059-i*.047;section=math.sqrt(1-((y+.233)/.20)**2);w=.075*section
        curve('abdomen segment',[(w*math.cos(a),y,.035+.067*section*math.sin(a))
             for a in (0,.52,1.04,1.57,2.10,2.62,3.14)],.0027,light,steps=2)
        for s in(-1,1):ball('spiracle',(s*w,y,.025),(.004,.008,.004),dark,10,6)
    chest=Thorax(mesh,ball,[(.286,.173,.085,-.015,.139),
        (.173,.079,.079,-.025,.132),(.079,-.052,.091,-.032,.128)],green)
    # Pronotum saddle has flared side lobes and a raised midline keel.
    for s in(-1,1):
        wing('pronotum side lobe',[(.01,.29),(.082,.28),(.106,.13),(.07,.08),(.012,.11)],green,s,.112,.065)
        curve('pronotum lateral edge',mirror([(.073,.28,.095),(.099,.19,.075),(.074,.095,.08)],s),.004,light)
    tube('pronotum median keel',[(0,.285,.14),(0,.20,.16),(0,.10,.14)],[.004,.006,.004],light,6)
    head=ball('vertical face',(0,.32,.065),(.075,.065,.105),light,24,14)
    ball('mouth shield',(0,.375,.009),(.039,.025,.032),green,16,10)
    for s in(-1,1):
        ball('compound eye',(s*.060,.33,.116),(.029,.034,.04),eye)
        antenna('short segmented antenna',mirror([(.04,.36,.14),(.08,.48,.19),(.09,.61,.21)],s),dark,18,.005)
        wing('narrow folded forewing',[(.009,.16),(.073,.105),(.089,-.10),(.052,-.41),(.018,-.45),(.002,-.08)],wingmat,s,.135,.004)
        for k in range(4):
            x=.015+k*.014
            curve('forewing longitudinal vein',mirror([(x,.10,.14+.045*x),(x+.007,-.09,.14+.045*x),(x*.65,-.36,.14+.045*x)],s),.0019,stripe)
        for k in range(5):tube('forewing cross vein',mirror([(.012,-.02-k*.065,.142),(.074-k*.006,-.04-k*.06,.144)],s),.001,stripe,5)
        leg('foreleg',[chest.coxa(0,s,.015,green),(s*.12,.27,.005),
                       (s*.20,.37,-.105),(s*.23,.42,-.115)],light,dark,.012)
        leg('middle leg',[chest.coxa(1,s,.016,green),(s*.19,.08,-.018),
                         (s*.24,-.075,-.105),(s*.27,-.12,-.115)],green,dark,.013)
        # Enlarged folded femur and slender long tibia are distinct joints.
        a=chest.coxa(2,s,.026,green);b=Vector((s*.23,-.28,.11));c=Vector((s*.27,.075,-.115));d=Vector((s*.34,.14,-.13))
        tube('jumping femur',[a,a.lerp(b,.35),a.lerp(b,.7),b],[.029,.052,.042,.018],green,16)
        ball('hind knee',b,(.024,)*3,dark,14,8)
        tube('long hind tibia',[b,b.lerp(c,.65),c],[.014,.011,.007],light,9)
        leg('hind tarsus',[c,c.lerp(d,.65),d],light,dark,.008)
        for k in range(9):
            p=b.lerp(c,.13+k*.085)
            tube('hind tibial spine',[p,p+Vector((s*.018,-.01,.006))],[.0035,.0003],dark,5)
        for k in range(4):
            p=a.lerp(b,.24+k*.15)
            tube('femur chevron',[p+Vector((s*.02,.015,.035)),p+Vector((s*.035,-.005,.025))],.002,stripe,5)
        tube('short abdominal cercus',[(s*.025,-.398,.03),(s*.04,-.455,.025)],[.006,.001],dark,7)

def stick():
    bark=mat('TwigBrown',(.19,.14,.065),.7);olive=mat('OliveRidges',(.25,.27,.10),.66)
    dark=mat('DarkJoints',(.055,.045,.021),.6);pale=mat('PaleNodes',(.36,.30,.16),.73)
    eye=mat('SmallEyes',(.018,.015,.010),.29)
    # Wingless stick-insect form. Long mesothorax and metathorax carry the
    # middle and hind legs; the segmented abdomen begins behind them.
    ball('small head',(0,.43,.018),(.032,.055,.029),bark,20,10)
    chest=Thorax(mesh,ball,[(.383,.318,.023,-.015,.030),
        (.318,.011,.024,-.018,.030),(.011,-.205,.027,-.031,.023)],bark)
    for i in range(9):
        y=-.21-i*.059;r=.026-i*.0017
        tube('abdominal segment '+str(i+1),[(0,y,-.006),(0,y-.025,-.006),(0,y-.056,-.008)],[r*.85,r,r*.80],bark,12)
        tube('segment ring',[(0,y-.049,-.008),(0,y-.055,-.008)],[r*.84,r*.82],pale,12)
        for s in(-1,1):ball('spiracle',(s*r,y-.025,.001),(.002,.004,.002),dark,8,6)
    for s in(-1,1):
        ball('small lateral eye',(s*.028,.446,.029),(.009,.012,.009),eye,14,8)
        antenna('filiform antenna',mirror([(.018,.475,.026),(.052,.61,.035),(.09,.79,.025)],s),olive,25,.0038)
        plans=[[(.019,.34,.006),(.10,.52,.01),(.14,.77,-.09),(.16,.94,-.10)],
               [(.023,.015,.0),(.27,.10,.045),(.43,-.025,-.09),(.48,-.08,-.10)],
               [(.023,-.19,-.005),(.22,-.32,.024),(.35,-.63,-.09),(.38,-.79,-.10)]]
        for i,p in enumerate(plans):
            points=mirror(p,s)
            points[0]=chest.coxa(i,s,.010,bark,fraction=(.60,.88,.88)[i])
            leg('walking leg '+str(i+1),points,bark,dark,.0115)
            for k in range(2):
                a=Vector(points[k]);b=Vector(points[k+1]);q=a.lerp(b,.48)
                tube('leg twig thorn',[q,q+Vector((s*.014,.009,.009))],[.003,.0002],olive,5)
        tube('small terminal cercus',[(s*.008,-.738,-.005),(s*.017,-.77,-.003)],[.004,.001],dark,6)
    for i in range(18):
        y=.30-i*.049
        x=(1 if i%2 else -1)*.019
        ball('bark-like raised node',(x,y,.015),(.004,.009,.003),pale,10,6)
    curve('dorsal fine keel',[(0,.32,.03),(0,.02,.03),(0,-.20,.022),(0,-.55,.016)],.002,olive)

def earwig():
    brown=mat('MahoganyCuticle',(.19,.060,.023),.36);dark=mat('DarkSutures',(.035,.016,.009),.47)
    ochre=mat('TawnyLegs',(.46,.29,.13),.48);wingmat=mat('ShortTegmina',(.29,.12,.046),.36)
    edge=mat('TergaEdges',(.33,.13,.047),.43);eye=mat('CompoundEyes',(.009,.009,.008),.23)
    chest=Thorax(mesh,ball,[(.264,.163,.083,-.017,.065),
        (.163,.096,.080,-.026,.068),(.096,.028,.084,-.027,.053)],brown)
    ball('flattened abdomen',(0,-.18,.0),(.104,.219,.038),brown,24,12)
    for i in range(8):
        y=.015-i*.05;w=.108*math.sqrt(max(.18,1-((y+.14)/.255)**2))
        ball('overlapping tergite',(0,y,.021),(w,.031,.025),brown,20,8)
        curve('tergite rear seam',[(-w*.96,y-.025,.022),(0,y-.027,.046),(w*.96,y-.025,.022)],.0026,edge,steps=4)
        for s in(-1,1):tube('lateral abdomen seta',[(s*w,y,.016),(s*(w+.019),y-.01,.024)],[.0007,.0001],ochre,4)
    ball('pronotum',(0,.20,.025),(.086,.078,.043),brown,24,12)
    ball('head',(0,.32,.029),(.072,.073,.039),brown,24,12)
    for s in(-1,1):
        ball('small compound eye',(s*.060,.335,.046),(.016,.022,.019),eye,16,10)
        antenna('long beaded antenna',mirror([(.045,.372,.027),(.085,.46,.016),(.15,.63,.020)],s),dark,20,.0055)
        # Earwig forewings end early, exposing most abdominal tergites.
        wing('short leathery forewing',[(.004,.16),(.086,.15),(.086,.025),(.065,-.01),(.004,.005)],wingmat,s,.066,.004)
        curve('tegmen outer rim',mirror([(.078,.15,.073),(.084,.04,.073),(.063,-.004,.073)],s),.0025,edge)
        for j in range(3):
            root=chest.coxa(j,s,.012,ochre)
            y=root.y
            leg('walking leg '+str(j+1),[root,(s*.145,y+(.025 if j==0 else -.025),-.015),
                (s*.20,y+(.13-j*.14),-.055),(s*.235,y+(.16-j*.15),-.058)],ochre,dark,.010)
        # Large curved cerci, a male-like forceps form; not a stinger.
        curve('curved abdominal forceps',mirror([(.058,-.34,.008),(.098,-.405,.015),(.105,-.48,.018),(.064,-.535,.027),(.013,-.55,.029)],s),.021,brown,end=.0015,steps=7,sides=12)
        tube('forceps inner tooth',mirror([(.094,-.43,.018),(.058,-.442,.022)],s),[.010,.0007],dark,7)
        ball('mandible base',(s*.023,.384,.016),(.020,.022,.013),dark,14,8)
        curve('mandible tip',mirror([(.032,.386,.013),(.026,.412,.01),(.008,.414,.009)],s),.005,dark,end=.001)
        leg('short maxillary palp',mirror([(.044,.375,.014),(.057,.399,.011),(.052,.424,.012)],s),ochre,dark,.004)

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
for name,builder in zip(NAMES,[cicada,grasshopper,stick,earwig]):
    current=bpy.data.collections.new(name);scene.collection.children.link(current);parts=[]
    builder();collections.append(finish(name))

current=bpy.data.collections.new('Gallery');scene.collection.children.link(current);parts=[]
scene.name='Reserve large insects | gallery'
bg=mat('Background',(.027,.041,.043),.85);caption=mat('Caption',(.71,.80,.73),.8)
for i,(name,col) in enumerate(zip(NAMES,collections)):
    x=(-.80 if i%2==0 else .80);y=(.79 if i<2 else -.79)
    inst=bpy.data.objects.new(name+' overview',None);inst.instance_type='COLLECTION';inst.instance_collection=col
    inst.location=(x,y,.20);current.objects.link(inst)
    if name=='Grasshopper':inst.rotation_euler=(0,.40,.10)
    for line,body,offset,size in [(0,['01  CICADA','02  GRASSHOPPER','03  STICK INSECT','04  EARWIG'][i],-.64,.070),(1,'ANATOMY STUDY  /  NOT TO SCALE',-.73,.032)]:
        data=bpy.data.curves.new(name+' caption '+str(line),'FONT');data.body=body;data.align_x='CENTER';data.size=size
        obj=bpy.data.objects.new(data.name,data);current.objects.link(obj);obj.location=(x,y+offset,-.07);data.materials.append(caption)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.09));bpy.context.object.name='Gallery ground';bpy.context.object.data.materials.append(bg)
data=bpy.data.cameras.new('Gallery camera');camera=bpy.data.objects.new('Gallery camera',data);scene.collection.objects.link(camera)
camera.location=(0,-.6,7);camera.rotation_euler=(Vector((0,-.10,0))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=3.45;scene.camera=camera
for name,loc,power,size,color in [('Key',(-3,2,5),450,4,(.91,.97,1)),('Warm fill',(3,-2,4),280,3,(1,.86,.68)),('Rim',(0,4,3),260,3,(.70,.86,1))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Gallery world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.2,.24,.27,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
bpy.ops.wm.save_as_mainfile(filepath=str(SAVE));bpy.ops.wm.open_mainfile(filepath=str(SAVE));bpy.ops.render.render(write_still=True)
print('RESERVE_LARGE_REPORT='+json.dumps(reports,ensure_ascii=False))
print('RESERVE_LARGE_COMPLETE')
