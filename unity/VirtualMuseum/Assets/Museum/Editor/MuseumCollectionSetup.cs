using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

public static class MuseumCollectionSetup
{
    const string Models="Assets/Museum/Models/Collections/";
    const string Materials="Assets/Museum/Materials/Collections";
    const string CollectionPath="Assets/Museum/ExpandedCollection.asset";
    static MuseumCollection.Entry E(string id,string title,string english,string description,int pattern,string caption)
    {
        var model=AssetDatabase.LoadAssetAtPath<GameObject>(Models+id+".fbx");
        if(!model)throw new FileNotFoundException("Missing collection asset: "+id);
        return new MuseumCollection.Entry {model=model,title=title,english=english,description=description+"\n\n形態を比較するための制作模型です。特定の実物標本をスキャンしたものではありません。",microscopePattern=pattern,microscopeCaption=caption};
    }

    [MenuItem("Museum/Expand Natural History Collection")]
    public static void Apply()
    {
        if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Stop Play before editing the collection.");
        var scene=SceneManager.GetActiveScene();
        if(scene.isDirty)throw new InvalidOperationException("Save current scene before applying collection changes.");
        var app=UnityEngine.Object.FindAnyObjectByType<MuseumExperience>();
        if(!app || scene.path!=MuseumWebBuild.ScenePath)throw new InvalidOperationException("Open MuseumV1 first.");
        AssetDatabase.Refresh();
        if(!AssetDatabase.IsValidFolder(Materials))AssetDatabase.CreateFolder("Assets/Museum/Materials","Collections");
        foreach(var file in Directory.GetFiles(Models,"*.fbx"))ImportMaterials(file.Replace('\\','/'));
        var entries=new[] {
            E("NaturalBeetle","コガネムシの仲間","BEETLE / ELYTRA","背側では上翅の合わせ目、腹側では脚の付け根を観察します。前胸・中胸・後胸のそれぞれに1対ずつ、合計6本の脚が付きます。",0,"複眼をイメージした模式図"),
            E("SwallowtailButterfly","アゲハチョウの仲間","BUTTERFLY / WINGS","2対の翅は中胸と後胸に付きます。翅脈や後翅の尾状突起を見たら、模型を回して胸の3節から出る脚も数えてみましょう。",1,"翅の鱗粉をイメージした模式図"),
            E("FossilAmmonite","アンモナイトの化石","AMMONITE / FOSSIL","外側ほど太くなる殻の巻きと、殻表面の肋を観察します。母岩に残された化石の姿をイメージした模型です。",2,"殻の模様をイメージした模式図"),
            E("StagBeetle","クワガタムシの仲間","STAG BEETLE / MANDIBLES","大きな大あご、硬い上翅、節のある触角と脚を比較します。大あごの形は種類や雌雄によって異なります。",0,"複眼の模式図"),
            E("Dragonfly","トンボの成虫","DRAGONFLY / ADULT","大きな複眼、2対の透明な翅と翅脈、細長く分節した腹部が見どころです。ヤゴの展示とも比較できます。",3,"翅や体表の構造をイメージした模式図"),
            E("Honeybee","ミツバチの仲間","HONEYBEE / POLLINATOR","胸部の毛と2対の翅を観察します。胸の3節には脚が1対ずつ付き、働きバチは後脚の脛節にある花粉かごで花粉を運びます。",0,"複眼の模式図"),
            E("Mantis","カマキリの仲間","MANTIS / RAPTorial LEGS","獲物をつかむ棘のある前脚は、長い前胸に付きます。残る2対は中胸と後胸に付いています。",3,"体表の模式図"),
            E("DivingBeetle","ゲンゴロウの仲間","DIVING BEETLE / AQUATIC","後胸から出る後脚の、平たい節と毛を見てみましょう。泳ぐときに水をかく部分です。上翅の下には胸の後半と腹が続きます。",3,"体表の模式図"),
            E("WaterScorpion","タイコウチの仲間","WATER SCORPION / AQUATIC","獲物をつかむ前脚、平たい体、腹端の呼吸管を観察します。名前に反してサソリではなく昆虫の仲間です。",3,"体表の模式図"),
            E("DragonflyNymph","トンボの幼虫・ヤゴ","DRAGONFLY / NYMPH","成虫よりずんぐりした水中生活の姿を観察します。6本の脚、翅になる部分、腹部の節を成虫と比較してください。",3,"幼虫の体表をイメージした模式図"),
            E("CaddisflyLarva","トビケラの幼虫","CADDISFLY / LARVA","小石でできた巣から頭と胸が出ており、胸に3対の脚があります。腹の末端には巣にとどまるためのかぎ爪があります。",4,"幼虫の体表をイメージした模式図"),
            E("Caterpillar","イモムシの体のつくり","CATERPILLAR / LARVA","頭のすぐ後ろの3節に硬い脚が1対ずつ付きます。腹部のやわらかい腹脚の先には、小さなかぎが並んでいます。",4,"幼虫の毛と体表の模式図"),
            E("Paramecium","ゾウリムシの拡大模型","PARAMECIUM / CILIATE","体を覆う繊毛と、細胞内部を見せる切開表現を観察します。肉眼では小さい単細胞生物を大きな模型にしています。",5,"細胞構造をイメージした模式図"),
            E("Euglena","ミドリムシの拡大模型","EUGLENA / FLAGELLUM","細長い細胞の形、鞭毛、内部の葉緑体などをイメージした造形です。内部を見やすくするため一部を開いています。",6,"細胞構造をイメージした模式図"),
            E("Diatom","珪藻の拡大模型","DIATOM / FRUSTULE","ガラス質の殻の輪郭と、規則的な細かい模様を観察します。実際より大きく、構造を強調した教材模型です。",7,"殻の条線をイメージした模式図"),
            E("QuartzCluster","水晶の結晶群","QUARTZ / CRYSTALS","六角柱と尖った先端、結晶が集まる姿を回して観察します。結晶面の向きや大きさの違いを見比べてください。",8,"結晶面をイメージした模式図"),
            E("PyriteCluster","黄鉄鉱の結晶群","PYRITE / CRYSTALS","金属光沢、立方体の輪郭、面に見える条線を観察します。水晶とは異なる結晶の形を比較できます。",9,"結晶面と条線の模式図"),
            E("KingfisherMount","カワセミの剥製型模型","KINGFISHER / MOUNT","長い嘴、青い背と橙色の胸、重なった羽、枝をつかむ足を観察します。剥製の展示姿勢を再現した制作模型です。",10,"羽枝をイメージした模式図"),
            E("SquirrelMount","リスの剥製型模型","SQUIRREL / MOUNT","大きな尾、耳、前脚、毛の流れを観察します。哺乳類の体のつくりを比較するための剥製型の模型です。",11,"毛をイメージした模式図"),
            E("RearingTerrarium","中が見える飼育箱","REARING / TERRARIUM","透明な側面から、床材、朽木、葉、箱内の昆虫を観察できます。蓋のメッシュや枠の構造も回して見てください。",12,"葉や床材をイメージした模式図"),
            E("OrbWeaverSpider","クモの体のつくり","SPIDER / ARACHNID","クモは昆虫ではありません。頭胸部と腹部、8本の脚、口の近くの小さな触肢を、6本脚の昆虫と比較します。",3,"体表や毛をイメージした模式図"),
            E("Cockroach","ゴキブリの仲間","BLATTODEA / COCKROACH","シロアリと同じゴキブリ目の比較展示です。平たい体、前胸背板、長い触角、棘のある6本の脚を観察します。",3,"体表の模式図"),
            E("Termite","シロアリの仲間","BLATTODEA / TERMITE","ゴキブリと同じゴキブリ目に含まれる昆虫です。淡い体、触角、腹部の形を比較してください。シロアリはアリの仲間ではありません。",3,"体表の模式図")
        };
        var data=AssetDatabase.LoadAssetAtPath<MuseumCollection>(CollectionPath);
        if(!data){data=ScriptableObject.CreateInstance<MuseumCollection>();AssetDatabase.CreateAsset(data,CollectionPath);}
        data.entries=entries;EditorUtility.SetDirty(data);
        var previous=GameObject.Find("Expanded collection displays");
        if(previous)Undo.DestroyObjectImmediate(previous);
        var root=new GameObject("Expanded collection displays");Undo.RegisterCreatedObjectUndo(root,"Expand museum collection");
        foreach(var old in UnityEngine.Object.FindObjectsByType<MuseumExhibit>(FindObjectsInactive.Include))
            if(old.name=="DummyBeetle" || old.name=="DummyButterfly" || old.name=="DummyAmmonite") {Undo.RecordObject(old.gameObject,"Replace old display");old.gameObject.SetActive(false);}
        var destinations=new Transform[entries.Length+2];
        Array.Copy(app.destinations,destinations,5);
        var wayfinding=UnityEngine.Object.FindAnyObjectByType<MuseumWayfinding>();
        var landmarks=wayfinding.landmarks.Where(l=>l.kind!=MuseumWayfinding.Kind.Specimen).ToList();
        var ivory=AssetDatabase.LoadAssetAtPath<Material>("Assets/Museum/Materials/Porcelain.mat");
        var wood=AssetDatabase.LoadAssetAtPath<Material>("Assets/Museum/Materials/Walnut.mat");
        var paper=AssetDatabase.LoadAssetAtPath<Material>("Assets/Museum/Materials/Paper.mat");
        foreach(float z in new[]{1.9f,5.5f,8.5f,12.1f})Plinth(root.transform,new Vector3(3.25f,0,z),new Vector3(1.48f,1, z==1.9f?1.55f:1.15f),ivory,wood,paper);
        Plinth(root.transform,new Vector3(-2.1f,0,11.8f),new Vector3(1.5f,1,1.1f),ivory,wood,paper);
        Plinth(root.transform,new Vector3(-2.1f,0,9.5f),new Vector3(1.45f,1,1.1f),ivory,wood,paper);
        Plinth(root.transform,new Vector3(0,0,11.7f),new Vector3(1.65f,1,1.1f),ivory,wood,paper);
        Label(root.transform,"ゴキブリ目 / ゴキブリとシロアリ",new Vector3(0,1.12f,11.2f),new Vector2(1.4f,.085f));
        for(int i=0;i<entries.Length;i++)
        {
            Vector3 location;float size;
            if(i<3){location=new Vector3(3.25f,0,4+3*i);size=i==1?1f:.8f;}
            else if(i<=6){int j=i-3;location=new Vector3(3.25f+(j%2==0?-.36f:.36f),0,1.9f+(j/2==0?-.45f:.10f));size=.48f;}
            else if(i<=14){int group=(i-7)/4,j=(i-7)%4;location=new Vector3(3.25f+(j%2==0?-.36f:.36f),0,(group==0?5.5f:8.5f)+(j/2==0?-.28f:.28f));size=.48f;}
            else if(i<=16){location=new Vector3(3.25f+(i==15?-.36f:.36f),0,12.1f);size=.62f;}
            else if(i<=18){location=new Vector3(-2.1f+(i==17?-.37f:.37f),0,11.8f);size=.65f;}
            else if(i==19){location=new Vector3(-2.1f,0,9.5f);size=1.1f;}
            else if(i==20){location=new Vector3(3.25f,0,2.52f);size=.40f;}
            else {location=new Vector3(i==21?-.4f:.4f,0,11.7f);size=.65f;}
            var display=new GameObject("Collection "+(i+1).ToString("00")+" / "+entries[i].title);display.transform.SetParent(root.transform,false);
            var visual=(GameObject)PrefabUtility.InstantiatePrefab(entries[i].model);visual.transform.SetParent(display.transform,false);
            Bounds bounds=BoundsOf(visual);float scale=size/Mathf.Max(bounds.size.x,Mathf.Max(bounds.size.y,bounds.size.z));
            visual.transform.localScale*=scale;visual.transform.localPosition-=bounds.center*scale;
            bounds=BoundsOf(visual);display.transform.position=location+Vector3.up*(1.11f+bounds.size.y*.5f);
            // Imported mounts face +Z; the table labels sit on the -Z edge.
            if(i==17 || i==18)display.transform.rotation=Quaternion.Euler(0,180,0);
            var exhibit=display.AddComponent<MuseumExhibit>();exhibit.index=i;
            var collider=display.AddComponent<BoxCollider>();collider.size=new Vector3(Mathf.Max(.16f,bounds.size.x+.03f),Mathf.Max(.18f,bounds.size.y+.03f),Mathf.Max(.16f,bounds.size.z+.03f));
            var approach=i>=21?new Vector3(location.x,.06f,10.5f):i==17||i==18?new Vector3(-1.2f,.06f,10.5f):new Vector3(location.x>0?1.55f:-.55f,.06f,location.z);
            int destination=i<3?i:i+2;
            if(i>=3){var point=new GameObject("Destination: "+entries[i].title).transform;point.SetParent(root.transform,false);point.SetPositionAndRotation(approach,Quaternion.Euler(0,i>=21?0:location.x>0?90:-90,0));destinations[destination]=point;}
            var anchor=new GameObject("Collection approach "+(i+1)).transform;anchor.SetParent(root.transform,false);anchor.position=new Vector3(approach.x+(i<3?0:i%2==0?-.23f:.23f),.045f,approach.z);
            int displayGroup=i<3?100+i:i<=6||i==20?1:i<=10?2:i<=14?3:i<=16?4:i<=18?5:i==19?6:7;
            string title=entries[i].title.Replace("の仲間","").Replace("の体のつくり","").Replace("の拡大模型","").Replace("の剥製型模型","");
            landmarks.Add(new MuseumWayfinding.Landmark {anchor=anchor,target=exhibit,kind=MuseumWayfinding.Kind.Specimen,title=title,badgeHeight=1.65f,displayGroup=displayGroup});
            Label(root.transform,(i+1).ToString("00")+"  "+entries[i].title,new Vector3(location.x,1.115f,location.z-LabelOffset(i)),LabelArea(i));
        }
        FitLegacyPlinthLabels();
        Undo.RecordObject(app,"Expand collection destinations");app.collection=data;app.specimenModels=entries.Select(e=>e.model).ToArray();app.destinations=destinations;
        Undo.RecordObject(wayfinding,"Expand collection wayfinding");wayfinding.landmarks=landmarks.ToArray();
        EditorUtility.SetDirty(app);EditorUtility.SetDirty(wayfinding);AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        Debug.Log("Expanded collection ready: "+entries.Length+" observation models and "+destinations.Length+" destinations.");
    }

    static Bounds BoundsOf(GameObject o){var rs=o.GetComponentsInChildren<Renderer>();var b=rs[0].bounds;foreach(var r in rs)b.Encapsulate(r.bounds);return b;}
    static void Box(Transform parent,string name,Vector3 position,Vector3 size,Material material)
    {var o=GameObject.CreatePrimitive(PrimitiveType.Cube);o.name=name;o.transform.SetParent(parent,false);o.transform.localPosition=position;o.transform.localScale=size;o.GetComponent<Renderer>().sharedMaterial=material;}
    static void Plinth(Transform parent,Vector3 position,Vector3 size,Material ivory,Material wood,Material paper)
    {Box(parent,"Collection plinth",position+Vector3.up*.5f,size,ivory);Box(parent,"Collection tray",position+Vector3.up*1.035f,new Vector3(size.x,.07f,size.z),wood);Box(parent,"Collection lining",position+Vector3.up*1.078f,new Vector3(size.x-.10f,.025f,size.z-.10f),paper);}
    // Tabletop labels share a finite cell with a specimen. Measure the bundled
    // font instead of assuming that characterSize is the width of one glyph.
    static Vector2 LabelArea(int index) => new Vector2(index<3 || index==19 || index==20?1.05f:.60f,.075f);
    static float LabelOffset(int index) => index<3 || index==19?.46f:index>=21?.39f:index>=15 && index<=18?.41f:.24f;

    [MenuItem("Museum/Fit Display Labels")]
    public static void FitDisplayLabels()
    {
        if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Stop Play before fitting labels.");
        var scene=SceneManager.GetActiveScene();
        if(scene.path!=MuseumWebBuild.ScenePath)throw new InvalidOperationException("Open MuseumV1 first.");
        var root=GameObject.Find("Expanded collection displays");
        if(!root)throw new InvalidOperationException("The expanded collection is not present.");
        var exhibits=root.GetComponentsInChildren<MuseumExhibit>();
        foreach(var text in root.GetComponentsInChildren<TextMesh>())
        {
            bool numbered=text.text.Length>=4 && text.text.Substring(2,2)=="  " && int.TryParse(text.text.Substring(0,2),out _);
            int index=numbered?int.Parse(text.text.Substring(0,2))-1:-1;
            var area=numbered?LabelArea(index):new Vector2(1.4f,.085f);
            FitLabel(text,area);
            var exhibit=numbered?exhibits.FirstOrDefault(e=>e.index==index):null;
            if(exhibit)
            {
                Undo.RecordObject(text.transform,"Position display label");
                var position=text.transform.position;
                position.z=exhibit.transform.position.z-LabelOffset(index);
                text.transform.position=position;
            }
        }
        FitLegacyPlinthLabels();
        EditorSceneManager.MarkSceneDirty(scene);
        Debug.Log("Fitted 24 collection labels and 3 legacy plinth labels to their display areas.");
    }

    static void FitLegacyPlinthLabels()
    {
        foreach(var name in new[]{"Sign 01  BEETLE","Sign 02  BUTTERFLY","Sign 03  AMMONITE"})
        {
            var label=GameObject.Find(name)?.GetComponent<TextMesh>();
            if(label)FitLabel(label,new Vector2(1f,.14f));
        }
    }

    static void FitLabel(TextMesh text,Vector2 area)
    {
        Undo.RecordObject(text,"Fit display label");
        text.font.RequestCharactersInTexture(text.text,text.fontSize,text.fontStyle);
        var size=text.GetComponent<Renderer>().localBounds.size;
        var scale=text.transform.lossyScale;
        float width=size.x*Mathf.Abs(scale.x),height=size.y*Mathf.Abs(scale.y);
        if(width<=0 || height<=0)throw new InvalidOperationException("Cannot measure label: "+text.text);
        text.characterSize*=Mathf.Min(1f,area.x/width,area.y/height);
        EditorUtility.SetDirty(text);
    }

    static void Label(Transform parent,string value,Vector3 position,Vector2 area)
    {
        var o=new GameObject(value);o.transform.SetParent(parent,false);o.transform.position=position;o.transform.rotation=Quaternion.Euler(70,0,0);
        var t=o.AddComponent<TextMesh>();t.text=value;t.fontSize=64;t.characterSize=.026f;t.anchor=TextAnchor.MiddleCenter;t.color=new Color(.08f,.19f,.17f);
        t.font=Resources.Load<Font>("MuseumFonts/NotoSansJP-Regular");o.GetComponent<Renderer>().sharedMaterial=AssetDatabase.LoadAssetAtPath<Material>("Assets/Museum/Materials/World lettering.mat");
        FitLabel(t,area);
    }
    static void ImportMaterials(string path)
    {
        var importer=(ModelImporter)AssetImporter.GetAtPath(path);
        var sources=AssetDatabase.LoadAllAssetsAtPath(path).OfType<Material>()
            .Concat(importer.GetExternalObjectMap().Values.OfType<Material>()).Distinct().ToArray();
        foreach(var source in sources)
        {
            string safe=string.Concat(source.name.Select(c=>char.IsLetterOrDigit(c)||c=='_'||c=='-'?c:'_'));
            string materialPath=Materials+"/"+safe+".mat";
            var material=AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if(!material){material=new Material(source);material.shader=Shader.Find("Standard");AssetDatabase.CreateAsset(material,materialPath);}
            if(source.name.Contains("HabitatGlass"))material.color=new Color(.72f,.91f,.94f,.12f);
            if(source.name.Contains("PyriteBrass"))material.SetFloat("_Metallic",.86f);
            if(source.name.Contains("PyriteStriations"))material.SetFloat("_Metallic",.78f);
            if(source.name=="NaturalBeetle_Elytra")material.SetFloat("_Metallic",.45f);
            if(source.name=="StagBeetle_Elytra")material.SetFloat("_Metallic",.12f);
            if((source.name.StartsWith("NaturalBeetle_") || source.name.StartsWith("StagBeetle_")) && (source.name.EndsWith("Thorax") || source.name.EndsWith("Striae")))material.SetFloat("_Metallic",.3f);
            if(material.color.a<.99f)
            {
                material.SetFloat("_Mode",3);material.SetInt("_SrcBlend",(int)BlendMode.SrcAlpha);material.SetInt("_DstBlend",(int)BlendMode.OneMinusSrcAlpha);material.SetInt("_ZWrite",0);
                material.DisableKeyword("_ALPHATEST_ON");material.DisableKeyword("_ALPHAPREMULTIPLY_ON");material.EnableKeyword("_ALPHABLEND_ON");material.renderQueue=3000;
            }
            importer.AddRemap(new AssetImporter.SourceAssetIdentifier(source),material);EditorUtility.SetDirty(material);
        }
        importer.SaveAndReimport();
    }
}
