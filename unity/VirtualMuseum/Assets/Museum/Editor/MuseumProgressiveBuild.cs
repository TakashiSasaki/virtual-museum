using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

// Generated assets are disposable. Authoring FBXs, catalog and saved scene remain intact.
public sealed class MuseumProgressiveBuild : IPreprocessBuildWithReport, IProcessSceneWithReport, IPostprocessBuildWithReport
{
    const string Generated = "Assets/Museum/GeneratedWeb";
    const string Catalog = Generated + "/Collection.asset";
    const string BundleCache = "Library/MuseumWebBundles";
    [Serializable] sealed class BundleIndex {public int version=1;public int exhibitionCount;public BundleFile[] entries;}
    [Serializable] sealed class BundleFile {public string file;public long bytes;}
    public int callbackOrder => 100;

    [MenuItem("Museum/Web/Prepare Progressive Content")]
    public static void Prepare()
    {
        if(EditorApplication.isPlayingOrWillChangePlaymode)
            throw new InvalidOperationException("Stop Play before preparing web content.");
        Directory.CreateDirectory(Generated);
        AssetDatabase.Refresh();
        var source = AssetDatabase.LoadAssetAtPath<MuseumCollection>("Assets/Museum/ExpandedCollection.asset");
        var reserve = AssetDatabase.LoadAssetAtPath<MuseumCollection>("Assets/Museum/ReserveCollection.asset");
        var entries=source.entries.Concat(reserve.entries).ToArray();
        var catalog = AssetDatabase.LoadAssetAtPath<MuseumCollection>(Catalog);
        if(!catalog) {catalog=ScriptableObject.CreateInstance<MuseumCollection>();AssetDatabase.CreateAsset(catalog,Catalog);}
        catalog.entries = new MuseumCollection.Entry[entries.Length];
        catalog.exhibitionCount=source.entries.Length;
        catalog.reserveThumbnails=MuseumBackyardPreview.Generate(reserve.entries,"Assets/Museum/Textures/ReserveThumbnails.png");
        reserve.reserveThumbnails=catalog.reserveThumbnails;EditorUtility.SetDirty(reserve);
        var builds = new List<AssetBundleBuild>();
        long fullVertices=0, liteVertices=0;
        for(int i=0;i<entries.Length;i++)
        {
            var entry=entries[i];
            var instance=Object.Instantiate(entry.model);
            try
            {
                var filters=instance.GetComponentsInChildren<MeshFilter>();
                var materials=new List<Material>();
                var groups=new List<List<CombineInstance>>();
                foreach(var filter in filters)
                {
                    var renderer=filter.GetComponent<MeshRenderer>();
                    if(!renderer || !filter.sharedMesh)continue;
                    for(int sub=0;sub<filter.sharedMesh.subMeshCount;sub++)
                    {
                        var mat=renderer.sharedMaterials[Mathf.Min(sub,renderer.sharedMaterials.Length-1)];
                        int index=materials.IndexOf(mat);
                        if(index<0){index=materials.Count;materials.Add(mat);groups.Add(new List<CombineInstance>());}
                        groups[index].Add(new CombineInstance {mesh=filter.sharedMesh,subMeshIndex=sub,
                            transform=instance.transform.worldToLocalMatrix*filter.transform.localToWorldMatrix});
                    }
                }
                var full=Combine(groups,false);var lite=Combine(groups,true);
                fullVertices+=full.vertexCount;liteVertices+=lite.vertexCount;
                SaveMesh(full,$"{Generated}/Detail{i:00}.asset");
                SaveMesh(lite,$"{Generated}/Preview{i:00}.asset");
                var proxy=new GameObject(entry.model.name+" preview");
                proxy.transform.localRotation=entry.model.transform.localRotation;
                proxy.transform.localScale=entry.model.transform.localScale;
                proxy.AddComponent<MeshFilter>().sharedMesh=AssetDatabase.LoadAssetAtPath<Mesh>($"{Generated}/Preview{i:00}.asset");
                proxy.AddComponent<MeshRenderer>().sharedMaterials=materials.ToArray();
                var prefab=PrefabUtility.SaveAsPrefabAsset(proxy,$"{Generated}/Preview{i:00}.prefab");
                Object.DestroyImmediate(proxy);
                catalog.entries[i]=new MuseumCollection.Entry {title=entry.title,english=entry.english,category=entry.category,description=entry.description,
                    model=prefab,microscopePattern=entry.microscopePattern,microscopeCaption=entry.microscopeCaption};
                builds.Add(new AssetBundleBuild {assetBundleName=$"specimen-{i:00}",assetNames=new[]{$"{Generated}/Detail{i:00}.asset"},addressableNames=new[]{"mesh"}});
            }
            finally {Object.DestroyImmediate(instance);}
        }
        MuseumRoomBuild.Prepare(builds,catalog);
        Directory.CreateDirectory(BundleCache);
        EditorUtility.SetDirty(catalog);AssetDatabase.SaveAssets();
        var manifest=BuildPipeline.BuildAssetBundles(BundleCache,builds.ToArray(),
            BuildAssetBundleOptions.ChunkBasedCompression|BuildAssetBundleOptions.StrictMode,BuildTarget.WebGL);
        if(!manifest)throw new BuildFailedException("Could not build specimen bundles.");
        MuseumRoomBuild.Finish(manifest,BundleCache);
        // Bundle builds can reload imported assets and invalidate editor handles.
        catalog=AssetDatabase.LoadAssetAtPath<MuseumCollection>(Catalog);
        for(int i=0;i<catalog.entries.Length;i++)
        {
            string name=$"specimen-{i:00}";
            catalog.entries[i].detailBundle=name+"-"+manifest.GetAssetBundleHash(name)+".bundle";
            catalog.entries[i].detailBytes=new FileInfo(Path.Combine(BundleCache,name)).Length;
        }
        EditorUtility.SetDirty(catalog);AssetDatabase.SaveAssets();
        File.WriteAllText(Generated+"/source-hash.txt",SourceHash());
        Debug.Log($"Progressive content ready: {catalog.entries.Length} bundles; vertices {fullVertices:N0} -> {liteVertices:N0} in room previews.");
    }

    static string SourceHash() => AssetDatabase.GetAssetDependencyHash("Assets/Museum/ExpandedCollection.asset")+"/"+
        AssetDatabase.GetAssetDependencyHash("Assets/Museum/ReserveCollection.asset")+"/"+
        AssetDatabase.GetAssetDependencyHash("Assets/Museum/Editor/MuseumBackyardPreview.cs")+"/"+
        AssetDatabase.GetAssetDependencyHash("Assets/Museum/Editor/MuseumProgressiveBuild.cs")+"/"+
        AssetDatabase.GetAssetDependencyHash(MuseumWebBuild.ScenePath)+"/"+
        AssetDatabase.GetAssetDependencyHash("Assets/Museum/Editor/MuseumRoomBuild.cs");

    public void OnPreprocessBuild(BuildReport report)
    {
        if(report.summary.platform!=BuildTarget.WebGL)return;
        if(!File.Exists(Generated+"/source-hash.txt") || File.ReadAllText(Generated+"/source-hash.txt")!=SourceHash())
            throw new BuildFailedException("Progressive content is missing or stale. Run Museum/Web/Prepare Progressive Content first.");
    }

    static void SaveMesh(Mesh mesh,string path)
    {
        mesh.name=Path.GetFileNameWithoutExtension(path);
        var previous=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(previous){EditorUtility.CopySerialized(mesh,previous);EditorUtility.SetDirty(previous);Object.DestroyImmediate(mesh);}
        else AssetDatabase.CreateAsset(mesh,path);
    }

    static Mesh Combine(List<List<CombineInstance>> groups,bool simplified)
    {
        var temporary=new List<Mesh>();var combined=new List<CombineInstance>();
        try
        {
            foreach(var group in groups)
            {
                var input=group.ToArray();
                if(simplified)for(int i=0;i<input.Length;i++)
                {
                    var copy=input[i];var mesh=Simplify(copy.mesh,copy.subMeshIndex);
                    temporary.Add(mesh);copy.mesh=mesh;copy.subMeshIndex=0;input[i]=copy;
                }
                var part=new Mesh {indexFormat=IndexFormat.UInt32};
                part.CombineMeshes(input,true,true);temporary.Add(part);
                combined.Add(new CombineInstance {mesh=part,transform=Matrix4x4.identity});
            }
            var result=new Mesh {name=simplified?"Room preview":"Detailed specimen",indexFormat=IndexFormat.UInt32};
            result.CombineMeshes(combined.ToArray(),false,false);
            result.RecalculateBounds();return result;
        }
        finally {foreach(var mesh in temporary)Object.DestroyImmediate(mesh);}
    }

    // Vertex clustering retains each original part and material. It never drops
    // arbitrary triangles (which would make holes in wings or thin appendages).
    static Mesh Simplify(Mesh source,int submesh)
    {
        var vertices=source.vertices;var normals=source.normals;var uv=source.uv;
        float cell=Mathf.Max(source.bounds.size.x,Mathf.Max(source.bounds.size.y,source.bounds.size.z))/14f;
        cell=Mathf.Max(cell,.000001f);
        var buckets=new Dictionary<Vector3Int,int>();var positions=new List<Vector3>();
        var ns=new List<Vector3>();var uvs=new List<Vector2>();var counts=new List<int>();
        var map=new int[vertices.Length];
        for(int i=0;i<vertices.Length;i++)
        {
            var p=vertices[i]/cell;var key=new Vector3Int(Mathf.RoundToInt(p.x),Mathf.RoundToInt(p.y),Mathf.RoundToInt(p.z));
            if(!buckets.TryGetValue(key,out int index))
            {index=positions.Count;buckets[key]=index;positions.Add(Vector3.zero);ns.Add(Vector3.zero);uvs.Add(Vector2.zero);counts.Add(0);}
            map[i]=index;positions[index]+=vertices[i];ns[index]+=normals.Length>i?normals[i]:Vector3.up;
            uvs[index]+=uv.Length>i?uv[i]:Vector2.zero;counts[index]++;
        }
        for(int i=0;i<positions.Count;i++){positions[i]/=counts[i];ns[i]=ns[i].normalized;uvs[i]/=counts[i];}
        var triangles=new List<int>();var original=source.GetTriangles(submesh);
        for(int i=0;i<original.Length;i+=3)
        {int a=map[original[i]],b=map[original[i+1]],c=map[original[i+2]];if(a==b||b==c||a==c)continue;triangles.Add(a);triangles.Add(b);triangles.Add(c);}
        var mesh=new Mesh {indexFormat=IndexFormat.UInt32};mesh.SetVertices(positions);mesh.SetNormals(ns);mesh.SetUVs(0,uvs);mesh.SetTriangles(triangles,0);mesh.RecalculateBounds();return mesh;
    }

    public void OnProcessScene(Scene scene,BuildReport report)
    {
        if(report==null || report.summary.platform!=BuildTarget.WebGL || scene.path!=MuseumWebBuild.ScenePath)return;
        var catalog=AssetDatabase.LoadAssetAtPath<MuseumCollection>(Catalog);
        if(!catalog || catalog.entries.Any(e=>string.IsNullOrEmpty(e.detailBundle)))
            throw new BuildFailedException("Run Museum/Web/Prepare Progressive Content before building Web.");
        foreach(var root in scene.GetRootGameObjects())
        {
            foreach(var app in root.GetComponentsInChildren<MuseumExperience>(true))
            {app.collection=catalog;app.reserveCollection=null;app.specimenModels=catalog.entries.Select(e=>e.model).ToArray();}
            foreach(var exhibit in root.GetComponentsInChildren<MuseumExhibit>(true))
            {
                if(!exhibit.gameObject.activeInHierarchy){Object.DestroyImmediate(exhibit.gameObject);continue;}
                var visual=exhibit.transform.childCount>0?exhibit.transform.GetChild(0):null;
                if(!visual)throw new BuildFailedException("Missing specimen visual: "+exhibit.name);
                var proxy=Object.Instantiate(catalog.entries[exhibit.index].model,exhibit.transform);
                proxy.transform.localPosition=visual.localPosition;proxy.transform.localRotation=visual.localRotation;proxy.transform.localScale=visual.localScale;
                Object.DestroyImmediate(visual.gameObject);
            }
        }
        MuseumRoomBuild.ProcessScene(scene);
    }

    public void OnPostprocessBuild(BuildReport report)
    {
        if(report.summary.platform!=BuildTarget.WebGL)return;
        CopyContent(report.summary.outputPath);
    }

    public static void CopyContent(string output)
    {
        var catalog=AssetDatabase.LoadAssetAtPath<MuseumCollection>(Catalog);
        string content=Path.Combine(output,"Content");Directory.CreateDirectory(content);
        MuseumRoomBuild.CopyContent(content,BundleCache);
        // This owned output directory contains only hashed generated bundles.
        foreach(var old in Directory.GetFiles(content,"specimen-*.bundle"))File.Delete(old);
        for(int i=0;i<catalog.entries.Length;i++)File.Copy(Path.Combine(BundleCache,$"specimen-{i:00}"),Path.Combine(content,catalog.entries[i].detailBundle),true);
        File.WriteAllText(Path.Combine(content,"catalog.json"),JsonUtility.ToJson(new BundleIndex {exhibitionCount=catalog.exhibitionCount,
            entries=catalog.entries.Select(e=>new BundleFile {file=e.detailBundle,bytes=e.detailBytes}).ToArray()},true));
    }

    [MenuItem("Museum/Web/Optimize Surface Textures")]
    public static void OptimizeTextures()
    {
        foreach(var guid in AssetDatabase.FindAssets("t:Texture2D",new[]{"Assets/Museum/Textures"}))
        {
            var path=AssetDatabase.GUIDToAssetPath(guid);var importer=AssetImporter.GetAtPath(path) as TextureImporter;
            if(!importer)continue;
            var settings=importer.GetPlatformTextureSettings("WebGL");
            settings.overridden=true;settings.maxTextureSize=path.Contains("Thumbnails")?1024:512;
            // Portable WebGL2 formats; surface scalar maps use only their red
            // channel, color photos have no alpha, normal maps retain RGBA.
            settings.format=path.Contains("Roughness") || path.Contains("Height")?TextureImporterFormat.R8:
                importer.textureType==TextureImporterType.NormalMap?TextureImporterFormat.RGBA32:TextureImporterFormat.RGB24;
            importer.SetPlatformTextureSettings(settings);importer.SaveAndReimport();
        }
    }
}
