"""Five original insect studies prepared for later museum exhibits.

Run in a separate Blender background process with --threads 2 --python this_file.
Pass -- --overwrite only after reviewing the owned output files below.
Editable mesh parts remain in individual Study scenes; only export copies are
joined by material. Canonical axes: head +Y, dorsal +Z. Bounds centre at origin,
longest dimension 1 metre for observation, not biological scale. These are
generalized anatomical teaching models, not exact species scans.

Primary morphology references consulted 2026-11-07; no artwork/textures copied:
https://australian.museum/learn/species-identification/ask-an-expert/what-do-mayflies-look-like/
https://mdc.mo.gov/discover-nature/field-guide/mayflies
https://extension.umn.edu/garden-and-home/yard-and-garden/yard-and-garden-insects/lacewing
https://mdc.mo.gov/discover-nature/field-guide/water-striders
https://askabiologist.asu.edu/mosquito-anatomy
https://ipm.ucanr.edu/home-and-landscape/mosquitoes/
https://extension.arizona.edu/publication/controlling-mosquito-larvae-urban-drainage-structures-arizona

Mayfly is a two-tailed adult with four upright wings; Lacewing has four net-veined
roof-shaped wings. WaterStrider is a wingless adult form. Mosquito has one wing
pair and a separate pair of halteres; MosquitoLarva is a legless Culex-like form
with a posterior respiratory siphon. Wing membrane material alpha is 0.24;
Unity must configure the corresponding Fade/transparent blend explicitly.
"""
import bpy, math, random, runpy, sys, json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[1]
BLEND=ROOT/'blender/scenes/collections/reserve_winged_aquatic.blend'
PREVIEW=ROOT/'blender/previews/collections/reserve_winged_aquatic.png'
EXPORT=ROOT/'unity/VirtualMuseum/Assets/Museum/Models/Reserve'
NAMES=['Mayfly','Lacewing','WaterStrider','Mosquito','MosquitoLarva']
if '--overwrite' not in sys.argv and any(p.exists() for p in [BLEND,PREVIEW]+[EXPORT/(n+'.fbx') for n in NAMES]):
    raise RuntimeError('Owned reserve outputs exist. Review before using --overwrite.')
for p in [BLEND.parent,PREVIEW.parent,EXPORT]: p.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
export_groups=runpy.run_path(str(ROOT/'work/export_static_fbx.py'))['export_selected_groups']
Thorax=runpy.run_path(str(ROOT/'work/insect_anatomy.py'))['Thorax']
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
random.seed(6294)
parts=[]; current=None; reports=[]

def material(label,color,rough=.4,alpha=1,metal=0):
    m=bpy.data.materials.new(current.name+'_'+label); m.use_nodes=True
    m.diffuse_color=(*color,alpha)
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,alpha)
    p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=alpha;p.inputs['Metallic'].default_value=metal
    if alpha<1:m.surface_render_method='DITHERED'
    return m

def mesh(name,verts,faces,mat,smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(current.name+' | '+name,data);current.objects.link(obj)
    data.materials.append(mat)
    for p in data.polygons:p.use_smooth=smooth
    parts.append(obj);return obj

def ball(name,loc,scale,mat,seg=18,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    obj=bpy.context.object;obj.name=current.name+' | '+name;obj.scale=scale
    for col in list(obj.users_collection):col.objects.unlink(obj)
    current.objects.link(obj);obj.data.materials.append(mat)
    for p in obj.data.polygons:p.use_smooth=True
    parts.append(obj);return obj

def tube(name,points,radii,mat,sides=7):
    ps=[Vector(p) for p in points]
    if isinstance(radii,(float,int)):radii=[radii]*len(ps)
    verts=[];faces=[]
    for i,p in enumerate(ps):
        tangent=(ps[min(i+1,len(ps)-1)]-ps[max(i-1,0)]).normalized()
        cross=tangent.cross(Vector((0,0,1)))
        if cross.length<.01:cross=tangent.cross(Vector((0,1,0)))
        cross.normalize(); other=tangent.cross(cross).normalized()
        for j in range(sides):
            a=j*math.tau/sides;verts.append(tuple(p+radii[i]*(cross*math.cos(a)+other*math.sin(a))))
    for i in range(len(ps)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces += [tuple(reversed(range(sides))),tuple((len(ps)-1)*sides+j for j in range(sides))]
    return mesh(name,verts,faces,mat)

def curve(name,controls,radius,mat,end=.001,steps=5,sides=6):
    p=[Vector(q) for q in controls];ps=[]
    for i in range(len(p)-1):
        a=p[max(0,i-1)];b=p[i];c=p[i+1];d=p[min(len(p)-1,i+2)]
        for j in range(steps):
            t=j/steps;ps.append(.5*((2*b)+(c-a)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    ps.append(p[-1]);return tube(name,ps,[radius+(end-radius)*i/(len(ps)-1) for i in range(len(ps))],mat,sides)

def mirrored(points,s):return [(s*x,y,z) for x,y,z in points]

def leg(name,points,cuticle,joint,r=.009,bristles=False):
    ps=[Vector(p) for p in points]
    for i in range(len(ps)-1):
        a,b=ps[i:i+2];ri=r*(1-.17*i)
        tube(name+' segment '+str(i),[a,a.lerp(b,.36),b],[ri*.82,ri,ri*.57],cuticle,7)
        if i<len(ps)-2:ball(name+' joint '+str(i),b,(ri*.76,)*3,joint,10,6)
        if bristles and i>=1:
            for j in range(9):
                p=a.lerp(b,.12+j*.085)
                tube(name+' fine hydrophobic seta',[p,p+Vector((.008 if p.x>0 else -.008,0,.003))],[.00065,.00012],joint,4)
    direction=(ps[-1]-ps[-2]).normalized();tip=ps[-1]
    tube(name+' tapered tarsus',[tip,tip+direction*.045,tip+direction*.061],[r*.44,r*.25,.0006],joint,6)

def wing(name,origin,long_axis,wide_axis,membrane,vein,net=False):
    """Closed thin wing with a geometric rib network; UV-independent materials."""
    o=Vector(origin);u=Vector(long_axis);v=Vector(wide_axis);normal=u.cross(v).normalized()
    # Mirroring a wing reverses its cross product. Keep visible veins on the
    # dorsal face on both sides instead of burying one network under the film.
    if normal.z<0:normal=-normal
    def point(t,f=0):return o+u*t+v*(math.sin(math.pi*t)**.8)*f
    outline=[point(i/16,1) for i in range(17)]+[point(i/16,-.55) for i in range(15,0,-1)]
    n=len(outline);verts=[tuple(p+normal*.0008) for p in outline]+[tuple(p-normal*.0008) for p in outline]
    lookup={tuple(p):i for i,p in enumerate(outline)};faces=[]
    for tri in tessellate_polygon([outline]):
        ids=tuple(p if isinstance(p,int) else lookup[tuple(p)] for p in tri)
        cross=(outline[ids[1]]-outline[ids[0]]).cross(outline[ids[2]]-outline[ids[0]])
        if cross.dot(normal)<0:ids=ids[::-1]
        faces += [ids,tuple(n+i for i in reversed(ids))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh(name+' closed membrane',verts,faces,membrane,False)
    tube(name+' leading and trailing border',outline+[outline[0]],.0016,vein,5)
    for f in [-.35,0,.38,.72]:
        pts=[point(i/18,f)+normal*.0012 for i in range(19)]
        tube(name+' longitudinal vein',pts,.00145,vein,5)
    for i in range(1,12 if net else 8):
        t=i/(12 if net else 8)
        for j,(a,b) in enumerate([(-.55,-.35),(-.35,0),(0,.38),(.38,.72),(.72,1)]):
            tt=min(.96,t+( .023 if j%2 else -.015))
            tube(name+' cross vein',[point(t,a)+normal*.0016,point(tt,b)+normal*.0016],.00105,vein,4)
    return point

def mayfly():
    body=material('AmberCuticle',(.37,.20,.065),.43)
    band=material('SegmentBands',(.15,.065,.022),.52)
    light=material('PaleJoints',(.61,.43,.19),.43)
    eye=material('CompoundEyes',(.10,.047,.031),.19)
    membrane=material('WingMembrane',(.75,.83,.76),.29,.24)
    vein=material('WingVeins',(.25,.22,.10),.44)
    chest=Thorax(mesh,ball,[(.172,.132,.047,-.021,.066),
        (.132,.056,.070,-.043,.093),(.056,.009,.051,-.031,.069)],body)
    ball('head capsule',(0,.208,.035),(.064,.057,.048),light)
    for i in range(10):
        y=-.011-i*.043;r=.047-i*.0032
        ball('abdominal segment '+str(i+1),(0,y,.012-i*.001),(r,.032,r*.72),body)
        tube('dorsal segment boundary',[(r*math.cos(a),y-.021,.012-i*.001+r*.73*math.sin(a)) for a in [j*math.pi/14 for j in range(15)]],.0025,band,5)
    for s in (-1,1):
        ball('large compound eye',(s*.044,.217,.062),(.032,.032,.030),eye)
        curve('short bristle antenna',mirrored([(.023,.247,.055),(.038,.294,.07),(.054,.332,.068)],s),.0028,band,.0004)
        plans=[[(.14,.22,-.025),(.18,.40,-.07),(.13,.53,-.085)],
               [(.17,.00,-.01),(.22,.01,-.12),(.29,.035,-.13)],
               [(.16,-.15,-.04),(.21,-.22,-.12),(.29,-.29,-.13)]]
        for j,pts in enumerate(plans):
            leg('thoracic leg '+str(j+1),[chest.coxa(j,s,.009,light)]+mirrored(pts,s),light,band,.007)
        curve('threadlike caudal cercus',mirrored([(.014,-.40,.008),(.085,-.65,.01),(.16,-.95,.04),(.22,-1.21,.07)],s),.006,light,.00065,steps=10)
        for j in range(17):
            t=j/17;p=Vector((s*(.014+.206*t),-.40-.81*t,.008+.062*t))
            ball('cercus annulus',p,(.0042*(1-t*.6),.006,.0042*(1-t*.6)),band,8,4)
        wing('upright forewing '+str(s),(s*.037,.105,.07),(s*.13,-.04,.53),(s*.018,-.20,-.014),membrane,vein,True)
        wing('small hindwing '+str(s),(s*.039,.045,.055),(s*.105,-.055,.22),(s*.009,-.105,-.008),membrane,vein)

def lacewing():
    body=material('GreenCuticle',(.18,.42,.075),.43)
    dark=material('Joints',(.065,.17,.025),.5)
    pale=material('PaleStripe',(.52,.66,.18),.45)
    eye=material('GoldenEyes',(.55,.30,.045),.22,1,.24)
    membrane=material('WingMembrane',(.72,.88,.57),.31,.24)
    vein=material('NetVeins',(.25,.40,.10),.4)
    chest=Thorax(mesh,ball,[(.182,.135,.046,-.018,.074),
        (.135,.083,.061,-.030,.093),(.083,.025,.055,-.024,.078)],body)
    ball('head',(0,.225,.025),(.067,.051,.046),body)
    for i in range(10):
        r=.043-i*.0025
        y=.006-i*.041
        ball('abdomen segment '+str(i+1),(0,y,.005),(r,.027,r*.72),body)
        tube('pale abdominal dorsal stripe',[(0,y+.017,.005+r*.58),(0,y,.005+r*.73),
            (0,y-.017,.005+r*.58)],.004,pale,6)
    for s in (-1,1):
        ball('golden compound eye',(s*.058,.231,.036),(.025,.029,.026),eye)
        curve('long thread antenna',mirrored([(.027,.260,.039),(.062,.38,.045),(.055,.58,.05),(.098,.74,.08)],s),.0033,dark,.0005,steps=9)
        for j in range(3):
            target=[.30,-.05,-.26][j]
            root=chest.coxa(j,s,.008,body)
            leg('slender walking leg '+str(j+1),[root,(s*.11,root.y+.01,-.025),
                (s*.18,target,-.09),(s*.21,target-.05,-.12)],pale,dark,.006)
        # Hindwing sits under the larger forewing, both in a tent-like pose.
        wing('roof hindwing '+str(s),(s*.036,.07,.054),(s*.15,-.52,-.04),(s*.095,-.01,-.055),membrane,vein,True)
        wing('roof forewing '+str(s),(s*.028,.116,.080),(s*.20,-.576,-.045),(s*.115,.0,-.045),membrane,vein,True)

def strider():
    shell=material('DarkCuticle',(.038,.031,.023),.36)
    joints=material('LegJoints',(.018,.016,.012),.48)
    stripe=material('SilverFlanks',(.60,.62,.52),.36,1,.12)
    brown=material('WarmLegs',(.16,.105,.052),.45)
    eye=material('Eyes',(.008,.012,.013),.18)
    chest=Thorax(mesh,ball,[(.284,.193,.053,-.007,.065),
        (.193,.058,.067,-.018,.066),(.058,-.012,.063,-.019,.059)],shell)
    ball('pronotum',(0,.245,.03),(.054,.069,.04),shell)
    ball('head',(0,.315,.028),(.049,.050,.034),brown)
    for i in range(8):
        y=-.025-i*.041;r=.060*(1-i*.075)
        ball('wingless abdominal tergite '+str(i),(0,y,.018),(r,.030,.033),shell)
        for s in (-1,1):ball('silver flank mark',(s*r*.87,y,.024),(.006,.027,.009),stripe,12,6)
    for s in (-1,1):
        ball('compound eye',(s*.040,.325,.042),(.017,.023,.019),eye,14,8)
        curve('four-segment antenna',mirrored([(.027,.35,.028),(.076,.43,.025),(.115,.53,.028),(.14,.64,.035)],s),.0042,brown,.0012,steps=5)
        leg('short grasping foreleg',[chest.coxa(0,s,.010,brown),(s*.12,.27,-.045),
            (s*.13,.39,-.085),(s*.065,.43,-.086)],brown,joints,.010)
        leg('long rowing middle leg',[chest.coxa(1,s,.013,brown,fraction=.72),(s*.25,.17,.025),
            (s*.48,.24,-.12),(s*.66,.20,-.14)],brown,joints,.010,True)
        leg('long steering hind leg',[chest.coxa(2,s,.012,brown,fraction=.37),(s*.22,-.21,.008),
            (s*.43,-.44,-.12),(s*.56,-.58,-.14)],brown,joints,.009,True)
    tube('folded piercing rostrum',[(0,.341,-.004),(0,.28,-.034),(0,.20,-.039)],[.008,.006,.002],joints,7)
    for i in range(65):
        y=random.uniform(-.25,.22);x=random.uniform(-.035,.035)
        tube('velvety body hair',[(x,y,.058),(x+random.uniform(-.004,.004),y-.008,.067)],[.0007,.0001],stripe,4)

def mosquito():
    body=material('BrownCuticle',(.16,.105,.063),.42)
    dark=material('DarkJoints',(.035,.026,.021),.49)
    pale=material('CreamScaleBands',(.55,.47,.30),.46)
    eye=material('Eyes',(.022,.030,.025),.17)
    membrane=material('WingMembrane',(.66,.69,.60),.34,.24)
    vein=material('WingScales',(.20,.16,.10),.49)
    chest=Thorax(mesh,ball,[(.190,.153,.042,-.010,.082),
        (.153,.078,.061,-.035,.133),(.078,.038,.043,-.023,.083)],body)
    ball('head',(0,.225,.066),(.047,.047,.041),body)
    for i in range(8):
        r=.038-i*.0023;y=.020-i*.055
        ball('slender abdomen segment '+str(i+1),(0,y,.013-i*.004),(r,.039,r*.75),body)
        tube('cream dorsal scale band',[(r*.93*math.cos(a),y+.016,.013-i*.004+r*.76*math.sin(a)) for a in [j*math.pi/10 for j in range(11)]],.0031,pale,5)
    curve('long proboscis',[(0,.26,.06),(0,.40,.048),(0,.53,.044)],.008,body,.003,steps=8)
    for s in (-1,1):
        ball('large compound eye',(s*.034,.233,.078),(.025,.031,.027),eye)
        curve('female antenna',mirrored([(.025,.256,.092),(.051,.34,.13),(.085,.45,.15)],s),.0028,dark,.0005,steps=7)
        for j in range(8):
            t=j/9;p=Vector((s*(.029+.05*t),.27+.16*t,.10+.05*t))
            for q in (-1,1):tube('antennal seta',[p,p+Vector((s*q*.013,.012,.006))],[.0007,.0001],pale,4)
        curve('short maxillary palp',mirrored([(.013,.265,.052),(.021,.31,.052),(.027,.33,.05)],s),.0038,pale,.001)
        for j in range(3):
            root=chest.coxa(j,s,.008,body,angle=-.96)
            tips=[.32,-.13,-.48];ty=tips[j]
            points=[root,(s*.19,root.y+(.11 if j==0 else -.06),.01),(s*.29,ty,-.13),
                    (s*.39,ty-.09,-.19)]
            leg('long leg '+str(j+1),points,body,dark,.006)
            a,b=Vector(points[1]),Vector(points[2]);tube('pale leg band',[a.lerp(b,.82),a.lerp(b,.90)],[.0049,.0045],pale,7)
        # True flies have a single flight-wing pair; these small knobs are halteres.
        tube('haltere stalk',[chest.surface(2,.57,.30,s),(s*.087,.012,.053)],[.0034,.0024],pale,7)
        ball('haltere knob',(s*.087,.012,.053),(.010,.012,.011),pale,12,6)
        wing('single flight wing '+str(s),(s*.038,.13,.102),(s*.30,-.34,.012),(s*.048,.065,.004),membrane,vein)
    for i in range(55):
        a=random.random()*math.tau;fraction=random.uniform(0,1)
        p=chest.surface(1,fraction,a)
        tube('thoracic scale seta',[p,p+Vector((math.cos(a)*.007,-.008,math.sin(a)*.007))],[.0007,.0001],pale,4)

def larva():
    body=material('OliveSoftBody',(.30,.32,.17),.53)
    dark=material('HeadCapsule',(.12,.085,.04),.41)
    band=material('SegmentMargins',(.16,.18,.08),.50)
    pale=material('SetaeAndPapillae',(.60,.57,.34),.53)
    eye=material('Eyes',(.01,.014,.012),.21)
    ball('sclerotized head capsule',(0,.31,.025),(.11,.10,.080),dark,24,12)
    ball('broad legless thorax',(0,.155,.027),(.14,.105,.095),body,24,12)
    centers=[]
    for i in range(8):
        t=i/7;x=.055*math.sin(t*math.pi*1.35);y=.04-i*.069;z=.018+.023*math.sin(t*math.pi)
        centers.append(Vector((x,y,z)));r=.085-i*.0045
        ball('legless abdominal segment '+str(i+1),(x,y,z),(r,.045,r*.72),body,20,10)
        tube('segment suture',[(x+r*.96*math.cos(a),y-.025,z+r*.74*math.sin(a)) for a in [j*math.pi/12 for j in range(13)]],.003,band,5)
        for s in (-1,1):
            start=Vector((x+s*r*.9,y,z+.015))
            for hair in range(5):
                tip=start+Vector((s*(.034+.008*hair),-.027+hair*.013,.006+.007*hair))
                tube('lateral hair tuft', [start,tip], [.0014,.00015],pale,4)
    for s in (-1,1):
        ball('larval lateral eye',(s*.085,.34,.07),(.017,.022,.014),eye,14,8)
        curve('larval antenna',mirrored([(.083,.365,.062),(.135,.425,.069),(.145,.46,.071)],s),.004,dark,.001)
        for i in range(16):
            start=Vector((s*.035,.39,.014));end=Vector((s*(.028+i*.0035),.455+(i%5)*.009,-.02+.005*(i%3)))
            tube('feeding mouth brush',[start,start.lerp(end,.6)+Vector((0,0,.008)),end],[.0017,.0011,.0002],pale,4)
        for j in range(8):
            p=Vector((s*.12,.15,.04));tube('thoracic lateral hair',[p,p+Vector((s*(.055+j*.008),.05-j*.013,.03))],[.0018,.0002],pale,4)
    end=centers[-1]
    siphon=[end+Vector((0,-.025,.025)),end+Vector((.025,-.10,.10)),end+Vector((.048,-.20,.18))]
    tube('posterior respiratory siphon',siphon,[.023,.017,.010],dark,12)
    ball('siphon spiracular opening',siphon[-1],(.011,.007,.011),eye,12,6)
    # The brush and four papillae arise behind the siphon on the anal segment.
    saddle=end+Vector((0,-.048,-.015))
    ball('anal saddle',saddle,(.032,.032,.026),band,16,8)
    for s in (-1,1):
        for j in range(2):
            root=saddle+Vector((s*.014,-.024,.012-j*.024))
            curve('paired anal papilla', [root,root+Vector((s*.018,-.05,-.02)),root+Vector((s*.036,-.082,-.027))],.013,pale,.003,steps=5,sides=8)
    for j in range(16):
        p=saddle+Vector((0,-.013,-.020));tube('ventral anal brush',[p,p+Vector((-.055+j*.007,-.085,-.06))],[.0018,.0002],pale,4)

def finish(name):
    bpy.context.view_layer.update();points=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box]
    low=Vector(tuple(min(v[i] for v in points) for i in range(3)));high=Vector(tuple(max(v[i] for v in points) for i in range(3)))
    center=(low+high)/2;factor=1/max(high-low)
    for o in parts:o.location=(o.location-center)*factor;o.scale*=factor
    bpy.context.view_layer.update();tri=0
    for o in parts:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
    if tri>25000:raise RuntimeError(name+' exceeds 25k triangle budget: '+str(tri))
    result=export_groups(EXPORT/(name+'.fbx'),parts)
    result.update(name=name,triangles=tri,bounds=[v*factor for v in high-low],longest_dimension=1)
    result['materials']=[{'name':m.name,'rgba':list(m.diffuse_color),'roughness':m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value,'metallic':m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value} for m in sorted({o.data.materials[0] for o in parts},key=lambda m:m.name)]
    reports.append(result)
    study=bpy.data.scenes.new('Study | '+name);study.collection.children.link(current);scene.collection.children.unlink(current)
    return current

collections=[]
for name,build in zip(NAMES,[mayfly,lacewing,strider,mosquito,larva]):
    current=bpy.data.collections.new(name);scene.collection.children.link(current);parts=[]
    build();collections.append(finish(name))

scene.name='Reserve winged and aquatic insects | gallery'
current=bpy.data.collections.new('Gallery');scene.collection.children.link(current);parts=[]
floor=material('Background',(.035,.049,.052),.82);letter=material('Captions',(.72,.82,.75),.6)
positions=[(-1.60,.85),(0,.85),(1.60,.85),(-.80,-.85),(.80,-.85)]
for i,(name,col,(x,y)) in enumerate(zip(NAMES,collections,positions)):
    obj=bpy.data.objects.new(name+' gallery instance',None);obj.instance_type='COLLECTION';obj.instance_collection=col;current.objects.link(obj)
    points=[o.matrix_world@Vector(v) for o in col.objects for v in o.bound_box]
    minz=min(p.z for p in points);obj.location=(x,y,-minz+.03)
    if i==0:obj.rotation_euler.z=math.radians(65)
    if i==1:obj.rotation_euler.z=math.radians(20)
    curve_data=bpy.data.curves.new(name+' caption','FONT');curve_data.body=['01  MAYFLY','02  GREEN LACEWING','03  WATER STRIDER','04  MOSQUITO','05  MOSQUITO LARVA'][i]
    curve_data.size=.063;curve_data.align_x='CENTER';curve_data.materials.append(letter)
    label=bpy.data.objects.new(name+' caption',curve_data);current.objects.link(label);label.location=(x,y-.67,.007)
    note=bpy.data.curves.new(name+' subtitle','FONT');note.body='ANATOMY STUDY / NOT TO SCALE';note.size=.030;note.align_x='CENTER';note.materials.append(letter)
    text=bpy.data.objects.new(name+' subtitle',note);current.objects.link(text);text.location=(x,y-.74,.007)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));bpy.context.object.name='Gallery ground';bpy.context.object.data.materials.append(floor)
cam_data=bpy.data.cameras.new('Gallery camera');cam=bpy.data.objects.new('Gallery camera',cam_data);scene.collection.objects.link(cam)
cam.location=(0,-3.2,9);cam.rotation_euler=(Vector((0,-.02,.10))-cam.location).to_track_quat('-Z','Y').to_euler();cam_data.type='ORTHO';cam_data.ortho_scale=5.20;scene.camera=cam
for name,loc,power,size,color in [('Key',(-3,1,5),430,4,(.90,.97,1)),('Warm fill',(3,-2,4),260,3,(1,.86,.68)),('Rim',(0,4,3),340,3,(.65,.83,1))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Gallery world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.23,.25,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.render.engine='CYCLES';scene.cycles.samples=28;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
scene['asset_report']=json.dumps(reports)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));bpy.ops.wm.open_mainfile(filepath=str(BLEND));bpy.ops.render.render(write_still=True)
print('RESERVE_WINGED_REPORT='+json.dumps(reports));print('RESERVE_WINGED_COMPLETE')
