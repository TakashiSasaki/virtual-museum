"""Build six insects and one spider as original anatomical museum studies.

Run in a separate Blender process: blender --background --threads 4 --python
work/build_terrestrial_collection.py [-- --overwrite]. No running scene is used.
Pass --spider-only to add/update only the spider in the saved source and gallery,
leaving the original six FBX files and editable collections unchanged.
The models illustrate recognizable groups; they are not exact species replicas.

Anatomical references (consulted 2026-11-07; no external artwork/textures copied):
https://naturalhistory.si.edu/education/teaching-resources/life-science/what-insect
https://australian.museum/learn/species-identification/ask-an-expert/what-do-beetles-look-like/
https://australian.museum/learn/species-identification/ask-an-expert/what-do-butterflies-moths-and-skippers-look-like/
https://australian.museum/learn/animals/insects/praying-mantises-order-mantodea/
https://www.nhm.ac.uk/discover/stag-beetles.html
https://www.uaex.uada.edu/farm-ranch/special-programs/beekeeping/about-honey-bees.aspx
https://british-dragonflies.org.uk/odonata/species-and-identification/
https://australian.museum/learn/species-identification/ask-an-expert/what-is-a-spiders/
https://www.amnh.org/research/science-conservation/projects/case-studies/spiders

Blender axes: head +Y, dorsal surface +Z. Exports have bounds-centred origin
and longest dimension 1 m (observation normalization, not biological scale).
Editable body parts are retained in separate source scenes. FBX copies alone
are joined by material. Wing membranes need transparent, double-sided Unity
materials; the remaining meshes are opaque. No generated raster dependency.
"""
import bpy, math, random, runpy, sys, json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

REPO=Path(__file__).resolve().parents[1]
BLEND=REPO/'blender/scenes/collections/terrestrial.blend'
PREVIEW=REPO/'blender/previews/collections/terrestrial.png'
EXPORT=REPO/'unity/VirtualMuseum/Assets/Museum/Models/Collections'
NAMES=['NaturalBeetle','SwallowtailButterfly','StagBeetle','Dragonfly','Honeybee','Mantis','OrbWeaverSpider']
SPIDER_ONLY='--spider-only' in sys.argv
if not SPIDER_ONLY and '--overwrite' not in sys.argv and any(p.exists() for p in [BLEND,PREVIEW]+[EXPORT/(n+'.fbx') for n in NAMES]):
    raise RuntimeError('Owned outputs already exist; review them and pass --overwrite to regenerate.')
for folder in (BLEND.parent,PREVIEW.parent,EXPORT): folder.mkdir(parents=True,exist_ok=True)
if SPIDER_ONLY:
    if not BLEND.exists():raise RuntimeError('The saved terrestrial source is required for --spider-only')
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.context.window.scene=bpy.data.scenes['Terrestrial collection | gallery']
    for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
    for name in ('Gallery','OrbWeaverSpider'):
        col=bpy.data.collections.get(name)
        if col:
            for obj in list(col.objects):bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.collections.remove(col)
    old_study=bpy.data.scenes.get('Study | OrbWeaverSpider')
    if old_study:bpy.data.scenes.remove(old_study)
else:bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
export_groups=runpy.run_path(str(REPO/'work/export_static_fbx.py'))['export_selected_groups']
Thorax=runpy.run_path(str(REPO/'work/insect_anatomy.py'))['Thorax']
work_scene=bpy.context.scene
current=None
parts=[]
reports=[]
random.seed(317)

def material(name,color,rough=.4,metal=0,alpha=1):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
    m.diffuse_color=(*color,alpha)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,alpha)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Alpha'].default_value=alpha
    if alpha<1:
        m.surface_render_method='DITHERED';m.use_transparent_shadow=True
    return m

def add_object(name,mesh,mat):
    obj=bpy.data.objects.new(current.name+' | '+name,mesh);current.objects.link(obj)
    if mat:mesh.materials.append(mat)
    parts.append(obj);return obj

def mesh_part(name, vertices, faces, mat):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    return add_object(name,mesh,mat)

def sphere(name,loc,scale,mat,segments=20,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    obj=bpy.context.object;obj.name=current.name+' | '+name;obj.scale=scale
    for c in list(obj.users_collection):c.objects.unlink(obj)
    current.objects.link(obj);obj.data.materials.append(mat)
    for face in obj.data.polygons:face.use_smooth=True
    parts.append(obj);return obj

def tube(name,points,radii,mat,sides=7):
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
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=add_object(name,mesh,mat)
    for f in mesh.polygons:f.use_smooth=True
    return obj

def smooth_path(points,steps=4):
    points=[Vector(p) for p in points];out=[]
    for i in range(len(points)-1):
        a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(len(points)-1,i+2)]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return out+[points[-1]]

def curve(name,points,radius,mat,sides=6,steps=4,end=None):
    pts=smooth_path(points,steps)
    radii=[radius*(1-i/(len(pts)-1))+((end if end is not None else radius)*i/(len(pts)-1)) for i in range(len(pts))]
    return tube(name,pts,radii,mat,sides)

def mirror(points,side,z=None):
    return [(side*p[0],p[1],p[2] if len(p)>2 else (z or 0)) for p in points]

def plate(name,outline,mat,side=1,z=.045,thickness=.0015,curve_up=.025,rounded=False):
    # A solid, two-sided thin wing; concave outlines are tessellated correctly.
    if rounded:
        for unused in range(2):
            rounded_outline=[]
            for i,p in enumerate(outline):
                prev=outline[i-1];nxt=outline[(i+1)%len(outline)]
                rounded_outline.extend([(p[0]*.86+prev[0]*.14,p[1]*.86+prev[1]*.14),
                                        (p[0]*.86+nxt[0]*.14,p[1]*.86+nxt[1]*.14)])
            outline=rounded_outline
    points=[Vector((side*x,y,z+curve_up*abs(x))) for x,y in outline]
    triangles=tessellate_polygon([points]);lookup={tuple(p):i for i,p in enumerate(points)}
    n=len(points);verts=[tuple(p) for p in points]+[(p.x,p.y,p.z-thickness) for p in points]
    faces=[]
    for tri in triangles:
        ids=tuple(p if isinstance(p,int) else lookup[tuple(p)] for p in tri)
        # Ensure the top points towards +Z on either reflected wing.
        cross=(points[ids[1]]-points[ids[0]]).cross(points[ids[2]]-points[ids[0]])
        if cross.z<0:ids=ids[::-1]
        faces.extend([ids,tuple(n+i for i in reversed(ids))])
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    return add_object(name,mesh,mat)

def leg(name,points,mat,radius=.012,clawmat=None):
    pts=[Vector(p) for p in points]
    for i in range(len(pts)-1):
        r=radius*(1-.19*i)
        tube(name+' segment '+str(i+1),[pts[i],pts[i].lerp(pts[i+1],.35),pts[i+1]],[r*.8,r,r*.53],mat,8)
        if i<len(pts)-2:sphere(name+' joint '+str(i),pts[i+1],(r*.83,)*3,mat,12,6)
    end=pts[-1];direction=(pts[-1]-pts[-2]).normalized()
    for side in (-1,1):
        tube(name+' tarsal claw',[end,end+direction*.022+Vector((side*.008,0,0)),end+direction*.028+Vector((side*.006,0,.008))],
             [radius*.31,radius*.21,.001],clawmat or mat,5)

def six_beetle_legs(chest,mat,joint,wide=.25):
    for side in (-1,1):
        for i in range(3):
            root=chest.coxa(i,side,.019,mat,fraction=.65 if i==2 else .5)
            y=root.y
            dy=(.13,-.025,-.16)[i]
            pts=[root,(side*(wide*.8),y+dy*.55,-.035),
                 (side*wide,y+dy,-.07),(side*(wide+.055),y+dy*1.35,-.075)]
            leg(('L' if side<0 else 'R')+str(i+1),pts,mat,.014,joint)

def shell_half(side,width,length,center_y,height,mat):
    verts=[];faces=[];ny=22;nx=12
    for i in range(ny+1):
        t=math.pi*i/ny
        for j in range(nx+1):
            a=math.pi*.5*j/nx
            verts.append((side*(.0025+width*math.sin(t)*math.sin(a)),center_y+length*math.cos(t),.018+height*math.sin(t)*math.cos(a)))
    for i in range(ny):
        for j in range(nx):
            a=i*(nx+1)+j;face=(a,a+1,a+nx+2,a+nx+1)
            if side>0:face=face[::-1]
            faces.append(face)
    mesh=bpy.data.meshes.new('elytron');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=add_object('elytron '+str(side),mesh,mat)
    for f in mesh.polygons:f.use_smooth=True
    return obj

def beetle(stag=False):
    pre=current.name
    shell=material(pre+'_Elytra',(.12,.052,.022) if stag else (.047,.25,.14),.34,.45 if not stag else .12)
    thorax=material(pre+'_Thorax',(.038,.027,.023) if stag else (.025,.13,.08),.34,.3)
    dark=material(pre+'_Joint',(.016,.014,.012),.43)
    ridge=material(pre+'_Striae',(.071,.032,.015) if stag else (.026,.13,.065),.34,.3)
    eyes=material(pre+'_Eye',(.006,.009,.007),.16)
    brass=material(pre+'_CuticleEdge',(.25,.125,.055) if stag else (.16,.24,.064),.3,.25)
    width=.16 if stag else .205;length=.24 if stag else .29;cy=-.12
    shoulder=cy+length-.007
    rear_chest=-.088 if stag else -.072
    chest=Thorax(mesh_part,sphere,[(.232,shoulder,.140,-.057,.064),
        (shoulder,.046 if stag else .063,width*.83,-.064,.047),
        (.046 if stag else .063,rear_chest,width*.92,-.077,.048)],thorax)
    # The elytra roof the meso- and metathorax as well as the abdomen.
    abdomen_front=rear_chest+.025
    abdomen_back=cy-length
    abdomen_y=(abdomen_front+abdomen_back)/2
    abdomen_half=(abdomen_front-abdomen_back)/2
    sphere('abdominal underside',(0,abdomen_y,-.016),(width*.84,abdomen_half,.079),dark,24,12)
    for side in (-1,1):
        shell_half(side,width,length,cy,.085 if stag else .125,shell)
        for j in range(1,7):
            a=j*math.pi/15;pts=[]
            for i in range(17):
                t=.20+i*(math.pi-.40)/16
                pts.append((side*(.003+width*math.sin(t)*math.sin(a)),cy+length*math.cos(t),.020+(.085 if stag else .125)*math.sin(t)*math.cos(a)))
            tube('elytral longitudinal groove',pts,.0016,ridge,5)
    sphere('pronotum',(0,.145,.025),(.165 if stag else .173,.113,.082),thorax,24,12)
    sphere('head',(0,.265,.025),(.135 if stag else .105,.092,.062),thorax,24,12)
    for side in (-1,1):
        sphere('compound eye',(side*(.119 if stag else .091),.285,.046),(.027,.034,.028),eyes,16,8)
        antenna=[(.08,.30,.04),(.15,.34,.01),(.20,.32,.015),(.23,.35,.025)]
        curve('elbowed antenna',mirror(antenna,side),.006,dark,end=.0035)
        for l in range(3):
            end=(side*(.228+l*.011),.352,.028)
            sphere('antennal lamella',end,(.007,.020,.005),brass,12,6)
    six_beetle_legs(chest,thorax,dark,wide=.27 if stag else .29)
    for i in range(5):
        y=rear_chest-.033-i*(rear_chest-abdomen_back-.057)/4
        slice_scale=math.sqrt(1-((y-abdomen_y)/abdomen_half)**2)
        points=[(width*.84*slice_scale*math.sin(a),y,-.017-.079*slice_scale*math.cos(a))
                for a in (-1.2,-.8,-.4,0,.4,.8,1.2)]
        curve('ventral abdominal suture',points,.0025,ridge,steps=3)
    if stag:
        for side in (-1,1):
            path=[(.074,.32,.02),(.137,.40,.028),(.146,.50,.035),(.105,.59,.04),(.047,.635,.045)]
            curve('arched mandible',mirror(path,side),.032,shell,sides=10,steps=5,end=.003)
            for x,y,size in [(.13,.43,.052),(.135,.49,.035),(.105,.56,.025)]:
                tube('mandible inner tooth',mirror([(x,y,.035),(x-size,y+.023,.035)],side),[.018,.0015],shell,7)
    else:
        for side in (-1,1):
            curve('mouthpart',mirror([(.035,.335,.01),(.05,.36,.005),(.018,.374,.003)],side),.011,dark,end=.003)

def butterfly():
    pre=current.name
    dark=material(pre+'_WingBlack',(.018,.019,.017),.68)
    yellow=material(pre+'_WingCream',(.91,.77,.30),.69)
    blue=material(pre+'_WingBlue',(.10,.32,.43),.54)
    red=material(pre+'_WingRed',(.59,.11,.052),.58)
    body=material(pre+'_Body',(.038,.031,.022),.66)
    hair=material(pre+'_Hair',(.40,.34,.19),.75)
    chest=Thorax(mesh_part,sphere,[(.147,.105,.024,-.004,.052),
        (.105,.043,.036,-.011,.064),(.043,-.007,.031,-.008,.056)],body)
    fore=[(.032,.08),(.09,.22),(.24,.36),(.40,.43),(.50,.385),(.51,.34),(.46,.245),(.43,.19),(.375,.11),(.31,.06),(.24,.006),(.17,-.04),(.075,-.045)]
    hind=[(.022,.015),(.16,.025),(.28,-.01),(.34,-.09),(.345,-.17),(.31,-.22),(.281,-.22),(.267,-.365),(.245,-.385),(.228,-.23),(.195,-.265),(.167,-.251),(.14,-.276),(.108,-.25),(.08,-.247),(.035,-.13)]
    creamfore=[(.055,.10),(.14,.24),(.265,.34),(.395,.381),(.454,.347),(.407,.22),(.34,.125),(.25,.052),(.15,-.005),(.065,-.02)]
    creamhind=[(.055,-.016),(.15,-.002),(.25,-.039),(.286,-.10),(.28,-.168),(.237,-.195),(.18,-.212),(.12,-.213),(.068,-.16)]
    for side in (-1,1):
        plate('forewing',fore,dark,side,z=.027,rounded=True)
        plate('hindwing',hind,dark,side,z=.021,rounded=True)
        plate('forewing cream field',creamfore,yellow,side,z=.030,rounded=True)
        plate('hindwing cream field',creamhind,yellow,side,z=.024,rounded=True)
        roots=[(.031,.08,.031),(.023,.015,.026)]
        for j,edge in enumerate([( .44,.34),(.41,.25),(.35,.15),(.27,.07),(.17,-.01)]):
            midpoint=(edge[0]*.58,edge[1]*.62+.035,.038)
            curve('forewing major vein',mirror([roots[0],midpoint,(edge[0],edge[1],.034+edge[0]*.025)],side),.003,dark,steps=4)
        for edge in [(.28,-.10),(.26,-.17),(.20,-.21),(.13,-.22)]:
            curve('hindwing major vein',mirror([roots[1],(.12,edge[1]*.45,.033),(edge[0],edge[1],.029+edge[0]*.025)],side),.0024,dark,steps=4)
        for x,y in [(.45,.315),(.42,.23),(.365,.145),(.30,.075),(.22,.005)]:
            sphere('submarginal cream spot',(side*x,y,.037+x*.025),(.014,.023,.0025),yellow,12,6)
        for x,y in [(.298,-.15),(.255,-.207),(.193,-.235),(.135,-.235)]:
            plate('blue marginal crescent',[(x-.013,y+.009),(x+.012,y+.013),(x+.017,y-.006),(x-.006,y-.014)],blue,side,z=.033)
        sphere('hindwing red eyespot',(side*.098,-.213,.037),(.017,.016,.0028),red,16,6)
        curve('clubbed antenna',mirror([(.018,.17,.045),(.045,.25,.07),(.067,.30,.08)],side),.0035,body,end=.002)
        sphere('antennal club',(side*.067,.301,.08),(.006,.014,.005),body,12,6)
        sphere('compound eye',(side*.019,.175,.041),(.013,.019,.016),body,12,8)
        for i in range(3):
            root=chest.coxa(i,side,.006,body)
            leg('fine thoracic leg',[root,(side*.057,.14-i*.065,-.028),
                                     (side*.095,.11-i*.07,-.045)],body,.004)
    sphere('head',(0,.166,.035),(.026,.026,.026),body,18,8)
    curve('coiled proboscis',[(0,.171+.014*math.cos(i*.42),.014+.013*math.sin(i*.42)) for i in range(15)],.0022,body,steps=2)
    for i in range(7):sphere('abdominal segment',(0,.006-i*.029,.022),(.025*(1-i*.075),.023,.023*(1-i*.07)),body,16,8)
    for i in range(85):
        a=random.random()*math.tau;fraction=random.uniform(0,1)
        p=chest.surface(1,fraction,a)
        tube('thorax short seta',[p,p+Vector((.005*math.cos(a),.003,.006*math.sin(a)))], [.0009,.0001],hair,4)

def membrane(name,outline,side,wing,vein,root,z=.04):
    plate(name,outline,wing,side,z=z,thickness=.0008,rounded=True)
    edge=[(x,y,z+.025*x+.001) for x,y in outline]
    curve(name+' leading edge',mirror(edge+[edge[0]],side),.0017,vein,steps=2)
    # Longitudinal veins fan from the wing base; connected cross-veins make the
    # membranous surface inspectable even with restrained alpha in Unity.
    tip=max(outline,key=lambda p:p[0]);base=Vector((root[0],root[1],z+.002))
    for j,index in enumerate(range(1,len(outline)-1)):
        endpoint=Vector((outline[index][0],outline[index][1],z+.025*outline[index][0]+.002))
        if (endpoint-base).length<.12:continue
        mid=base.lerp(endpoint,.52);mid.y+=.006*(1 if j%2==0 else -1)
        curve(name+' longitudinal vein',mirror([base,mid,endpoint],side),.0012,vein,steps=3)
    # Spanwise connecting mesh on the central membrane.
    for i in range(2,10):
        t=i/11;x=root[0]+(tip[0]-root[0])*t
        center=root[1]+(tip[1]-root[1])*t
        half=.017*math.sin(math.pi*t)
        curve(name+' cross vein',mirror([(x-.012,center-half,z+.025*x+.002),(x,center,z+.025*x+.002),(x+.009,center+half,z+.025*x+.002)],side),.0008,vein,steps=1,sides=4)

def dragonfly():
    pre=current.name
    blue=material(pre+'_AbdomenBlue',(.055,.23,.30),.32,.12)
    dark=material(pre+'_DarkCuticle',(.025,.040,.031),.36)
    gold=material(pre+'_ThoraxStripe',(.46,.42,.16),.43)
    eyes=material(pre+'_Eye',(.16,.27,.17),.23,.12)
    wing=material(pre+'_WingMembrane',(.72,.82,.80),.20,alpha=.23)
    vein=material(pre+'_WingVein',(.10,.13,.105),.48)
    chest=Thorax(mesh_part,sphere,[(.210,.177,.039,-.024,.060),
        (.177,.104,.063,-.035,.087),(.104,.027,.058,-.027,.075)],dark)
    sphere('head capsule',(0,.227,.039),(.058,.040,.045),dark,18,10)
    for side in (-1,1):
        curve('thorax lateral stripe',[(side*.045,.17,.065),(side*.05,.12,.077),(side*.04,.04,.067)],.008,gold)
        sphere('large compound eye',(side*.035,.225,.065),(.043,.045,.042),eyes,20,10)
        curve('short antenna',[(side*.012,.25,.06),(side*.020,.29,.07)],.002,dark)
        fore=[(.045,.15),(.21,.20),(.46,.245),(.555,.229),(.57,.201),(.53,.173),(.34,.135),(.08,.104)]
        hind=[(.045,.079),(.23,.057),(.46,.014),(.53,-.02),(.525,-.047),(.48,-.071),(.29,-.047),(.11,.005)]
        membrane('forewing',fore,side,wing,vein,(.045,.15),.037)
        membrane('hindwing',hind,side,wing,vein,(.045,.079),.032)
        plate('forewing pterostigma',[(.475,.229),(.505,.228),(.508,.215),(.478,.215)],dark,side,z=.052)
        plate('hindwing pterostigma',[(.45,.014),(.48,.003),(.486,-.009),(.454,.002)],dark,side,z=.047)
        for i in range(3):
            root=chest.coxa(i,side,.009,dark)
            leg('thoracic grasping leg',[root,(side*.086,.21-i*.043,-.041),
                (side*.10,.14-i*.066,-.075),(side*.075,.10-i*.066,-.085)],dark,.006)
    sphere('face',(0,.255,.04),(.026,.027,.023),gold,16,8)
    for i in range(10):
        y=.028-i*.055;r=.031*(1-i*.068);end_r=.031*(1-(i+1)*.068)
        tube('abdomen segment %02d'%i,[(0,y,.015),(0,y-.025,.015),(0,y-.050,.015)],
             [r,r*.98,end_r],blue,18)
        tube('dark abdominal joint %02d'%i,[(0,y-.050,.015),(0,y-.055,.015)],[end_r,end_r],dark,18)
    for side in (-1,1):curve('terminal appendage',[(side*.009,-.516,.015),(side*.018,-.545,.014)],.004,dark,end=.001)

def bee():
    pre=current.name
    amber=material(pre+'_AmberCuticle',(.55,.28,.055),.5)
    dark=material(pre+'_DarkCuticle',(.036,.024,.014),.42)
    eye=material(pre+'_Eye',(.009,.009,.008),.15)
    fur=material(pre+'_GoldenSetae',(.65,.46,.19),.78)
    wing=material(pre+'_WingMembrane',(.75,.78,.69),.23,alpha=.27)
    vein=material(pre+'_WingVein',(.24,.17,.075),.5)
    pollen=material(pre+'_Pollen',(.86,.53,.065),.72)
    chest=Thorax(mesh_part,sphere,[(.171,.124,.069,-.042,.097),
        (.124,.023,.104,-.060,.126),(.023,-.052,.089,-.052,.101)],dark)
    # In bees the first abdominal segment (propodeum) is fused behind T3.
    sphere('propodeum',(0,-.058,.024),(.068,.031,.064),dark,18,10)
    sphere('narrow abdominal attachment',(0,-.089,.016),(.028,.029,.028),dark,16,8)
    sphere('head',(0,.219,.02),(.079,.070,.067),dark,22,12)
    for side in (-1,1):
        sphere('compound eye',(side*.057,.231,.047),(.031,.049,.040),eye,18,10)
        curve('elbowed antenna',mirror([(.026,.265,.052),(.057,.31,.057),(.078,.326,.039),(.086,.344,.035)],side),.004,dark)
        fore=[(.067,.11),(.20,.29),(.35,.38),(.405,.365),(.421,.328),(.38,.275),(.25,.16),(.095,.062)]
        hind=[(.075,.010),(.20,.134),(.293,.176),(.32,.158),(.30,.119),(.21,.051),(.09,-.016)]
        membrane('forewing',fore,side,wing,vein,(.067,.11),.067)
        membrane('hindwing',hind,side,wing,vein,(.075,.010),.052)
        for i in range(3):
            root=chest.coxa(i,side,.014,dark)
            y=root.y;dy=(.10,-.02,-.14)[i]
            knee=Vector((side*.145,y+dy*.3,-.046))
            ankle=Vector((side*.195,y+dy,-.08))
            leg('jointed leg',[root,knee,ankle,(side*.235,y+dy*1.25,-.08)],dark,.010)
            if i==2:
                tibia=sphere('broadened hind tibia',knee.lerp(ankle,.53),(.021,(ankle-knee).length*.46,.010),amber,16,8)
                tibia.rotation_euler=(ankle-knee).to_track_quat('Y','Z').to_euler()
                sphere('pollen load',knee.lerp(ankle,.57)+Vector((side*.009,0,.010)),(.020,.031,.013),pollen,16,8)
    # Closed, contiguous abdominal rings, with a naturally tapering tip.
    rings=35;sides=28;verts=[];faces_by_mat={amber:[],dark:[]}
    for i in range(rings+1):
        t=i/rings;y=-.094-.292*t;r=.110*(math.sin(math.pi*(.07+.93*t))**.7)
        for j in range(sides):
            a=j*math.tau/sides;verts.append((r*math.cos(a),y,.017+r*.70*math.sin(a)))
    for i in range(rings):
        t=(i+.5)/rings;m=dark if (int(t*6)%2 or t>.88) else amber
        for j in range(sides):faces_by_mat[m].append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    for mat,faces in faces_by_mat.items():
        mesh=bpy.data.meshes.new('abdomen bands');mesh.from_pydata(verts,[],faces);mesh.update()
        obj=add_object('segmented abdomen '+mat.name,mesh,mat)
        for f in mesh.polygons:f.use_smooth=True
    for i in range(320):
        u=random.uniform(-1,1);a=random.random()*math.tau;v=math.sqrt(1-u*u)
        normal=Vector((v*math.cos(a),u,v*math.sin(a)))
        segment=0 if u>.63 else 2 if u<-.52 else 1
        p=chest.surface(segment,(1-u)*.5,a)
        length=random.uniform(.007,.018)
        tube('thoracic branched hair',[p,p+normal*length],[.0012,.00015],fur,4)
    for i in range(3):sphere('ocellus',(0,.228+i*.012,.082),(.006,.006,.004),eye,10,6)

def mantis():
    pre=current.name
    green=material(pre+'_GreenCuticle',(.18,.31,.075),.47)
    wing=material(pre+'_Forewing',(.23,.38,.105),.57)
    pale=material(pre+'_Vein',(.39,.47,.18),.56)
    dark=material(pre+'_JointSpine',(.075,.095,.025),.43)
    eyes=material(pre+'_Eye',(.36,.43,.17),.37)
    stripe=material(pre+'_VentralOchre',(.46,.38,.11),.53)
    sphere('abdomen',(0,-.226,.005),(.072,.174,.041),stripe,20,12)
    chest=Thorax(mesh_part,sphere,[(.367,.112,.031,-.002,.071),
        (.112,.028,.054,-.029,.051),(.028,-.066,.061,-.034,.050)],green)
    # Triangular head capsule with large eyes at the two lateral corners.
    plate('triangular head',[(-.082,.417),(0,.365),(.082,.417),(.069,.46),(-.069,.46)],green,z=.037,thickness=.040,curve_up=0)
    for side in (-1,1):
        sphere('compound eye',(side*.071,.432,.052),(.031,.035,.027),eyes,20,10)
        curve('long filament antenna',mirror([(.036,.45,.05),(.058,.55,.06),(.090,.66,.065),(.12,.735,.08)],side),.0025,dark,end=.0007)
        outline=[(.004,.065),(.053,.005),(.071,-.16),(.045,-.37),(.01,-.39),(.001,-.19)]
        plate('folded forewing',outline,wing,side,z=.044,thickness=.006)
        curve('forewing longitudinal vein',mirror([(.018,.04,.055),(.035,-.10,.057),(.022,-.36,.056)],side),.0024,pale)
        for i in range(7):
            y=.012-i*.045;w=.05*(1-max(0,-y-.17)*1.4)
            curve('forewing oblique vein',mirror([(.012,y-.03,.057),(w,y,.057)],side),.0013,pale,steps=2)
        # Foreleg coxa extends forward; enlarged femur and folding tibia make
        # the characteristic grasping apparatus, with opposing spine rows.
        root=chest.coxa(0,side,.015,green,fraction=.26)
        hip,knee,tip=map(Vector,mirror([(.082,.39,.019),(.154,.245,.022),(.091,.36,.028)],side))
        tube('elongated fore coxa',[root,root.lerp(hip,.55),hip],[.012,.018,.010],green,10)
        leg('raptorial foreleg',[hip,knee,tip,(side*.078,.385,.027)],green,.018,dark)
        for i in range(5):
            p=hip.lerp(knee,.16+i*.16)
            tube('femoral grasping spine',[p,p+Vector((-side*.020,-.011,-.005))],[.004,.0004],dark,5)
        for i in range(4):
            p=knee.lerp(tip,.14+i*.18)
            tube('tibial grasping spine',[p,p+Vector((side*.016,.003,-.005))],[.003,.0003],dark,5)
        for i in (1,2):
            root=chest.coxa(i,side,.012,green)
            y=root.y
            leg('walking leg',[root,(side*.16,y-.035,-.012),(side*.245,y-.19,-.073),
                               (side*.33,y-.23,-.075)],green,.009,dark)
    sphere('mouth shield',(0,.387,.060),(.018,.016,.007),stripe,12,8)

def spider():
    # A generalized female orb-weaver: two principal regions, eight walking
    # legs on the prosoma, small palps, eight simple eyes and posterior spinnerets.
    random.seed(718)
    pre=current.name
    cuticle=material(pre+'_BrownCuticle',(.21,.105,.045),.48)
    abdomen=material(pre+'_Abdomen',(.30,.185,.085),.62)
    dark=material(pre+'_DarkJoint',(.047,.027,.016),.53)
    folium=material(pre+'_Folium',(.085,.047,.024),.68)
    cream=material(pre+'_CreamPattern',(.62,.47,.25),.66)
    eye=material(pre+'_Eye',(.009,.008,.006),.17)
    hair=material(pre+'_Setae',(.37,.26,.13),.8)
    sphere('cephalothorax',(0,.115,.015),(.103,.122,.058),cuticle,24,12)
    sphere('soft abdomen',(0,-.145,.04),(.161,.203,.132),abdomen,28,18)
    tube('narrow pedicel',[(0,.008,.015),(0,-.025,.025)],[.023,.021],dark,12)
    # Short radial carapace grooves converge on the fovea.
    for side in (-1,1):
        for i in range(4):
            curve('carapace radial groove',mirror([(.015,.09,.072),(.055,.04+i*.036,.061),(.083,.03+i*.039,.044)],side),.0017,dark,steps=3)
    curve('fovea',[(0,.055,.073),(0,.09,.075),(0,.109,.073)],.0025,dark)

    def dorsal(x,y,lift=.0014):
        return (x,y,.04+.132*math.sqrt(max(.001,1-(x/.161)**2-((y+.145)/.203)**2))+lift)
    # The folium is a fine conforming patch instead of a floating flat decal.
    outline=[(0,.035),(.032,.005),(.054,-.027),(.082,-.04),(.065,-.067),(.10,-.09),(.075,-.12),(.105,-.146),
             (.079,-.18),(.083,-.205),(.055,-.224),(.052,-.255),(.025,-.283),(0,-.31)]
    outline+= [(-x,y) for x,y in reversed(outline[1:-1])]
    center=Vector((0,-.14));verts=[dorsal(*center)];segments=len(outline);rings=7;faces=[]
    for ring in range(1,rings+1):
        for point in outline:
            xy=center.lerp(Vector(point),ring/rings);verts.append(dorsal(xy.x,xy.y))
    for j in range(segments):faces.append((0,1+j,1+(j+1)%segments))
    for ring in range(rings-1):
        base=1+ring*segments;next_base=base+segments
        for j in range(segments):faces.append((base+j,next_base+j,next_base+(j+1)%segments,base+(j+1)%segments))
    mesh=bpy.data.meshes.new('conforming abdominal folium');mesh.from_pydata(verts,[],faces);mesh.update()
    for face in mesh.polygons:
        if face.normal.z<0:face.flip()
        face.use_smooth=True
    add_object('leaf-like dorsal folium',mesh,folium)
    for side in (-1,1):
        for i in range(5):
            y=-.026-i*.049;x=.032+(math.sin(i*math.pi/5)*.023)
            sphere('paired abdominal cream spot',dorsal(side*x,y,.003),( .012-i*.001,.008,.0025),cream,12,6)
        boundary=[dorsal(side*x,y,.0025) for x,y in outline[:14]]
        tube('cream folium border',boundary,.0018,cream,5)
    # Four pairs with clearly differentiated swept directions and angular knee
    # joints. Each distal tarsus carries the three small web-building claws.
    plans=[(.18,.46,.42),(.13,.43,.22),(.079,.40,-.16),(.028,.36,-.40)]
    for side in (-1,1):
        for leg_index,(root_y,reach,tip_y) in enumerate(plans):
            dy=tip_y-root_y
            knee_y=root_y+dy*.55+(.065 if leg_index<2 else -.055)
            pts=mirror([(.073,root_y,.009),(.113,root_y+dy*.08,.022),
                        (reach*.48,knee_y,.078),
                        (reach*.58,knee_y+(.007 if leg_index<2 else -.007),.061),
                        (reach*.83,knee_y+(tip_y-knee_y)*.65,-.035),
                        (reach*.96,knee_y+(tip_y-knee_y)*.92,-.080),
                        (reach,tip_y,-.088)],side)
            for j in range(len(pts)-1):
                a=Vector(pts[j]);b=Vector(pts[j+1]);radius=[.016,.018,.016,.012,.008,.005][j]
                tube('walking leg %d %s segment %d'%(leg_index+1,side,j+1),[a,a.lerp(b,.4),b],
                     [radius*.86,radius,radius*.65],cuticle,8)
                if j in (1,3,4):
                    tube('leg dark annulus',[a.lerp(b,.60),a.lerp(b,.79)],[radius*.92,radius*.83],dark,8)
                    tube('leg cream annulus',[a.lerp(b,.34),a.lerp(b,.44)],[radius*1.015,radius*.995],cream,8)
                if j<5:sphere('leg articulating joint',b,(radius*.75,)*3,dark,8,6)
                for h in range(3):
                    t=.18+h*.30;p=a.lerp(b,t);direction=Vector((side*.7,.2 if h%2 else -.2,.8)).normalized()
                    tube('fine leg seta',[p,p+direction*random.uniform(.008,.017)],[.0008,.0001],hair,4)
            end=Vector(pts[-1]);direction=(end-Vector(pts[-2])).normalized()
            for claw in (-1,0,1):
                tube('three terminal claws',[end,end+direction*.014+Vector((claw*.004,0,0)),end+direction*.019+Vector((claw*.004,0,.004))],
                     [.0017,.001,.0002],dark,5)
        # Palps are deliberately much shorter than any walking leg.
        leg('small pedipalp',mirror([(.036,.207,.02),(.059,.246,.004),(.053,.277,-.006)],side),cuticle,.007,dark)
        sphere('chelicera basal segment',(side*.022,.226,.016),(.014,.024,.016),dark,14,8)
        curve('curved fang',mirror([(.021,.245,.008),(.025,.265,-.007),(.009,.269,-.017)],side),.004,dark,end=.0007)
        for eye_index,(x,y,z,r) in enumerate([(.015,.223,.052,.0075),(.017,.203,.064,.0065),(.045,.221,.046,.0055),(.050,.208,.052,.0055)]):
            sphere('simple eye '+str(side)+' '+str(eye_index),(side*x,y,z),(r,r,r*.80),eye,12,8)
        for i in range(3):
            sphere('posterior spinneret',(side*(.009+i*.01),-.334+i*.007,-.006),(.007,.016,.007),dark,12,6)
    # Sparse actual geometry for body setae remains visible on close inspection.
    for i in range(220):
        u=random.uniform(-.8,.9);a=random.random()*math.tau;v=math.sqrt(1-u*u)
        normal=Vector((v*math.cos(a),u,v*math.sin(a)))
        p=Vector((normal.x*.161,-.145+normal.y*.203,.04+normal.z*.132))
        tube('abdominal fine seta',[p,p+normal*random.uniform(.004,.012)],[.00065,.00008],hair,4)

def finish_asset(name):
    bpy.context.view_layer.update()
    points=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center=(lo+hi)/2;factor=1/max(hi-lo)
    for obj in parts:
        obj.location=(obj.location-center)*factor;obj.scale*=factor
    bpy.context.view_layer.update()
    triangles=0
    for obj in parts:
        obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
    if triangles>20000:raise RuntimeError(name+' triangle budget exceeded: '+str(triangles))
    result=export_groups(EXPORT/(name+'.fbx'),parts)
    result.update(name=name,triangles=triangles,longest_dimension=1.0,blender_head_axis='+Y',blender_dorsal_axis='+Z')
    result['materials']=[{'name':m.name,'rgba':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value} for m in sorted({o.data.materials[0] for o in parts},key=lambda m:m.name)]
    if not 4<=result['material_groups']<=8:raise RuntimeError('Material budget outside 4–8')
    reports.append(result)
    study=bpy.data.scenes.new('Study | '+name);study.collection.children.link(current)
    work_scene.collection.children.unlink(current)
    return current

collections=[]
for name,builder in zip(NAMES,[lambda:beetle(False),butterfly,lambda:beetle(True),dragonfly,bee,mantis,spider]):
    if SPIDER_ONLY and name!='OrbWeaverSpider':
        collections.append(bpy.data.collections[name]);continue
    current=bpy.data.collections.new(name);work_scene.collection.children.link(current);parts=[]
    builder();collections.append(finish_asset(name))

# Clean specimen gallery: source parts remain at the origin in their Study
# scenes, while collection instances are arranged for the overview render.
current=bpy.data.collections.new('Gallery');work_scene.collection.children.link(current);parts=[]
work_scene.name='Terrestrial collection | gallery'
ground=material('Gallery_Background',(.025,.045,.048),.83)
labelmat=material('Gallery_Label',(.72,.80,.73),.7)
for i,(name,col) in enumerate(zip(NAMES,collections)):
    x=((i if i<4 else i-4)-(1.5 if i<4 else 1))*1.40;y=.80 if i<4 else -.80
    obj=bpy.data.objects.new(name+' preview',None);obj.instance_type='COLLECTION';obj.instance_collection=col
    obj.location=(x,y,.15);current.objects.link(obj)
    textcurve=bpy.data.curves.new(name+' caption','FONT');textcurve.body=['01   EMERALD BEETLE','02   SWALLOWTAIL','03   STAG BEETLE','04   DRAGONFLY','05   HONEY BEE','06   PRAYING MANTIS','07   ORB-WEAVER SPIDER'][i]
    textcurve.size=.067;textcurve.align_x='CENTER';textcurve.extrude=0
    label=bpy.data.objects.new(name+' label',textcurve);current.objects.link(label);label.location=(x,y-.66,-.055);textcurve.materials.append(labelmat)
    textcurve2=bpy.data.curves.new(name+' note','FONT');textcurve2.body='ARACHNID  /  NOT TO SCALE' if i==6 else 'ANATOMY STUDY  /  NOT TO SCALE';textcurve2.size=.034;textcurve2.align_x='CENTER'
    label2=bpy.data.objects.new(name+' note',textcurve2);current.objects.link(label2);label2.location=(x,y-.73,-.055);textcurve2.materials.append(labelmat)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.075));plane=bpy.context.object;plane.name='Gallery background';plane.data.materials.append(ground)
camera_data=bpy.data.cameras.new('Gallery camera');camera=bpy.data.objects.new('Gallery camera',camera_data);work_scene.collection.objects.link(camera)
camera.location=(0,-.8,9.3);target=Vector((0,-.06,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=5.85;work_scene.camera=camera
for name,loc,power,size,color in [('Key',(-3,2,5),420,4,(.90,.96,1)),('Warm fill',(3,-1,4),250,3,(1,.85,.66)),('Rim',(0,4,3),280,3,(.68,.85,1))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    obj=bpy.data.objects.new(name,data);work_scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
work_scene.world=bpy.data.worlds.new('Gallery world');work_scene.world.use_nodes=True;work_scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.2,.24,.27,1);work_scene.world.node_tree.nodes['Background'].inputs[1].default_value=.30
work_scene.render.engine='CYCLES';work_scene.cycles.samples=32;work_scene.cycles.use_denoising=True
work_scene.render.resolution_x=1800;work_scene.render.resolution_y=1200;work_scene.render.resolution_percentage=100
work_scene.view_settings.view_transform='AgX';work_scene.render.image_settings.file_format='PNG';work_scene.render.filepath=str(PREVIEW)
work_scene.render.threads_mode='FIXED';work_scene.render.threads=4
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
# Reload the saved gallery to rebuild dependency data after replacing collection
# instances; it also makes the preview exercise the on-disk editable artifact.
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
bpy.ops.render.render(write_still=True)
print('TERRESTRIAL_REPORT='+json.dumps(reports,ensure_ascii=False))
print('TERRESTRIAL_COMPLETE')
