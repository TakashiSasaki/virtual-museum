"""Create eight original, enlarged teaching models, editable Blender source and Unity FBX.

Run in a separate Blender background process. Never loads or changes an open project.
Use -- --overwrite only after reviewing this script's specific output files.
Axes before FBX export: X lateral, +Y anterior, +Z dorsal; centered, longest dimension 1 m.
These are generalized anatomical interpretations, not species-identification replicas.
Microscopic organisms use enlarged structures and exposed interiors for observation.

Anatomical references (consulted 2026-11-07; no source images/textures copied):
https://midge.cfans.umn.edu/vsmivp/coleoptera/coleopteraadult/dytiscidaeadult
https://extension.umaine.edu/home-and-garden-ipm/fact-sheets/common-name-listing/water-scorpions/
https://mdc.mo.gov/discover-nature/field-guide/dragonflies
https://ipm.ucanr.edu/PMG/G/I-LP-GENL-KC.001.html
https://mdc.mo.gov/discover-nature/field-guide/caddisfly-larvae
https://www.nies.go.jp/chiiki1/protoz/morpho/ciliopho/parameci.htm
https://www.science.umd.edu/labs/delwiche/PSlife/lectures/Euglenophyta.html
https://diatoms.org/glossary/Raphe
https://researcharchive.calacademy.org/research/diatoms/overview/glossary.html
"""
import bpy, math, random, runpy, sys, json, os
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
Thorax = runpy.run_path(str(ROOT / 'work/insect_anatomy.py'))['Thorax']
EXPORT = ROOT / 'unity/VirtualMuseum/Assets/Museum/Models/Collections'
SAVE = ROOT / 'blender/scenes/collections/aquatic_micro.blend'
PREVIEW = ROOT / 'blender/previews/collections/aquatic_micro.png'
NAMES = ['DivingBeetle', 'WaterScorpion', 'DragonflyNymph', 'Caterpillar',
         'CaddisflyLarva', 'Paramecium', 'Euglena', 'Diatom']
targets = [SAVE, PREVIEW] + [EXPORT / (n + '.fbx') for n in NAMES]
if '--overwrite' not in sys.argv and any(p.exists() for p in targets):
    raise RuntimeError('Collection output exists. Review before passing --overwrite.')
for directory in [EXPORT, SAVE.parent, PREVIEW.parent]: directory.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = 'Aquatic and microscopic collection | teaching models'
scene.unit_settings.system = 'METRIC'
scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
random.seed(8162)
parts = []; prefix = ''; statistics = []

def material(label, color, rough=.4, metal=0):
    m = bpy.data.materials.new(prefix + '_' + label)
    m.diffuse_color = (*color, 1); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    return m

def finish(obj, name, mat, smooth=True):
    obj.name = prefix + '_' + name
    obj.data.materials.append(mat)
    if smooth:
        for poly in obj.data.polygons: poly.use_smooth = True
    parts.append(obj)
    return obj

def mesh(name, vertices, faces, mat, smooth=True):
    data = bpy.data.meshes.new(prefix + '_' + name)
    data.from_pydata(vertices, [], faces); data.update()
    obj = bpy.data.objects.new(prefix + '_' + name, data); scene.collection.objects.link(obj)
    return finish(obj, name, mat, smooth)

def ball(name, loc, scale, mat, seg=18, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1, location=loc)
    obj = bpy.context.object; obj.scale = scale
    return finish(obj, name, mat)

def tube(name, pts, radii, mat, sides=8):
    points = [Vector(p) for p in pts]
    if isinstance(radii, (int, float)): radii = [radii] * len(points)
    vertices=[]; faces=[]
    for i,p in enumerate(points):
        tangent = points[min(i+1,len(points)-1)] - points[max(0,i-1)]
        tangent.normalize()
        ref = Vector((0,0,1)) if abs(tangent.z) < .9 else Vector((1,0,0))
        a = tangent.cross(ref).normalized(); b = tangent.cross(a).normalized()
        for j in range(sides):
            phi=j*math.tau/sides
            vertices.append(p + radii[i]*(math.cos(phi)*a+math.sin(phi)*b))
    for i in range(len(points)-1):
        for j in range(sides):
            nj=(j+1)%sides
            faces.append((i*sides+j,i*sides+nj,(i+1)*sides+nj,(i+1)*sides+j))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*sides+j for j in range(sides))])
    return mesh(name,vertices,faces,mat)

def ring(name, center, rx, ry, mat, r=.006, plane='XY', n=32):
    pts=[]
    for i in range(n+1):
        a=i*math.tau/n
        offset=(rx*math.cos(a),ry*math.sin(a),0) if plane=='XY' else (rx*math.cos(a),0,ry*math.sin(a))
        pts.append(Vector(center)+Vector(offset))
    return tube(name,pts,r,mat,6)

def leg(name, pts, mat, rad=.018, clawmat=None, single_claw=False):
    tube(name,pts,[rad,rad*1.15,rad*.64,rad*.25],mat)
    for i in [1,2]: ball(name+'_joint',pts[i],(rad*1.2,)*3,mat,12,6)
    if clawmat:
        p=Vector(pts[-1]); d=(p-Vector(pts[-2])).normalized()
        for side in ([0] if single_claw else [-1,1]):
            tube(name+'_claw',[p,p+d*rad*1.15+Vector((side*rad*.45,0,-rad*.40)),
                p+d*rad*1.65+Vector((side*rad*.30,0,-rad*.78))],
                [rad*.30,rad*.19,rad*.05],clawmat,6)

def leaflet(name, a, b, width, depth, mat):
    a,b=Vector(a),Vector(b)
    obj=ball(name,(a+b)/2,(width,(b-a).length/2,depth),mat)
    obj.rotation_mode='QUATERNION'; obj.rotation_quaternion=(b-a).to_track_quat('Y','Z')
    return obj

def begin(name):
    global parts,prefix
    parts=[];prefix=name

def export_model(name, label, position):
    bpy.context.view_layer.update()
    coordinates=[o.matrix_world @ Vector(c) for o in parts for c in o.bound_box]
    lo=Vector(tuple(min(c[a] for c in coordinates) for a in range(3)))
    hi=Vector(tuple(max(c[a] for c in coordinates) for a in range(3)))
    center=(lo+hi)/2; factor=1/max(hi-lo)
    root=bpy.data.objects.new(name,None);scene.collection.objects.link(root)
    root['interpretation']='Original generalized teaching model, enlarged details; not a species-accurate replica'
    for o in parts:
        o.location=(o.location-center)*factor; o.scale*=factor; o.parent=root
    bpy.context.view_layer.update()
    groups={}; dupes=[]
    dg=bpy.context.evaluated_depsgraph_get()
    for o in parts:
        assert len(o.data.materials)==1
        mat=o.data.materials[0]
        copy=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
        obj=bpy.data.objects.new(name+'_export',copy);scene.collection.objects.link(obj)
        obj.matrix_world=o.matrix_world.copy(); groups.setdefault(mat,[]).append(obj);dupes.append(obj)
    merged=[]
    for mat,objs in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:o.select_set(True)
        bpy.context.view_layer.objects.active=objs[0]
        if len(objs)>1: bpy.ops.object.join()
        obj=bpy.context.object;obj.name=mat.name;merged.append(obj)
    tris=0
    for o in merged:o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
    assert tris < 20000,(name,tris)
    assert 4 <= len(merged) <= 8,(name,len(merged))
    bpy.ops.object.select_all(action='DESELECT')
    for o in merged:o.select_set(True)
    bpy.context.view_layer.objects.active=merged[0]
    temporary=EXPORT/('.'+name+'.exporting')
    bpy.ops.export_scene.fbx(filepath=str(temporary),use_selection=True,object_types={'MESH'},
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',
        use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
    os.replace(temporary,EXPORT/(name+'.fbx'))
    for o in merged:bpy.data.objects.remove(o,do_unlink=True)
    root.location=position
    root['triangles']=tris;root['materials']=len(groups)
    statistics.append({'name':name,'triangles':tris,'materials':len(groups),'editable_parts':len(parts),
                       'normalized_dimensions':list((hi-lo)*factor),'material_names':[m.name for m in groups]})
    # Labels remain gallery-only and are never exported.
    data=bpy.data.curves.new(name+'_label','FONT');data.body=label;data.size=.082;data.align_x='CENTER'
    obj=bpy.data.objects.new(name+'_label',data);scene.collection.objects.link(obj)
    obj.location=(position[0],position[1]-.7,-.23);obj.data.materials.append(gallery_ink)

gallery_ink=material('Gallery_ink',(.065,.11,.12),.8)

# Dytiscid-like streamlined adult; six legs, swimming setae on the hind pair.
begin('DivingBeetle')
shell=material('Olive_chitin',(.052,.083,.038),.23,.08)
gold=material('Ochre_margin',(.56,.40,.095),.35)
under=material('Ventral_chitin',(.14,.105,.048),.48)
dark=material('Eyes_and_claws',(.008,.013,.012),.16)
hair=material('Swimming_setae',(.58,.49,.23),.56)
chest=Thorax(mesh,ball,[(.326,.206,.173,-.048,.088),
    (.206,.102,.182,-.067,.068),(.102,-.053,.211,-.076,.072)],under)
ball('ventral abdomen',(0,-.225,-.007),(.196,.187,.087),under,24,12)
for y in (-.10,-.155,-.21,-.265,-.32,-.37):
    section=math.sqrt(1-((y+.225)/.187)**2)
    tube('ventral abdominal seam',[(.196*section*math.sin(a),y,-.008-.087*section*math.cos(a))
         for a in (-1.15,-.77,-.38,0,.38,.77,1.15)],.0023,dark,6)
for side in [-1,1]:
    # A continuous half-dome gives the paired elytra one streamlined outline,
    # with a narrow median suture rather than two disconnected oval lobes.
    vertices=[]; faces=[]
    for iy in range(25):
        phi=math.pi*iy/24
        for ix in range(13):
            theta=math.pi*.5*ix/12
            vertices.append((side*(.0015+.235*math.sin(phi)*math.sin(theta)),
                             -.065+.345*math.cos(phi), .052+.108*math.sin(phi)*math.cos(theta)))
    for iy in range(24):
        for ix in range(12):
            a=iy*13+ix;face=(a,a+13,a+14,a+1)
            faces.append(face if side>0 else tuple(reversed(face)))
    mesh('elytron',vertices,faces,shell)
    pts=[]
    for j in range(27):
        a=-math.pi/2+math.pi*j/26
        pts.append((side*(.012+.228*math.cos(a)),-.065+.342*math.sin(a),.071))
    tube('elytral_margin',pts,.008,gold,6)
    # Long shallow striae follow the convex elytra.
    for stripe in [.045,.083,.122,.159]:
        tube('elytral_stria',[(side*stripe,y,.053+.108*math.sqrt(max(.02,1-((y+.065)/.345)**2-(stripe/.235)**2))) for y in [-.28,-.21,-.12,0,.10]],.0016,under,5)
ball('pronotum',(0,.248,.035),(.19,.098,.095),shell)
tube('pronotal_margin',[(-.18,.245,.08),(-.12,.32,.08),(0,.337,.08),(.12,.32,.08),(.18,.245,.08)],.008,gold)
ball('head',(0,.35,.018),(.118,.095,.07),shell)
for s in [-1,1]:
    ball('compound_eye',(s*.098,.373,.043),(.033,.041,.033),dark)
    tube('antenna',[(s*.075,.412,.028),(s*.135,.46,.038),(s*.19,.49,.026),(s*.23,.505,.01)],[.009,.007,.004,.0015],gold)
    for i in range(3):
        root=chest.coxa(i,s,.021 if i==2 else .016,under,
                        fraction=.73 if i==2 else .53,angle=-.92)
        y=root.y
        if i<2:
            leg('walking_leg',[root,(s*.265,y+.021,-.04),(s*.31,y-.10,-.073),
                               (s*.36,y-.15,-.075)],under,.016,dark)
        else:
            ball('broad metacoxal plate', (s*.092,y,-.057),(.084,.029,.018),under,14,8)
            knee=Vector((s*.306,-.146,-.038));ankle=Vector((s*.368,-.336,-.054))
            tip=Vector((s*.31,-.448,-.062))
            leg('swimming_leg',[root,knee,ankle,tip],under,.022,dark)
            leaflet('flattened_hind_tibia',knee,ankle,.030,.013,gold)
            leaflet('flattened_hind_tarsus',ankle,tip,.018,.008,under)
            for start,end,count in ((knee,ankle,11),(ankle,tip,6)):
                for j in range(count):
                    p=start.lerp(end,(j+1)/(count+1))
                    tube('paddle_fringe',[p,p+Vector((s*.040,-.017,.001)),
                        p+Vector((s*.065,-.032,0))],[.0022,.0014,.0005],hair,5)
export_model(prefix,'01  DIVING BEETLE',(-1.95,.9,0))

# Nepa-like broad water scorpion: grasping forelegs and paired respiratory siphon.
begin('WaterScorpion')
body=material('Leaf_brown',(.20,.12,.065),.58)
edge=material('Dry_russet',(.37,.25,.13),.62)
dark=material('Eyes',(.017,.013,.009),.2)
seam=material('Seams',(.085,.055,.025),.62)
chest=Thorax(mesh,ball,[(.295,.174,.125,-.028,.052),
    (.174,.067,.152,-.038,.054),(.067,-.060,.166,-.039,.053)],body)
ball('flat_abdomen',(0,-.19,0),(.198,.155,.047),body,24,12)
for s in [-1,1]:
    leaflet('hemelytron',(s*.07,.17,.035),(s*.04,-.31,.041),.115,.024,edge)
    tube('wing_vein',[(s*.016,.12,.063),(s*.11,-.035,.069),(s*.06,-.255,.065)],.004,seam,6)
ball('pronotum',(0,.22,.005),(.13,.11,.045),body)
ball('head',(0,.33,.005),(.069,.07,.043),edge)
for s in [-1,1]:
    ball('eye',(s*.06,.34,.028),(.018,.022,.019),dark,14,8)
    root=chest.coxa(0,s,.023,edge,fraction=.31)
    leg('grasping_foreleg',[root,(s*.22,.42,.025),(s*.20,.53,.013),(s*.13,.39,.011)],edge,.024,seam)
    for j in range(5):
        tube('grasping_teeth',[(s*.20,.43+j*.017,.015),(s*.175,.423+j*.017,.018)],[.005,.0008],seam,5)
    for i,tip in [(1,.10),(2,-.23)]:
        root=chest.coxa(i,s,.014,body)
        leg('walking_leg',[root,(s*.32,root.y+.03,-.02),
            (s*.37,tip-.12,-.031),(s*.43,tip-.18,-.035)],body,.014,seam)
    tube('siphon_half',[(s*.011,-.31,0),(s*.009,-.52,.005),(s*.005,-.73,.01)],[.010,.007,.002],edge,8)
tube('beak',[(0,.37,-.016),(0,.27,-.063),(0,.19,-.04)],[.018,.012,.002],seam,8)
export_model(prefix,'02  WATER SCORPION',(-.65,.9,0))

# Anisopteran nymph, not a damselfly: no external leaflike tail gills.
begin('DragonflyNymph')
armor=material('Olive_armor',(.21,.245,.095),.49)
ridge=material('Segment_rims',(.32,.32,.15),.53)
limb=material('Jointed_limbs',(.17,.18,.075),.48)
eye=material('Compound_eyes',(.075,.062,.029),.24)
dark=material('Sutures',(.06,.065,.023),.6)
chest=Thorax(mesh,ball,[(.273,.204,.105,-.031,.081),
    (.204,.138,.121,-.038,.088),(.138,.067,.125,-.040,.082)],armor)
for i in range(10):
    y=.039-i*.049; w=.14*(1-.071*i)
    ball('abdominal_tergite_%02d'%i,(0,y,0),(w,.04,.056*(1-i*.05)),armor)
    tube('segment_suture',[(-w*.87,y-.014,.026),(0,y-.024,.054*(1-i*.05)),(w*.87,y-.014,.026)],.004,ridge,6)
    if i>3:
        for s in [-1,1]:tube('lateral_spine',[(s*w*.85,y,0),(s*(w+.018),y-.03,.008)],[.008,.001],limb,6)
ball('head',(0,.315,.021),(.15,.09,.068),ridge,22,12)
leaflet('folded labial mask',(0,.211,-.036),(0,.377,-.048),.050,.015,limb)
for s in [-1,1]:
    ball('compound_eye',(s*.126,.34,.043),(.052,.057,.047),eye)
    tube('short_antenna',[(s*.065,.371,.056),(s*.071,.42,.066),(s*.095,.449,.053)],[.007,.004,.001],limb,6)
    for i in range(3):
        root=chest.coxa(i,s,.015,limb)
        y=root.y
        leg('thoracic_leg',[root,(s*(.22+i*.018),y+.03,-.017),
            (s*(.28+i*.02),y-.10,-.058),(s*(.32+i*.015),y-.13,-.06)],limb,.012,dark)
    for i,xoff,tail in ((1,.050,-.025),(2,.085,-.074)):
        base=chest.surface(i,.45,.96,s)
        tip=Vector((s*xoff,tail,.061))
        leaflet('forewing pad' if i==1 else 'hindwing pad',base,tip,.026,.012,ridge)
        tube('wing pad seam',[base.lerp(tip,.26)+Vector((0,0,.010)),
            base.lerp(tip,.76)+Vector((0,0,.010))],.0022,dark,5)
    tube('labial_palp',[(s*.035,.345,-.053),(s*.061,.39,-.061),(s*.014,.397,-.055)],[.014,.013,.003],limb,8)
tube('dorsal epiproct',[(0,-.418,.024),(0,-.463,.011)],[.012,.001],limb,7)
for s in (-1,1):
    tube('ventral paraproct',[(s*.017,-.419,-.013),(s*.024,-.469,-.003)],[.013,.001],limb,7)
    tube('short lateral cercus',[(s*.028,-.415,.011),(s*.037,-.444,.010)],[.008,.001],limb,7)
export_model(prefix,'03  DRAGONFLY NYMPH',(.65,.9,0))

# Generalized lepidopteran larva: 3 thoracic pairs and prolegs on A3-6 and A10.
begin('Caterpillar')
skin=material('Leaf_green',(.29,.48,.11),.56)
ridge=material('Lateral_cream',(.68,.72,.30),.55)
headmat=material('Head_capsule',(.25,.33,.075),.4)
dark=material('Spiracles_ocelli',(.055,.07,.023),.42)
feet=material('Legs',(.38,.40,.14),.5)
setae=material('Setae',(.67,.63,.34),.67)
for i in range(13):
    y=.36-i*.065; x=.028*math.sin(i*.42); z=.018*math.sin(i*.3)
    radius=.080 if i<3 else .088-.0025*max(0,i-7)
    segment=('T%d thorax'%(i+1)) if i<3 else ('A%d abdomen'%(i-2))
    thoracic_shell=ball(segment,(x,y,z),(radius,.043,radius*.92),skin,18,9)
    if i<3:thoracic_shell['thoracic_segment']=i+1
    for s in [-1,1]:
        if i==0 or 3<=i<=10:
            ball('spiracle_rim',(x+s*radius*.93,y,z+.012),(.005,.014,.012),ridge,12,6)
            ball('spiracle',(x+s*radius*.974,y,z+.013),(.003,.009,.007),dark,12,6)
        tube('lateral_stripe',[(x+s*radius*.79,y-.029,z+.042),(x+s*radius*.90,y,z+.04),(x+s*radius*.79,y+.029,z+.042)],.005,ridge,6)
        for t in [0,1]:
            tube('short_seta',[(x+s*radius*.62,y+t*.012,z+radius*.62),(x+s*radius*.78,y+t*.012,z+radius*.85)],[.0015,.0004],setae,5)
        if i<3:
            root=Vector((x+s*.050,y,z-.057))
            socket=ball(segment+' coxa',root,(.010,.011,.009),feet,10,6)
            socket['leg_segment']=i+1;socket['leg_side']=s
            leg('thoracic_true_leg',[root,(x+s*.072,y+.01,z-.084),
                (x+s*.070,y+.032,z-.106),(x+s*.058,y+.047,z-.105)],feet,.008,dark,single_claw=True)
        if i in [5,6,7,8,12]:
            base=Vector((x+s*.049,y,z-.072))
            ball(segment+' fleshy proleg',base,(.025,.024,.045),skin,14,8)
            for j in range(10):
                a=j*math.tau/10;out=Vector((math.cos(a),math.sin(a),0))
                p=base+out*.014+Vector((0,0,-.035))
                tube('proleg crochet',[p,p+Vector((0,0,-.007)),
                    p-out*.005+Vector((0,0,-.009))],[.0018,.0014,.0005],dark,4)
ball('head_capsule',(0,.431,-.002),(.077,.068,.074),headmat,22,12)
for s in [-1,1]:
    for j in range(6):
        a=j*math.pi/5
        ball('stemmata',(s*.068,.448+.018*math.cos(a),.01+.022*math.sin(a)),(.004,.005,.005),dark,10,6)
    tube('mandible',[(s*.028,.48,-.022),(s*.021,.502,-.038),(s*.003,.497,-.04)],[.014,.010,.003],feet)
export_model(prefix,'04  CATERPILLAR',(1.95,.9,0))

# Case-bearing caddisfly larva with a granular mineral case and six exposed legs.
begin('CaddisflyLarva')
soft=material('Soft_abdomen',(.65,.59,.40),.65)
chitin=material('Head_and_sclerites',(.18,.092,.031),.34)
dark=material('Mouth_eyes',(.025,.021,.012),.3)
case=material('Silk_case',(.25,.21,.15),.85)
stoneA=material('Pale_grains',(.52,.47,.35),.87)
stoneB=material('Dark_grains',(.27,.26,.21),.82)
stoneC=material('Ochre_grains',(.40,.29,.15),.84)
for i in range(9):
    width=.072-i*.0037
    ball('soft abdominal segment %d'%(i+1),(0,.135-i*.063,0),(width,.043,width*.85),soft,16,8)
# Hollow tapered wall, rather than a sealed solid hiding the larva's head.
verts=[];faces=[];N=28
for y,r in [(.17,.112),(-.46,.068),(.17,.094),(-.46,.053)]:
    for j in range(N):
        a=math.tau*j/N;verts.append((r*math.cos(a),y,r*math.sin(a)))
for a,b in [(0,1),(2,3),(0,2),(1,3)]:
    for j in range(N):k=(j+1)%N;faces.append((a*N+j,a*N+k,b*N+k,b*N+j))
mesh('open_case',verts,faces,case)
for row in range(14):
    y=.148-row*.043;radius=.111-(.148-y)*.07
    for j in range(11):
        a=(j+(row%2)*.5)*math.tau/11
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(radius*math.cos(a),y,radius*math.sin(a)))
        obj=bpy.context.object;obj.scale=(random.uniform(.019,.03),random.uniform(.025,.036),random.uniform(.014,.024))
        obj.rotation_euler=(random.random()*2,random.random()*2,random.random()*2)
        finish(obj,'case_grain',random.choice([stoneA,stoneB,stoneC]),False)
chest=Thorax(mesh,ball,[(.349,.291,.074,-.043,.075),
    (.291,.229,.072,-.045,.064),(.229,.165,.070,-.047,.055)],chitin)
for i in range(3):
    for s in [-1,1]:
        root=chest.coxa(i,s,.011,chitin)
        y=root.y
        leg('thoracic_leg',[root,(s*.116,y+.025,-.023),(s*.13,y+.06,-.049),
            (s*.117,y+.081,-.052)],chitin,.009,dark,single_claw=True)
ball('head',(0,.385,.013),(.068,.064,.053),chitin)
for s in [-1,1]:
    ball('stemmata',(s*.06,.402,.035),(.009,.016,.01),dark,12,6)
    tube('mandible',[(s*.026,.431,.005),(s*.034,.455,-.001),(s*.005,.461,-.004)],[.012,.009,.003],dark,7)
    tube('terminal anal proleg',[(s*.017,-.388,-.014),(s*.027,-.422,-.019),
        (s*.040,-.448,-.014)],[.012,.010,.007],soft,8)
    tube('terminal anal hook',[(s*.040,-.446,-.014),(s*.052,-.454,-.011),
        (s*.049,-.462,-.007)],[.004,.003,.0007],chitin,7)
export_model(prefix,'05  CADDISFLY LARVA',(-1.95,-.95,0))

def cell_body(name, widths, lengths, heights, mat, n=32, cutaway=False, bend=.0):
    vertices=[];faces=[]
    # Open dorsal sector is deliberate: enlarged organs remain observable without transparent shaders.
    for i,(y,w,h) in enumerate(zip(lengths,widths,heights)):
        for j in range(n+1):
            a=math.radians(35)+math.radians(290)*j/n if cutaway else math.tau*j/n
            vertices.append((w*math.sin(a)+bend*math.sin(i*.30),y,h*math.cos(a)))
    for i in range(len(lengths)-1):
        for j in range(n):faces.append((i*(n+1)+j,i*(n+1)+j+1,(i+1)*(n+1)+j+1,(i+1)*(n+1)+j))
    obj=mesh(name,vertices,faces,mat)
    # A real thickness keeps both outside and exposed inside visible with Unity's
    # ordinary back-face-culling opaque shaders; no two-sided material is needed.
    wall=obj.modifiers.new('Visible cutaway wall thickness','SOLIDIFY')
    wall.thickness=.003;wall.offset=0
    return obj

# Slipper-shaped ciliate with ciliary rows, oral groove, nuclei and two radial vacuoles.
begin('Paramecium')
mem=material('Pellicle',(.40,.60,.59),.38)
cyto=material('Cytoplasm',(.57,.72,.66),.52)
cilia=material('Cilia',(.64,.64,.40),.47)
nuc=material('Nuclei',(.30,.25,.32),.43)
vacuole=material('Vacuoles',(.27,.47,.49),.3)
oral=material('Oral_groove',(.18,.36,.34),.5)
ys=[-.46+i*.046 for i in range(21)]
ws=[.17*(math.sin(math.pi*i/20)**.6)*(1+.14*math.sin(i*.25))+.003 for i in range(21)]
hs=[w*.65 for w in ws]
cell_body('open_pellicle',ws,ys,hs,mem,32,True,.018)
ball('exposed_cytoplasm',(.01,-.005,-.015),(.12,.39,.065),cyto,28,16)
for i in range(2,20):
    for j in range(16):
        a=math.tau*j/16+.09*(i%2);y=ys[i];w=ws[i];h=hs[i]
        if math.cos(a)>.82:continue
        p=Vector((w*math.sin(a)+.018*math.sin(i*.3),y,h*math.cos(a)))
        outward=Vector((math.sin(a),-.25,math.cos(a))).normalized()
        tube('cilium',[p,p+outward*.026+Vector((0,-.006,0)),p+outward*.047+Vector((0,-.02,0))],[.0022,.0015,.0006],cilia,5)
ball('macronucleus',(-.019,-.028,.067),(.046,.085,.034),nuc,20,12)
ball('micronucleus',(.032,.035,.061),(.014,.016,.014),nuc,14,8)
for y in [-.257,.245]:
    ball('contractile_vacuole',(.016,y,.045),(.037,.037,.018),vacuole)
    for j in range(7):
        a=math.tau*j/7
        tube('radial_canal',[(.016+math.cos(a)*.03,y+math.sin(a)*.03,.047),(.016+math.cos(a)*.068,y+math.sin(a)*.068,.041)],[.007,.002],vacuole,6)
for x,y,r in [(-.065,.115,.021),(.059,-.14,.023),(-.044,-.17,.018),(.037,.14,.014)]:ball('food_vacuole',(x,y,.049),(r,r,.014),vacuole,16,8)
tube('oral_groove',[(.11,.22,.074),(.12,.12,.065),(.093,.025,.053),(.063,-.046,.035)],[.015,.022,.02,.008],oral,10)
export_model(prefix,'06  PARAMECIUM  /  CUTAWAY',(-.65,-.95,0))

# Euglenid, with exposed chloroplasts, pellicular strips, reservoir, stigma, flagellum.
begin('Euglena')
mem=material('Pellicle',(.22,.42,.16),.43)
cyto=material('Cytoplasm',(.47,.64,.28),.5)
chloro=material('Chloroplasts',(.065,.25,.067),.43)
stigma=material('Eyespot',(.63,.105,.039),.42)
nucleus=material('Nucleus',(.55,.49,.20),.52)
canal=material('Reservoir',(.12,.25,.12),.4)
ys=[-.43+i*.038 for i in range(21)]
ws=[.115*(math.sin(math.pi*i/20)**.85)+.002 for i in range(21)]
hs=[w*.75 for w in ws]
cell_body('open_pellicle',ws,ys,hs,mem,28,True)
ball('exposed_cytoplasm',(0,-.04,-.008),(.085,.30,.052),cyto,24,12)
for j in range(10):
    pts=[]
    for i in range(1,20):
        a=math.tau*j/10+i*.075
        if math.cos(a)>.84:continue
        pts.append((ws[i]*math.sin(a)*1.012,ys[i],hs[i]*math.cos(a)*1.012))
    if len(pts)>1:tube('pellicular_strip',pts,.0025,cyto,5)
for i in range(11):
    y=-.28+i*.041;s=-1 if i%2 else 1
    leaf=ball('chloroplast',(s*.035,y,.045),(.025,.042,.012),chloro,16,8);leaf.rotation_euler.z=s*.35
ball('nucleus',(0,-.07,.055),(.028,.038,.022),nucleus)
ball('reservoir',(0,.267,.018),(.027,.036,.027),canal)
ball('eyespot',(.044,.22,.05),(.018,.024,.012),stigma)
tube('emergent_flagellum',[(0,.29,.03),(-.018,.36,.04),(-.07,.43,.065),(-.08,.51,.07),(-.018,.58,.05),(.065,.60,.03),(.10,.63,.015)],[.007,.006,.005,.004,.003,.002,.0008],mem,8)
export_model(prefix,'07  EUGLENA  /  CUTAWAY',(.65,-.95,0))

# Generalized pennate frustule: paired valves, girdle, bilateral striae, areolae and raphe.
begin('Diatom')
silica=material('Silica_valves',(.72,.65,.41),.31)
ribs=material('Silica_ribs',(.88,.80,.55),.37)
well=material('Recessed_areolae',(.23,.24,.18),.58)
girdle=material('Girdle_bands',(.54,.49,.29),.48)
raphe=material('Raphe_slit',(.17,.16,.095),.55)
for z in [-.041,.041]:
    ball('valve',(0,0,z),(.175,.48,.027),silica,32,16)
    for i in range(-16,17):
        y=i*.025;w=.175*math.sqrt(max(0,1-(y/.48)**2))
        if abs(y)<.035:continue
        for s in [-1,1]:
            tube('transverse_stria',[(s*.021,y,z+math.copysign(.026,z)),(s*w*.50,y+math.copysign(.005,y),z+math.copysign(.025,z)),(s*w*.91,y+math.copysign(.009,y),z+math.copysign(.013,z))],.004,ribs,6)
            for j in range(1,5):
                x=s*(.018+(w-.03)*j/5)
                # Inset dark centers surrounded by the raised striae read as pores at observation distance.
                ball('areola',(x,y+.010,z+math.copysign(.026*(1-(x/.22)**2),z)),(.006,.004,.0019),well,6,3)
    for sy in [-1,1]:
        tube('raphe',[(0,sy*.025,z+math.copysign(.027,z)),(.004,sy*.20,z+math.copysign(.026,z)),(0,sy*.425,z+math.copysign(.018,z))],.0035,raphe,6)
    ball('central_nodule',(0,0,z+math.copysign(.027,z)),(.022,.027,.006),ribs,16,8)
for z in [-.015,0,.015]:ring('girdle',(0,0,z),.172,.475,girdle,.004,n=56)
export_model(prefix,'08  PENNATE DIATOM',(1.95,-.95,0))

# Calm catalog presentation. Source remains editable; gallery furniture is not in FBX.
prefix='Gallery';parts=[]
ground=material('Background',(.76,.79,.75),.82)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.27));bpy.context.object.data.materials.append(ground)
for name,loc,power,size in [('Key',(-3,-2,6),700,5),('Fill',(4,1,4),450,4),('Rim',(0,4,5),500,3)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('Collection overview',bpy.data.cameras.new('Collection overview'))
scene.collection.objects.link(camera);camera.location=(0,-3.4,8.0)
camera.rotation_euler=(Vector((0,-.1,0))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=5.7;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=28;scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Collection studio world')
scene.world.color=(.25,.25,.25)
scene.view_settings.view_transform='AgX'
scene.render.resolution_x=2200;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
scene['collection_statistics']=json.dumps(statistics)
scene['references']=__doc__
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(SAVE))
bpy.ops.render.render(write_still=True)
print('COLLECTION_STATISTICS='+json.dumps(statistics))
print('AQUATIC_MICRO_COLLECTION_COMPLETE')
