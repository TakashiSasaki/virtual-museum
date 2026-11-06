"""Generic original pottery and stone-tool studies; no site, date or culture attribution.
Uses mesh/export helpers from the adjacent fossil generator without running its builders.
Separate background Blender process, two threads; --overwrite required for owned outputs.
"""
import bpy, math, random, runpy, sys, json, ast, bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
ROOT=Path(__file__).resolve().parents[1]
SAVE=ROOT/'blender/scenes/collections/reserve_artifacts.blend'
PREVIEW=ROOT/'blender/previews/collections/reserve_artifacts.png'
EXPORT=ROOT/'unity/VirtualMuseum/Assets/Museum/Models/Reserve'
NAMES=['EarthenwareDeepBowl','EarthenwareJar','PotterySherd','PolishedStoneAxe','KnappedArrowhead','StoneScraper']
if '--overwrite' not in sys.argv and any(p.exists() for p in [SAVE,PREVIEW]+[EXPORT/(n+'.fbx') for n in NAMES]):raise RuntimeError('Review owned outputs before --overwrite')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
export_groups=runpy.run_path(str(ROOT/'work/export_static_fbx.py'))['export_selected_groups']
source=(ROOT/'work/build_reserve_fossils.py').read_text(encoding='utf-8')
tree=ast.parse(source)
for node in tree.body:
    if isinstance(node,ast.FunctionDef):exec(compile(ast.Module(body=[node],type_ignores=[]),'<fossil helpers>','exec'))
random.seed(129);reports=[];collections=[]
def vessel(jar=False):
    clay=mat('Terracotta',(.38,.17,.08),.9);cord=mat('CordMarks',(.25,.10,.04),.94)
    profile=([(0,-.43),(.20,-.43),(.30,-.32),(.36,-.1),(.31,.15),(.15,.31),(.15,.43),(.18,.46),(.14,.46),(.11,.42),(.12,.31),(.27,.14),(.32,-.1),(.26,-.30),(.17,-.38),(0,-.38)] if jar else [(0,-.43),(.19,-.43),(.23,-.30),(.29,0),(.37,.40),(.38,.44),(.34,.44),(.33,.39),(.25,0),(.19,-.30),(.16,-.38),(0,-.38)])
    n=72;v=[];f=[]
    for r,z in profile:
        for j in range(n):
            t=j*math.tau/n;rr=r*(1+.008*math.sin(t*7+z*9));v.append((rr*math.cos(t),rr*math.sin(t),z))
    for i in range(len(profile)-1):
        for j in range(n):f.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    mesh('hollow thick walled vessel',v,f,clay)
    if not jar:
        for z in [.18,.23,.28,.33]:
            r=.29+z*.20+.004;tube('cord band',[(r*math.cos(j*math.tau/100),r*math.sin(j*math.tau/100),z+.003*math.sin(j)) for j in range(101)],.004,cord,5)
        for j in range(64):
            t=j*math.tau/64;tube('diagonal cord',[( (.29+z*.20+.005)*math.cos(t+z*.3),(.29+z*.20+.005)*math.sin(t+z*.3),z) for z in [.18,.23,.28,.33]],.0025,cord,4)
def sherd():
    clay=mat('WeatheredClay',(.44,.23,.12),.96);core=mat('DarkCore',(.23,.14,.09),.97)
    n=32;edge=[]
    for i in range(n):
        t=math.tau*i/n;r=random.uniform(.9,1.1);edge.append((.38*r*math.cos(t),.42*r*math.sin(t)))
    v=[(0,0,.02)]+[(x,y,.02+x*x*.5) for x,y in edge]+[(0,0,-.05)]+[(x,y,-.05+x*x*.5) for x,y in edge];f=[]
    for i in range(n):f.extend([(0,1+i,1+(i+1)%n),(n+1,n+2+(i+1)%n,n+2+i),(1+i,n+2+i,n+2+(i+1)%n,1+(i+1)%n)])
    mesh('curved broken wall',v,f,clay,False)
    for y in [-.21,-.13,-.05,.03,.11,.19]:tube('cord marks',[(x,y,.026+x*x*.5) for x in [-.25,-.125,0,.125,.25]],.006,core,5)
def stone(kind):
    m=mat('Greenstone' if kind==0 else 'Flint',(.12,.20,.18) if kind==0 else (.25,.22,.18),.30 if kind==0 else .57)
    if kind==0:
        profile=[(-.46,.20,.009),(-.38,.22,.05),(-.13,.19,.10),(.16,.15,.085),(.35,.11,.065),(.43,.04,.025)];n=24;v=[];f=[]
        for y,w,h in profile:
            for j in range(n):t=j*math.tau/n;v.append((w*math.cos(t),y,h*math.sin(t)))
        for i in range(len(profile)-1):
            for j in range(n):f.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
        f.extend([tuple(reversed(range(n))),tuple((len(profile)-1)*n+j for j in range(n))]);mesh('polished tapered axe',v,f,m)
    else:
        outline=([(-.08,-.43),(-.1,-.27),(-.29,-.33),(0,.48),(.29,-.33),(.1,-.27),(.08,-.43)] if kind==1 else [(-.34,-.32),(-.42,-.08),(-.32,.22),(-.12,.40),(.16,.37),(.38,.14),(.34,-.20),(.12,-.35)])
        edge=[]
        for i,a in enumerate(outline):
            b=outline[(i+1)%len(outline)]
            for j in range(4):
                t=j/4;edge.append((a[0]*(1-t)+b[0]*t+random.uniform(-.008,.008),a[1]*(1-t)+b[1]*t))
        n=len(edge);v=[(x,y,0) for x,y in edge]
        for s in [1,-1]:
            for x,y in edge:v.append((x*.54,y*.54,s*(.07+random.uniform(-.02,.02))))
        v.extend([(0,0,.10),(0,0,-.10)]);f=[]
        for i in range(n):
            j=(i+1)%n
            for o,c in [(n,3*n),(2*n,3*n+1)]:f.extend([(i,j,o+i),(j,o+j,o+i),(o+i,o+j,c)])
        mesh('flake scar facets',v,f,m,False)
for name,build in zip(NAMES,[lambda:vessel(False),lambda:vessel(True),sherd,lambda:stone(0),lambda:stone(1),lambda:stone(2)]):
    current=bpy.data.collections.new(name);scene.collection.children.link(current);parts=[];build()
    for o in parts:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.modifiers.new('Portable triangles','TRIANGULATE')
    collections.append(finish(name))
tail=source[source.index("current=bpy.data.collections.new('Gallery')"):]
tail=tail.replace("positions=[(-1.25,.75),(0,.75),(1.25,.75),(-.65,-.72),(.65,-.72)]","positions=[(-1.25,.75),(0,.75),(1.25,.75),(-1.25,-.72),(0,-.72),(1.25,-.72)]").replace("labels=['01  TRILOBITE','02  ORTHOCONE SECTION','03  CRINOID COLUMNALS','04  SHARK TOOTH','05  FERN COMPRESSION']","labels=['01  DEEP BOWL','02  EARTHENWARE JAR','03  POTTERY SHERD','04  POLISHED AXE','05  KNAPPED POINT','06  SCRAPER']").replace('GENERALIZED FOSSIL STUDY','GENERALIZED ARTIFACT STUDY').replace('camera.location=(0,-1.4,8)','camera.location=(0,-5,8)').replace('scene.cycles.samples=32','scene.cycles.samples=16').replace('RESERVE_FOSSILS','RESERVE_ARTIFACTS')
tail=tail.replace("inst.location=(x,y,.11)","inst.location=(x,y,.58 if i<2 else .11)")
exec(tail)

