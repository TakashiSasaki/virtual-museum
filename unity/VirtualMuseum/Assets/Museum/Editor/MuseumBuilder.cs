using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;

public static class MuseumBuilder
{
    const string Root="Assets/Museum/";
    static Material ivory, dark, green, wood, floor, brass;

    [MenuItem("Museum/Build Version 1 Scene")]
    public static void Build()
    {
        if(EditorApplication.isPlaying) throw new System.InvalidOperationException("Stop Play mode before rebuilding.");
        var active=SceneManager.GetActiveScene();
        if(active.isDirty) throw new System.InvalidOperationException("Save current scene before rebuilding.");
        string scenePath=Root+"Scenes/MuseumV1.unity";
        if(File.Exists(scenePath)) throw new System.InvalidOperationException("Scene already exists; use the saved scene. Rebuild only into a new path.");
        Directory.CreateDirectory(Root+"Scenes");Directory.CreateDirectory(Root+"Materials");
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        ivory=Mat("Porcelain",new Color(.84f,.86f,.81f));dark=Mat("Ink",new Color(.045f,.10f,.11f));
        green=Mat("Museum green",new Color(.06f,.27f,.22f));wood=Mat("Walnut",new Color(.22f,.13f,.075f));
        floor=Mat("Carpet",new Color(.42f,.41f,.35f));brass=Mat("Brass",new Color(.75f,.55f,.25f));
        RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight=new Color(.68f,.71f,.72f);RenderSettings.skybox=null;
        RenderSettings.fog=false;
        var app=new GameObject("Museum experience").AddComponent<MuseumExperience>();
        // One 12 x 14 m room; no partitions or hidden rooms.
        Box("Walkable floor",new Vector3(0,-.12f,7),new Vector3(12,.24f,14),floor);
        Box("Back wall",new Vector3(0,1.8f,14),new Vector3(12.2f,3.6f,.2f),ivory);
        Box("Left wall",new Vector3(-6,1.8f,7),new Vector3(.2f,3.6f,14),ivory);
        Box("Right wall",new Vector3(6,1.8f,7),new Vector3(.2f,3.6f,14),ivory);
        Box("Entrance wall left",new Vector3(-3.7f,1.8f,0),new Vector3(4.6f,3.6f,.2f),ivory);
        Box("Entrance wall right",new Vector3(3.7f,1.8f,0),new Vector3(4.6f,3.6f,.2f),ivory);
        Box("Entrance glazing",new Vector3(0,1.3f,0),new Vector3(2.8f,2.6f,.08f),dark);
        for(int s=-1;s<=1;s+=2) Box("Door frame",new Vector3(s*1.4f,1.35f,.08f),new Vector3(.07f,2.7f,.12f),brass);
        Box("Door lintel",new Vector3(0,2.7f,.08f),new Vector3(2.9f,.07f,.12f),brass);
        Box("Ceiling",new Vector3(0,3.65f,7),new Vector3(12,.1f,14),ivory);
        for(int z=2;z<14;z+=3) {
            for(int x=-3;x<=3;x+=6) {
                Box("Linear light",new Vector3(x,3.54f,z),new Vector3(.14f,.06f,1.5f),Mat("Light ivory",Color.white));
                var l=new GameObject("Ceiling illumination").AddComponent<Light>();l.type=LightType.Point;l.range=7;l.intensity=1.3f;l.color=new Color(1,.95f,.85f);l.transform.position=new Vector3(x,3.1f,z);
            }
        }
        var sun=new GameObject("Soft fill").AddComponent<Light>();sun.type=LightType.Directional;sun.intensity=.65f;sun.transform.rotation=Quaternion.Euler(60,-25,0);sun.shadows=LightShadows.Soft;
        for(int z=4;z<=10;z+=3) {
            var shelf=Model("SpecimenShelf",new Vector3(5.35f,0,z),Quaternion.Euler(0,-90,0));
            Obstacle(shelf,new Vector3(0,1.4f,0),new Vector3(1.9f,2.8f,.85f));
            var bench=Model("ObservationBench",new Vector3(-5.35f,0,z),Quaternion.Euler(0,90,0));
            Obstacle(bench,new Vector3(0,.42f,0),new Vector3(3,.84f,.9f));
            var scope=Model("Microscope",new Vector3(-5.18f,.9f,z),Quaternion.Euler(0,90,0));
            scope.AddComponent<MicroscopeStation>();Obstacle(scope,new Vector3(0,.3f,0),new Vector3(.42f,.65f,.5f));
        }
        Box("Work area floor",new Vector3(-4.7f,.012f,7),new Vector3(2.4f,.02f,11.5f),Mat("Work floor",new Color(.76f,.76f,.69f)));
        Box("Metal floor strip",new Vector3(-3.45f,.025f,7),new Vector3(.14f,.025f,11.5f),brass);
        for(int z=2;z<13;z+=2) Box("Aisle marker",new Vector3(0,.012f,z),new Vector3(.045f,.015f,.65f),Mat("Wayfinding",new Color(.64f,.66f,.57f)));
        app.specimenModels=new GameObject[3];app.destinations=new Transform[5];
        string[] models={"DummyBeetle","DummyButterfly","DummyAmmonite"};
        string[] labels={"01  BEETLE","02  BUTTERFLY","03  AMMONITE"};
        for(int i=0;i<3;i++) {
            float z=4+i*3;
            Box("Exhibit plinth "+i,new Vector3(3.25f,.5f,z),new Vector3(1.45f,1,1.15f),ivory);
            Box("Walnut tray "+i,new Vector3(3.25f,1.03f,z),new Vector3(1.32f,.07f,1.02f),wood);
            Box("Specimen lining "+i,new Vector3(3.25f,1.075f,z),new Vector3(1.2f,.025f,.90f),Mat("Paper",new Color(.92f,.9f,.8f)));
            app.specimenModels[i]=AssetDatabase.LoadAssetAtPath<GameObject>(Root+"Models/"+models[i]+".fbx");
            var display=Model(models[i],new Vector3(3.25f,1.12f,z),Quaternion.identity);display.transform.localScale=Vector3.one*1.5f;
            var ex=display.AddComponent<MuseumExhibit>();ex.index=i;Obstacle(display,new Vector3(0,.04f,0),new Vector3(.64f,.20f,.65f));
            Sign(labels[i],new Vector3(2.51f,.80f,z),Quaternion.Euler(0,90,0),.11f,dark.color);
            app.destinations[i]=Destination("Exhibit "+i,new Vector3(1.65f,.06f,z),90);
        }
        app.destinations[3]=Destination("Microscope",new Vector3(-3.1f,.06f,7),-90);
        app.destinations[4]=Destination("Entrance",new Vector3(0,.06f,1.8f),0);
        Sign("COLLECTION OF INSECTS",new Vector3(0,2.7f,13.83f),Quaternion.identity,.18f,green.color);
        Sign("EHIME UNIVERSITY MUSEUM",new Vector3(0,2.28f,13.82f),Quaternion.identity,.09f,dark.color);
        Sign("01  /  EXPLORE THE COLLECTION",new Vector3(0,1.9f,13.82f),Quaternion.identity,.065f,dark.color);
        Box("Back information panel",new Vector3(0,1.2f,13.83f),new Vector3(3,.75f,.06f),green);
        Sign("LOOK  /  ROTATE  /  DISCOVER",new Vector3(0,1.25f,13.77f),Quaternion.identity,.09f,Color.white);
        var npc=Model("Aimonite",new Vector3(.8f,0,6),Quaternion.identity);app.guide=npc.transform;
        npc.AddComponent<GuideMarker>();Obstacle(npc,new Vector3(0,1,0),new Vector3(1.3f,2,.55f),true);

        var player=new GameObject("Visitor");player.transform.position=app.destinations[4].position;
        var cc=player.AddComponent<CharacterController>();cc.height=1.7f;cc.center=new Vector3(0,.85f,0);cc.radius=.25f;cc.stepOffset=.15f;app.visitor=cc;
        var cam=new GameObject("Visitor camera").AddComponent<Camera>();cam.tag="MainCamera";cam.transform.SetParent(player.transform);cam.transform.localPosition=new Vector3(0,1.6f,0);cam.fieldOfView=65;cam.farClipPlane=60;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.09f,.14f,.14f);cam.gameObject.AddComponent<AudioListener>();app.visitorCamera=cam;
        app.specimenStage=new GameObject("Inspection model anchor").transform;app.specimenStage.position=new Vector3(100,0,0);
        var inspect=new GameObject("Inspection camera").AddComponent<Camera>();inspect.transform.position=new Vector3(100,.55f,-.85f);inspect.transform.LookAt(app.specimenStage);inspect.clearFlags=CameraClearFlags.SolidColor;inspect.backgroundColor=new Color(.035f,.12f,.13f);inspect.nearClipPlane=.01f;inspect.farClipPlane=4;inspect.orthographic=true;inspect.orthographicSize=.42f;
        app.specimenCamera=inspect;var rt=new RenderTexture(1024,1024,24);rt.name="Specimen view";AssetDatabase.CreateAsset(rt,Root+"SpecimenView.renderTexture");app.specimenView=rt;inspect.targetTexture=rt;inspect.gameObject.SetActive(false);
        var il=new GameObject("Inspection softbox").AddComponent<Light>();il.transform.position=new Vector3(99.6f,1,-.4f);il.type=LightType.Point;il.intensity=2;il.range=3;
        PlayerSettings.productName="Virtual Museum — Prototype 01";PlayerSettings.companyName="Virtual Museum";PlayerSettings.runInBackground=true;PlayerSettings.defaultScreenWidth=1440;PlayerSettings.defaultScreenHeight=900;PlayerSettings.fullScreenMode=FullScreenMode.Windowed;
        EditorSceneManager.SaveScene(SceneManager.GetActiveScene(),scenePath);
        EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene(scenePath,true)};
        AssetDatabase.SaveAssets();Selection.activeGameObject=app.gameObject;
        SceneView.lastActiveSceneView?.LookAt(new Vector3(0,1.3f,7),Quaternion.Euler(20,0,0),10);
        Debug.Log("Museum V1 scene built with 3 exhibits and 5 destinations.");
    }
    static Material Mat(string name,Color c)
    {
        string p=Root+"Materials/"+name+".mat";var m=AssetDatabase.LoadAssetAtPath<Material>(p);
        if(m)return m;m=new Material(Shader.Find("Standard")){name=name,color=c};m.SetFloat("_Glossiness",.22f);AssetDatabase.CreateAsset(m,p);return m;
    }
    static GameObject Box(string name,Vector3 pos,Vector3 scale,Material m)
    {var o=GameObject.CreatePrimitive(PrimitiveType.Cube);o.name=name;o.transform.position=pos;o.transform.localScale=scale;o.GetComponent<Renderer>().sharedMaterial=m;return o;}
    static GameObject Model(string name,Vector3 pos,Quaternion rotation)
    {
        var asset=AssetDatabase.LoadAssetAtPath<GameObject>(Root+"Models/"+name+".fbx");
        if(!asset)throw new System.IO.FileNotFoundException("Missing Blender FBX: "+name);
        var o=(GameObject)PrefabUtility.InstantiatePrefab(asset);o.name=name;o.transform.SetPositionAndRotation(pos,rotation);return o;
    }
    static void Obstacle(GameObject o,Vector3 center,Vector3 size,bool trigger=false) {var c=o.AddComponent<BoxCollider>();c.center=center;c.size=size;c.isTrigger=trigger;}
    static Transform Destination(string name,Vector3 p,float yaw) {var o=new GameObject("Destination: "+name);o.transform.SetPositionAndRotation(p,Quaternion.Euler(0,yaw,0));return o.transform;}
    static void Sign(string text,Vector3 pos,Quaternion rot,float size,Color color)
    {
        var o=new GameObject("Sign "+text);o.transform.SetPositionAndRotation(pos,rot);var t=o.AddComponent<TextMesh>();
        t.text=text;t.fontSize=80;t.characterSize=size*.2f;t.anchor=TextAnchor.MiddleCenter;t.alignment=TextAlignment.Center;t.color=color;
        var material=AssetDatabase.LoadAssetAtPath<Material>(Root+"Materials/World lettering.mat");
        if(!material) { material=new Material(t.GetComponent<Renderer>().sharedMaterial);material.shader=Shader.Find("Museum/WorldText");AssetDatabase.CreateAsset(material,Root+"Materials/World lettering.mat"); }
        t.GetComponent<Renderer>().sharedMaterial=material;
    }

}
