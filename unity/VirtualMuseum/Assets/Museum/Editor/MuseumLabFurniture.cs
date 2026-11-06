using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>Adds laboratory furniture to the existing room without rebuilding it.</summary>
public static class MuseumLabFurniture
{
    const string Root = "Assets/Museum/";
    const string GroupName = "Lab furnishings";
    const float WorkFloor = .022f;

    readonly struct Placement
    {
        public readonly string Model, Name;
        public readonly Vector3 Position;
        public readonly float Yaw;
        public readonly bool Seat;
        public Placement(string model, string name, Vector3 position, float yaw, bool seat = false)
        { Model = model; Name = name; Position = position; Yaw = yaw; Seat = seat; }
    }

    static readonly Placement[] Layout =
    {
        new("LabSwivelChair", "Swivel chair 01", new(-4.55f, WorkFloor, 3.35f), -86, true),
        new("LabSwivelChair", "Swivel chair 02", new(-4.55f, WorkFloor, 6.35f), -98, true),
        new("LabSwivelChair", "Swivel chair 03", new(-4.55f, WorkFloor, 9.35f), -81, true),
        new("LabRoundStool", "Round swivel stool 01", new(-4.65f, WorkFloor, 5.5f), 25, true),
        new("LabRoundStool", "Round swivel stool 02", new(-4.65f, WorkFloor, 8.5f), -20, true),
        new("LabDrawerCabinet", "Under-bench drawers 01", new(-5.35f, WorkFloor, 4.8f), 90),
        new("LabDrawerCabinet", "Under-bench drawers 02", new(-5.35f, WorkFloor, 7.8f), 90),
        new("LabDrawerCabinet", "Under-bench drawers 03", new(-5.35f, WorkFloor, 10.8f), 90),
        new("LabUtilityCart", "Laboratory trolley 01", new(-4.7f, WorkFloor, 1.65f), 90),
        new("LabUtilityCart", "Laboratory trolley 02", new(-4.7f, WorkFloor, 12.3f), 90),
        new("LabTallCabinet", "Storage cabinet 01", new(-3.8f, 0, 13.6f), 180),
        new("LabTallCabinet", "Storage cabinet 02", new(-2.5f, 0, 13.6f), 180)
    };

    [MenuItem("Museum/Add Laboratory Furniture")]
    public static void Add()
    {
        var scene = SceneManager.GetActiveScene();
        if (EditorApplication.isPlayingOrWillChangePlaymode || scene.isDirty ||
            scene.path != Root + "Scenes/MuseumV1.unity")
            throw new InvalidOperationException("Open the saved MuseumV1 scene and stop Play mode first.");
        if (scene.GetRootGameObjects().Any(o => o.name == GroupName))
            throw new InvalidOperationException("Lab furnishings already exist. Edit the existing group; no duplicates were added.");

        var models = Layout.Select(p => p.Model).Distinct().ToDictionary(n => n,
            n => AssetDatabase.LoadAssetAtPath<GameObject>(Root + "Models/" + n + ".fbx"));
        foreach (var entry in models)
            if (!entry.Value) throw new FileNotFoundException("Import the Blender model first: " + entry.Key);
        var palette = MakePalette();
        // Reject unknown finishes before touching the scene.
        foreach (var model in models.Values)
        foreach (var renderer in model.GetComponentsInChildren<Renderer>(true))
        foreach (var material in renderer.sharedMaterials)
            ResolveMaterial(material, palette);

        var group = new GameObject(GroupName);
        Undo.RegisterCreatedObjectUndo(group, "Add laboratory furniture");
        try
        {
            foreach (var item in Layout)
            {
                var obj = (GameObject)PrefabUtility.InstantiatePrefab(models[item.Model], scene);
                obj.name = item.Name;
                obj.transform.SetParent(group.transform, false);
                obj.transform.SetPositionAndRotation(item.Position, Quaternion.Euler(0, item.Yaw, 0));
                foreach (var renderer in obj.GetComponentsInChildren<Renderer>(true))
                {
                    renderer.sharedMaterials = renderer.sharedMaterials.Select(m => ResolveMaterial(m, palette)).ToArray();
                    PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
                }
                if (item.Seat)
                {
                    var collider = obj.AddComponent<CapsuleCollider>();
                    collider.radius = item.Model == "LabSwivelChair" ? .33f : .31f;
                    collider.height = item.Model == "LabSwivelChair" ? .97f : .64f;
                    collider.center = new Vector3(0, collider.height / 2, 0);
                }
                else
                {
                    var collider = obj.AddComponent<BoxCollider>();
                    var size = item.Model == "LabDrawerCabinet" ? new Vector3(.46f,.68f,.50f) :
                               item.Model == "LabUtilityCart" ? new Vector3(.58f,.80f,.42f) :
                               new Vector3(1.10f,1.85f,.46f);
                    collider.size = size;
                    collider.center = Vector3.up * size.y / 2;
                }
                PrefabUtility.RecordPrefabInstancePropertyModifications(obj.transform);
            }
            EditorSceneManager.MarkSceneDirty(scene);
            if (!EditorSceneManager.SaveScene(scene)) throw new IOException("Could not save the furnished room.");
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = group;
            Debug.Log("Museum: added 3 swivel chairs, 2 round stools, 3 drawer cabinets, 2 trolleys and 2 storage cabinets.");
        }
        catch
        {
            UnityEngine.Object.DestroyImmediate(group);
            throw;
        }
    }

    static Material ResolveMaterial(Material source, Dictionary<string, Material> palette)
    {
        string name = source ? source.name : "";
        foreach (var entry in palette)
            if (name.EndsWith(entry.Key, StringComparison.Ordinal)) return entry.Value;
        throw new InvalidOperationException("Unknown laboratory finish: " + name);
    }

    static Dictionary<string, Material> MakePalette()
    {
        string path = Root + "Materials/Lab";
        if (!AssetDatabase.IsValidFolder(path)) AssetDatabase.CreateFolder(Root + "Materials", "Lab");
        var result = new Dictionary<string, Material>();
        void Add(string name, Color color, float roughness, float metallic = 0)
        {
            string file = path + "/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(file);
            if (!material)
            {
                material = new Material(Shader.Find("Standard")) { name = name };
                AssetDatabase.CreateAsset(material, file);
            }
            material.SetColor("_Color", color);
            material.SetFloat("_Glossiness", 1 - roughness);
            material.SetFloat("_Metallic", metallic);
            EditorUtility.SetDirty(material);
            result[name] = material;
        }
        Add("Graphite vinyl", new Color(.055f,.062f,.064f), .54f);
        Add("Black polymer", new Color(.025f,.030f,.033f), .55f);
        Add("Brushed steel", new Color(.48f,.52f,.54f), .27f, .85f);
        Add("Rubber tyres", new Color(.014f,.017f,.019f), .82f);
        Add("Dark frame", new Color(.12f,.14f,.145f), .43f, .05f);
        Add("Powder coat", new Color(.72f,.75f,.72f), .42f);
        Add("Worktop laminate", new Color(.82f,.83f,.80f), .36f);
        Add("Label paper", new Color(.82f,.81f,.72f), .80f);
        return result;
    }
}
