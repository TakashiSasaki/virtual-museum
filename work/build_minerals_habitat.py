"""Build original educational collection models; no museum specimen is copied.

Run in a separate Blender background process, e.g. blender --background
--factory-startup --python work/build_minerals_habitat.py. Units are metres,
Blender +Z up / -Y front. Every exported asset has a centred origin and a
maximum dimension of one metre. Source parts stay editable; exports merge by
material. This generator only owns the paths declared below.

Morphology references (no downloaded artwork/textures):
https://learningzone.oumnh.ox.ac.uk/node/2168186
https://museum.wales/mineralogy-of-wales/database/?mineral=266
https://www.rspb.org.uk/birds-and-wildlife/kingfisher
https://www.woodlandtrust.org.uk/trees-woods-and-wildlife/animals/mammals/red-squirrel/
https://www.nhm.ac.uk/discover/what-is-an-ammonite.html
"""
import bpy
import math
import random
import json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'blender/scenes/collections/minerals_habitat.blend'
PREVIEW = ROOT / 'blender/previews/collections/minerals_habitat.png'
EXPORT = ROOT / 'unity/VirtualMuseum/Assets/Museum/Models/Collections'
TAG = 'museum_minerals_habitat_v1'
if bpy.data.filepath and Path(bpy.data.filepath).resolve() != SOURCE.resolve():
    raise RuntimeError('Run in a fresh background process, not an unrelated blend')
for directory in (SOURCE.parent, PREVIEW.parent, EXPORT):
    directory.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.name = 'Minerals and habitat | editable collection models'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
rng = random.Random(4821)
parts = []
assets = {}
asset = ''

def material(name, color, roughness=.5, metallic=0, alpha=1):
    m = bpy.data.materials.new('Collection_' + name)
    m.use_nodes = True
    m.diffuse_color = (*color, alpha)
    m.roughness = roughness
    m.metallic = metallic
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, alpha)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        m.surface_render_method = 'DITHERED'
        p.inputs['IOR'].default_value = 1.45
    return m

stone = material('MineralMatrix', (.18,.16,.13), .88)
stone_light = material('MatrixWeathering', (.39,.34,.26), .92)
quartz = material('QuartzPearl', (.70,.82,.85), .16, .05)
quartz_shade = material('QuartzFacetBlue', (.45,.61,.67), .21, .05)
quartz_high = material('QuartzFacetWhite', (.91,.94,.93), .13, .03)
pyrite = material('PyriteBrass', (.62,.44,.13), .23, .86)
pyrite_dark = material('PyriteStriations', (.35,.24,.065), .34, .78)
blue = material('KingfisherBlue', (.018,.31,.46), .42, .06)
blue_light = material('KingfisherAzure', (.035,.49,.62), .45, .03)
blue_dark = material('KingfisherWing', (.015,.13,.22), .55)
orange = material('KingfisherBreast', (.67,.22,.045), .73)
ivory = material('WarmIvory', (.86,.79,.62), .75)
black = material('EyeAndBill', (.012,.016,.018), .20)
wood = material('NaturalBranch', (.20,.11,.055), .88)
foot_mat = material('BirdFeet', (.43,.105,.055), .72)
fur = material('SquirrelChestnut', (.34,.13,.047), .82)
fur_light = material('SquirrelGuardHair', (.49,.235,.08), .88)
fur_dark = material('SquirrelFurShadow', (.19,.064,.025), .87)
fur_belly = material('SquirrelBelly', (.68,.54,.34), .91)
ear_inner = material('SquirrelEarInner', (.32,.15,.10), .85)
frame_mat = material('HabitatFrame', (.055,.068,.063), .42, .25)
glass = material('HabitatGlass', (.70,.88,.86), .12, .02, .12)
soil = material('HabitatSoil', (.105,.064,.026), .94)
leaf_mat = material('HabitatLeaves', (.20,.32,.07), .87)
leaf_dark = material('HabitatLeafVeins', (.08,.145,.025), .93)
beetle_mat = material('HabitatBeetleShell', (.045,.11,.075), .23, .32)
beetle_head = material('HabitatBeetleLegs', (.022,.028,.017), .42)
fossil = material('FossilLimestone', (.47,.32,.16), .78)
fossil_rib = material('FossilRibHighlight', (.59,.43,.23), .81)
fossil_suture = material('FossilSuture', (.25,.16,.08), .91)

def finish(obj, name, mat, smooth=False):
    obj.name = asset + ' | ' + name
    obj['generator'] = TAG
    if mat: obj.data.materials.append(mat)
    if smooth and obj.type=='MESH':
        for p in obj.data.polygons: p.use_smooth = True
    parts.append(obj)
    return obj

def mesh(name, vertices, faces, mat, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    return finish(obj, name, mat, smooth)

def ellipsoid(name, center, scale, mat, seg=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=center)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj,name,mat,True)

def box(name, center, scale, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    obj=bpy.context.object;obj.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(obj,name,mat)
    if bevel:
        mod=obj.modifiers.new('Small edge bevel','BEVEL');mod.width=bevel;mod.segments=1
        obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return obj

def rod(name,a,b,r,mat,r2=None,n=10):
    a,b=Vector(a),Vector(b);delta=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=delta.length,location=(a+b)/2)
    obj=bpy.context.object
    obj.rotation_mode='QUATERNION';obj.rotation_quaternion=delta.to_track_quat('Z','Y')
    return finish(obj,name,mat,True)

def tube(name,points,radii,mat,n=10):
    points=[Vector(p) for p in points];verts=[];faces=[]
    for i,p in enumerate(points):
        tangent=points[min(len(points)-1,i+1)]-points[max(0,i-1)]
        rotation=tangent.to_track_quat('Z','Y')
        radius=radii[i] if isinstance(radii,list) else radii
        for j in range(n):
            t=j*math.tau/n
            verts.append(tuple(p+rotation@Vector((radius*math.cos(t),radius*math.sin(t),0))))
    for i in range(len(points)-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n
            faces.append((a,b,b+n,a+n))
    faces += [tuple(range(n-1,-1,-1)),tuple((len(points)-1)*n+j for j in range(n))]
    return mesh(name,verts,faces,mat,True)

def smooth_path(points,radii,subdivisions=5):
    values=[Vector(p) for p in points];result=[];sizes=[]
    for i in range(len(values)-1):
        a=values[max(0,i-1)];b=values[i];c=values[i+1];d=values[min(len(values)-1,i+2)]
        for step in range(subdivisions):
            t=step/subdivisions
            result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
            sizes.append(radii[i]*(1-t)+radii[i+1]*t)
    result.append(values[-1]);sizes.append(radii[-1])
    return result,sizes

def blade(name,start,end,width,mat,side=(1,0,0),bulge=.008,steps=7):
    a,b=Vector(start),Vector(end);side=Vector(side).normalized()
    along=(b-a).normalized();normal=along.cross(side).normalized()
    verts=[];faces=[]
    for i in range(steps+1):
        t=i/steps;w=width*(math.sin(math.pi*t)**.65)
        for cross in (-1,0,1):
            verts.append(tuple(a.lerp(b,t)+side*w*cross+normal*bulge*math.sin(math.pi*t)*(1-abs(cross))))
    for i in range(steps):
        for j in range(2):
            k=i*3+j;faces.append((k,k+1,k+4,k+3))
    obj=mesh(name,verts,faces,mat,True)
    solid=obj.modifiers.new('Feather or leaf thickness','SOLIDIFY');solid.thickness=.0012
    return obj

def rough_rock(name,center,scale,mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=center)
    obj=bpy.context.object
    for v in obj.data.vertices:
        v.co *= rng.uniform(.86,1.13)
        v.co.x*=scale[0];v.co.y*=scale[1];v.co.z*=scale[2]
    return finish(obj,name,mat)

def begin(name):
    global asset, parts
    asset=name;parts=[]

def end():
    bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    coords=[o.matrix_world@v.co for o in parts for v in o.evaluated_get(depsgraph).data.vertices]
    low=Vector(tuple(min(p[k] for p in coords) for k in range(3)))
    high=Vector(tuple(max(p[k] for p in coords) for k in range(3)))
    center=(low+high)/2;factor=1/max(high-low)
    root=bpy.data.objects.new(asset,None);scene.collection.objects.link(root)
    root['generator']=TAG
    root['interpretation']='Original educational model; not a measured museum specimen'
    for o in parts:
        transform=Matrix.Scale(factor,4)@o.matrix_world
        transform.translation=(o.matrix_world.translation-center)*factor
        o.matrix_world=transform
        o.parent=root
    assets[asset]=(root,list(parts))

# Quartz: irregular matrix and intergrown six-sided prisms, each with a point.
begin('QuartzCluster')
rough_rock('weathered matrix',(0,0,.075),(.39,.28,.10),stone)
for i in range(25):
    a=i*2.399;rad=.29*math.sqrt((i+.5)/25)
    x,y=math.cos(a)*rad,math.sin(a)*rad*.7
    height=.28+.40*(1-rad/.4)+rng.uniform(-.10,.10)
    radius=rng.uniform(.045,.074)
    vertices=[]
    for z,r in ((0,radius),(.78*height,radius),(height,0)):
        for j in range(6):
            t=j*math.tau/6
            vertices.append((r*math.cos(t),r*math.sin(t),z))
    faces=[tuple(range(5,-1,-1))]
    for row in range(2):
        for j in range(6): faces.append((row*6+j,row*6+(j+1)%6,(row+1)*6+(j+1)%6,(row+1)*6+j))
    obj=mesh('hexagonal crystal %02d'%i,vertices,faces,quartz)
    obj.data.materials.append(quartz_high);obj.data.materials.append(quartz_shade)
    for p in obj.data.polygons:p.material_index=(p.index+i)%3
    obj.location=(x,y,.09);obj.rotation_euler=(y*.7,-x*.7,rng.uniform(0,math.pi))
for i in range(14):
    rough_rock('matrix fleck', (rng.uniform(-.3,.3),rng.uniform(-.18,.18),.06),(.05,.035,.025),stone_light)
end()

# Pyrite: overlapping cubic crystals with physical, shallow face striations.
begin('PyriteCluster')
rough_rock('host matrix',(0,0,.07),(.40,.29,.10),stone)
for i,(pos,size) in enumerate([((-.12,.04,.28),.36),((.14,.09,.25),.30),((.10,-.13,.18),.25),((-.25,-.09,.16),.22),((.28,-.04,.14),.17),((-.02,.24,.20),.20),((-.28,.16,.13),.16)]):
    cube=box('striated cube %d'%i,pos,(size,)*3,pyrite,.002)
    cube.rotation_euler=(rng.uniform(-.20,.20),rng.uniform(-.18,.18),rng.uniform(-.4,.4))
    for axis in range(3):
        for stripe in range(1,12):
            coordinate=-size*.5+size*stripe/12
            # Three visible faces, alternating perpendicular growth directions.
            if axis==0: loc=(coordinate,-size*.501,0);dims=(size*.006,.0014,size*.93)
            elif axis==1: loc=(size*.501,0,coordinate);dims=(.0014,size*.93,size*.006)
            else: loc=(0,coordinate,size*.501);dims=(size*.93,size*.006,.0014)
            line=box('crystal face growth striation',(0,0,0),dims,pyrite_dark)
            line.location=Vector(pos)+cube.rotation_euler.to_matrix()@Vector(loc)
            line.rotation_euler=cube.rotation_euler
for i in range(18):
    rough_rock('matrix grain',(rng.uniform(-.31,.31),rng.uniform(-.2,.2),.08),(.04,.035,.027),stone_light)
end()

# Kingfisher mount: a compact, short-tailed bird with characteristic long bill.
begin('KingfisherMount')
rough_rock('mount base',(0,0,.045),(.30,.23,.06),stone)
tube('perch branch',[(-.25,.02,.08),(-.12,.015,.24),(.12,.02,.28),(.29,.06,.34)],[.045,.039,.032,.018],wood,12)
tube('perch fork',[(.10,.02,.27),(.18,.15,.36),(.21,.17,.44)],[.023,.017,.008],wood,10)
body=ellipsoid('rounded torso',(0,.015,.49),(.145,.19,.21),blue)
body.rotation_euler.x=.25
ellipsoid('orange breast',(0,-.125,.48),(.123,.093,.17),orange)
ellipsoid('neck',(0,-.04,.64),(.115,.115,.11),blue)
ellipsoid('large head',(0,-.10,.71),(.145,.155,.137),blue)
ellipsoid('white throat',(0,-.18,.615),(.075,.045,.07),ivory)
for sign in (-1,1):
    ellipsoid('orange cheek',(sign*.119,-.112,.674),(.035,.085,.047),orange,20,10)
    ellipsoid('neck white patch',(sign*.105,-.006,.64),(.029,.055,.052),ivory,20,10)
    ellipsoid('dark eye',(sign*.137,-.145,.731),(.018,.022,.019),black,20,10)
    ellipsoid('eye glint',(sign*.150,-.153,.739),(.002,.003,.003),ivory,12,6)
    for row in range(3):
        for j in range(7):
            start=(sign*(.105+row*.014),-.04+j*.018,.59-row*.043)
            tip=(sign*(.125+row*.014),.18+j*.012,.34-row*.013)
            blade('overlapping wing feather',start,tip,.022,blue_dark if j%3==0 else blue,side=(sign,0,.1),bulge=.008)
    for j in range(4):
        blade('short tail feather',(sign*.015+j*.010,.12,.36),(sign*.035+j*.012,.29,.28),.022,blue_light,side=(1,0,0),bulge=.003)
    ankle=(sign*.063,-.02,.32)
    rod('short red leg',(sign*.065,.005,.37),ankle,.012,foot_mat,n=10)
    for toe in (-1,0,1):
        path=[ankle,(sign*.063+toe*.014,-.065,.291),(sign*.063+toe*.02,-.08,.269)]
        tube('perching toe',path,[.007,.005,.002],foot_mat,8)
    tube('rear toe',[ankle,(sign*.067,.05,.29),(sign*.063,.058,.26)],[.006,.004,.002],foot_mat,8)
# A closed four-sided bill, separating upper and lower mandibles subtly.
mesh('dagger bill',[(-.040,-.22,.73),(.040,-.22,.73),(0,-.22,.76),(0,-.22,.697),(0,-.54,.715)],[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(0,3,1,2)],black)
rod('bill dividing line',(-.03,-.235,.719),(0,-.52,.715),.0025,blue_dark,n=6)
for row in range(5):
    for col in range(9):
        x=(col-4)*.025;y=-.19+row*.035
        z=.71+.137*math.sqrt(max(0,1-(x/.15)**2-((y+.1)/.16)**2))
        blade('crown feather fleck',(x,y,z-.002),(x,y+.019,z),.0035,blue_light,side=(1,0,0),bulge=.0005,steps=3)
for row in range(6):
    for j in range(7):
        x=(j-3)*.029;z=.38+row*.036
        y=-.125-.093*math.sqrt(max(0,1-(x/.128)**2-((z-.48)/.175)**2))
        blade('fine overlapping breast feather',(x,y,z+.015),(x,y-.002,z-.025),.011,orange,side=(1,0,0),bulge=.002,steps=3)
end()

# Small mammal mount: russet squirrel, upright with forepaws and bushy tail.
begin('SquirrelMount')
rough_rock('woodland mount',(0,0,.045),(.30,.25,.06),wood)
tail_points=[(0,.10,.20),(.13,.24,.35),(.18,.28,.56),(.14,.24,.76),(.04,.16,.91),(-.10,.07,.91),(-.16,.02,.80)]
tail_radii=[.075,.12,.145,.15,.135,.10,.035]
tail_points,tail_radii=smooth_path(tail_points,tail_radii,5)
tube('continuous bushy tail',tail_points,tail_radii,fur,22)
for i,p in enumerate(tail_points[:-1]):
    p=Vector(p);q=Vector(tail_points[i+1]);tangent=(q-p).normalized()
    rotation=tangent.to_track_quat('Z','Y')
    for j in range(7):
        a=j*math.tau/7+i*.32
        radial=rotation@Vector((math.cos(a),math.sin(a),0))
        c=p.lerp(q,.5)+radial*((tail_radii[i]+tail_radii[i+1])*.50+.001)
        blade('tail guard hair',c-tangent*.020,c+tangent*.035+radial*.008,.006,fur_light if j%3 else fur_dark,side=rotation@Vector((-math.sin(a),math.cos(a),0)),bulge=.002,steps=3)
ellipsoid('haunch',(0,.025,.25),(.18,.15,.19),fur)
ellipsoid('upright torso',(0,-.025,.40),(.14,.135,.22),fur)
ellipsoid('belly fur',(0,-.135,.38),(.105,.04,.155),fur_belly)
ellipsoid('neck',(0,-.07,.57),(.105,.11,.10),fur)
ellipsoid('head',(0,-.125,.64),(.125,.13,.12),fur)
ellipsoid('tapered muzzle',(0,-.235,.605),(.076,.09,.060),fur_light)
ellipsoid('nose',(0,-.307,.621),(.025,.019,.018),black,20,10)
for sign in (-1,1):
    ear=ellipsoid('upright ear',(sign*.086,-.077,.743),(.047,.034,.088),fur)
    ear.rotation_euler.y=sign*-.12
    ellipsoid('inner ear',(sign*.086,-.103,.75),(.027,.012,.057),ear_inner,20,10)
    for i in range(5):
        blade('ear tuft',(sign*.085+(i-2)*.012,-.08,.80),(sign*.09+(i-2)*.014,-.07,.868-rng.uniform(0,.022)),.009,fur_dark,side=(1,0,0),bulge=.002,steps=4)
    ellipsoid('eye',(sign*.112,-.193,.662),(.016,.018,.021),black,20,10)
    ellipsoid('eye catchlight',(sign*.123,-.201,.668),(.002,.003,.003),ivory,12,6)
    ellipsoid('rear foot',(sign*.115,-.12,.105),(.060,.13,.043),fur_dark)
    tube('foreleg',[(sign*.104,-.07,.49),(sign*.12,-.19,.41),(sign*.05,-.255,.45)],[.038,.029,.025],fur,12)
    ellipsoid('front paw',(sign*.046,-.258,.455),(.032,.028,.035),fur_light,20,10)
    for j in range(3):
        rod('forepaw digits',(sign*.035+j*.009,-.277,.47),(sign*.026+j*.011,-.278,.438),.004,fur_dark,n=6)
        rod('rear claws',(sign*.11+(j-1)*.018,-.22,.103),(sign*.11+(j-1)*.018,-.25,.097),.0035,ivory,n=6)
    for j in range(3):
        tube('fine whisker',[(sign*.04,-.285,.61),(sign*.10,-.29,.61+(j-1)*.014),(sign*.16,-.28,.61+(j-1)*.025)],.0009,black,5)
    for j in range(24):
        a=j*2.399;z=.23+(j%8)*.043;x=sign*(.115+.018*math.sin(a));y=-.03+.08*math.cos(a)
        blade('body fur clump',(x,y,z),(x*1.035,y-.008,z-.045),.010,fur_light if j%3 else fur_dark,side=(0,1,0),bulge=.003,steps=3)
ellipsoid('held seed',(0,-.266,.455),(.035,.036,.050),wood,20,10)
end()

# Educational insect enclosure, with visibly open space behind clear panes.
begin('RearingTerrarium')
W,D,H=1,.62,.64
box('dark base',(0,0,.025),(W,D,.05),frame_mat,.009)
box('substrate',(0,0,.085),(.95,.57,.10),soil,.008)
for x in (-.49,.49):
    for y in (-.30,.30): box('corner post',(x,y,.34),(.020,.020,.62),frame_mat,.002)
for z in (.055,.635):
    for y in (-.30,.30): box('long rim',(0,y,z),(W,.022,.025),frame_mat,.002)
    for x in (-.49,.49): box('short rim',(x,0,z),(.022,D,.025),frame_mat,.002)
for y in (-.297,.297):box('clear front or back',(0,y,.345),(.968,.003,.565),glass)
for x in (-.487,.487):box('clear side',(x,0,.345),(.003,.576,.565),glass)
for i in range(29):
    x=-.47+i*.94/28
    rod('ventilation mesh', (x,-.285,.642),(x,.285,.642),.0014,frame_mat,n=6)
for i in range(18):
    y=-.285+i*.57/17
    rod('ventilation mesh',(-.47,y,.643),(.47,y,.643),.0014,frame_mat,n=6)
box('lid grip',(0,0,.667),(.18,.045,.025),frame_mat,.006)
for i in range(42):
    rough_rock('substrate bark fragment',(rng.uniform(-.44,.44),rng.uniform(-.25,.25),.142),(.021,.016,.010),wood if i%3 else stone_light)
tube('decaying log',[(-.36,.09,.15),(-.14,.09,.21),(.14,.10,.27),(.33,.13,.33)],[.055,.055,.043,.025],wood,14)
tube('climbing fork',[(.06,.1,.25),(.13,.05,.4),(.24,.04,.49)],[.027,.019,.009],wood,10)
for j in range(12):
    x=rng.uniform(-.36,.35);y=rng.uniform(-.20,.21);z=.16+rng.uniform(0,.03)
    tip=(x+rng.uniform(-.1,.1),y+rng.uniform(-.11,.11),z+.02)
    blade('fallen leaf',(x,y,z),tip,.035,leaf_mat,side=(1,.1,0),bulge=.012)
    rod('leaf vein',(x,y,z+.003),tip,.0015,leaf_dark,n=5)
for sign in (-1,1):
    stem=(sign*.34,.18,.16)
    tube('plant stem',[stem,(sign*.34,.18,.30),(sign*.30,.17,.46)],.004,leaf_dark,6)
    for j in range(5):
        p=(sign*.34,.18,.23+j*.043)
        q=(sign*(.34+(.09 if j%2 else -.10)),.13,.27+j*.043)
        blade('living foliage',p,q,.029,leaf_mat,side=(0,1,0),bulge=.009)

def beetle(center,length,heading):
    start=len(parts);c=Vector(center)
    ellipsoid('beetle joined elytra',(0,.01,0),(.037*length,.062*length,.026*length),beetle_mat,20,10)
    ellipsoid('beetle pronotum',(0,-.045*length,.002),(.032*length,.028*length,.024*length),beetle_head,20,10)
    ellipsoid('beetle head',(0,-.077*length,.003),(.022*length,.022*length,.019*length),beetle_head,16,8)
    rod('elytral seam',(0,-.035*length,.025*length),(0,.068*length,.008*length),.0015*length,beetle_head,n=5)
    for sign in (-1,1):
        for i in range(3):
            y=(-.039+i*.036)*length
            tube('six jointed legs',[(sign*.025*length,y,0),(sign*.054*length,y+.015*length,-.012*length),(sign*.074*length,y+.032*length,-.027*length)],[.004*length,.003*length,.0012*length],beetle_head,6)
        tube('antenna',[(sign*.013*length,-.084*length,.008*length),(sign*.036*length,-.105*length,.008*length),(sign*.042*length,-.12*length,.015*length)],.0018*length,beetle_head,6)
    rotation=Matrix.Rotation(heading,4,'Z')
    for obj in parts[start:]: obj.matrix_world=Matrix.Translation(c)@rotation@obj.matrix_world
beetle((-.25,-.12,.185),1.0,-.6)
beetle((.28,-.13,.185),.82,.65)
beetle((-.07,.085,.279),.80,-.1)
end()

# Ribbed ammonite fossil: expanding coiled whorls and fine wavy sutures.
# This is a sculpted teaching model, without a species/locality attribution.
begin('FossilAmmonite')
rough_rock('fossil host limestone',(0,.03,.075),(.40,.18,.10),stone_light)
rough_rock('attached stone support',(-.04,.055,.16),(.24,.11,.12),stone_light)
points=270;sides=18;turn=math.pi*4.8
vertices=[];faces=[]
for i in range(points+1):
    t=i/points;theta=turn*(t-1)-1.0
    radial=.028*math.exp(math.log(.37/.028)*t)
    radius=.49*radial+.009
    ridge=1+.085*math.cos(theta*30)
    for j in range(sides):
        a=j*math.tau/sides
        r=radial+radius*math.cos(a)*ridge
        vertices.append((r*math.cos(theta),radius*.64*math.sin(a)*ridge,.50+r*math.sin(theta)))
for i in range(points):
    for j in range(sides):
        a=i*sides+j;b=i*sides+(j+1)%sides
        faces.append((a,b,b+sides,a+sides))
faces.append(tuple(range(sides-1,-1,-1)))
faces.append(tuple(points*sides+j for j in range(sides)))
shell=mesh('coiled fossil with raised ribs',vertices,faces,fossil,True)
shell.data.materials.append(fossil_rib)
for poly in shell.data.polygons:
    segment=poly.index//sides
    if math.cos((turn*(segment/points-1)-1.0)*30)>.8:poly.material_index=1
for i in range(36):
    t=.45+i*.54/35;theta=turn*(t-1)-1.0
    radial=.028*math.exp(math.log(.37/.028)*t);radius=.49*radial+.009
    curve=[]
    for j in range(11):
        a=math.pi+.16+j*(math.pi-.32)/10
        ripple=.017*math.sin(j*2.8)+.007*math.sin(j*6.2)
        th=theta+ripple
        r=radial+radius*math.cos(a)*(1+.085*math.cos(th*30))
        curve.append((r*math.cos(th),radius*.64*math.sin(a)*(1+.085*math.cos(th*30))-.0015,.50+r*math.sin(th)))
    tube('wavy shell suture',curve,.00115,fossil_suture,5)
for i in range(18):
    rough_rock('adhering matrix',(rng.uniform(-.28,.29),.04,rng.uniform(.07,.13)),(.038,.045,.025),fossil)
end()

def export_asset(name,root,originals):
    copies=[]
    depsgraph=bpy.context.evaluated_depsgraph_get()
    grouped={}
    for obj in originals:
        evaluated=obj.evaluated_get(depsgraph)
        data=bpy.data.meshes.new_from_object(evaluated,depsgraph=depsgraph)
        copy=bpy.data.objects.new(name+' export',data)
        scene.collection.objects.link(copy);copy.matrix_world=obj.matrix_world.copy()
        # Multi-material quartz faces stay in one mesh with preserved indices.
        key=tuple(m.name for m in data.materials)
        grouped.setdefault(key,[]).append(copy);copies.append(copy)
    exported=[]
    for key,group in grouped.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group:obj.select_set(True)
        bpy.context.view_layer.objects.active=group[0]
        if len(group)>1:bpy.ops.object.join()
        merged=bpy.context.object
        merged.name=name+'_'+key[0].replace('Collection_','')
        exported.append(merged)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in exported:obj.select_set(True)
    bpy.context.view_layer.objects.active=exported[0]
    temporary=EXPORT/('.'+name+'.pending')
    bpy.ops.export_scene.fbx(filepath=str(temporary),use_selection=True,object_types={'MESH'},
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',
        bake_space_transform=False,use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='STRIP')
    temporary.replace(EXPORT/(name+'.fbx'))
    triangles=sum(len(poly.vertices)-2 for obj in exported for poly in obj.data.polygons)
    coords=[obj.matrix_world@v.co for obj in exported for v in obj.data.vertices]
    bounds=[max(p[k] for p in coords)-min(p[k] for p in coords) for k in range(3)]
    info={'asset':name,'triangles':triangles,'meshes':len(exported),'materials':sorted({m.name for obj in exported for m in obj.data.materials}),
          'bounds':[round(v,4) for v in bounds]}
    print('COLLECTION_ASSET '+json.dumps(info))
    for obj in exported:
        data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
        if data.users==0:bpy.data.meshes.remove(data)

for name,(root,objects) in assets.items():
    export_asset(name,root,objects)

# Gallery staging stays in the source, but asset-local transforms retain their
# centred origin. Exporting above intentionally happens before this staging.
positions={'QuartzCluster':(-1.15,.7,.54),'PyriteCluster':(0,.7,.54),
    'KingfisherMount':(1.15,.7,.54),'SquirrelMount':(1.15,-.7,.54),
    'RearingTerrarium':(0,-.7,.53),'FossilAmmonite':(-1.15,-.7,.54)}
for name,(root,objects) in assets.items():root.location=positions[name]
bpy.context.view_layer.update()
asset='Preview';parts=[]
preview_mat=material('PreviewPlinth',(.11,.14,.15),.76)
floor_mat=material('PreviewFloor',(.035,.045,.052),.78)
for name,(root,objects) in assets.items():
    low=min((o.matrix_world@v.co).z for o in objects for v in o.data.vertices)
    root.location.z-=low-.08
    # update matrix before measuring on the next pass
    bpy.context.view_layer.update()
    box('individual plinth',(root.location.x,root.location.y,.035),(1.0,.82,.07),preview_mat,.015)
    bpy.ops.object.text_add(location=(root.location.x-.45,root.location.y-.425,.06))
    text=bpy.context.object;text.name=name+' | preview label'
    text.data.body={'QuartzCluster':'QUARTZ / CRYSTALS','PyriteCluster':'PYRITE / CUBIC','KingfisherMount':'KINGFISHER / MOUNT','SquirrelMount':'SQUIRREL / MOUNT','RearingTerrarium':'INSECT HABITAT / CLEAR ENCLOSURE','FossilAmmonite':'AMMONITE / RIBBED FOSSIL'}[name]
    text.data.size=.047;text.data.extrude=.0002;text.data.materials.append(ivory)
box('gallery ground',(.0,0,-.025),(200,200,.02),floor_mat)
scene.world=bpy.data.worlds.new('Minerals habitat studio')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.27,.31,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
for position,power,size in [((-3,-4,6),850,5),((4,-2,4),650,3),((0,3,5),1000,4)]:
    bpy.ops.object.light_add(type='AREA',location=position)
    light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(Vector((0,0,.45))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3.25,-6.7,4.5))
camera=bpy.context.object
camera.rotation_euler=(Vector((.1,.1,.45))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=5.2;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=1800;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.render.filepath=str(PREVIEW)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),check_existing=False)
bpy.ops.render.render(write_still=True)
print('COLLECTION_COMPLETE '+str(PREVIEW.relative_to(ROOT)))
