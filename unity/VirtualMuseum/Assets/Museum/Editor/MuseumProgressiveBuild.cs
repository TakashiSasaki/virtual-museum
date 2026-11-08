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
    // Main-room entries predate the category field used by the reserve catalog.
    static readonly HashSet<string> InsectDisplays = new()
    {
        "NaturalBeetle", "SwallowtailButterfly", "StagBeetle", "Dragonfly", "Honeybee", "Mantis",
        "DivingBeetle", "WaterScorpion", "DragonflyNymph", "Caterpillar", "CaddisflyLarva",
        "Cockroach", "Termite", "RearingTerrarium"
    };
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
                bool preserveAnatomy = InsectDisplays.Contains(entry.model.name) ||
                    (entry.category?.StartsWith("昆虫", StringComparison.Ordinal) ?? false);
                var full=Combine(groups,false);
                var lite=Combine(groups,true,preserveAnatomy ? materials : null);
                // Keep small joints in the mesh while reducing the serialized Web preview.
                if(preserveAnatomy)MeshUtility.SetMeshCompression(lite,ModelImporterMeshCompression.High);
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

    static Mesh Combine(List<List<CombineInstance>> groups,bool simplified,List<Material> anatomyMaterials=null)
    {
        var temporary=new List<Mesh>();var combined=new List<CombineInstance>();
        try
        {
            for (int groupIndex = 0; groupIndex < groups.Count; groupIndex++)
            {
                var input=groups[groupIndex].ToArray();
                // The two surfaces of a very thin membrane can collapse into one.
                bool wingMembrane = anatomyMaterials != null && anatomyMaterials[groupIndex] &&
                    anatomyMaterials[groupIndex].name.Contains("WingMembrane", StringComparison.Ordinal);
                if(simplified && !wingMembrane)for(int i=0;i<input.Length;i++)
                {
                    var copy=input[i];var mesh=Simplify(copy.mesh,copy.subMeshIndex,anatomyMaterials != null);
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

    sealed class MeshIsland
    {
        public Bounds bounds;
        public int vertices;
        public Vector3 cell;
        public bool omit;
    }

    // FBX export joins many independent parts by material. Clustering the whole
    // group can erase a leg or weld it to the body. Find the original islands by
    // triangles and coincident vertices, including duplicate vertices at UV seams.
    static int[] FindIslands(Vector3[] vertices, int[] triangles, out Dictionary<int, MeshIsland> islands)
    {
        var parents = Enumerable.Repeat(-1, vertices.Length).ToArray();
        var atPosition = new Dictionary<Vector3, int>();
        foreach (int vertex in triangles)
        {
            if (parents[vertex] >= 0) continue;
            if (!atPosition.TryGetValue(vertices[vertex], out int same))
            {
                same = vertex;
                atPosition.Add(vertices[vertex], vertex);
            }
            parents[vertex] = same;
        }
        int Root(int vertex)
        {
            while (parents[vertex] != vertex)
            {
                parents[vertex] = parents[parents[vertex]];
                vertex = parents[vertex];
            }
            return vertex;
        }
        for (int i = 0; i < triangles.Length; i += 3)
        {
            int root = Root(triangles[i]);
            parents[Root(triangles[i + 1])] = root;
            parents[Root(triangles[i + 2])] = root;
        }
        islands = new Dictionary<int, MeshIsland>();
        for (int i = 0; i < vertices.Length; i++)
        {
            if (parents[i] < 0) continue;
            int root = parents[i] = Root(i);
            if (!islands.TryGetValue(root, out var island))
            {
                island = new MeshIsland {bounds = new Bounds(vertices[i], Vector3.zero)};
                islands.Add(root, island);
            }
            island.bounds.Encapsulate(vertices[i]);
            island.vertices++;
        }
        return parents;
    }

    static float LongestAxis(Vector3 size) => Mathf.Max(size.x, Mathf.Max(size.y, size.z));

    static Mesh Simplify(Mesh source,int submesh,bool preserveAnatomy)
    {
        var vertices=source.vertices;var normals=source.normals;var uv=source.uv;
        var original=source.GetTriangles(submesh);
        float extent=LongestAxis(source.bounds.size);
        float cell=Mathf.Max(extent/14f,.000001f);
        Dictionary<int, MeshIsland> islands = null;
        int[] islandForVertex = preserveAnatomy ? FindIslands(vertices, original, out islands) : null;
        if (islands != null)
        {
            // Remove isolated miniature details such as setae from the preview.
            // Keep small meshes like jointed legs intact and reduce larger shells locally.
            float detailCutoff = extent / 57f;
            bool hasLargerIsland = islands.Values.Any(island => LongestAxis(island.bounds.size) >= detailCutoff);
            foreach (var island in islands.Values)
            {
                var size = island.bounds.size;
                island.omit = hasLargerIsland && LongestAxis(size) < detailCutoff;
                float targetCell = LongestAxis(size) / 10f;
                island.cell = new Vector3(Mathf.Max(.000001f, Mathf.Min(targetCell, size.x / 5f)),
                    Mathf.Max(.000001f, Mathf.Min(targetCell, size.y / 5f)),
                    Mathf.Max(.000001f, Mathf.Min(targetCell, size.z / 5f)));
            }
        }
        var buckets=new Dictionary<(int island,Vector3Int cell),int>();var positions=new List<Vector3>();
        var ns=new List<Vector3>();var uvs=new List<Vector2>();var counts=new List<int>();
        var map=new int[vertices.Length];
        for(int i=0;i<vertices.Length;i++)
        {
            int islandIndex = 0;
            Vector3 point = vertices[i] / cell;
            if (islandForVertex != null)
            {
                islandIndex = islandForVertex[i];
                if (islandIndex < 0 || islands[islandIndex].omit) { map[i] = -1; continue; }
                var island = islands[islandIndex];
                if (island.vertices <= 120) point = new Vector3(i, 0, 0);
                else
                {
                    var local = vertices[i] - island.bounds.min;
                    point = new Vector3(local.x / island.cell.x, local.y / island.cell.y, local.z / island.cell.z);
                }
            }
            var key=(islandIndex,new Vector3Int(Mathf.RoundToInt(point.x),Mathf.RoundToInt(point.y),Mathf.RoundToInt(point.z)));
            if(!buckets.TryGetValue(key,out int index))
            {index=positions.Count;buckets[key]=index;positions.Add(Vector3.zero);ns.Add(Vector3.zero);uvs.Add(Vector2.zero);counts.Add(0);}
            map[i]=index;positions[index]+=vertices[i];ns[index]+=normals.Length>i?normals[i]:Vector3.up;
            uvs[index]+=uv.Length>i?uv[i]:Vector2.zero;counts[index]++;
        }
        for(int i=0;i<positions.Count;i++){positions[i]/=counts[i];ns[i]=ns[i].normalized;uvs[i]/=counts[i];}
        var triangles=new List<int>();
        for(int i=0;i<original.Length;i+=3)
        {int a=map[original[i]],b=map[original[i+1]],c=map[original[i+2]];if(a<0||b<0||c<0||a==b||b==c||a==c)continue;triangles.Add(a);triangles.Add(b);triangles.Add(c);}
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
