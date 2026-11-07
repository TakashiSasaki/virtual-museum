using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Object=UnityEngine.Object;

// The plan is editor-only JSON. No original meshes/textures are referenced by the player.
public static class MuseumRoomBuild
{
    const string Generated="Assets/Museum/GeneratedWeb/Room";
    const string PlanPath=Generated+"/plan.json";
    [Serializable] public sealed class Plan {public Group[] groups;public MaterialMap[] materials;}
    [Serializable] public sealed class Group
    {
        public string id,label,file;
        public long bytes;
        public string[] meshes=Array.Empty<string>(),textures=Array.Empty<string>();
    }
    [Serializable] public sealed class MaterialMap {public string source,clone;public Property[] properties;}
    [Serializable] public sealed class Property {public string name,texture;}
    static string Key(Object asset)
    {
        AssetDatabase.TryGetGUIDAndLocalFileIdentifier(asset,out string guid,out long id);
        return guid+"_"+id;
    }
    static Mesh MeshOf(Renderer r)
    {
        if(r is SkinnedMeshRenderer skin)return skin.sharedMesh;
        var filter=r.GetComponent<MeshFilter>();return filter?filter.sharedMesh:null;
    }
    static bool RoomModel(string path) => path.StartsWith("Assets/Museum/Models/") && path.EndsWith(".fbx") &&
        !path.Contains("/Collections/") && !Path.GetFileName(path).StartsWith("Dummy");
    static IEnumerable<Renderer> Renderers(Scene scene) => scene.GetRootGameObjects().SelectMany(r=>r.GetComponentsInChildren<Renderer>(true));
    static string Label(string model) => model switch
    {
        "Aimonite"=>"アイモナイト君", "Microscope"=>"顕微鏡", "SpecimenShelf"=>"標本棚", _=>"研究室の什器"
    };

    public static void Prepare(List<AssetBundleBuild> builds, MuseumCollection catalog)
    {
        Directory.CreateDirectory(Generated);AssetDatabase.Refresh();
        var scene=EditorSceneManager.OpenPreviewScene(MuseumWebBuild.ScenePath);
        try
        {
            var renderers=Renderers(scene).Where(r=>r.gameObject.activeInHierarchy).ToArray();
            var groups=new List<Group>();
            var meshes=renderers.Select(MeshOf).Where(m=>m && RoomModel(AssetDatabase.GetAssetPath(m))).Distinct();
            foreach(var model in meshes.GroupBy(AssetDatabase.GetAssetPath).OrderBy(g=>g.Key))
            {
                var name=Path.GetFileNameWithoutExtension(model.Key);
                var ordered=model.OrderBy(Key).ToArray();
                var group=new Group {id="room-"+name.ToLowerInvariant(),label=Label(name),meshes=ordered.Select(Key).ToArray()};
                var payload=ScriptableObject.CreateInstance<MuseumRoomPayload>();
                payload.meshes=ordered.Select(m=>Object.Instantiate(m)).ToArray();
                SavePayload(group,payload,builds);groups.Add(group);
            }
            var materials=renderers.SelectMany(r=>r.sharedMaterials).Concat(catalog.entries.SelectMany(e=>
                e.model.GetComponentsInChildren<Renderer>(true).SelectMany(r=>r.sharedMaterials))).Where(m=>m).Distinct().ToArray();
            var maps=new List<MaterialMap>();var textures=new Dictionary<string,Texture2D>();
            foreach(var material in materials)
            {
                var properties=new List<Property>();
                foreach(var property in material.GetTexturePropertyNames())
                {
                    var texture=material.GetTexture(property) as Texture2D;
                    string path=AssetDatabase.GetAssetPath(texture);
                    if(!texture || !path.StartsWith("Assets/Museum/Textures/") || path.Contains("Thumbnails"))continue;
                    textures[path]=texture;properties.Add(new Property {name=property,texture=path});
                }
                if(properties.Count==0)continue;
                string clonePath=Generated+"/Material-"+Key(material)+".mat";
                var clone=new Material(material){name=material.name+" (streamed surface)"};
                foreach(var property in properties)clone.SetTexture(property.name,null);
                var existing=AssetDatabase.LoadAssetAtPath<Material>(clonePath);
                if(existing){EditorUtility.CopySerialized(clone,existing);EditorUtility.SetDirty(existing);Object.DestroyImmediate(clone);}
                else AssetDatabase.CreateAsset(clone,clonePath);
                maps.Add(new MaterialMap {source=Key(material),clone=clonePath,properties=properties.ToArray()});
            }
            // Small independent texture groups, no duplicate images across bundles.
            foreach(var family in textures.OrderBy(p=>p.Key).GroupBy(p=>Path.GetFileNameWithoutExtension(p.Key).Split('_')[0].ToLowerInvariant()))
            {
                var group=new Group{id="room-surface-"+family.Key,label="室内の質感",textures=family.Select(p=>p.Key).ToArray()};
                var payload=ScriptableObject.CreateInstance<MuseumRoomPayload>();payload.textures=family.Select(p=>p.Value).ToArray();
                SavePayload(group,payload,builds);groups.Add(group);
            }
            var plan=new Plan {groups=groups.ToArray(),materials=maps.ToArray()};
            File.WriteAllText(PlanPath,JsonUtility.ToJson(plan,true));
            // Preview prefabs can also share room materials. Keep their texture references out of startup data.
            var replacements=maps.ToDictionary(m=>m.source,m=>AssetDatabase.LoadAssetAtPath<Material>(m.clone));
            foreach(var entry in catalog.entries)
            {
                string path=AssetDatabase.GetAssetPath(entry.model);
                var prefab=PrefabUtility.LoadPrefabContents(path);
                try {ReplaceMaterials(prefab.GetComponentsInChildren<Renderer>(true),replacements);PrefabUtility.SaveAsPrefabAsset(prefab,path);}
                finally {PrefabUtility.UnloadPrefabContents(prefab);}
            }
            AssetDatabase.SaveAssets();
        }
        finally {EditorSceneManager.ClosePreviewScene(scene);}
    }

    static void SavePayload(Group group,MuseumRoomPayload payload,List<AssetBundleBuild> builds)
    {
        string path=Generated+"/"+group.id+".asset";
        // Generated payloads are never referenced by the authoring scene.
        if(File.Exists(path))AssetDatabase.DeleteAsset(path);
        AssetDatabase.CreateAsset(payload,path);
        for(int i=0;i<payload.meshes.Length;i++)
        {payload.meshes[i].name="Mesh "+i;AssetDatabase.AddObjectToAsset(payload.meshes[i],payload);}
        EditorUtility.SetDirty(payload);
        builds.Add(new AssetBundleBuild{assetBundleName=group.id,assetNames=new[]{path},addressableNames=new[]{"payload"}});
    }

    public static void Finish(AssetBundleManifest manifest,string cache)
    {
        var plan=ReadPlan();
        foreach(var group in plan.groups)
        {group.file=group.id+"-"+manifest.GetAssetBundleHash(group.id)+".bundle";group.bytes=new FileInfo(Path.Combine(cache,group.id)).Length;}
        File.WriteAllText(PlanPath,JsonUtility.ToJson(plan,true));
    }
    static Plan ReadPlan()
    {
        if(!File.Exists(PlanPath))throw new BuildFailedException("Prepare progressive room content before building.");
        return JsonUtility.FromJson<Plan>(File.ReadAllText(PlanPath));
    }
    static void ReplaceMaterials(IEnumerable<Renderer> renderers,Dictionary<string,Material> replacements)
    {
        foreach(var renderer in renderers)renderer.sharedMaterials=renderer.sharedMaterials.Select(m=>
            m && replacements.TryGetValue(Key(m),out var replacement)?replacement:m).ToArray();
    }

    public static void ProcessScene(Scene scene)
    {
        var plan=ReadPlan();var renderers=Renderers(scene).ToArray();
        var app=scene.GetRootGameObjects().SelectMany(r=>r.GetComponentsInChildren<MuseumExperience>(true)).Single();
        var streaming=app.gameObject.AddComponent<MuseumRoomStreaming>();streaming.experience=app;
        var replacements=plan.materials.ToDictionary(m=>m.source,m=>AssetDatabase.LoadAssetAtPath<Material>(m.clone));
        ReplaceMaterials(renderers,replacements);
        var chunks=new List<MuseumRoomStreaming.Chunk>();
        Material placeholderMaterial=null;
        foreach(var group in plan.groups)
        {
            if(string.IsNullOrEmpty(group.file))throw new BuildFailedException("Room bundles not finalized.");
            var chunk=new MuseumRoomStreaming.Chunk {file=group.file,label=group.label,bytes=group.bytes};
            var meshTargets=new List<MuseumRoomStreaming.MeshTarget>();
            var placeholders=new List<GameObject>();
            var roots=new Dictionary<Transform,List<Renderer>>();
            foreach(var renderer in renderers)
            {
                var mesh=MeshOf(renderer);if(!mesh)continue;
                int index=Array.IndexOf(group.meshes,Key(mesh));if(index<0)continue;
                var root=renderer.transform;
                while(root.parent && root.parent!=app.transform)
                {
                    var instanceRoot=PrefabUtility.GetNearestPrefabInstanceRoot(root.gameObject);
                    if(instanceRoot && instanceRoot.transform==root)break;
                    root=root.parent;
                }
                if(!roots.ContainsKey(root))roots[root]=new List<Renderer>();roots[root].Add(renderer);
                meshTargets.Add(new MuseumRoomStreaming.MeshTarget {filter=renderer.GetComponent<MeshFilter>(),skin=renderer as SkinnedMeshRenderer,index=index});
            }
            foreach(var root in roots)
            {
                if(root.Key.GetComponentInParent<GuideMarker>())continue;
                var bounds=new Bounds(root.Value[0].bounds.center,Vector3.zero);
                foreach(var r in root.Value)bounds.Encapsulate(r.bounds);
                if(!placeholderMaterial)placeholderMaterial=new Material(Shader.Find("Standard")){name="Loading furniture",color=new Color(.47f,.56f,.54f)};
                var placeholder=GameObject.CreatePrimitive(PrimitiveType.Cube);placeholder.name="Furniture loading preview";
                Object.DestroyImmediate(placeholder.GetComponent<Collider>());
                SceneManager.MoveGameObjectToScene(placeholder,scene);
                placeholder.transform.position=bounds.center;placeholder.transform.localScale=bounds.size;
                placeholder.transform.SetParent(root.Key,true);
                placeholder.GetComponent<Renderer>().sharedMaterial=placeholderMaterial;placeholders.Add(placeholder);
            }
            foreach(var target in meshTargets)
            {if(target.filter)target.filter.sharedMesh=null;if(target.skin)target.skin.sharedMesh=null;}
            chunk.meshes=meshTargets.ToArray();chunk.placeholders=placeholders.ToArray();
            var textureTargets=new List<MuseumRoomStreaming.TextureTarget>();
            foreach(var material in plan.materials)foreach(var property in material.properties)
            {
                int index=Array.IndexOf(group.textures,property.texture);if(index<0)continue;
                textureTargets.Add(new MuseumRoomStreaming.TextureTarget{material=AssetDatabase.LoadAssetAtPath<Material>(material.clone),property=property.name,index=index});
            }
            chunk.textures=textureTargets.ToArray();chunks.Add(chunk);
        }
        streaming.chunks=chunks.ToArray();
    }

    public static void CopyContent(string content,string cache)
    {
        var plan=ReadPlan();foreach(var old in Directory.GetFiles(content,"room-*.bundle"))File.Delete(old);
        foreach(var group in plan.groups)File.Copy(Path.Combine(cache,group.id),Path.Combine(content,group.file),true);
        File.WriteAllText(Path.Combine(content,"room.json"),JsonUtility.ToJson(new RoomIndex {entries=plan.groups.Select(g=>new RoomFile{file=g.file,bytes=g.bytes}).ToArray()},true));
    }
    [Serializable] sealed class RoomIndex {public int version=1;public RoomFile[] entries;}
    [Serializable] sealed class RoomFile {public string file;public long bytes;}
}
